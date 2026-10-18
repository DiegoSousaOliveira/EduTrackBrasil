// Busca com autocomplete (padrão ARIA "combobox" + "listbox").
// Ignora acentos, maiúsculas e pontuação; aceita "teresina pi" ou "Teresina - PI".

import { escaparHtml, normalizar } from "./formato.js";

const MAX_SUGESTOES = 8;
const SIGLAS = new Set("AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split(" "));

/** Chave de comparação: normalizado e com hífen/apóstrofo/barra virando espaço ("olho-d'agua" -> "olho d agua"). */
const chave = (texto) => normalizar(texto).replace(/[^a-z0-9]+/g, " ").trim();

export function criarIndice(municipios) {
  return municipios.map((m) => ({ ...m, chave: chave(m.busca) }));
}

/** Retorna { resultados, total } ordenados: igual > começa com > palavra começa com > contém. */
export function buscar(indice, termo) {
  let q = chave(termo);
  if (q.length < 2) return { resultados: [], total: 0 };
  let uf = null;
  const partes = q.split(" ");
  const ultima = partes.at(-1).toUpperCase();
  if (partes.length > 1 && SIGLAS.has(ultima)) {
    uf = ultima;
    q = partes.slice(0, -1).join(" ");
  }
  const encontrados = [];
  for (const m of indice) {
    if (uf && m.uf !== uf) continue;
    let pontos;
    if (m.chave === q) pontos = 0;
    else if (m.chave.startsWith(q)) pontos = 1;
    else if (m.chave.includes(` ${q}`)) pontos = 2;
    else if (m.chave.includes(q)) pontos = 3;
    else continue;
    encontrados.push({ m, pontos });
  }
  encontrados.sort((a, b) => a.pontos - b.pontos || a.m.chave.length - b.m.chave.length || a.m.chave.localeCompare(b.m.chave));
  return { resultados: encontrados.slice(0, MAX_SUGESTOES).map((e) => e.m), total: encontrados.length };
}

/**
 * Liga a busca aos elementos da página.
 * aoBuscar({ termo, total, metodo }) é chamado quando a pessoa confirma uma busca;
 * aoEscolher(municipio, { metodo, termo }) quando um município é escolhido.
 */
export function iniciarBusca({ campo, lista, status, indice, aoBuscar, aoEscolher }) {
  let atuais = [];
  let ativo = -1;
  let total = 0;

  function fechar() {
    lista.hidden = true;
    campo.setAttribute("aria-expanded", "false");
    campo.removeAttribute("aria-activedescendant");
    ativo = -1;
  }

  function marcarAtivo(i) {
    ativo = i;
    [...lista.children].forEach((li, j) => li.setAttribute("aria-selected", String(j === i)));
    if (i >= 0 && lista.children[i]) {
      campo.setAttribute("aria-activedescendant", lista.children[i].id);
      lista.children[i].scrollIntoView({ block: "nearest" });
    } else {
      campo.removeAttribute("aria-activedescendant");
    }
  }

  function atualizar() {
    ({ resultados: atuais, total } = buscar(indice, campo.value));
    if (chave(campo.value).length < 2) {
      fechar();
      status.textContent = "";
      return;
    }
    if (atuais.length === 0) {
      lista.innerHTML = '<li class="vazio" role="option" aria-disabled="true" id="sugestao-vazia">Nenhum município encontrado</li>';
    } else {
      lista.innerHTML = atuais
        .map((m, i) => `<li role="option" id="sugestao-${i}" data-id="${m.id}" aria-selected="false">
            <span>${escaparHtml(m.nome)}</span><span class="uf">${m.uf}</span></li>`)
        .join("");
    }
    lista.hidden = false;
    campo.setAttribute("aria-expanded", "true");
    ativo = -1;
    status.textContent = total === 0 ? "Nenhum município encontrado" :
      `${total} ${total === 1 ? "município encontrado" : "municípios encontrados"}${total > atuais.length ? `, mostrando ${atuais.length}` : ""}`;
  }

  function escolher(m, metodo) {
    const termo = campo.value;
    aoBuscar?.({ termo, total, metodo });
    campo.value = `${m.nome} – ${m.uf}`;
    fechar();
    aoEscolher(m, { metodo, termo });
  }

  let espera;
  campo.addEventListener("input", () => {
    clearTimeout(espera);
    espera = setTimeout(atualizar, 80);
  });

  campo.addEventListener("keydown", (ev) => {
    const aberto = !lista.hidden && atuais.length > 0;
    if (ev.key === "ArrowDown" && aberto) {
      ev.preventDefault();
      marcarAtivo((ativo + 1) % atuais.length);
    } else if (ev.key === "ArrowUp" && aberto) {
      ev.preventDefault();
      marcarAtivo(ativo <= 0 ? atuais.length - 1 : ativo - 1);
    } else if (ev.key === "Escape") {
      fechar();
    }
  });

  // Enter: escolhe a sugestão destacada (autocomplete) ou a primeira (busca digitada)
  campo.form.addEventListener("submit", (ev) => {
    ev.preventDefault();
    clearTimeout(espera);
    if (ativo >= 0 && atuais[ativo]) return escolher(atuais[ativo], "autocomplete");
    atualizar();
    if (atuais.length > 0) return escolher(atuais[0], "digitado");
    if (chave(campo.value).length >= 2) aoBuscar?.({ termo: campo.value, total: 0, metodo: "digitado" });
  });

  // mousedown (e não click) para escolher antes de o campo perder o foco
  lista.addEventListener("mousedown", (ev) => {
    const li = ev.target.closest("li[data-id]");
    if (!li) return;
    ev.preventDefault();
    escolher(atuais.find((m) => m.id === li.dataset.id), "autocomplete");
  });

  campo.addEventListener("blur", () => setTimeout(fechar, 120));
  campo.addEventListener("focus", () => {
    if (chave(campo.value).length >= 2 && !campo.value.includes("–")) atualizar();
  });
}
