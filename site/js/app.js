// EduTrackBrasil – orquestra a página: busca, estado da tela, renderização e compartilhamento.

import { buscar, criarIndice, iniciarBusca } from "./busca.js";
import { FORMATO_CARTAO, copiarTexto, gerarCartao, montarResumo } from "./cartao.js";
import { carregarMunicipios, carregarReferencias, carregarUf } from "./dados.js";
import {
  ARTIGO_TAXA, NOMES_ETAPA, NOMES_ETAPA_LONGO, NOMES_REDE, NOMES_TAXA, comparar, formatarNumero, formatarPct,
  normalizar, ultimoValor, valorNoAno,
} from "./formato.js";
import { desenharLinha, graficosDisponiveis, tabela } from "./grafico.js";
import { track } from "./track.js";

const $ = (seletor) => document.querySelector(seletor);

const estado = {
  indice: [],
  porId: new Map(),
  referencias: null,
  municipio: null, // { id, nome, uf, rendimento, ideb }
  dadosUf: null,
  etapa: "ef_ai",
  rede: "total",
  indicador: "aprovacao",
  comparar: true,
  cartao: null, // { blob, arquivo, url }
};

// ---------- Inicialização ----------

async function iniciar() {
  try {
    const [municipios, referencias] = await Promise.all([carregarMunicipios(), carregarReferencias()]);
    estado.indice = criarIndice(municipios);
    estado.porId = new Map(municipios.map((m) => [m.id, m]));
    estado.referencias = referencias;
  } catch (erro) {
    mostrarErro("Não foi possível carregar a lista de municípios. Verifique sua conexão e recarregue a página.");
    console.error(erro);
    return;
  }

  const campo = $("#campo-busca");
  campo.disabled = false;
  $("#atalhos").hidden = false;
  iniciarBusca({
    campo, lista: $("#lista-sugestoes"), status: $("#status-busca"), indice: estado.indice,
    // search: só quando a busca é confirmada (Enter ou escolha de sugestão), nunca a cada tecla
    aoBuscar: ({ termo, total, metodo }) =>
      track("search", { search_term: normalizar(termo).slice(0, 100), results_count: total, search_method: metodo }),
    aoEscolher: (m) => selecionar(m.id, { origem: "busca" }),
  });

  document.querySelectorAll(".chip[data-id]").forEach((botao) =>
    botao.addEventListener("click", () => {
      const m = estado.porId.get(botao.dataset.id);
      if (!m) return;
      campo.value = `${m.nome} – ${m.uf}`;
      selecionar(m.id, { origem: "atalho" });
    }));

  ligarFiltro("etapa", (v) => { estado.etapa = v; renderizarTudo(); });
  ligarFiltro("rede", (v) => { estado.rede = v; renderizarRendimento(); });
  ligarFiltro("indicador", (v) => { estado.indicador = v; renderizarGraficoRendimento(); });
  $("#comparar").addEventListener("change", (ev) => {
    estado.comparar = ev.target.checked;
    track("compare_toggle", { comparacao: estado.comparar ? "ativada" : "desativada" });
    renderizarGraficoRendimento();
    renderizarIdeb();
  });

  $("#gerar-cartao").addEventListener("click", abrirCartao);
  ligarDialogo();
  observarGraficos();

  // Tema claro/escuro mudou: redesenha os gráficos com as novas cores
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => estado.municipio && renderizarTudo());

  // Link compartilhado (?m=codigo) e botão voltar do navegador
  const abrirDaUrl = () => {
    const id = new URLSearchParams(location.search).get("m");
    if (id && estado.porId.has(id)) {
      const m = estado.porId.get(id);
      campo.value = `${m.nome} – ${m.uf}`;
      selecionar(id, { atualizarUrl: false });
    }
  };
  window.addEventListener("popstate", abrirDaUrl);
  abrirDaUrl();
}

function ligarFiltro(nome, aoMudar) {
  document.querySelectorAll(`input[name="${nome}"]`).forEach((input) =>
    input.addEventListener("change", () => {
      if (!input.checked) return;
      track("change_filter", { filter_name: nome, filter_value: input.value });
      aoMudar(input.value);
    }));
}

