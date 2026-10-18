"""Relatório de qualidade dos dados (docs/relatorio_qualidade.md), gerado a cada execução do pipeline."""
import pandas as pd

from pipeline.extract import RAIZ
from pipeline.transform import ETAPAS, Diagnostico

RELATORIO = RAIZ / "docs" / "relatorio_qualidade.md"
ANOS_ESPERADOS = list(range(2007, 2026))
NOMES_ETAPA = {"ef_ai": "Fund. anos iniciais", "ef_af": "Fund. anos finais", "em": "Ensino médio"}


def _tabela(cabecalho: list[str], linhas: list[list]) -> str:
    out = ["| " + " | ".join(cabecalho) + " |", "|" + "---|" * len(cabecalho)]
    out += ["| " + " | ".join(str(c) for c in linha) + " |" for linha in linhas]
    return "\n".join(out)


def _soma_fora_de_100(dados: pd.DataFrame, chave: str) -> pd.DataFrame:
    """Combinações em que aprovação + reprovação + abandono estão presentes e não somam ~100."""
    piv = dados.pivot(index=[chave, "ano", "rede", "etapa"], columns="taxa", values="valor").dropna()
    soma = piv.sum(axis=1)
    fora = ((soma - 100).abs() > 0.5).to_numpy()
    return piv.loc[fora].assign(soma=soma[fora])


