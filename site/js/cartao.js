// Cartão-resumo da cidade desenhado em <canvas> (1080x1350) e opções de compartilhamento.

import { NOMES_ETAPA, NOMES_REDE, formatarNumero, formatarPct, ultimoValor, valorNoAno } from "./formato.js";

export const FORMATO_CARTAO = "png_1080x1350";
const L = 1080;
const A = 1350;
const M = 72; // margem
const FONTE = 'system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif';
const C = { fundo: "#f6f8fb", primaria: "#0f5e9c", texto: "#142033", suave: "#4d5b70", caixa: "#ffffff", borda: "#d5dde8" };

function retanguloArredondado(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

/** Quebra o texto em até `maxLinhas`, diminuindo a fonte se precisar. Retorna { linhas, tamanho }. */
function ajustarTexto(ctx, texto, larguraMax, tamanho, maxLinhas, peso = 800) {
  for (let t = tamanho; t >= 36; t -= 4) {
    ctx.font = `${peso} ${t}px ${FONTE}`;
    const palavras = texto.split(" ");
    const linhas = [];
    let atual = "";
    for (const p of palavras) {
      const teste = atual ? `${atual} ${p}` : p;
      if (ctx.measureText(teste).width <= larguraMax || !atual) atual = teste;
      else { linhas.push(atual); atual = p; }
    }
    linhas.push(atual);
    if (linhas.length <= maxLinhas && linhas.every((l) => ctx.measureText(l).width <= larguraMax)) return { linhas, tamanho: t };
  }
  return { linhas: [texto], tamanho: 36 };
}

/**
 * Resumo usado no cartão: aprovação mais recente por etapa (rede escolhida) e IDEB 2025 (rede pública).
 */
export function montarResumo({ municipio, dadosUf, referencias, rede }) {
  const anos = dadosUf.anos_rendimento;
  const refUf = referencias.uf[municipio.uf];
  const refBr = referencias.brasil;
  const etapas = ["ef_ai", "ef_af", "em"].map((etapa) => {
    const ultimo = ultimoValor(municipio.rendimento[rede][etapa].aprovacao, anos);
    const anosRef = referencias.anos_rendimento;
    const ideb = municipio.ideb[etapa];
    const anosIdebRef = referencias.anos_ideb[etapa];
    const ultimaEdicao = dadosUf.anos_ideb[etapa].at(-1);
    return {
      etapa,
      aprovacao: ultimo?.valor ?? null,
      ano: ultimo?.ano ?? null,
      aprovacaoUf: ultimo ? valorNoAno(refUf.rendimento[rede][etapa].aprovacao, anosRef, ultimo.ano) : null,
      aprovacaoBr: ultimo ? valorNoAno(refBr.rendimento[rede][etapa].aprovacao, anosRef, ultimo.ano) : null,
      ideb: ideb.status === "divulgado" ? ideb.valores.at(-1) : null,
      edicaoIdeb: ultimaEdicao,
      idebUf: valorNoAno(refUf.ideb[etapa].valores, anosIdebRef, ultimaEdicao),
      idebBr: valorNoAno(refBr.ideb[etapa].valores, anosIdebRef, ultimaEdicao),
    };
  });
  return { nome: municipio.nome, uf: municipio.uf, nomeUf: dadosUf.nome, rede, etapas };
}

/** Desenha o cartão e devolve um Blob PNG. */
export async function gerarCartao(resumo, urlSite) {
  const canvas = document.createElement("canvas");
  canvas.width = L;
  canvas.height = A;
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = C.fundo;
  ctx.fillRect(0, 0, L, A);

  // Faixa superior
  ctx.fillStyle = C.primaria;
  ctx.fillRect(0, 0, L, 150);
  ctx.fillStyle = "#fff";
  ctx.font = `800 46px ${FONTE}`;
  ctx.textBaseline = "middle";
  ctx.fillText("EduTrackBrasil", M, 75);
  ctx.font = `500 26px ${FONTE}`;
  ctx.textAlign = "right";
  ctx.fillText("Educação em números · INEP", L - M, 77);
  ctx.textAlign = "left";
  ctx.textBaseline = "alphabetic";

  // Nome da cidade
  let y = 250;
  const titulo = ajustarTexto(ctx, `${resumo.nome} – ${resumo.uf}`, L - 2 * M, 76, 2);
  ctx.fillStyle = C.texto;
  ctx.font = `800 ${titulo.tamanho}px ${FONTE}`;
  titulo.linhas.forEach((linha, i) => {
    if (i > 0) y += titulo.tamanho * 1.1;
    ctx.fillText(linha, M, y);
  });
  y += 56;
  ctx.fillStyle = C.suave;
  ctx.font = `500 30px ${FONTE}`;
  ctx.fillText(resumo.nomeUf, M, y);
  y += 66;

  // Aprovação por etapa
  const anoRend = resumo.etapas.find((e) => e.ano)?.ano;
  ctx.fillStyle = C.texto;
  ctx.font = `700 34px ${FONTE}`;
  ctx.fillText(`Taxa de aprovação${anoRend ? ` (${anoRend})` : ""}`, M, y);
  ctx.fillStyle = C.suave;
  ctx.font = `500 24px ${FONTE}`;
  ctx.fillText(NOMES_REDE[resumo.rede], M, y + 36);
  y += 64;
  for (const e of resumo.etapas) {
    retanguloArredondado(ctx, M, y, L - 2 * M, 104, 20);
    ctx.fillStyle = C.caixa;
    ctx.fill();
    ctx.strokeStyle = C.borda;
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = C.texto;
    ctx.font = `700 32px ${FONTE}`;
    ctx.fillText(NOMES_ETAPA[e.etapa], M + 32, y + 46);
    ctx.fillStyle = C.suave;
    ctx.font = `500 24px ${FONTE}`;
    const refs = e.aprovacao == null ? "sem dado no período"
      : `${resumo.uf} ${formatarPct(e.aprovacaoUf)} · Brasil ${formatarPct(e.aprovacaoBr)}`;
    ctx.fillText(refs, M + 32, y + 82);
    ctx.fillStyle = C.primaria;
    ctx.font = `800 64px ${FONTE}`;
    ctx.textAlign = "right";
    ctx.fillText(formatarPct(e.aprovacao), L - M - 32, y + 74);
    ctx.textAlign = "left";
    y += 120;
  }

  // IDEB
  y += 56;
  const edicao = resumo.etapas[0].edicaoIdeb;
  ctx.fillStyle = C.texto;
  ctx.font = `700 34px ${FONTE}`;
  ctx.fillText(`IDEB ${edicao}`, M, y);
  ctx.fillStyle = C.suave;
  ctx.font = `500 24px ${FONTE}`;
  ctx.fillText("rede pública · escala de 0 a 10", M, y + 36);
  y += 64;
  const gap = 24;
  const largura = (L - 2 * M - 2 * gap) / 3;
  resumo.etapas.forEach((e, i) => {
    const x = M + i * (largura + gap);
    retanguloArredondado(ctx, x, y, largura, 180, 20);
    ctx.fillStyle = C.caixa;
    ctx.fill();
    ctx.strokeStyle = C.borda;
    ctx.stroke();
    ctx.fillStyle = C.texto;
    ctx.font = `700 26px ${FONTE}`;
    ctx.fillText(NOMES_ETAPA[e.etapa], x + 24, y + 44);
    if (e.ideb != null) {
      ctx.fillStyle = C.primaria;
      ctx.font = `800 68px ${FONTE}`;
      ctx.fillText(formatarNumero(e.ideb), x + 24, y + 116);
    } else {
      ctx.fillStyle = C.suave;
      ctx.font = `600 26px ${FONTE}`;
      ctx.fillText("não divulgado", x + 24, y + 96);
      ctx.fillText("pelo INEP", x + 24, y + 128);
    }
    ctx.fillStyle = C.suave;
    ctx.font = `500 22px ${FONTE}`;
    ctx.fillText(`${resumo.uf} ${formatarNumero(e.idebUf)} · BR ${formatarNumero(e.idebBr)}`, x + 24, y + 160);
  });

  // Rodapé
  ctx.fillStyle = C.suave;
  ctx.font = `500 24px ${FONTE}`;
  ctx.fillText("Fonte: INEP – Censo Escolar (taxas de rendimento) e Ideb 2025.", M, A - 100);
  ctx.fillText("No ensino médio, o IDEB do estado é da rede estadual.", M, A - 68);
  ctx.fillStyle = C.primaria;
  ctx.font = `700 26px ${FONTE}`;
  ctx.fillText(urlSite.replace(/^https?:\/\//, ""), M, A - 30);

  return new Promise((resolve, reject) => canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("Falha ao gerar a imagem"))), "image/png"));
}

/** Copia texto para a área de transferência, com plano B para navegadores antigos. */
export async function copiarTexto(texto) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(texto);
    return;
  }
  const area = document.createElement("textarea");
  area.value = texto;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.appendChild(area);
  area.select();
  const ok = document.execCommand("copy");
  area.remove();
  if (!ok) throw new Error("cópia não suportada");
}
