"""Executa o pipeline completo: python -m pipeline.run (a partir da raiz do projeto)."""
import time
import warnings

from pipeline import export, quality, transform
from pipeline.extract import RAW_DIR, verificar_md5


def main() -> None:
    warnings.filterwarnings("ignore", category=UserWarning)  # avisos de estilo das planilhas
    inicio = time.time()
    diag = transform.Diagnostico()

    print("1/6 Conferindo md5 dos ZIPs...")
    md5 = [r for z in sorted(RAW_DIR.rglob("*.zip")) if "escolas" not in z.parts for r in verificar_md5(z)]

    print("2/6 Rendimento por município (19 planilhas, ~1 min)...")
    rend_mun = transform.rendimento_municipios(diag)
    print("3/6 Rendimento de Brasil e UFs...")
    rend_ref = transform.rendimento_referencias(diag)
    print("4/6 IDEB...")
    ideb_mun = transform.ideb_municipios(diag)
    ideb_ref = transform.ideb_referencias(diag)

    print("5/6 Gerando JSONs em site/data/...")
    tamanhos = export.exportar(rend_mun, rend_ref, ideb_mun, ideb_ref)

    print("6/6 Relatório de qualidade...")
    resumo = quality.gerar(md5, diag, rend_mun, rend_ref, ideb_mun, ideb_ref, tamanhos)

    print(f"\nPronto em {time.time() - inicio:.0f}s.")
    print(f"  Municípios: {resumo['municipios']}")
    print(f"  md5 com falha: {resumo['md5_falhas']} | anos faltantes: {resumo['anos_faltantes'] or 'nenhum'}")
    print(f"  Taxas fora de 0–100: {resumo['fora_faixa']} | IDEB fora de 0–10: {resumo['ideb_fora_faixa']} "
          f"| somas != 100: {resumo['soma_fora_100']}")
    for etapa, st in resumo["ideb_status"].items():
        print(f"  IDEB {etapa}: {st}")
    print(f"  Relatório: {quality.RELATORIO.relative_to(quality.RAIZ)}")


if __name__ == "__main__":
    main()
