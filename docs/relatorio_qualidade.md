# Relatório de qualidade dos dados

Gerado automaticamente por `python -m pipeline.run`. Não edite à mão.

## 1. Integridade dos arquivos (md5 do INEP)

- Conferidos: 62 · OK: 62 · falhas: 0 · citados no md5 mas ausentes do ZIP: 0

## 2. Anos disponíveis

- Rendimento por município: 2007–2025; anos faltantes: nenhum
- Rendimento Brasil/UFs: 2007–2025; anos faltantes: nenhum
- IDEB por município, Fund. anos iniciais: edições [2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023, 2025]
- IDEB por município, Fund. anos finais: edições [2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023, 2025]
- IDEB por município, Ensino médio: edições [2017, 2019, 2021, 2023, 2025]
- Referências com Brasil + 27 UFs em todos os anos: sim

## 3. Municípios por ano (rede Total)

Colunas de etapa = municípios **sem** taxa de aprovação naquele ano (sem matrícula na etapa ou dado não divulgado).

| Ano | Municípios | Fund. anos iniciais | Fund. anos finais | Ensino médio |
|---|---|---|---|---|
| 2007 | 5564 | 1 | 0 | 50 |
| 2008 | 5564 | 2 | 4 | 25 |
| 2009 | 5565 | 0 | 0 | 19 |
| 2010 | 5565 | 0 | 0 | 14 |
| 2011 | 5565 | 0 | 0 | 13 |
| 2012 | 5565 | 0 | 0 | 12 |
| 2013 | 5570 | 0 | 0 | 10 |
| 2014 | 5570 | 0 | 0 | 10 |
| 2015 | 5570 | 0 | 0 | 10 |
| 2016 | 5570 | 0 | 0 | 9 |
| 2017 | 5570 | 0 | 0 | 10 |
| 2018 | 5570 | 0 | 0 | 9 |
| 2019 | 5570 | 0 | 0 | 9 |
| 2020 | 5570 | 8 | 9 | 9 |
| 2021 | 5570 | 0 | 0 | 9 |
| 2022 | 5570 | 0 | 0 | 7 |
| 2023 | 5570 | 1 | 1 | 7 |
| 2024 | 5570 | 0 | 0 | 7 |
| 2025 | 5571 | 0 | 0 | 7 |

## 4. Municípios que não existem em todos os anos

Municípios criados depois de 2007 só têm dados a partir do ano de instalação (o gráfico mostra lacuna antes).

- 1504752 Mojuí dos Campos (PA): sem dados em [2007, 2008, 2009, 2010, 2011, 2012]
- 2206720 Nazária (PI): sem dados em [2007, 2008]
- 4212650 Pescaria Brava (SC): sem dados em [2007, 2008, 2009, 2010, 2011, 2012]
- 4220000 Balneário Rincão (SC): sem dados em [2007, 2008, 2009, 2010, 2011, 2012]
- 4314548 Pinto Bandeira (RS): sem dados em [2007, 2008, 2009, 2010, 2011, 2012]
- 5006275 Paraíso das Águas (MS): sem dados em [2007, 2008, 2009, 2010, 2011, 2012]
- 5101837 Boa Esperança do Norte (MT): sem dados em [2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]

## 5. Municípios sem nenhum dado de rendimento numa etapa (2007–2025, rede Total)

- Fund. anos iniciais: 0
- Fund. anos finais: 0
- Ensino médio: 6 (ex.: Chapada de Areia-TO, Monte Santo do Tocantins-TO, Jequiá da Praia-AL, Roteiro-AL, Serra da Saudade-MG, São Pedro da Serra-RS)

## 6. Valores fora da faixa esperada

- Taxas fora de 0–100: municípios 0, referências 0
- IDEB fora de 0–10: 0
- Aprovação + reprovação + abandono com diferença > 0,5 de 100: municípios 0, referências 0

## 7. Textos não numéricos encontrados nas colunas de valor (tratados como ausentes)

| Texto | Ocorrências |
|---|---|
| `-` | 56594 |
| `--` | 1695 |

## 8. IDEB na última edição (rede Pública)

`nao_divulgado` = o município está na planilha mas com '-'; `sem_registro` = não aparece na planilha.

| Etapa | Edição | Divulgado | Não divulgado | Sem registro |
|---|---|---|---|---|
| Fund. anos iniciais | 2025 | 5478 | 90 | 3 |
| Fund. anos finais | 2025 | 5491 | 78 | 2 |
| Ensino médio | 2025 | 5428 | 135 | 8 |