function mostrarErro(mensagem) {
  const aviso = $("#erro-carga");
  aviso.textContent = mensagem;
  aviso.hidden = !mensagem;
}

// ---------- Seleção de município ----------

/**
 * Abre um município. `origem`: "busca" ou "atalho" (escolha ativa -> select_content)
 * ou "url" (link compartilhado / botão voltar -> sem select_content).
 */
async function selecionar(id, { atualizarUrl = true, origem = "url" } = {}) {
  const basico = estado.porId.get(id);
  mostrarErro("");
  let dadosUf;
  try {
    dadosUf = await carregarUf(basico.uf);
  } catch (erro) {
    mostrarErro(`Não foi possível carregar os dados de ${basico.uf}. Tente novamente.`);
    console.error(erro);
    return;
  }
  estado.dadosUf = dadosUf;
  estado.municipio = { ...basico, ...dadosUf.municipios[id] };
  if (atualizarUrl) {
    const params = new URLSearchParams(location.search); // preserva ?debug_tracking
    params.set("m", id);
    history.pushState({ m: id }, "", `?${params}`);
  }
  document.title = `${basico.nome} – ${basico.uf} | EduTrackBrasil`;
  if (origem !== "url") {
    track("select_content", { content_type: "municipio", content_id: id, municipio_nome: basico.nome });
  }

  $("#painel").hidden = false;
  renderizarTudo();
  reiniciarObservacaoGraficos();
  $("#nome-municipio").focus({ preventScroll: true });
  $("#nome-municipio").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
}

// ---------- Renderização ----------

function renderizarTudo() {
  if (!estado.municipio) return;
  const m = estado.municipio;
  $("#nome-municipio").textContent = `${m.nome} – ${m.uf}`;
  $("#info-municipio").textContent = `${estado.dadosUf.nome} · código IBGE ${m.id}`;
  renderizarRendimento();
  renderizarIdeb();
}

function renderizarRendimento() {
  renderizarCartoes();
  renderizarGraficoRendimento();
}

const refsDoMunicipio = () => ({ uf: estado.referencias.uf[estado.municipio.uf], br: estado.referencias.brasil });

function renderizarCartoes() {
  const { municipio: m, dadosUf, etapa, rede, referencias } = estado;
  const anos = dadosUf.anos_rendimento;
  const serie = m.rendimento[rede][etapa];
  const ultimo = ultimoValor(serie.aprovacao, anos);
  const { uf, br } = refsDoMunicipio();
  const container = $("#cartoes");

  $("#contexto-indicadores").textContent =
    `${NOMES_ETAPA_LONGO[etapa]} · ${NOMES_REDE[rede]}. Comparação com as médias oficiais do estado e do Brasil na mesma rede.`;

  if (!ultimo) {
    avisarIndisponivel("rendimento", etapa, "sem_dados");
    $("#ano-indicadores").textContent = "";
    container.innerHTML = `<div class="cartao cartao--indisponivel"><p class="cartao__valor">Sem dados de rendimento para esta etapa
      e rede no período 2007–2025.</p><p class="nota">Isso costuma acontecer quando o município não tem matrículas nessa etapa.</p></div>`;
    return;
  }
  $("#ano-indicadores").textContent = String(ultimo.ano);
  container.innerHTML = ["aprovacao", "reprovacao", "abandono"].map((taxa) => {
    const valor = serie[taxa][ultimo.indice];
    const vUf = valorNoAno(uf.rendimento[rede][etapa][taxa], referencias.anos_rendimento, ultimo.ano);
    const vBr = valorNoAno(br.rendimento[rede][etapa][taxa], referencias.anos_rendimento, ultimo.ano);
    const linha = (rotulo, v) => {
      const c = comparar(valor, v, taxa);
      return `<li><span class="rotulo-ref">${rotulo} ${formatarPct(v)}</span>
        <span class="valor-ref ${c.classe}">${c.texto}</span></li>`;
    };
    return `<article class="cartao">
      <h4 class="cartao__titulo">${NOMES_TAXA[taxa]}</h4>
      <p class="cartao__valor">${formatarPct(valor)}</p>
      <ul class="cartao__comparacao" aria-label="Comparação">
        ${linha(`Estado (${m.uf})`, vUf)}
        ${linha("Brasil", vBr)}
      </ul>
    </article>`;
  }).join("");
}

