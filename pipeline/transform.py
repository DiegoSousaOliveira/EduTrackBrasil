"""Transforma as planilhas do INEP em tabelas no formato longo (uma linha por valor).

Formato longo = em vez de uma coluna por etapa/ano, cada linha diz
(quem, ano, rede, etapa, taxa, valor). Fica fácil filtrar, testar e pivotar.
"""
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from pipeline.extract import (RAW_DIR, chave_unidade, colunas_ideb, ler_planilhas, localizar_cabecalho,
                              localizar_cabecalho_ideb, normalizar, para_numero, rotulos_colunas)

ETAPAS = ("ef_ai", "ef_af", "em")
TAXAS = ("aprovacao", "reprovacao", "abandono")
REDES_RENDIMENTO = ("total", "publica")

# Rede usada no IDEB das referências. A planilha de UFs não tem linha "Pública"
# no ensino médio; como o EM público é quase todo estadual, usamos a Estadual.
REDE_IDEB_UF = {"ef_ai": "publica", "ef_af": "publica", "em": "estadual"}
REDE_IDEB_BRASIL = {"ef_ai": "publica", "ef_af": "publica", "em": "publica"}

ARQUIVOS_IDEB_MUNICIPIOS = {
    "ef_ai": "divulgacao_anos_iniciais_municipios_2025.zip",
    "ef_af": "divulgacao_anos_finais_municipios_2025.zip",
    "em": "divulgacao_ensino_medio_municipios_2025.zip",
}
ARQUIVO_IDEB_UFS = "divulgacao_regioes_ufs_ideb_2025.zip"
ARQUIVO_IDEB_BRASIL = "divulgacao_brasil_ideb_2025.zip"

# Rótulo (normalizado) das colunas de identificação -> nome padronizado
COLUNAS_ID = {
    "ano": "ano", "regiao": "regiao", "uf": "uf", "codigo do municipio": "co_municipio",
    "nome do municipio": "nome", "localizacao": "localizacao", "rede": "rede",
    "dependencia administrativa": "rede", "abrangencia": "unidade", "unidade geografica": "unidade",
}


@dataclass
class Diagnostico:
    """O que foi visto durante a leitura; vira o relatório de qualidade."""
    tokens: Counter = field(default_factory=Counter)
    arquivos: list = field(default_factory=list)  # (fonte, zip, arquivo, aba, ano, linhas)
    avisos: list = field(default_factory=list)


def classificar_coluna(rotulo: str) -> tuple[str, str] | None:
    """'taxa de aprovacao > ... > anos iniciais' -> ('aprovacao', 'ef_ai'). Outras colunas -> None.

    Cobre os dois layouts do INEP:
    - 2007–2010: 'aprovacao 1a a 4a serie/1o a 5o ano', '... 5a a 8a serie/ 6o ao 9o ano', 'total aprovacao medio'
    - 2011–2025: 'anos iniciais', 'anos finais', 'ensino medio > total' / 'total aprovacao no ens. medio'
    """
    if "reprova" in rotulo:
        taxa = "reprovacao"
    elif "abandono" in rotulo:
        taxa = "abandono"
    elif "aprova" in rotulo:
        taxa = "aprovacao"
    else:
        return None
    if "anos iniciais" in rotulo or "1a a 4a serie" in rotulo:
        return taxa, "ef_ai"
    if "anos finais" in rotulo or "5a a 8a serie" in rotulo:
        return taxa, "ef_af"
    if "medio" in rotulo and "total" in rotulo and "seriad" not in rotulo:
        return taxa, "em"
    return None


def mapear_colunas(rotulos: list[str]) -> tuple[dict[str, int], dict[tuple[str, str], int]]:
    """Acha, pelo texto, as colunas de identificação e as 9 colunas de taxa que usamos.

    Falha alto se alguma das 9 (3 taxas x 3 etapas) faltar ou aparecer duas vezes:
    melhor quebrar o pipeline do que publicar um número da coluna errada.
    """
    ids, valores = {}, {}
    for i, rotulo in enumerate(rotulos):
        if rotulo in COLUNAS_ID:
            ids.setdefault(COLUNAS_ID[rotulo], i)
            continue
        alvo = classificar_coluna(rotulo)
        if alvo:
            if alvo in valores:
                raise ValueError(f"coluna {alvo} encontrada duas vezes: {valores[alvo]} e {i}")
            valores[alvo] = i
    faltando = [(t, e) for t in TAXAS for e in ETAPAS if (t, e) not in valores]
    if faltando:
        raise ValueError(f"colunas não encontradas: {faltando}")
    for obrigatoria in ("ano", "localizacao", "rede"):
        if obrigatoria not in ids:
            raise ValueError(f"coluna de identificação '{obrigatoria}' não encontrada")
    return ids, valores


