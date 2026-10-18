"""Testes das regras de leitura, com rótulos copiados das planilhas reais do INEP."""
import pandas as pd
import pytest

from pipeline.extract import chave_unidade, colunas_ideb, normalizar, para_numero, rotulos_colunas
from pipeline.transform import classificar_coluna, etapa_da_aba, mapear_colunas, padronizar_rede


def test_normalizar_remove_acentos_e_espacos():
    assert normalizar("  Aprovação 1ª a 4ª  Série/1º a 5º Ano ") == "aprovacao 1a a 4a serie/1o a 5o ano"


@pytest.mark.parametrize("texto, esperado", [
    ("Brasil", "BR"), ("BRASIL", "BR"), ("PI", "PI"), ("Piauí", "PI"), ("R. G. do Norte", "RN"),
    ("M. G. do Sul", "MS"), ("Rio Grande do Sul", "RS"), ("Distrito Federal", "DF"),
    ("Nordeste", None), ("Centro - Oeste", None), ("Centro_Oeste", None),
])
def test_chave_unidade(texto, esperado):
    assert chave_unidade(texto) == esperado


def test_para_numero_trata_ausentes_virgula_e_float_longo():
    s = pd.Series(["90.4", "--", "-", "ND", "73.09999999999998", "5,6", None])
    r = para_numero(s).tolist()
    assert r[0] == 90.4 and r[4] == 73.1 and r[5] == 5.6
    assert all(pd.isna(v) for v in (r[1], r[2], r[3], r[6]))


@pytest.mark.parametrize("texto, esperado", [
    ("Publico", "publica"), ("Pública", "publica"), ("Pública (4)", "publica"), ("Total (3)(4)", "total"),
    ("Particular", "privada"), ("Privada (1)", "privada"), ("Estadual", "estadual"),
])
def test_padronizar_rede(texto, esperado):
    assert padronizar_rede(texto) == esperado


@pytest.mark.parametrize("rotulo, esperado", [
    # Layout 2007–2010
    ("taxa de aprovacao - ensino fundamental de 8 e 9 anos > aprovacao 1a a 4a serie/1o a 5o ano", ("aprovacao", "ef_ai")),
    ("taxa de reprovacao - ensino fundamental de 8 e 9 anos > reprovacao 5a a 8a serie/ 6o ao 9o ano", ("reprovacao", "ef_af")),
    ("taxa de abandono - ensino medio > total abandono - medio", ("abandono", "em")),
    ("taxa de aprovacao - ensino medio > total aprovacao medio nao seriado", None),
    ("taxa de aprovacao - ensino fundamental de 8 e 9 anos > aprovacao na 1a serie/2o ano", None),
    # Layout 2011–2015
    ("taxa de aprovacao - ensino fundamental de 8 e 9 anos > aprovacao - anos iniciais (1o ao 5o ano)", ("aprovacao", "ef_ai")),
    ("taxa de reprovacao - ensino medio > total reprovacao no ens. medio", ("reprovacao", "em")),
    ("taxa de aprovacao - ensino medio > total aprovacao medio nao-seriado", None),
    # Layout 2016–2025
    ("taxa de abandono > ensino fundamental de 8 e 9 anos > anos finais", ("abandono", "ef_af")),
    ("taxa de aprovacao > ensino medio > total", ("aprovacao", "em")),
    ("taxa de aprovacao > ensino medio > nao-seriado", None),
    ("taxa de aprovacao > ensino fundamental de 8 e 9 anos > total", None),
    ("nome do municipio", None),
])
def test_classificar_coluna(rotulo, esperado):
    assert classificar_coluna(rotulo) == esperado


def _cabecalho_2016():
    """Miniatura do cabeçalho de 2016–2020: grupo mesclado + linha de códigos desalinhada (como em 2020)."""
    linhas = [
        ["Ano", "Localização", "Dependência Administrativa", "Taxa de Aprovação", None, None, None, None,
         "Taxa de Reprovação", None, None, None, None, "Taxa de Abandono", None, None, None, None],
        [None, None, None, "Ensino Fundamental de 8 e 9 anos", None, None, "Ensino Médio", None] * 1 +
        ["Ensino Fundamental de 8 e 9 anos", None, None, "Ensino Médio", None] +
        ["Ensino Fundamental de 8 e 9 anos", None, None, "Ensino Médio", None],
        [None, None, None] + ["Total", "Anos Iniciais", "Anos Finais", "Total", "Não-Seriado"] * 3,
        ["ano", "TIPOLOCA", "DEPENDAD"] + ["tap_fun", "tap_f14", "tap_f04", "tap_med", "tap_ns"] * 3,
        ["2020", "Total", "Pública"] + ["90"] * 15,
    ]
    return pd.DataFrame(linhas)


def test_rotulos_ignoram_linha_de_codigos_e_propagam_grupos():
    df = _cabecalho_2016()
    rotulos = rotulos_colunas(df, 0, 4)
    assert rotulos[5] == "taxa de aprovacao > ensino fundamental de 8 e 9 anos > anos finais"
    assert rotulos[11] == "taxa de reprovacao > ensino medio > total"
    ids, valores = mapear_colunas(rotulos)
    assert ids == {"ano": 0, "localizacao": 1, "rede": 2}
    assert valores[("abandono", "em")] == 16


def test_mapear_colunas_falha_quando_falta_coluna():
    with pytest.raises(ValueError, match="não encontradas"):
        mapear_colunas(["ano", "localizacao", "rede", "taxa de aprovacao > ensino medio > total"])


def test_colunas_ideb_usa_rotulo_quando_falta_codigo():
    df = pd.DataFrame([
        ["Brasil", "Rede", "IDEB\n2021\n(N x P)", "IDEB\n20211\n(N x P)", "IDEB\n2023\n(N x P)"],
        [None, None, None, None, None],
        [None, None, None, None, None],
        ["BRASIL", "rede", "VL_OBSERVADO_2019", "VL_OBSERVADO_2021", None],
    ])
    assert colunas_ideb(df, 3) == {2019: 2, 2021: 3, 2023: 4}


@pytest.mark.parametrize("aba, esperado", [
    ("UF e Regiões (AI)", "ef_ai"), ("Brasil (Anos Finais)", "ef_af"), ("Brasil (EM)", "em"), ("Plan1", None),
])
def test_etapa_da_aba(aba, esperado):
    assert etapa_da_aba(aba) == esperado
