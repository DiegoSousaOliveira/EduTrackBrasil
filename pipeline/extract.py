"""Leitura dos arquivos brutos do INEP direto dos ZIPs (sem extrair nada no disco).

Aqui ficam as funções "de baixo nível": abrir planilhas, conferir md5,
achar onde começa o cabeçalho e transformar os rótulos das colunas em
algo comparável entre anos. Ver docs/inspecao_dados.md para o porquê de cada regra.
"""
import hashlib
import io
import re
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
RAW_DIR = RAIZ / "data" / "raw"
EXTENSOES_PLANILHA = (".xls", ".xlsx")

# Valores que o INEP usa para "sem dado". Qualquer outro texto não numérico
# também vira ausente, mas é contado para aparecer no relatório de qualidade.
AUSENTES_CONHECIDOS = {"", "--", "-", "nd", "nd*", "nd**", "nd***"}

UFS = {
    "RO": "Rondônia", "AC": "Acre", "AM": "Amazonas", "RR": "Roraima", "PA": "Pará",
    "AP": "Amapá", "TO": "Tocantins", "MA": "Maranhão", "PI": "Piauí", "CE": "Ceará",
    "RN": "Rio Grande do Norte", "PB": "Paraíba", "PE": "Pernambuco", "AL": "Alagoas",
    "SE": "Sergipe", "BA": "Bahia", "MG": "Minas Gerais", "ES": "Espírito Santo",
    "RJ": "Rio de Janeiro", "SP": "São Paulo", "PR": "Paraná", "SC": "Santa Catarina",
    "RS": "Rio Grande do Sul", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
    "GO": "Goiás", "DF": "Distrito Federal",
}


def normalizar(texto) -> str:
    """Minúsculas, sem acento e com espaços simples. 'Anos Iniciais (1º ao 5º Ano)' -> 'anos iniciais (1o ao 5o ano)'."""
    s = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def _so_letras(texto) -> str:
    return re.sub(r"[^a-z]", "", normalizar(texto))


_CHAVES_UF = {sigla.lower(): sigla for sigla in UFS}
_CHAVES_UF.update({_so_letras(nome): sigla for sigla, nome in UFS.items()})
# Abreviações usadas na planilha de Regiões/UFs do IDEB
_CHAVES_UF.update({"rgdonorte": "RN", "rgdosul": "RS", "mgdosul": "MS"})


def chave_unidade(texto) -> str | None:
    """Converte 'Brasil', 'PI', 'Piauí' ou 'R. G. do Norte' em 'BR'/'PI'/'RN'. Regiões e textos desconhecidos -> None."""
    chave = _so_letras(texto)
    if chave == "brasil":
        return "BR"
    return _CHAVES_UF.get(chave)


def para_numero(serie: pd.Series, tokens: Counter | None = None) -> pd.Series:
    """Texto -> número com 1 casa decimal. Ausentes ('--', '-', 'ND'...) viram NaN.

    Textos não numéricos são contados em `tokens` para o relatório de qualidade.
    """
    s = serie.fillna("").astype(str).str.strip()
    s = s.str.replace(",", ".", regex=False)  # vírgula decimal
    num = pd.to_numeric(s, errors="coerce")
    if tokens is not None:
        tokens.update(s[num.isna()].value_counts().to_dict())
    # 2007 tem valores como 73.09999999999998 (artefato de ponto flutuante)
    return num.round(1)


def ler_planilhas(zip_path: Path) -> list[tuple[str, str, pd.DataFrame]]:
    """Lê todas as abas de todas as planilhas (.xls/.xlsx) de um ZIP.

    Retorna [(nome_do_arquivo, nome_da_aba, DataFrame_bruto)], tudo como texto.
    Os .ods duplicados e arquivos temporários (~$...) são ignorados.
    """
    saida = []
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            nome = Path(info.filename).name
            if info.is_dir() or nome.startswith("~$") or not nome.lower().endswith(EXTENSOES_PLANILHA):
                continue
            abas = pd.read_excel(io.BytesIO(z.read(info)), sheet_name=None, header=None,
                                 dtype=str, engine="calamine")
            for aba, df in abas.items():
                saida.append((info.filename, aba, df))
    return saida