function renderizarGraficoRendimento() {
  const { municipio: m, dadosUf, etapa, rede, indicador, referencias } = estado;
  const anos = dadosUf.anos_rendimento;
  const { uf, br } = refsDoMunicipio();
  const alinhar = (serie) => anos.map((a) => valorNoAno(serie, referencias.anos_rendimento, a));
  const series = [{ rotulo: m.nome, valores: m.rendimento[rede][etapa][indicador], tipo: "municipio" }];
  if (estado.comparar) {
    series.push({ rotulo: `Estado (${m.uf})`, valores: alinhar(uf.rendimento[rede][etapa][indicador]), tipo: "uf" });
    series.push({ rotulo: "Brasil", valores: alinhar(br.rendimento[rede][etapa][indicador]), tipo: "brasil" });
  }
  const nomeTaxa = NOMES_TAXA[indicador].toLowerCase();
  $("#titulo-evolucao").textContent = `Evolução ${ARTIGO_TAXA[indicador]} ${nomeTaxa}, ${anos[0]}–${anos.at(-1)}`;
  desenharLinha($("#grafico-rendimento"), {
    anos, series, sufixo: "%", comecarEmZero: indicador !== "aprovacao", anotar2020: true,
    descricao: `Gráfico de linha: taxa de ${nomeTaxa} em ${m.nome}, ${NOMES_ETAPA[etapa].toLowerCase()}, ${NOMES_REDE[rede]}, de ${anos[0]} a ${anos.at(-1)}. Os mesmos dados estão na tabela abaixo.`,
  });
  tabela($("#tabela-rendimento"), { anos, series, sufixo: "%" });
  avisarSemGraficos();
}

