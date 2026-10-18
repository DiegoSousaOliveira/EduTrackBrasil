# Inspeção dos dados brutos do INEP

Registro da Etapa 1: como os arquivos em `data/raw/` são de verdade, antes de escrever o pipeline.
Tudo aqui foi verificado abrindo os arquivos, não suposto.

## Visão geral

| Pasta | Arquivos | Conteúdo |
|---|---|---|
| `rendimento/municipios/` | 19 ZIPs (2007–2025) | 1 planilha por ano; 2007 e 2011 têm 2 abas (N/NE/CO e S/SE) |
| `rendimento/brasil_uf/` | 19 ZIPs (2007–2025) | 2007–2016: 3 arquivos separados (Brasil, Regiões, UFs); 2017–2025: 1 arquivo combinado |
| `ideb/` | 5 ZIPs | AI, AF e EM por município; Regiões/UFs (3 abas); Brasil (3 abas) |

- Todos os arquivos são ZIP. A partir de 2015 cada ZIP traz `.xlsx` + `.ods` + `md5`. **Os md5 conferem em todos.**
- Formatos: `.xls` em 2007–2011 (e regiões até 2014), `.xlsx` no resto.
- Nomes de arquivo dentro dos ZIPs antigos estão em CP437 (`REGI�ES`). O ano sai do nome do ZIP e é confirmado pela coluna `Ano`.
- `TAXAS RENDIMENTO UF 2008.xls` tem a aba chamada "Rendimento por UF - **2009**", mas a coluna `Ano` diz 2008 e os valores diferem do arquivo de 2009 (0 linhas iguais). É só erro no nome da aba.
- O arquivo de municípios de 2022 está no mesmo formato INEP dos demais (md5 do INEP confere, 27 UFs, 5.570 municípios, 61 colunas).

## Taxas de rendimento por município

**Cabeçalho:** 3–4 linhas de título, depois um cabeçalho de 3 linhas mescladas (indicador › etapa › série).
A linha "Ano/Região/UF/…" é a linha 6 (base 0) em 2007–2015 e a linha 5 em 2016–2025.
Dados começam na linha 9 (linha 10 em 2015). Em 2020–2025 há uma linha extra de códigos (`NU_ANO_CENSO`, `1_CAT_FUN_AI`…).

**Colunas de identificação (7):** Ano, Região, UF, Código do Município, Nome do Município, Localização, Rede/Dependência Administrativa.

**Colunas de valores (54):** 3 blocos de 18 (aprovação, reprovação, abandono). A ordem dentro do bloco muda:

| Layout | Anos | Fund. total | Anos iniciais | Anos finais | Médio total |
|---|---|---|---|---|---|
| A | 2007–2010 | col 18 | col 16 ("1ª a 4ª Série/1º a 5º Ano") | col 17 ("5ª a 8ª Série/6º ao 9º Ano") | col 24 |
| B | 2011–2025 | col 7 | col 8 | col 9 | col 19 |

→ o pipeline localiza colunas **pelo texto do cabeçalho**, não pela posição. Validação: aprovação + reprovação + abandono = 100,0 em todos os anos e etapas, no recorte Total/Total.

**Valores categóricos (variam entre anos):**
- Rede: `Publico` (2007–2014) / `Pública` (2015+); `Particular` / `Privada`; `Total`, `Federal`, `Estadual`, `Municipal`.
- Localização: `Total`, `Urbana`, `Rural`.
- Região: `Centro_Oeste` (até 2014) / `Centro-Oeste`.
- Nome do município: MAIÚSCULO sem acento até 2014 (`SAO DOMINGOS`), grafia correta a partir de 2015 (`São Domingos`). Usar o nome do ano mais recente.

**Ausentes:** só `--`. Não há "ND", "-" nem vírgula decimal. Há 1 célula vazia (2007). Valores entre 0 e 100.
**Floats longos:** 2007 tem ~160 mil valores como `73.09999999999998` → arredondar para 1 casa.
**Rodapé:** linha "Fonte: …" e, até 2015, 3 linhas de "Notas".