def padronizar_rede(texto) -> str:
    """'Publico', 'Pública', 'Pública (4)' -> 'publica'; 'Particular'/'Privada' -> 'privada'."""
    r = normalizar(re.sub(r"\(.*?\)|\*", "", str(texto)))
    return {"publico": "publica", "particular": "privada"}.get(r, r)


def _planilha_para_longo(df: pd.DataFrame, chaves_extra: tuple[str, ...]) -> pd.DataFrame:
    """Uma aba de rendimento -> formato longo, já filtrado em localização Total e redes Total/Pública."""
    inicio, dados = localizar_cabecalho(df)
    ids, valores = mapear_colunas(rotulos_colunas(df, inicio, dados[0]))
    base = df.loc[dados]
    loc = base[ids["localizacao"]].map(normalizar)
    rede = base[ids["rede"]].map(padronizar_rede)
    base = base[(loc == "total") & rede.isin(REDES_RENDIMENTO)]
    partes = []
    for (taxa, etapa), col in valores.items():
        parte = pd.DataFrame({
            "ano": base[ids["ano"]].str[:4].astype(int).values,
            "rede": base[ids["rede"]].map(padronizar_rede).values,
            "etapa": etapa, "taxa": taxa,
            "valor_bruto": base[col].values,
        })
        for chave in chaves_extra:
            parte[chave] = base[ids[chave]].values if chave in ids else None
        partes.append(parte)
    return pd.concat(partes, ignore_index=True)