function renderizarIdeb() {
  const { municipio: m, dadosUf, etapa, referencias } = estado;
  const { uf, br } = refsDoMunicipio();

  $("#cartoes-ideb").innerHTML = ["ef_ai", "ef_af", "em"].map((e) => {
    const ideb = m.ideb[e];
    const anosMun = dadosUf.anos_ideb[e];
    const edicao = anosMun.at(-1);
    const vUf = valorNoAno(uf.ideb[e].valores, referencias.anos_ideb[e], edicao);
    const vBr = valorNoAno(br.ideb[e].valores, referencias.anos_ideb[e], edicao);
    const redeUf = uf.ideb[e].rede === "estadual" ? " (rede estadual)" : "";
    const selecionada = e === etapa ? ' aria-current="true"' : "";
    if (ideb.status !== "divulgado") {
      avisarIndisponivel("ideb", e, ideb.status);
      const anterior = ultimoValor(ideb.valores, anosMun);
      const motivo = ideb.status === "sem_registro"
        ? "O município não aparece na planilha do INEP para esta etapa."
        : "O município está na planilha do INEP, mas sem resultado nesta edição (por exemplo, quando a participação no Saeb fica abaixo do mínimo).";
      return `<article class="cartao cartao--indisponivel"${selecionada}>
        <h4 class="cartao__titulo">${NOMES_ETAPA[e]} · ${edicao}</h4>
        <p class="cartao__valor">IDEB não divulgado pelo INEP</p>
        <p class="nota">${motivo}${anterior ? ` Último IDEB divulgado: <strong>${formatarNumero(anterior.valor)}</strong> (${anterior.ano}).` : ""}</p>
        <ul class="cartao__comparacao">
          <li><span class="rotulo-ref">Estado (${m.uf})${redeUf}</span><span class="valor-ref">${formatarNumero(vUf)}</span></li>
          <li><span class="rotulo-ref">Brasil</span><span class="valor-ref">${formatarNumero(vBr)}</span></li>
        </ul>
      </article>`;
    }
    const valor = ideb.valores.at(-1);
    const linha = (rotulo, v) => {
      const c = comparar(valor, v, "ideb", "pts");
      return `<li><span class="rotulo-ref">${rotulo} ${formatarNumero(v)}</span><span class="valor-ref ${c.classe}">${c.texto}</span></li>`;
    };
    return `<article class="cartao"${selecionada}>
      <h4 class="cartao__titulo">${NOMES_ETAPA[e]} · ${edicao}</h4>
      <p class="cartao__valor">${formatarNumero(valor)} <small>de 10</small></p>
      <ul class="cartao__comparacao" aria-label="Comparação">
        ${linha(`Estado (${m.uf})${redeUf}`, vUf)}
        ${linha("Brasil", vBr)}
      </ul>
    </article>`;
  }).join("");

  // Gráfico do IDEB da etapa selecionada; eixo com as edições das referências (o EM municipal só começa em 2017)
  const anos = referencias.anos_ideb[etapa];
  const anosMun = dadosUf.anos_ideb[etapa];
  const series = [{ rotulo: m.nome, valores: anos.map((a) => valorNoAno(m.ideb[etapa].valores, anosMun, a)), tipo: "municipio" }];
  if (estado.comparar) {
    const redeUf = uf.ideb[etapa].rede === "estadual" ? " – rede estadual" : "";
    series.push({ rotulo: `Estado (${m.uf})${redeUf}`, valores: uf.ideb[etapa].valores, tipo: "uf" });
    series.push({ rotulo: "Brasil", valores: br.ideb[etapa].valores, tipo: "brasil" });
  }
  desenharLinha($("#grafico-ideb"), {
    anos, series, comecarEmZero: true, maximo: 10,
    descricao: `Gráfico de linha: IDEB de ${m.nome}, ${NOMES_ETAPA[etapa].toLowerCase()}, rede pública, de ${anos[0]} a ${anos.at(-1)}. Os mesmos dados estão na tabela abaixo.`,
  });
  $("#legenda-ideb").textContent = `${NOMES_ETAPA_LONGO[etapa]}, rede pública.` +
    (etapa === "em" ? " Por município, o INEP só divulga o IDEB do ensino médio a partir de 2017." : "") +
    " Edições sem IDEB divulgado aparecem como lacuna.";
  tabela($("#tabela-ideb"), { anos, series });
  avisarSemGraficos();
}

function avisarSemGraficos() {
  if (graficosDisponiveis()) return;
  document.querySelectorAll(".tabela-dados").forEach((d) => { d.open = true; });
}

// ---------- Tracking: view_chart e data_unavailable ----------

const indisponiveisAvisados = new Set();

/** data_unavailable uma vez por município + indicador + etapa + motivo (re-render por filtro não repete). */
function avisarIndisponivel(indicador, etapa, motivo) {
  const chave = `${estado.municipio.id}|${indicador}|${etapa}|${motivo}`;
  if (indisponiveisAvisados.has(chave)) return;
  indisponiveisAvisados.add(chave);
  track("data_unavailable", { indicador, etapa, motivo });
}

const graficosVistos = new Set();
let observador = null;
const areasDeGrafico = () => [...document.querySelectorAll("figure[data-chart-id] .grafico__area")];

/** view_chart quando ≥ 50% da área do gráfico fica visível; uma vez por gráfico e por município. */
function observarGraficos() {
  if (!("IntersectionObserver" in window)) return;
  observador = new IntersectionObserver((entradas) => {
    for (const entrada of entradas) {
      // isIntersecting é true com qualquer pedaço visível (inclusive na checagem inicial): exige os 50%
      if (entrada.intersectionRatio < 0.5 || !estado.municipio) continue;
      const chartId = entrada.target.closest("figure").dataset.chartId;
      if (graficosVistos.has(chartId)) continue;
      graficosVistos.add(chartId);
      track("view_chart", {
        chart_id: chartId,
        indicador: chartId === "ideb" ? "ideb" : estado.indicador,
        etapa: estado.etapa,
        municipio_id: estado.municipio.id,
      });
    }
  }, { threshold: 0.5 });
  areasDeGrafico().forEach((area) => observador.observe(area));
}

