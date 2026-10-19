"""Formato do push de track(): todos os parâmetros do contrato, undefined nos que não são do evento.

Regressão do bug de vazamento: o modelo de dados do GTM é persistente e a tag do GA4 envia todos os
parâmetros mapeados; um parâmetro não limpo (ex.: search_term) aparecia em eventos seguintes (ex.: share).
"""
import copy
import json
import re

import pytest

from tracking.gerar import PARAMETROS_JS, RAIZ, CAMPOS_COMUNS, carregar_schema, eventos, parametros
from tracking.validacao import erros_do_push, normalizar_push

SCHEMA = carregar_schema()
EVENTOS = eventos(SCHEMA)
PARAMETROS = parametros(SCHEMA)


def push_como_track(exemplo: dict) -> dict:
    """Reproduz montarPush() do track.js: todos os parâmetros como undefined (None) + os do evento."""
    return {**{p: None for p in PARAMETROS}, **exemplo}


def test_lista_do_js_tem_todos_os_parametros_do_contrato():
    texto = PARAMETROS_JS.read_text(encoding="utf-8")
    lista = json.loads(re.search(r"Object\.freeze\((\[.*\])\)", texto).group(1))
    esperado = {p for e in EVENTOS for p in e["properties"]} - set(CAMPOS_COMUNS)
    assert set(lista) == esperado and len(lista) == len(set(lista))


@pytest.mark.parametrize("evento", EVENTOS, ids=[e["title"] for e in EVENTOS])
def test_push_completo_e_valido(evento):
    push = push_como_track(evento["examples"][0])
    assert set(push) >= set(PARAMETROS)  # toda chave conhecida está presente (limpa o GTM)
    assert erros_do_push(push) == []


def test_normalizar_descarta_indefinidos_e_chaves_do_gtm():
    push = {**push_como_track(EVENTOS[0]["examples"][0]), "gtm.uniqueEventId": 12}
    normal = normalizar_push(push)
    assert "gtm.uniqueEventId" not in normal and None not in normal.values()


def test_parametro_vazado_e_rejeitado():
    """O sintoma do bug: share com search_term de uma busca anterior."""
    share = copy.deepcopy(next(e for e in EVENTOS if e["title"] == "share")["examples"][0])
    vazado = push_como_track({**share, "search_term": "hugo napoleao"})
    assert erros_do_push(vazado), "um parâmetro de outro evento com valor deve violar o contrato"


def test_track_usa_a_lista_completa_e_nao_depende_do_historico():
    js = (RAIZ / "site" / "js" / "track.js").read_text(encoding="utf-8")
    assert 'import { PARAMETROS } from "./parametros-eventos.js"' in js
    assert "for (const nome of PARAMETROS) push[nome] = undefined" in js
    assert "chavesAnteriores" not in js  # abordagem antiga (só limpava o evento anterior) removida
