"""Gera o plano de medição e o contrato do navegador a partir do JSON Schema.

    python -m tracking.gerar             # escreve os arquivos
    python -m tracking.gerar --verificar # só confere se estão atualizados (usado nos testes)

O schema (tracking/schema/events.schema.json) é a fonte da verdade. Os arquivos
gerados não devem ser editados à mão: mude o schema e rode este script.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCHEMA = RAIZ / "tracking" / "schema" / "events.schema.json"
DOC = RAIZ / "tracking" / "docs" / "plano_de_medicao.md"
CONTRATO_JS = RAIZ / "site" / "js" / "contrato-eventos.js"
PARAMETROS_JS = RAIZ / "site" / "js" / "parametros-eventos.js"
CAMPOS_COMUNS = ("event", "event_id", "schema_version")


def carregar_schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def resolver(schema: dict, no: dict) -> dict:
    """Junta um nó com o alvo do seu $ref (as chaves ao lado do $ref têm prioridade)."""
    if "$ref" not in no:
        return no
    alvo = schema["$defs"][no["$ref"].split("/")[-1]]
    return {**resolver(schema, alvo), **{k: v for k, v in no.items() if k != "$ref"}}


def eventos(schema: dict) -> list[dict]:
    return [schema["$defs"][r["$ref"].split("/")[-1]] for r in schema["oneOf"]]


def _regras(p: dict) -> str:
    if "const" in p:
        return f"`{p['const']}`"
    if "enum" in p:
        return ", ".join(f"`{v}`" for v in p["enum"])
    partes = []
    if "pattern" in p:
        partes.append(f"regex `{p['pattern']}`")
    if "maxLength" in p:
        partes.append(f"até {p['maxLength']} caracteres")
    if "minimum" in p:
        partes.append(f"≥ {p['minimum']}")
    return "; ".join(partes) or "livre"


def _tabela(cabecalho: list[str], linhas: list[list[str]]) -> list[str]:
    return ["| " + " | ".join(cabecalho) + " |", "|" + "---|" * len(cabecalho),
            *["| " + " | ".join(str(c).replace("|", "\\|") for c in linha) + " |" for linha in linhas]]


def gerar_markdown(schema: dict) -> str:
    versao = schema["x-schema-version"]
    evs = eventos(schema)
    s = [
        "# Plano de medição – EduTrackBrasil", "",
        "> Gerado por `python -m tracking.gerar` a partir de `tracking/schema/events.schema.json`. "
        "Não edite à mão: mude o schema e gere de novo.", "",
        f"**Versão do contrato:** `{versao}` · **Eventos:** {len(evs)} · "
        "**Implementação:** `site/js/track.js` (helper) e `site/js/app.js` (gatilhos)", "",
        "## 1. Objetivo e KPIs", "",
        "**Objetivo:** ajudar cidadãos a entender a educação do próprio município.", "",
        *_tabela(["KPI", "Como medir"], [
            ["Engajamento com a busca", "% de sessões com `select_content`"],
            ["Busca sem resultado", "`search` com `results_count = 0` ÷ total de `search` (mostra como as pessoas escrevem os nomes)"],
            ["Consumo dos dados", "% de sessões com `view_chart` (por `chart_id`)"],
            ["Intenção de compartilhar", "`generate_card` ÷ sessões com `select_content`"],
            ["Conversão (evento-chave)", "`share` ÷ `generate_card`, quebrado por `method`"],
            ["Lacunas de dado vistas", "`data_unavailable` por `motivo` e `etapa`"],
        ]), "",
        "**Funil:** `page_view` → `search` → `select_content` → `view_chart` → `generate_card` → `share`.", "",
        "## 2. Convenções", "",
        "- Nomes de evento e parâmetro em `snake_case`. Limites do GA4 respeitados: evento ≤ 40 caracteres, "
        "≤ 25 parâmetros por evento, valor de parâmetro ≤ 100 caracteres (os testes conferem).",
        "- Eventos recomendados do GA4 onde existem (`search`, `select_content`, `share`); personalizados para o resto.",
        "- Todo push leva `event_id` (UUID v4, para deduplicar e reconciliar) e `schema_version` (versão deste contrato).",
        "- Códigos IBGE sempre como **texto** de 7 dígitos, nunca número.",
        "- **Todo push leva todos os parâmetros do contrato**: os que não pertencem ao evento vão como `undefined`. "
        "Motivo: o modelo de dados do GTM é persistente (guarda o último valor de cada chave entre pushes) e a tag "
        "do GA4 envia todos os parâmetros mapeados em todo evento; sem isso, um `search_term` antigo vazaria para um "
        "`share`. Com `undefined`, o GTM limpa o valor antigo e o GA4 descarta o parâmetro vazio. A lista vem de "
        "`site/js/parametros-eventos.js`, gerado deste schema.",
        "- Quem audita o `dataLayer` (testes, QA) deve descartar as chaves `undefined`/`null` e as chaves `gtm.*` "
        "(o GTM grava `gtm.uniqueEventId` em cada objeto) antes de validar contra o schema "
        "(ver `tracking/validacao.py`).",
        "- Em ambiente local (`localhost`, `127.0.0.1` ou `?debug_tracking`), cada push é mostrado no console e "
        "validado contra este contrato; violações aparecem como `console.warn`.", "",
        "## 3. Resumo dos eventos", "",
        *_tabela(["Evento", "Tipo", "Quando dispara", "Parâmetros"], [
            [f"`{e['title']}`" + (" ⭐" if e.get("x-evento-chave") else ""), e["x-tipo"], e["description"],
             ", ".join(f"`{p}`" for p in e["properties"] if p not in CAMPOS_COMUNS)]
            for e in evs]), "",
        "⭐ = evento-chave (conversão) no GA4.", "",
        "## 4. Tagbook (detalhe por evento)", "",
    ]
    for e in evs:
        exemplo = e["examples"][0]
        s += [f"### `{e['title']}`", "",
              f"- **Tipo:** {e['x-tipo']}" + (" · **evento-chave**" if e.get("x-evento-chave") else ""),
              f"- **O que significa:** {e['description']}",
              f"- **Gatilho exato:** {e['x-gatilho']}",
              "- **Status:** implementado no código · validação no GTM Preview / DebugView: pendente (fase GTM)", ""]
        linhas = []
        for nome, no in e["properties"].items():
            if nome in CAMPOS_COMUNS:
                continue
            p = resolver(schema, no)
            obrig = "sim" if nome in e["required"] else "não"
            linhas.append([f"`{nome}`", p.get("type", "string"), obrig, _regras(p), p.get("description", "")])
        s += _tabela(["Parâmetro", "Tipo", "Obrigatório", "Valores permitidos", "Descrição"], linhas)
        s += ["", "```js", f"window.dataLayer.push({json.dumps(exemplo, ensure_ascii=False, indent=2)});", "```", ""]

    s += ["## 5. Dicionário de parâmetros", "",
          "Cada parâmetro tem uma definição única, reutilizada entre eventos (evita dimensões duplicadas no GA4).", ""]
    uso: dict[str, set] = {}
    dimensao: dict[str, bool] = {}
    for e in evs:
        for nome, no in e["properties"].items():
            if nome in CAMPOS_COMUNS and nome == "event":
                continue
            uso.setdefault(nome, set()).add(e["title"])
            p = resolver(schema, no)
            dimensao[nome] = dimensao.get(nome, False) or bool(p.get("x-dimensao-ga4"))
    linhas = []
    for nome in sorted(uso):
        no = next(e["properties"][nome] for e in evs if nome in e["properties"])
        p = resolver(schema, no)
        obs = p.get("x-observacao", "")
        linhas.append([f"`{nome}`", p.get("type", "string"), _regras(p),
                       ", ".join(f"`{x}`" for x in sorted(uso[nome])),
                       "sim" if dimensao[nome] else "não", (p.get("description", "") + (f" {obs}" if obs else "")).strip()])
    s += _tabela(["Parâmetro", "Tipo", "Regras", "Usado em", "Dimensão personalizada GA4", "Definição"], linhas)
    dims = sorted(n for n, d in dimensao.items() if d)
    s += ["", "## 6. Dimensões personalizadas a registrar no GA4", "",
          f"Admin → Definições personalizadas → escopo **evento**. Total: **{len(dims)}** (limite: 50). "
          "Registrar antes de publicar: o registro não é retroativo nos relatórios padrão.", "",
          *[f"- `{d}`" for d in dims], ""]
    return "\n".join(s)


def gerar_js(schema: dict) -> str:
    return ("// Gerado por `python -m tracking.gerar` a partir de tracking/schema/events.schema.json. Não edite.\n"
            "// Usado só em ambiente local para validar os pushes no console (ver track.js).\n"
            f"export const CONTRATO = {json.dumps(schema, ensure_ascii=False, separators=(',', ':'))};\n")


def parametros(schema: dict) -> list[str]:
    """Todos os parâmetros de evento do contrato (sem event, event_id e schema_version), em ordem alfabética."""
    return sorted({p for e in eventos(schema) for p in e["properties"] if p not in CAMPOS_COMUNS})


def gerar_parametros_js(schema: dict) -> str:
    lista = json.dumps(parametros(schema), ensure_ascii=False)
    return ("// Gerado por `python -m tracking.gerar` a partir de tracking/schema/events.schema.json. Não edite.\n"
            "// Todos os parâmetros conhecidos: track() envia cada um deles em todo push (undefined quando não\n"
            "// pertence ao evento) para limpar valores antigos no modelo de dados persistente do GTM.\n"
            f"export const PARAMETROS = Object.freeze({lista});\n")


def arquivos_gerados() -> dict[Path, str]:
    schema = carregar_schema()
    return {DOC: gerar_markdown(schema), CONTRATO_JS: gerar_js(schema), PARAMETROS_JS: gerar_parametros_js(schema)}


def main() -> int:
    verificar = "--verificar" in sys.argv
    desatualizados = []
    for caminho, conteudo in arquivos_gerados().items():
        atual = caminho.read_text(encoding="utf-8") if caminho.exists() else None
        if atual == conteudo:
            continue
        if verificar:
            desatualizados.append(caminho.relative_to(RAIZ))
        else:
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.write_text(conteudo, encoding="utf-8", newline="\n")
            print(f"gerado: {caminho.relative_to(RAIZ)}")
    if desatualizados:
        print("Desatualizados (rode python -m tracking.gerar):", *desatualizados, sep="\n  ")
        return 1
    if verificar:
        print("Arquivos gerados estão atualizados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
