// Rótulos e formatação em português do Brasil.

export const NOMES_ETAPA = { ef_ai: "Anos iniciais", ef_af: "Anos finais", em: "Ensino médio" };
export const NOMES_ETAPA_LONGO = {
  ef_ai: "Ensino fundamental – anos iniciais (1º ao 5º ano)",
  ef_af: "Ensino fundamental – anos finais (6º ao 9º ano)",
  em: "Ensino médio",
};
export const NOMES_TAXA = { aprovacao: "Aprovação", reprovacao: "Reprovação", abandono: "Abandono" };
export const ARTIGO_TAXA = { aprovacao: "da", reprovacao: "da", abandono: "do" };
export const NOMES_REDE = { total: "todas as redes", publica: "rede pública", estadual: "rede estadual" };
// Para aprovação, mais alto é melhor; para reprovação e abandono, mais baixo é melhor.
export const MAIOR_E_MELHOR = { aprovacao: true, reprovacao: false, abandono: false };

const umaCasa = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

export const formatarNumero = (v) => (v == null ? "–" : umaCasa.format(v));
export const formatarPct = (v) => (v == null ? "–" : `${umaCasa.format(v)}%`);

/** Mesma regra do pipeline (pipeline/extract.py: normalizar): sem acento, minúsculas, espaços simples. */
export function normalizar(texto) {
  return texto
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^\x00-\x7f]/g, "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

/** Último valor não nulo de uma série alinhada com `anos`: { valor, ano, indice } ou null. */
export function ultimoValor(serie, anos) {
  for (let i = serie.length - 1; i >= 0; i--) {
    if (serie[i] != null) return { valor: serie[i], ano: anos[i], indice: i };
  }
  return null;
}

/** Valor de uma série no ano pedido (as séries de referência podem ter outra lista de anos). */
export function valorNoAno(serie, anos, ano) {
  const i = anos.indexOf(ano);
  return i < 0 ? null : serie[i];
}

/** Comparação município x referência: texto e se é melhor ou pior. */
export function comparar(valor, referencia, taxa, unidade = "p.p.") {
  if (valor == null || referencia == null) return { texto: "sem dado", classe: "" };
  const dif = Math.round((valor - referencia) * 10) / 10;
  if (Math.abs(dif) < 0.05) return { texto: "igual", classe: "" };
  const acima = dif > 0;
  const melhor = MAIOR_E_MELHOR[taxa] === undefined ? acima : acima === MAIOR_E_MELHOR[taxa];
  return {
    texto: `${formatarNumero(Math.abs(dif))} ${unidade} ${acima ? "acima" : "abaixo"}`,
    classe: melhor ? "melhor" : "pior",
  };
}

export function escaparHtml(texto) {
  return String(texto).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}