def verificar_md5(zip_path: Path) -> list[dict]:
    """Confere os arquivos md5 que o INEP inclui nos ZIPs (a partir de 2015).

    Cada linha do .txt tem 'hash  nome_do_arquivo'. Retorna um dict por linha
    com ok=True/False, ou ok=None quando o arquivo citado não está no ZIP.
    """
    resultados = []
    with zipfile.ZipFile(zip_path) as z:
        membros = {Path(n).name.lower(): n for n in z.namelist()}
        for n in z.namelist():
            if not n.lower().endswith(".txt"):
                continue
            for linha in z.read(n).decode("latin-1").splitlines():
                m = re.match(r"\s*([0-9a-fA-F]{32})\s+\*?(.+?)\s*$", linha)
                if not m:
                    continue
                alvo = Path(m.group(2)).name
                membro = membros.get(alvo.lower())
                ok = None
                if membro:
                    ok = hashlib.md5(z.read(membro)).hexdigest().lower() == m.group(1).lower()
                resultados.append({"zip": zip_path.name, "arquivo": alvo, "ok": ok})
    return resultados


_ANO = re.compile(r"^(19|20)\d\d(\.0)?$")


def localizar_cabecalho(df: pd.DataFrame) -> tuple[int, list[int]]:
    """Planilhas de rendimento: devolve (linha onde começa o cabeçalho, linhas de dados).

    O cabeçalho começa na linha cuja 1ª coluna é 'Ano'. Linhas de dados são as
    que têm um ano na 1ª coluna — isso descarta títulos e notas de rodapé.
    """
    col0 = df[0].fillna("").astype(str).str.strip()
    dados = [i for i, v in col0.items() if _ANO.match(v)]
    if not dados:
        raise ValueError("nenhuma linha de dados com ano na 1ª coluna")
    inicio = [i for i, v in col0.items() if normalizar(v) == "ano" and i < dados[0]]
    if not inicio:
        raise ValueError("linha de cabeçalho 'Ano' não encontrada")
    return inicio[0], dados


def rotulos_colunas(df: pd.DataFrame, inicio: int, primeira_linha_dados: int) -> list[str]:
    """Junta o cabeçalho de várias linhas em um rótulo por coluna.

    Ex.: 'taxa de aprovacao > ensino fundamental de 8 e 9 anos > anos iniciais'.
    - Linhas de códigos internos (NU_ANO_CENSO, tap_fun...) são descartadas:
      em 2020 elas estão desalinhadas das colunas reais.
    - Células mescladas só têm texto na 1ª coluna do grupo, então os rótulos
      de grupo são propagados para a direita (exceto na última linha, a das folhas).
    """
    bloco = df.iloc[inicio:primeira_linha_dados]
    bloco = bloco.dropna(how="all")
    tem_codigo = bloco.apply(lambda r: r.fillna("").astype(str).str.contains("_").any(), axis=1)
    bloco = bloco[~tem_codigo]
    linhas = [row.ffill() if i < len(bloco) - 1 else row for i, (_, row) in enumerate(bloco.iterrows())]
    rotulos = []
    for col in df.columns:
        partes = []
        for row in linhas:
            v = row[col]
            if isinstance(v, str) and v.strip():
                n = normalizar(v)
                if n not in partes:
                    partes.append(n)
        rotulos.append(" > ".join(partes))
    return rotulos


def localizar_cabecalho_ideb(df: pd.DataFrame) -> int:
    """IDEB: a linha de códigos (SG_UF, VL_OBSERVADO_2025...) é a que tem células começando com 'VL_'."""
    for i in range(min(40, len(df))):
        if df.iloc[i].fillna("").astype(str).str.startswith("VL_").any():
            return i
    raise ValueError("linha de códigos do IDEB não encontrada")


def colunas_ideb(df: pd.DataFrame, linha_codigos: int) -> dict[int, int]:
    """Devolve {ano: índice_da_coluna} das colunas do IDEB observado.

    Usa o código VL_OBSERVADO_AAAA; quando ele falta (IDEB 2023 de Anos Finais
    no arquivo do Brasil), usa o rótulo 'IDEB 2023 (N x P)'. Rótulos como
    'IDEB 20212' (número de nota colado ao ano) usam só os 4 primeiros dígitos.
    """
    anos = {}
    for c in df.columns:
        codigo = str(df.iloc[linha_codigos, c]).strip()
        m = re.fullmatch(r"VL_OBSERVADO_(\d{4})", codigo)
        if not m:
            rotulo = normalizar(" ".join(str(v) for v in df.iloc[max(0, linha_codigos - 3):linha_codigos, c]
                                         if isinstance(v, str)))
            m = re.match(r"ideb (\d{4})", rotulo) if codigo in ("", "nan") else None
        if m:
            ano = int(m.group(1))
            if ano in anos:
                raise ValueError(f"IDEB {ano} aparece em duas colunas ({anos[ano]} e {c})")
            anos[ano] = c
    if not anos:
        raise ValueError("nenhuma coluna de IDEB observado encontrada")
    return dict(sorted(anos.items()))
