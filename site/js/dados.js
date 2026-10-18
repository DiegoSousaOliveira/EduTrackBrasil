// Carregamento dos JSONs gerados pelo pipeline. Caminhos relativos: o site roda em subpasta (GitHub Pages).

const cacheUf = new Map();

async function carregarJSON(caminho) {
  const resposta = await fetch(caminho);
  if (!resposta.ok) throw new Error(`Não foi possível carregar ${caminho} (HTTP ${resposta.status})`);
  return resposta.json();
}

export const carregarMunicipios = () => carregarJSON("data/municipios.json");
export const carregarReferencias = () => carregarJSON("data/referencias.json");

/** Baixa só o arquivo do estado escolhido, uma única vez por sessão. */
export function carregarUf(uf) {
  if (!cacheUf.has(uf)) {
    const promessa = carregarJSON(`data/uf/${uf}.json`).catch((erro) => {
      cacheUf.delete(uf); // permite tentar de novo
      throw erro;
    });
    cacheUf.set(uf, promessa);
  }
  return cacheUf.get(uf);
}
