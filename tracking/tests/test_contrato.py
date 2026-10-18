"""Testes do contrato de eventos (tracking/schema/events.schema.json) e da sua implementação no site."""
import copy
import re

import pytest
from jsonschema import Draft202012Validator

from tracking.gerar import RAIZ, arquivos_gerados, carregar_schema, eventos

SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")
SCHEMA = carregar_schema()
VALIDADOR = Draft202012Validator(SCHEMA)
EVENTOS = eventos(SCHEMA)
NOMES = [e["title"] for e in EVENTOS]


def test_schema_e_um_json_schema_valido():
    Draft202012Validator.check_schema(SCHEMA)


def test_versao_do_contrato_bate_com_o_parametro_schema_version():
    assert SCHEMA["$defs"]["schema_version"]["const"] == SCHEMA["x-schema-version"]


@pytest.mark.parametrize("evento", EVENTOS, ids=NOMES)
def test_exemplos_validam(evento):
    for exemplo in evento["examples"]:
        VALIDADOR.validate(exemplo)  # oneOf: exatamente um evento pode casar


@pytest.mark.parametrize("evento", EVENTOS, ids=NOMES)
def test_limites_do_ga4(evento):
    # nome do evento: snake_case, até 40 caracteres; até 25 parâmetros por evento
    assert SNAKE_CASE.match(evento["title"]) and len(evento["title"]) <= 40
    assert evento["properties"]["event"]["const"] == evento["title"]
    assert len(evento["properties"]) - 1 <= 25
    for nome, regra in evento["properties"].items():
        assert SNAKE_CASE.match(nome) and len(nome) <= 40, nome
        regra = {**SCHEMA["$defs"].get(regra.get("$ref", "#/").split("/")[-1], {}), **regra}
        for valor in regra.get("enum", []) + ([regra["const"]] if "const" in regra else []):
            assert len(str(valor)) <= 100
        if regra.get("type") == "string" and "enum" not in regra and "const" not in regra:
            assert regra.get("maxLength", 0) <= 100 or "pattern" in regra, f"{nome} sem limite de tamanho"


def _exemplo(nome):
    return copy.deepcopy(next(e for e in EVENTOS if e["title"] == nome)["examples"][0])


# Inconsistências típicas que o contrato precisa barrar (as do plano: camelCase, share sem method,
# municipio_id numérico) e outras do dia a dia.
@pytest.mark.parametrize("descricao, mutacao", [
    ("evento em camelCase", lambda e: e.update(event="viewChart") or e),
    ("share sem method", lambda e: e.pop("method") and e),
    ("municipio_id numérico", lambda e: e.update(municipio_id=2204600) or e),
    ("código IBGE com 6 dígitos", lambda e: e.update(municipio_id="220460") or e),
    ("parâmetro não previsto", lambda e: e.update(cidade="Teresina") or e),
    ("search_term com maiúscula/acento", lambda e: e.update(search_term="São Paulo") or e),
    ("results_count negativo", lambda e: e.update(results_count=-1) or e),
    ("event_id que não é UUID v4", lambda e: e.update(event_id="123") or e),
    ("schema_version antiga", lambda e: e.update(schema_version="0.9.0") or e),
    ("método de share fora da lista", lambda e: e.update(method="instagram") or e),
])
def test_contrato_rejeita_inconsistencias(descricao, mutacao):
    base = {"evento em camelCase": "view_chart", "share sem method": "share", "municipio_id numérico": "view_chart",
            "código IBGE com 6 dígitos": "generate_card", "parâmetro não previsto": "change_filter",
            "search_term com maiúscula/acento": "search", "results_count negativo": "search",
            "event_id que não é UUID v4": "compare_toggle", "schema_version antiga": "data_unavailable",
            "método de share fora da lista": "share"}[descricao]
    assert not VALIDADOR.is_valid(mutacao(_exemplo(base))), descricao


def test_arquivos_gerados_estao_atualizados():
    for caminho, conteudo in arquivos_gerados().items():
        assert caminho.read_text(encoding="utf-8") == conteudo, f"{caminho.name} desatualizado: rode python -m tracking.gerar"


def test_todo_evento_do_contrato_esta_implementado_e_vice_versa():
    codigo = "\n".join(p.read_text(encoding="utf-8") for p in (RAIZ / "site" / "js").glob("*.js")
                       if p.name != "contrato-eventos.js")
    usados = set(re.findall(r'track\(\s*"([a-z_]+)"', codigo))
    assert usados == set(NOMES)