Referências: UFs usam rede Pública nos anos iniciais e finais e rede **Estadual** no ensino médio (a planilha de UFs não tem linha Pública no EM). Brasil usa rede Pública nas três etapas.

## 9. Arquivos lidos

| Fonte | ZIP | Arquivo | Aba | Ano(s) | Linhas (formato longo) |
|---|---|---|---|---|---|
| rendimento_municipios | TAXA_REND_2016_MUNICIPIOS.zip | TX_REND_MUNICIPIOS_2016.xlsx | MUNICIPIOS  | 2016 | 100260 |
| rendimento_municipios | TAXA_REND_2017_MUNICIPIOS.zip | TX_REND_MUNICIPIOS_2017.xlsx | MUNICIPIOS  | 2017 | 100260 |
| rendimento_municipios | TX_REND_MUNICIPIOS_2018.zip | TX_REND_MUNICIPIOS_2018.xlsx | MUNICIPIOS  | 2018 | 100260 |
| rendimento_municipios | tx_rend_municipios_2019.zip | tx_rend_municipios_2019.xlsx | MUNICIPIOS  | 2019 | 100260 |
| rendimento_municipios | tx_rend_municipios_2020.zip | tx_rend_municipios_2020.xlsx | MUNICIPIOS  | 2020 | 100260 |
| rendimento_municipios | tx_rend_municipios_2021.zip | tx_rend_municipios_2021.xlsx | MUNICIPIOS  | 2021 | 100260 |
| rendimento_municipios | tx_rend_municipios_2022.zip | tx_rend_municipios_2022.xlsx | MUNICIPIOS  | 2022 | 100260 |
| rendimento_municipios | tx_rend_municipios_2023.zip | tx_rend_municipios_2023.xlsx | MUNICIPIOS  | 2023 | 100260 |
| rendimento_municipios | tx_rend_municipios_2024.zip | tx_rend_municipios_2024.xlsx | MUNICIPIOS  | 2024 | 100260 |
| rendimento_municipios | tx_rend_municipios_2025.zip | tx_rend_municipios_2025.xlsx | MUNICIPIOS  | 2025 | 100278 |
| rendimento_municipios | tx_rendimento_municipios_2007.zip | TX RENDIMENTO MUNIC╓PIOS 2007.XLS | REND MUN NO, NE E CO | 2007 | 48744 |
| rendimento_municipios | tx_rendimento_municipios_2007.zip | TX RENDIMENTO MUNIC╓PIOS 2007.XLS | REND MUN SUL E SE | 2007 | 51408 |
| rendimento_municipios | tx_rendimento_municipios_2008.zip | TX RENDIMENTOS MUNICIPIOS 2008.xls | Tx Rendimento Municípios | 2008 | 100152 |
| rendimento_municipios | tx_rendimento_municipios_2009.zip | TX RENDIMENTOS MUNICIPIOS 2009.xls | Tx Rendimento Municípios | 2009 | 100170 |
| rendimento_municipios | tx_rendimento_municipios_2010.zip | TX RENDIMENTO MUNICIPIOS 2010.xls | RENDIMENTOS MUNICIPIOS 2010 | 2010 | 100170 |
| rendimento_municipios | tx_rendimento_municipios_2011_2.zip | tx_rendimento_municipios_2011.xls | MUNICÍPIOS - NORTE-NE-CO | 2011 | 48762 |
| rendimento_municipios | tx_rendimento_municipios_2011_2.zip | tx_rendimento_municipios_2011.xls | MUNICÍPIOS - SUL-SUDESTE | 2011 | 51408 |
| rendimento_municipios | tx_rendimento_municipios_2012.zip | tx_rendimento_municipios_2012.xlsx | MUNICIPIOS 2012 | 2012 | 100170 |
| rendimento_municipios | tx_rendimento_municipios_2013.zip | TAXAS RENDIMENTOS MUNICIPIOS 2013.xlsx | MUNICIPIOS 2013 | 2013 | 100260 |
| rendimento_municipios | tx_rendimento_municipios_2014.zip | TAXAS RENDIMENTOS MUNICIPIOS 2014.xlsx | MUNICIPIOS  | 2014 | 100260 |
| rendimento_municipios | tx_rendimento_municipios_2015.zip | TX_REND_MUN_2015.xlsx | MUNICIPIOS  | 2015 | 100260 |
| rendimento_referencias | TAXA_REND_2016_BRASIL_REGIOES_UFS.zip | TX_REND_BRASIL_2016.xlsx | BRASIL | 2016 | 18 |
| rendimento_referencias | TAXA_REND_2016_BRASIL_REGIOES_UFS.zip | TX_REND_REGIOES_2016.xlsx | REGIÕES |  | 0 |
| rendimento_referencias | TAXA_REND_2016_BRASIL_REGIOES_UFS.zip | TX_REND_UFS_2016.xlsx | UF  | 2016 | 486 |
| rendimento_referencias | TAXA_REND_2017_BRASIL_REGIOES_UFS.zip | TX_REND_BRASIL_REGIOES_UFS_2017.xlsx | BRASIL_REGIOES_UFS  | 2017 | 504 |
| rendimento_referencias | TX_REND_BRASIL_REGIOES_UFS_2018.zip | TX_REND_BRASIL_REGIOES_UFS_2018.xlsx | BRASIL_REGIOES_UFS  | 2018 | 504 |
| rendimento_referencias | tx_rend_brasil_regioes_ufs_2019.zip | tx_rend_brasil_regioes_ufs_2019.xlsx | BRASIL_REGIOES_UFS  | 2019 | 504 |
| rendimento_referencias | tx_rend_brasil_regioes_ufs_2020.zip | tx_rend_brasil_regioes_ufs_2020.xlsx | BRASIL_REGIOES_UFS  | 2020 | 504 |
| rendimento_referencias | tx_rend_brasil_regioes_ufs_2021.zip | tx_rend_brasil_regioes_ufs_2021.xlsx | BRASIL_REGIOES_UFS  | 2021 | 504 |
| rendimento_referencias | tx_rend_brasil_regioes_ufs_2022.zip | tx_rend_brasil_regioes_ufs_2022.xlsx | BRASIL_REGIOES_UFS  | 2022 | 504 |
| rendimento_referencias | tx_rend_brasil_regioes_ufs_2023.zip | tx_rend_brasil_regioes_ufs_2023.xlsx | BRASIL_REGIOES_UFS  | 2023 | 504 |
| rendimento_referencias | tx_rend_brasil_regioes_ufs_2024.zip | tx_rend_brasil_regioes_ufs_2024.xlsx | BRASIL_REGIOES_UFS  | 2024 | 504 |
| rendimento_referencias | tx_rend_brasil_regioes_ufs_2025.zip | tx_rend_brasil_regioes_ufs_2025.xlsx | BRASIL_REGIOES_UFS  | 2025 | 504 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2007.zip | Taxas de Rendimento_ REGIσES_ 2007.xls | REND. REGIÕES 2007 |  | 0 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2007.zip | TX RENDIMENTO BRASIL 2007.xls | REND. BRASIL 2007 | 2007 | 18 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2007.zip | TX RENDIMENTO UFS 2007.xls | REND. POR UF | 2007 | 486 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2008.zip | Taxas de Rendimento_REGIσES_ 2008.xls | Tx Rendimento - 2008 |  | 0 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2008.zip | TAXAS RENDIMENTO UF 2008.xls | Rendimento por UF - 2009 | 2008 | 486 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2008.zip | TX DE RENDIMENTO BRASIL 2008.xls | QUERY_FOR_RENDIMENTOUFREGBRASIL | 2008 | 18 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2009.zip | TAXAS RENDIMENTO BRASIL 2009.xls | Rendimento Brasil | 2009 | 18 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2009.zip | TAXAS RENDIMENTO REGIσES 2009.xls | Tx Rendimento - 2009 |  | 0 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2009.zip | TAXAS RENDIMENTO UF 2009.xls | Rendimento por UF - 2009 | 2009 | 486 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2010.zip | TAXAS RENDIMENTO UF 2010.xls | RENDIMENTOS UFS 2010 | 2010 | 486 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2010.zip | TAXAS RENDIMENTO BRASIL 2010.xls | Rendimento Brasil 2010 | 2010 | 18 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2010.zip | TAXAS RENDIMENTO REGIσES 2010.xls | RENDIMENTOS REGIÕES 2010 |  | 0 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2011_2.zip | tx_rendimento_brasil_2011.xls | Rendimento Brasil 2011 | 2011 | 18 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2011_2.zip | tx_rendimento_regiΣes_2011.xls | RENDIMENTOS REGIÕES 2011 |  | 0 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2011_2.zip | tx_rendimento_uf_2011.xls | RENDIMENTOS UFS 2011 | 2011 | 486 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2012.zip | tx_rendimento_brasil_2012.xlsx | BRASIL 2012 | 2012 | 18 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2012.zip | tx_rendimento_regioes_2012.xls | RENDIMENTOS REGIÕES 2012 |  | 0 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2012.zip | tx_rendimento_UFs_2012.xlsx | UF 2012 | 2012 | 486 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2013.zip | TAXAS RENDIMENTO REGIσES 2013.xls | RENDIMENTOS REGIÕES 2013 |  | 0 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2013.zip | TAXAS RENDIMENTOS BRASIL 2013.xlsx | BRASIL 2013 | 2013 | 18 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2013.zip | TAXAS RENDIMENTOS UF 2013.xlsx | UF 2013 | 2013 | 486 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2014.zip | TAXAS RENDIMENTOS BRASIL 2014.xlsx | BRASIL | 2014 | 18 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2014.zip | TAXAS RENDIMENTOS REGIσES 2014.xls | REGIÕES |  | 0 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2014.zip | TAXAS RENDIMENTOS UF 2014.xlsx | UF  | 2014 | 486 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2015.zip | TX_REND_BRASIL_2015.xlsx | BRASIL | 2015 | 18 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2015.zip | TX_REND_REG_2015.xlsx | REGIÕES |  | 0 |
| rendimento_referencias | tx_rendimento_brasil_regioes_UFs_2015.zip | TX_REND_UFS_2015.xlsx | UF  | 2015 | 486 |
| ideb_municipios | divulgacao_anos_iniciais_municipios_2025.zip | divulgacao_anos_iniciais_municipios_2025.xlsx | IDEB_AI_MUNICÍPIOS | 2005–2025 | 61248 |
| ideb_municipios | divulgacao_anos_finais_municipios_2025.zip | divulgacao_anos_finais_municipios_2025.xlsx | IDEB_AF_MUNICÍPIOS | 2005–2025 | 61259 |
| ideb_municipios | divulgacao_ensino_medio_municipios_2025.zip | divulgacao_ensino_medio_municipios_2025.xlsx | IDEB_Municípios (ENSINO MÉDIO) | 2017–2025 | 27815 |
| ideb_referencias | divulgacao_regioes_ufs_ideb_2025.zip | divulgacao_regioes_ufs_ideb_2025.xlsx | UF e Regiões (AI) | 2005–2025 | 297 |
| ideb_referencias | divulgacao_regioes_ufs_ideb_2025.zip | divulgacao_regioes_ufs_ideb_2025.xlsx | UF e Regiões (AF) | 2005–2025 | 297 |
| ideb_referencias | divulgacao_regioes_ufs_ideb_2025.zip | divulgacao_regioes_ufs_ideb_2025.xlsx | UF e Regiões (EM) | 2005–2025 | 297 |
| ideb_referencias | divulgacao_brasil_ideb_2025.zip | divulgacao_brasil_ideb_2025.xlsx | Brasil (Anos Iniciais) | 2005–2025 | 11 |
| ideb_referencias | divulgacao_brasil_ideb_2025.zip | divulgacao_brasil_ideb_2025.xlsx | Brasil (Anos Finais) | 2005–2025 | 11 |
| ideb_referencias | divulgacao_brasil_ideb_2025.zip | divulgacao_brasil_ideb_2025.xlsx | Brasil (EM) | 2005–2025 | 11 |

## 10. Arquivos gerados

| Arquivo | Tamanho (KB) |
|---|---|
| municipios.json | 390.3 |
| referencias.json | 59.8 |
| uf/AC.json | 46.7 |
| uf/AL.json | 218.9 |
| uf/AM.json | 131.2 |
| uf/AP.json | 34.7 |
| uf/BA.json | 892.2 |
| uf/CE.json | 384.1 |
| uf/DF.json | 2.5 |
| uf/ES.json | 164.4 |
| uf/GO.json | 515.1 |
| uf/MA.json | 458.4 |
| uf/MG.json | 1793.0 |
| uf/MS.json | 169.2 |
| uf/MT.json | 300.6 |
| uf/PA.json | 309.6 |
| uf/PB.json | 475.8 |
| uf/PE.json | 390.1 |
| uf/PI.json | 477.2 |
| uf/PR.json | 837.3 |
| uf/RJ.json | 195.9 |
| uf/RN.json | 359.7 |
| uf/RO.json | 110.1 |
| uf/RR.json | 32.1 |
| uf/RS.json | 1052.5 |
| uf/SC.json | 618.0 |
| uf/SE.json | 161.8 |
| uf/SP.json | 1341.0 |
| uf/TO.json | 292.4 |