def rendimento_municipios(diag: Diagnostico) -> pd.DataFrame:
    """Todas as planilhas de municípios -> colunas: ano, co_municipio, uf, nome, rede, etapa, taxa, valor."""
    frames = []
    for zip_path in sorted((RAW_DIR / "rendimento" / "municipios").glob("*.zip")):
        for arquivo, aba, df in _planilhas_validas(zip_path):
            longo = _planilha_para_longo(df, ("co_municipio", "uf", "nome"))
            diag.arquivos.append(("rendimento_municipios", zip_path.name, arquivo, aba,
                                  sorted(longo["ano"].unique().tolist()), len(longo)))
            frames.append(longo)
    dados = pd.concat(frames, ignore_index=True)
    dados["co_municipio"] = dados["co_municipio"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    dados["uf"] = dados["uf"].astype(str).str.strip()
    dados["nome"] = dados["nome"].astype(str).str.strip()
    dados["valor"] = para_numero(dados.pop("valor_bruto"), diag.tokens)
    return dados


def rendimento_referencias(diag: Diagnostico) -> pd.DataFrame:
    """Planilhas de Brasil/Regiões/UFs -> colunas: ano, unidade ('BR' ou sigla), rede, etapa, taxa, valor.

    As médias de UF vêm destas planilhas oficiais (não são calculadas a partir dos municípios).
    Linhas de regiões são descartadas.
    """
    frames = []
    for zip_path in sorted((RAW_DIR / "rendimento" / "brasil_uf").glob("*.zip")):
        for arquivo, aba, df in _planilhas_validas(zip_path):
            inicio, dados = localizar_cabecalho(df)
            ids, _ = mapear_colunas(rotulos_colunas(df, inicio, dados[0]))
            # A coluna que identifica a unidade muda: 'UF', 'Unidade Geográfica', 'Abrangência' ou 'Região'
            coluna_unidade = next(c for c in ("uf", "unidade", "regiao") if c in ids)
            longo = _planilha_para_longo(df, (coluna_unidade,))
            longo["unidade"] = longo.pop(coluna_unidade).map(chave_unidade)
            longo = longo[longo["unidade"].notna()]
            diag.arquivos.append(("rendimento_referencias", zip_path.name, arquivo, aba,
                                  sorted(longo["ano"].unique().tolist()), len(longo)))
            frames.append(longo)
    dados = pd.concat(frames, ignore_index=True)
    dados["valor"] = para_numero(dados.pop("valor_bruto"), diag.tokens)
    return dados


def _planilhas_validas(zip_path: Path):
    """Abas com dados de verdade (ignora abas vazias como 'Plan1')."""
    for arquivo, aba, df in ler_planilhas(zip_path):
        if df.shape[1] >= 10:
            yield arquivo, aba, df


def etapa_da_aba(nome_aba: str) -> str | None:
    n = normalizar(nome_aba)
    if "(ai)" in n or "iniciais" in n:
        return "ef_ai"
    if "(af)" in n or "finais" in n:
        return "ef_af"
    if "(em)" in n or "medio" in n:
        return "em"
    return None


def _ideb_longo(df: pd.DataFrame, col_unidade: int, col_rede: int, etapa: str, diag: Diagnostico) -> pd.DataFrame:
    """Uma aba do IDEB -> colunas: unidade_bruta, rede, etapa, ano, valor (linha de dados = tem rede preenchida)."""
    h = localizar_cabecalho_ideb(df)
    anos = colunas_ideb(df, h)
    corpo = df.iloc[h + 1:]
    corpo = corpo[corpo[col_rede].notna() & corpo[col_rede].astype(str).str.strip().ne("")].copy()
    corpo[col_unidade] = corpo[col_unidade].ffill()  # unidade pode vir só na 1ª linha do grupo
    partes = []
    for ano, col in anos.items():
        partes.append(pd.DataFrame({
            "unidade_bruta": corpo[col_unidade].astype(str).str.strip().values,
            "rede": corpo[col_rede].map(padronizar_rede).values,
            "etapa": etapa, "ano": ano,
            "valor": para_numero(corpo[col], diag.tokens).values,
        }))
    return pd.concat(partes, ignore_index=True)


def ideb_municipios(diag: Diagnostico) -> pd.DataFrame:
    """IDEB por município, rede Pública -> colunas: co_municipio, uf, etapa, ano, valor.

    Município ausente da planilha = 'sem_registro'; presente com '-' = 'nao_divulgado'
    (essa classificação é feita na exportação).
    """
    frames = []
    for etapa, nome_zip in ARQUIVOS_IDEB_MUNICIPIOS.items():
        zip_path = RAW_DIR / "ideb" / nome_zip
        (arquivo, aba, df), = ler_planilhas(zip_path)
        h = localizar_cabecalho_ideb(df)
        codigos = [str(v).strip() for v in df.iloc[h]]
        longo = _ideb_longo(df, codigos.index("CO_MUNICIPIO"), codigos.index("REDE"), etapa, diag)
        longo = longo.rename(columns={"unidade_bruta": "co_municipio"})
        longo["co_municipio"] = longo["co_municipio"].str.replace(r"\.0$", "", regex=True)
        longo = longo[longo["co_municipio"].str.fullmatch(r"\d{7}") & (longo["rede"] == "publica")]
        diag.arquivos.append(("ideb_municipios", nome_zip, arquivo, aba, sorted(longo["ano"].unique().tolist()),
                              len(longo)))
        frames.append(longo)
    return pd.concat(frames, ignore_index=True)


def ideb_referencias(diag: Diagnostico) -> pd.DataFrame:
    """IDEB de UFs e Brasil -> colunas: unidade, rede, etapa, ano, valor (só a rede escolhida para cada etapa)."""
    frames = []
    for nome_zip, redes in ((ARQUIVO_IDEB_UFS, REDE_IDEB_UF), (ARQUIVO_IDEB_BRASIL, REDE_IDEB_BRASIL)):
        for arquivo, aba, df in ler_planilhas(RAW_DIR / "ideb" / nome_zip):
            etapa = etapa_da_aba(aba)
            if etapa is None:
                diag.avisos.append(f"aba ignorada no IDEB: {nome_zip} / {aba}")
                continue
            longo = _ideb_longo(df, 0, 1, etapa, diag)
            longo["unidade"] = longo.pop("unidade_bruta").map(chave_unidade)
            longo = longo[longo["unidade"].notna() & (longo["rede"] == redes[etapa])]
            diag.arquivos.append(("ideb_referencias", nome_zip, arquivo, aba,
                                  sorted(longo["ano"].unique().tolist()), len(longo)))
            frames.append(longo)
    return pd.concat(frames, ignore_index=True)
