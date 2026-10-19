"""Validação de objetos do dataLayer contra o contrato (para testes e para o QA automatizado).

Os pushes de track() levam TODOS os parâmetros do contrato, com undefined nos que não são do
evento (para limpar o modelo de dados persistente do GTM). Lidos do navegador, esses valores
chegam como None (ou somem, se passarem por JSON). O GTM ainda grava gtm.uniqueEventId em cada
objeto. Antes de validar, descartamos as duas coisas.
"""
from jsonschema import Draft202012Validator

from tracking.gerar import carregar_schema

_VALIDADOR = Draft202012Validator(carregar_schema())


def normalizar_push(push: dict) -> dict:
    """Remove chaves sem valor (undefined/None) e chaves internas do GTM (gtm.*)."""
    return {k: v for k, v in push.items() if v is not None and not k.startswith("gtm.")}


def erros_do_push(push: dict) -> list[str]:
    """Violações do contrato (lista vazia = válido)."""
    return [erro.message for erro in _VALIDADOR.iter_errors(normalizar_push(push))]