**Cobertura:** todo município tem as linhas Total/Total e Total/Pública em todos os anos.

| Anos | Municípios |
|---|---|
| 2007–2008 | 5.564 |
| 2009–2012 | 5.565 (entra Nazária-PI) |
| 2013–2024 | 5.570 (entram Mojuí dos Campos-PA, Pescaria Brava-SC, Balneário Rincão-SC, Pinto Bandeira-RS, Paraíso das Águas-MS) |
| 2025 | 5.571 (entra Boa Esperança do Norte-MT, código 5101837) |

## Taxas de rendimento — Brasil, Regiões e UFs

- Mesmos 54 valores por linha e os mesmos dois layouts (A em 2007–2010, B em 2011–2025).
- Identificação da unidade muda: sigla (`PI`) em 2007–2014; nome (`Piauí`) em 2015–2016; coluna única "Unidade Geográfica" com Brasil + regiões + UFs misturados em 2017–2025.
- Arquivos de Brasil de 2009–2014 trazem Rede **antes** de Localização (ordem das colunas trocada).
- Brasil aparece como `Brasil` ou `BRASIL`.
- **Armadilha:** em 2016–2020 há uma linha de códigos internos (`tap_fun`, `tap_f14`…) que está **desalinhada em 2020** (a coluna "Anos Finais" tem o código `tap_f04`). Os valores seguem o rótulo descritivo → o pipeline ignora essa linha de códigos.

## IDEB 2025

- Cabeçalho de códigos na linha 9 (base 0); dados a partir da linha 10; ~15 linhas de notas no fim.
- Municípios: colunas `SG_UF`, `CO_MUNICIPIO` (7 dígitos), `NO_MUNICIPIO`, `REDE` (`Estadual`, `Municipal`, `Federal`, `Pública`), depois, por edição: `VL_APROVACAO_*`, `VL_INDICADOR_REND_*`, `VL_NOTA_MATEMATICA_*`, `VL_NOTA_PORTUGUES_*`, `VL_NOTA_MEDIA_*`, `VL_OBSERVADO_*` (o IDEB) e `VL_PROJECAO_*` (metas até 2021).
- Séries: anos iniciais e finais 2005–2025 (11 edições); ensino médio municipal só 2017–2025 (5 edições).
- Ausentes: `-` (vazio), `ND`, `ND*`, `ND***` (cada um explicado nas notas). No IDEB (`VL_OBSERVADO`) só aparece `-`.
- Vírgula decimal: só em `VL_NOTA_MATEMATICA_2015` e `VL_NOTA_PORTUGUES_2015` (AI e AF). O IDEB usa ponto.
- Rede Pública: 5.568 municípios em AI, 5.569 em AF, 5.563 em EM. IDEB 2025 numérico: 5.478 (AI), 5.491 (AF), 5.428 (EM).
- Municípios sem linha Pública: AI → Pescaria Brava-SC, Carlos Gomes-RS, Novo Cabrais-RS (+ Boa Esperança do Norte, que é novo); EM → 8 municípios (ex.: Campo Grande-AL, Roteiro-AL).
- Para a rede Pública, quando o IDEB é `-` a nota Saeb também é `-`; o arquivo não diz o motivo exato (ND só aparece em outras redes).
- Regiões/UFs: sem códigos nas 2 primeiras colunas; UFs por **nome abreviado** (`R. G. do Norte`, `M. G. do Sul`); rede com marcadores de nota (`Pública (4)`, `Total (3)(4)`); **`VL_INDICADOR_REND_2023` aparece duas vezes** na aba AI (a 2ª deveria ser 2025).
- Brasil: a coluna do IDEB 2023 na aba "Anos Finais" está **sem código** (só o rótulo "IDEB 2023"); rótulos de 2021 vêm com o número da nota colado (`20212`).