def gerar(md5: list[dict], diag: Diagnostico, rend_mun: pd.DataFrame, rend_ref: pd.DataFrame,
          ideb_mun: pd.DataFrame, ideb_ref: pd.DataFrame, tamanhos: dict[str, int]) -> dict:
    """Escreve o relatório e devolve um resumo com os números principais."""
    s = ["# Relatório de qualidade dos dados", "",
         "Gerado automaticamente por `python -m pipeline.run`. Não edite à mão.", ""]

    # 1. Integridade
    ok = sum(r["ok"] is True for r in md5)
    falhas = [r for r in md5 if r["ok"] is False]
    ausentes = [r for r in md5 if r["ok"] is None]
    s += ["## 1. Integridade dos arquivos (md5 do INEP)", "",
          f"- Conferidos: {len(md5)} · OK: {ok} · falhas: {len(falhas)} · citados no md5 mas ausentes do ZIP: {len(ausentes)}"]
    s += [f"  - FALHA: {r['zip']} / {r['arquivo']}" for r in falhas]
    s += [f"  - ausente: {r['zip']} / {r['arquivo']}" for r in ausentes]
    s.append("")

    # 2. Anos
    anos_mun = sorted(int(a) for a in rend_mun["ano"].unique())
    anos_ref = sorted(int(a) for a in rend_ref["ano"].unique())
    falta_mun = [a for a in ANOS_ESPERADOS if a not in anos_mun]
    falta_ref = [a for a in ANOS_ESPERADOS if a not in anos_ref]
    s += ["## 2. Anos disponíveis", "",
          f"- Rendimento por município: {anos_mun[0]}–{anos_mun[-1]}; anos faltantes: {falta_mun or 'nenhum'}",
          f"- Rendimento Brasil/UFs: {anos_ref[0]}–{anos_ref[-1]}; anos faltantes: {falta_ref or 'nenhum'}"]
    for e in ETAPAS:
        ed = sorted(int(a) for a in ideb_mun.loc[ideb_mun["etapa"] == e, "ano"].unique())
        s.append(f"- IDEB por município, {NOMES_ETAPA[e]}: edições {ed}")
    unid_por_ano = rend_ref.groupby("ano")["unidade"].nunique()
    incompletos = unid_por_ano[unid_por_ano != 28]
    s += [f"- Referências com Brasil + 27 UFs em todos os anos: {'sim' if incompletos.empty else incompletos.to_dict()}", ""]

    # 3. Cobertura por ano
    total = rend_mun[rend_mun["rede"] == "total"]
    linhas = []
    for ano, g in total.groupby("ano"):
        n = g["co_municipio"].nunique()
        sem = [g[(g["etapa"] == e) & (g["taxa"] == "aprovacao") & g["valor"].isna()]["co_municipio"].nunique()
               for e in ETAPAS]
        linhas.append([ano, n] + sem)
    s += ["## 3. Municípios por ano (rede Total)", "",
          "Colunas de etapa = municípios **sem** taxa de aprovação naquele ano (sem matrícula na etapa ou dado não divulgado).", "",
          _tabela(["Ano", "Municípios"] + [NOMES_ETAPA[e] for e in ETAPAS], linhas), ""]

    todos = set(rend_mun["co_municipio"])
    ausentes_ano = {a: sorted(todos - set(rend_mun.loc[rend_mun["ano"] == a, "co_municipio"])) for a in anos_mun}
    nomes = rend_mun.sort_values("ano").drop_duplicates("co_municipio", keep="last").set_index("co_municipio")
    novos = sorted({c for v in ausentes_ano.values() for c in v})
    s += ["## 4. Municípios que não existem em todos os anos", "",
          "Municípios criados depois de 2007 só têm dados a partir do ano de instalação (o gráfico mostra lacuna antes).", ""]
    s += [f"- {c} {nomes.at[c, 'nome']} ({nomes.at[c, 'uf']}): sem dados em "
          f"{[a for a, v in ausentes_ano.items() if c in v]}" for c in novos]
    s.append("")

    # 5. Municípios sem nenhum dado numa etapa
    vazio = total.groupby(["co_municipio", "etapa"])["valor"].apply(lambda v: v.isna().all())
    vazio = vazio[vazio].reset_index()
    s += ["## 5. Municípios sem nenhum dado de rendimento numa etapa (2007–2025, rede Total)", ""]
    for e in ETAPAS:
        cods = vazio.loc[vazio["etapa"] == e, "co_municipio"].tolist()
        ex = ", ".join(f"{nomes.at[c, 'nome']}-{nomes.at[c, 'uf']}" for c in cods[:8])
        s.append(f"- {NOMES_ETAPA[e]}: {len(cods)}" + (f" (ex.: {ex})" if cods else ""))
    s.append("")

    # 6. Valores fora da faixa e somas
    fora_mun = rend_mun[(rend_mun["valor"] < 0) | (rend_mun["valor"] > 100)]
    fora_ref = rend_ref[(rend_ref["valor"] < 0) | (rend_ref["valor"] > 100)]
    fora_ideb = pd.concat([ideb_mun, ideb_ref])
    fora_ideb = fora_ideb[(fora_ideb["valor"] < 0) | (fora_ideb["valor"] > 10)]
    soma_mun = _soma_fora_de_100(rend_mun, "co_municipio")
    soma_ref = _soma_fora_de_100(rend_ref, "unidade")
    s += ["## 6. Valores fora da faixa esperada", "",
          f"- Taxas fora de 0–100: municípios {len(fora_mun)}, referências {len(fora_ref)}",
          f"- IDEB fora de 0–10: {len(fora_ideb)}",
          f"- Aprovação + reprovação + abandono com diferença > 0,5 de 100: municípios {len(soma_mun)}, "
          f"referências {len(soma_ref)}", ""]

    # 7. Ausentes e textos não numéricos
    s += ["## 7. Textos não numéricos encontrados nas colunas de valor (tratados como ausentes)", "",
          _tabela(["Texto", "Ocorrências"], [[f"`{k}`" if k else "(vazio)", v] for k, v in diag.tokens.most_common()]),
          ""]

    # 8. IDEB
    cadastro = set(rend_mun.loc[rend_mun["ano"] == anos_mun[-1], "co_municipio"])
    linhas = []
    status = {}
    for e in ETAPAS:
        g = ideb_mun[(ideb_mun["etapa"] == e)]
        ultima = g["ano"].max()
        presentes = set(g["co_municipio"])
        divulgado = set(g.loc[(g["ano"] == ultima) & g["valor"].notna(), "co_municipio"])
        st = {"divulgado": len(cadastro & divulgado), "nao_divulgado": len(cadastro & (presentes - divulgado)),
              "sem_registro": len(cadastro - presentes)}
        status[e] = st
        linhas.append([NOMES_ETAPA[e], ultima, st["divulgado"], st["nao_divulgado"], st["sem_registro"]])
    s += ["## 8. IDEB na última edição (rede Pública)", "",
          "`nao_divulgado` = o município está na planilha mas com '-'; `sem_registro` = não aparece na planilha.", "",
          _tabela(["Etapa", "Edição", "Divulgado", "Não divulgado", "Sem registro"], linhas), "",
          "Referências: UFs usam rede Pública nos anos iniciais e finais e rede **Estadual** no ensino médio "
          "(a planilha de UFs não tem linha Pública no EM). Brasil usa rede Pública nas três etapas.", ""]

    # 9. Arquivos lidos e saídas
    s += ["## 9. Arquivos lidos", "",
          _tabela(["Fonte", "ZIP", "Arquivo", "Aba", "Ano(s)", "Linhas (formato longo)"],
                  [[f, z, a.split("/")[-1], ab, ", ".join(map(str, an)) if len(an) < 4 else f"{an[0]}–{an[-1]}", n]
                   for f, z, a, ab, an, n in diag.arquivos]), "",
          "## 10. Arquivos gerados", "",
          _tabela(["Arquivo", "Tamanho (KB)"], [[k, round(v / 1024, 1)] for k, v in sorted(tamanhos.items())]), ""]
    if diag.avisos:
        s += ["## Avisos", ""] + [f"- {a}" for a in diag.avisos] + [""]

    RELATORIO.write_text("\n".join(s), encoding="utf-8")
    return {"md5_falhas": len(falhas), "anos_faltantes": falta_mun + falta_ref, "fora_faixa": len(fora_mun) + len(fora_ref),
            "ideb_fora_faixa": len(fora_ideb), "soma_fora_100": len(soma_mun) + len(soma_ref), "ideb_status": status,
            "municipios": len(todos)}