/** Novo município: libera um novo view_chart por gráfico (re-observar dispara a checagem inicial). */
function reiniciarObservacaoGraficos() {
  if (!observador) return;
  graficosVistos.clear();
  areasDeGrafico().forEach((area) => {
    observador.unobserve(area);
    observador.observe(area);
  });
}

// ---------- Cartão e compartilhamento ----------

const urlDoMunicipio = (id) => `${location.origin}${location.pathname}?m=${id}`;

async function abrirCartao() {
  const botao = $("#gerar-cartao");
  botao.disabled = true;
  botao.textContent = "Gerando…";
  try {
    const { municipio: m } = estado;
    const resumo = montarResumo({ municipio: m, dadosUf: estado.dadosUf, referencias: estado.referencias, rede: estado.rede });
    const url = urlDoMunicipio(m.id);
    const blob = await gerarCartao(resumo, `${location.host}${location.pathname}`);
    const nomeArquivo = `edutrackbrasil-${m.id}.png`;
    if (estado.cartao?.objectUrl) URL.revokeObjectURL(estado.cartao.objectUrl);
    const objectUrl = URL.createObjectURL(blob);
    const arquivo = new File([blob], nomeArquivo, { type: "image/png" });
    const texto = `Veja como está a educação em ${m.nome} – ${m.uf} (dados do INEP):`;
    estado.cartao = { blob, arquivo, url, objectUrl, texto, formato: FORMATO_CARTAO };

    const previa = $("#previa-cartao");
    previa.src = objectUrl;
    previa.alt = `Cartão-resumo de ${m.nome} – ${m.uf} com taxas de aprovação e IDEB.`;
    $("#baixar").href = objectUrl;
    $("#baixar").download = nomeArquivo;
    $("#whatsapp").href = `https://wa.me/?text=${encodeURIComponent(`${texto} ${url}`)}`;
    $("#compartilhar").hidden = !(navigator.canShare && navigator.canShare({ files: [arquivo] }));
    $("#status-compartilhar").textContent = "";
    $("#dialogo-cartao").showModal();
    track("generate_card", { municipio_id: m.id, card_format: FORMATO_CARTAO });
  } catch (erro) {
    console.error(erro);
    mostrarErro("Não foi possível gerar o cartão neste navegador.");
  } finally {
    botao.disabled = false;
    botao.textContent = "Gerar cartão";
  }
}

function ligarDialogo() {
  const dialogo = $("#dialogo-cartao");
  const status = $("#status-compartilhar");
  const compartilhou = (method) =>
    track("share", { method, content_type: "cartao", item_id: estado.municipio.id });
  $("#fechar-cartao").addEventListener("click", () => dialogo.close());
  dialogo.addEventListener("click", (ev) => { if (ev.target === dialogo) dialogo.close(); }); // clique fora

  $("#compartilhar").addEventListener("click", async () => {
    const { arquivo, texto, url } = estado.cartao;
    try {
      await navigator.share({ files: [arquivo], title: "EduTrackBrasil", text: `${texto} ${url}` });
      compartilhou("web_share"); // só depois de concluir: cancelar o menu não conta
      status.textContent = "Compartilhado!";
    } catch (erro) {
      if (erro.name !== "AbortError") status.textContent = "Não deu para compartilhar. Tente baixar a imagem.";
    }
  });

  $("#whatsapp").addEventListener("click", () => compartilhou("whatsapp"));
  $("#baixar").addEventListener("click", () => {
    compartilhou("download");
    status.textContent = "Imagem baixada.";
  });

  $("#copiar-link").addEventListener("click", async () => {
    try {
      await copiarTexto(estado.cartao.url);
      compartilhou("copy_link");
      status.textContent = "Link copiado!";
    } catch {
      status.textContent = `Copie o link: ${estado.cartao.url}`;
    }
  });
}

iniciar();

// Exposto só para testes manuais no console (ex.: EduTrack.buscar("teresina"))
window.EduTrack = { estado, buscar: (termo) => buscar(estado.indice, termo) };
