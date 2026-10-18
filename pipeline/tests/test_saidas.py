"""Testes de contrato dos JSONs em site/data/ (rode `python -m pipeline.run` antes)."""
import json
import math
import re

import pytest

from pipeline.export import SITE_DATA
from pipeline.extract import UFS

ETAPAS = ("ef_ai", "ef_af", "em")
STATUS_IDEB = {"divulgado", "nao_divulgado", "sem_registro"}

if not (SITE_DATA / "municipios.json").exists():
    pytest.skip("JSONs ainda não gerados: rode python -m pipeline.run", allow_module_level=True)


def _ler(nome):
    return json.loads((SITE_DATA / nome).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def municipios():
    return _ler("municipios.json")


@pytest.fixture(scope="module")
def ufs():
    return {uf: _ler(f"uf/{uf}.json") for uf in UFS}


@pytest.fixture(scope="module")
def referencias():
    return _ler("referencias.json")


def _todas_series(dados_uf):
    for uf, d in dados_uf.items():
        for co, m in d["municipios"].items():
            for rede, etapas in m["rendimento"].items():
                for etapa, taxas in etapas.items():
                    yield uf, co, rede, etapa, taxas


def test_quantidade_de_municipios(municipios):
    assert 5560 <= len(municipios) <= 5580


def test_codigos_ibge_sao_strings_de_7_digitos(municipios):
    assert all(isinstance(m["id"], str) and re.fullmatch(r"\d{7}", m["id"]) for m in municipios)


def test_sem_duplicatas(municipios, ufs):
    ids = [m["id"] for m in municipios]
    assert len(ids) == len(set(ids))
    no_uf = [co for d in ufs.values() for co in d["municipios"]]
    assert len(no_uf) == len(set(no_uf))


def test_lista_de_busca_e_arquivos_por_uf_batem(municipios, ufs):
    assert {(m["id"], m["uf"]) for m in municipios} == {(co, uf) for uf, d in ufs.items() for co in d["municipios"]}
    # os 2 primeiros dígitos do código IBGE do município são o código da UF
    codigo_uf = {"RO": "11", "AC": "12", "AM": "13", "RR": "14", "PA": "15", "AP": "16", "TO": "17", "MA": "21",
                 "PI": "22", "CE": "23", "RN": "24", "PB": "25", "PE": "26", "AL": "27", "SE": "28", "BA": "29",
                 "MG": "31", "ES": "32", "RJ": "33", "SP": "35", "PR": "41", "SC": "42", "RS": "43", "MS": "50",
                 "MT": "51", "GO": "52", "DF": "53"}
    errados = [m for m in municipios if m["id"][:2] != codigo_uf[m["uf"]]]
    assert not errados, errados[:5]


def test_busca_sem_acento_e_minuscula(municipios):
    for m in municipios:
        assert m["busca"] == m["busca"].lower()
        assert m["busca"].isascii()


def test_series_alinhadas_com_os_anos(ufs, referencias):
    for uf, d in ufs.items():
        n = len(d["anos_rendimento"])
        for _, _, _, _, taxas in _todas_series({uf: d}):
            assert all(len(v) == n for v in taxas.values())
        for m in d["municipios"].values():
            for e in ETAPAS:
                assert len(m["ideb"][e]["valores"]) == len(d["anos_ideb"][e])


def test_taxas_entre_0_e_100(ufs, referencias):
    valores = [v for *_, taxas in _todas_series(ufs) for serie in taxas.values() for v in serie if v is not None]
    assert valores and all(0 <= v <= 100 for v in valores)


def test_aprovacao_reprovacao_abandono_somam_100(ufs):
    problemas = []
    for uf, co, rede, etapa, t in _todas_series(ufs):
        for i, (a, r, b) in enumerate(zip(t["aprovacao"], t["reprovacao"], t["abandono"])):
            if None not in (a, r, b) and not math.isclose(a + r + b, 100, abs_tol=0.5):
                problemas.append((uf, co, rede, etapa, i, a + r + b))
    assert not problemas, problemas[:5]


def test_ano_sem_dado_e_null_e_nao_zero(ufs):
    # Municípios novos (ex.: Boa Esperança do Norte-MT, instalado em 2025) têm null antes do 1º ano
    boa = ufs["MT"]["municipios"]["5101837"]["rendimento"]["total"]["ef_ai"]["aprovacao"]
    assert boa[:-1] == [None] * (len(boa) - 1) and boa[-1] is not None


def test_ideb_status_coerente(ufs):
    for d in ufs.values():
        for m in d["municipios"].values():
            for e in ETAPAS:
                ideb = m["ideb"][e]
                assert ideb["status"] in STATUS_IDEB
                assert (ideb["status"] == "divulgado") == (ideb["valores"][-1] is not None)
                if ideb["status"] == "sem_registro":
                    assert all(v is None for v in ideb["valores"])
                assert all(0 <= v <= 10 for v in ideb["valores"] if v is not None)


def test_referencias_tem_brasil_e_27_ufs(referencias):
    assert set(referencias["uf"]) == set(UFS)
    n = len(referencias["anos_rendimento"])
    for unidade in [referencias["brasil"], *referencias["uf"].values()]:
        for rede in ("total", "publica"):
            for e in ETAPAS:
                for serie in unidade["rendimento"][rede][e].values():
                    assert len(serie) == n and sum(v is not None for v in serie) == n  # médias oficiais completas
        for e in ETAPAS:
            assert len(unidade["ideb"][e]["valores"]) == len(referencias["anos_ideb"][e])
    assert referencias["uf"]["PI"]["ideb"]["em"]["rede"] == "estadual"
    assert referencias["brasil"]["ideb"]["ef_ai"]["rede"] == "publica"


def test_valores_conhecidos_do_ideb_2025(referencias):
    # Brasil, rede pública, 2025 (divulgação do INEP): 6,1 / 5,0 / 4,3
    br = referencias["brasil"]["ideb"]
    assert (br["ef_ai"]["valores"][-1], br["ef_af"]["valores"][-1], br["em"]["valores"][-1]) == (6.1, 5.0, 4.3)
