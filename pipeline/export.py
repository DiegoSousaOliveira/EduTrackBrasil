"""Gera os JSONs estáticos que o site consome (site/data/).

- municipios.json: lista leve para a busca (código, nome, UF, nome normalizado).
- uf/XX.json: dados completos dos municípios de um estado (o site baixa só o estado escolhido).
- referencias.json: médias oficiais de cada UF e do Brasil.

As séries são listas alinhadas com `anos_rendimento` / `anos_ideb`; ano sem dado = null
(o gráfico mostra lacuna, nunca zero).
"""
import json
import math
from pathlib import Path

import pandas as pd

from pipeline.extract import RAIZ, UFS, normalizar
from pipeline.transform import ETAPAS, REDE_IDEB_BRASIL, REDE_IDEB_UF, REDES_RENDIMENTO, TAXAS

SITE_DATA = RAIZ / "site" / "data"
FONTE = "INEP – Taxas de Rendimento Escolar (2007–2025) e Ideb 2025"
ULTIMA_EDICAO_IDEB = 2025


def _lista(valores) -> list:
    return [None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v) for v in valores]


def _series_rendimento(dados: pd.DataFrame, chave: str, anos: list[int]) -> dict:
    """{chave: {rede: {etapa: {taxa: [valores por ano]}}}} a partir do formato longo."""
    # pivot (e não pivot_table) dá erro se houver valor duplicado em vez de escolher um em silêncio
    piv = dados.pivot(index=[chave, "rede", "etapa", "taxa"], columns="ano", values="valor")
    piv = piv.reindex(columns=anos)
    saida = {}
    for (k, rede, etapa, taxa), linha in zip(piv.index, piv.to_numpy()):
        saida.setdefault(k, {}).setdefault(rede, {}).setdefault(etapa, {})[taxa] = _lista(linha)
    # ordem fixa das chaves, e séries vazias quando uma combinação não existe
    vazio = [None] * len(anos)
    return {k: {r: {e: {t: v.get(r, {}).get(e, {}).get(t, vazio) for t in TAXAS} for e in ETAPAS}
                for r in REDES_RENDIMENTO} for k, v in saida.items()}


def _series_ideb(dados: pd.DataFrame, chave: str, anos_por_etapa: dict) -> dict:
    """{chave: {etapa: [valores por edição]}}."""
    saida = {}
    for etapa, anos in anos_por_etapa.items():
        sub = dados[dados["etapa"] == etapa]
        piv = sub.pivot(index=chave, columns="ano", values="valor").reindex(columns=anos)
        for k, linha in zip(piv.index, piv.to_numpy()):
            saida.setdefault(k, {})[etapa] = _lista(linha)
    return saida


def _status_ideb(serie: list | None) -> str:
    """Situação do IDEB na última edição: divulgado, nao_divulgado (linha com '-') ou sem_registro (fora da planilha)."""
    if serie is None:
        return "sem_registro"
    return "divulgado" if serie[-1] is not None else "nao_divulgado"


def _gravar(caminho: Path, obj) -> int:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    caminho.write_text(texto, encoding="utf-8")
    return len(texto.encode("utf-8"))


def exportar(rend_mun: pd.DataFrame, rend_ref: pd.DataFrame, ideb_mun: pd.DataFrame,
             ideb_ref: pd.DataFrame) -> dict[str, int]:
    """Escreve todos os JSONs. Retorna {arquivo: tamanho em bytes}."""
    anos_rend = sorted(rend_mun["ano"].unique().tolist())
    anos_ideb_mun = {e: sorted(ideb_mun.loc[ideb_mun["etapa"] == e, "ano"].unique().tolist()) for e in ETAPAS}
    anos_ideb_ref = {e: sorted(ideb_ref.loc[ideb_ref["etapa"] == e, "ano"].unique().tolist()) for e in ETAPAS}

    # Nome e UF de cada município: os do ano mais recente (grafia com acento a partir de 2015)
    cadastro = (rend_mun.sort_values("ano").drop_duplicates("co_municipio", keep="last")
                .set_index("co_municipio")[["nome", "uf"]])
    tamanhos = {}

    lista = [{"id": co, "nome": r.nome, "uf": r.uf, "busca": normalizar(r.nome)} for co, r in cadastro.iterrows()]
    lista.sort(key=lambda m: (m["busca"], m["uf"]))
    tamanhos["municipios.json"] = _gravar(SITE_DATA / "municipios.json", lista)

    rend = _series_rendimento(rend_mun, "co_municipio", anos_rend)
    ideb = _series_ideb(ideb_mun, "co_municipio", anos_ideb_mun)
    pasta_uf = SITE_DATA / "uf"
    for antigo in pasta_uf.glob("*.json"):
        antigo.unlink()
    for uf, grupo in cadastro.groupby("uf"):
        municipios = {}
        for co in sorted(grupo.index):
            ideb_co = ideb.get(co, {})
            municipios[co] = {
                "nome": grupo.at[co, "nome"],
                "rendimento": rend[co],
                "ideb": {e: {"valores": ideb_co.get(e, [None] * len(anos_ideb_mun[e])),
                             "status": _status_ideb(ideb_co.get(e))} for e in ETAPAS},
            }
        obj = {"uf": uf, "nome": UFS[uf], "fonte": FONTE, "anos_rendimento": anos_rend,
               "anos_ideb": anos_ideb_mun, "rede_ideb": "publica", "municipios": municipios}
        tamanhos[f"uf/{uf}.json"] = _gravar(pasta_uf / f"{uf}.json", obj)

    rend_r = _series_rendimento(rend_ref, "unidade", anos_rend)
    ideb_r = _series_ideb(ideb_ref, "unidade", anos_ideb_ref)

    def unidade(k, redes_ideb):
        return {"nome": "Brasil" if k == "BR" else UFS[k], "rendimento": rend_r[k],
                "ideb": {e: {"rede": redes_ideb[e], "valores": ideb_r[k][e]} for e in ETAPAS}}

    referencias = {
        "fonte": FONTE, "anos_rendimento": anos_rend, "anos_ideb": anos_ideb_ref,
        "brasil": unidade("BR", REDE_IDEB_BRASIL),
        "uf": {uf: unidade(uf, REDE_IDEB_UF) for uf in UFS},
    }
    tamanhos["referencias.json"] = _gravar(SITE_DATA / "referencias.json", referencias)
    return tamanhos
