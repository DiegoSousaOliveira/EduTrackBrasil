# Plano de medição – EduTrackBrasil

> Gerado por `python -m tracking.gerar` a partir de `tracking/schema/events.schema.json`. Não edite à mão: mude o schema e gere de novo.

**Versão do contrato:** `1.0.0` · **Eventos:** 8 · **Implementação:** `site/js/track.js` (helper) e `site/js/app.js` (gatilhos)

## 1. Objetivo e KPIs

**Objetivo:** ajudar cidadãos a entender a educação do próprio município.

| KPI | Como medir |
|---|---|
| Engajamento com a busca | % de sessões com `select_content` |
| Busca sem resultado | `search` com `results_count = 0` ÷ total de `search` (mostra como as pessoas escrevem os nomes) |
| Consumo dos dados | % de sessões com `view_chart` (por `chart_id`) |
| Intenção de compartilhar | `generate_card` ÷ sessões com `select_content` |
| Conversão (evento-chave) | `share` ÷ `generate_card`, quebrado por `method` |
| Lacunas de dado vistas | `data_unavailable` por `motivo` e `etapa` |

**Funil:** `page_view` → `search` → `select_content` → `view_chart` → `generate_card` → `share`.

## 2. Convenções

- Nomes de evento e parâmetro em `snake_case`. Limites do GA4 respeitados: evento ≤ 40 caracteres, ≤ 25 parâmetros por evento, valor de parâmetro ≤ 100 caracteres (os testes conferem).
- Eventos recomendados do GA4 onde existem (`search`, `select_content`, `share`); personalizados para o resto.
- Todo push leva `event_id` (UUID v4, para deduplicar e reconciliar) e `schema_version` (versão deste contrato).
- Códigos IBGE sempre como **texto** de 7 dígitos, nunca número.
- O helper `track()` limpa os parâmetros do evento anterior que não fazem parte do evento atual (envia-os como `undefined`). Motivo: o modelo de dados do GTM é persistente, e uma variável de dataLayer leria o valor antigo, por exemplo `etapa` de um `view_chart` aparecendo num `share`.
- Em ambiente local (`localhost`, `127.0.0.1` ou `?debug_tracking`), cada push é mostrado no console e validado contra este contrato; violações aparecem como `console.warn`.

## 3. Resumo dos eventos

| Evento | Tipo | Quando dispara | Parâmetros |
|---|---|---|---|
| `search` | recomendado GA4 | A pessoa confirma uma busca de município. | `search_term`, `results_count`, `search_method` |
| `select_content` | recomendado GA4 | Um município é aberto por escolha ativa da pessoa. | `content_type`, `content_id`, `municipio_nome` |
| `view_chart` | personalizado | Um gráfico ficou visível na tela. | `chart_id`, `indicador`, `etapa`, `municipio_id` |
| `change_filter` | personalizado | A pessoa troca a etapa, a rede ou o indicador do gráfico. | `filter_name`, `filter_value` |
| `compare_toggle` | personalizado | A pessoa liga ou desliga a comparação com estado e Brasil nos gráficos. | `comparacao` |
| `generate_card` | personalizado | O cartão-resumo da cidade foi gerado e exibido. | `municipio_id`, `card_format` |
| `share` ⭐ | recomendado GA4 | O cartão foi compartilhado (evento-chave / conversão do projeto). | `method`, `content_type`, `item_id` |
| `data_unavailable` | personalizado | A tela mostrou um indicador sem dado (IDEB não divulgado ou etapa sem taxas de rendimento). | `indicador`, `etapa`, `motivo` |

⭐ = evento-chave (conversão) no GA4.

## 4. Tagbook (detalhe por evento)

### `search`

- **Tipo:** recomendado GA4
- **O que significa:** A pessoa confirma uma busca de município.
- **Gatilho exato:** Escolha de uma sugestão do autocomplete (clique ou Enter numa sugestão destacada) ou Enter com o texto digitado. Busca sem resultado também dispara, com results_count = 0. Digitar sem confirmar não dispara.
- **Status:** implementado no código · validação no GTM Preview / DebugView: pendente (fase GTM)

| Parâmetro | Tipo | Obrigatório | Valores permitidos | Descrição |
|---|---|---|---|---|
| `search_term` | string | sim | regex `^[^A-Z\u0080-\uffff]*$`; até 100 caracteres | Texto buscado, normalizado: minúsculas, sem acento e com espaços simples (mesma regra do pipeline). |
| `results_count` | integer | sim | ≥ 0 | Quantos municípios a busca encontrou (0 = busca sem resultado). |
| `search_method` | string | sim | `autocomplete`, `digitado` | Como a busca foi confirmada: escolhendo uma sugestão da lista ou apertando Enter no texto digitado. |

```js
window.dataLayer.push({
  "event": "search",
  "event_id": "3f1c2a9e-8b7d-4c1e-9f0a-6d2b5e8c4a71",
  "schema_version": "1.0.0",
  "search_term": "hugo napoleao",
  "results_count": 1,
  "search_method": "autocomplete"
});
```

### `select_content`

- **Tipo:** recomendado GA4
- **O que significa:** Um município é aberto por escolha ativa da pessoa.
- **Gatilho exato:** Logo depois do search, ao escolher o município, ou no clique em um atalho ('Experimente: …'). Abrir o site por link compartilhado (?m=código) e usar o botão voltar NÃO disparam: não houve escolha.
- **Status:** implementado no código · validação no GTM Preview / DebugView: pendente (fase GTM)

| Parâmetro | Tipo | Obrigatório | Valores permitidos | Descrição |
|---|---|---|---|---|
| `content_type` | string | sim | `municipio` | Tipo de conteúdo escolhido; sempre 'municipio'. |
| `content_id` | string | sim | regex `^[0-9]{7}$` | Código IBGE do município escolhido. |
| `municipio_nome` | string | sim | até 100 caracteres | Nome do município como exibido no site (com acento). |

```js
window.dataLayer.push({
  "event": "select_content",
  "event_id": "9b2e7d41-5c3a-4f8e-a1b6-0d4c7e9f2a35",
  "schema_version": "1.0.0",
  "content_type": "municipio",
  "content_id": "2204600",
  "municipio_nome": "Hugo Napoleão"
});
```

### `view_chart`

- **Tipo:** personalizado
- **O que significa:** Um gráfico ficou visível na tela.
- **Gatilho exato:** IntersectionObserver: pelo menos 50% do gráfico visível. Uma vez por gráfico e por município (trocar de cidade libera um novo disparo; trocar filtro não).
- **Status:** implementado no código · validação no GTM Preview / DebugView: pendente (fase GTM)

| Parâmetro | Tipo | Obrigatório | Valores permitidos | Descrição |
|---|---|---|---|---|
| `chart_id` | string | sim | `rendimento`, `ideb` | Qual gráfico entrou na tela. |
| `indicador` | string | sim | `aprovacao`, `reprovacao`, `abandono`, `rendimento`, `ideb` | Indicador mostrado ou ausente. Em view_chart: a taxa do gráfico de rendimento ou 'ideb'. Em data_unavailable: 'rendimento' (taxas) ou 'ideb'. |
| `etapa` | string | sim | `ef_ai`, `ef_af`, `em` | Etapa de ensino: ef_ai = fundamental anos iniciais, ef_af = fundamental anos finais, em = ensino médio. |
| `municipio_id` | string | sim | regex `^[0-9]{7}$` | Código IBGE do município em tela. |

```js
window.dataLayer.push({
  "event": "view_chart",
  "event_id": "c7a1e5f3-2d9b-4e6a-8c0f-1b3d5e7a9c24",
  "schema_version": "1.0.0",
  "chart_id": "rendimento",
  "indicador": "aprovacao",
  "etapa": "ef_ai",
  "municipio_id": "2204600"
});
```

### `change_filter`

- **Tipo:** personalizado
- **O que significa:** A pessoa troca a etapa, a rede ou o indicador do gráfico.
- **Gatilho exato:** Evento 'change' do botão de opção (só quando o valor muda de fato).
- **Status:** implementado no código · validação no GTM Preview / DebugView: pendente (fase GTM)

| Parâmetro | Tipo | Obrigatório | Valores permitidos | Descrição |
|---|---|---|---|---|
| `filter_name` | string | sim | `etapa`, `rede`, `indicador` | Qual filtro foi alterado. |
| `filter_value` | string | sim | `ef_ai`, `ef_af`, `em`, `total`, `publica`, `aprovacao`, `reprovacao`, `abandono` | Novo valor do filtro. |

```js
window.dataLayer.push({
  "event": "change_filter",
  "event_id": "5e8d2b7a-1f4c-4a9e-b3d6-7c0a2e5f8b19",
  "schema_version": "1.0.0",
  "filter_name": "etapa",
  "filter_value": "em"
});
```

### `compare_toggle`

- **Tipo:** personalizado
- **O que significa:** A pessoa liga ou desliga a comparação com estado e Brasil nos gráficos.
- **Gatilho exato:** Evento 'change' da caixa 'Comparar com estado e Brasil'.
- **Status:** implementado no código · validação no GTM Preview / DebugView: pendente (fase GTM)

| Parâmetro | Tipo | Obrigatório | Valores permitidos | Descrição |
|---|---|---|---|---|
| `comparacao` | string | sim | `ativada`, `desativada` | Estado da comparação com estado e Brasil depois do clique. |

```js
window.dataLayer.push({
  "event": "compare_toggle",
  "event_id": "a4f9c3e1-7b2d-4d8a-9e5c-3f1b6a8d0e57",
  "schema_version": "1.0.0",
  "comparacao": "desativada"
});
```

### `generate_card`

- **Tipo:** personalizado
- **O que significa:** O cartão-resumo da cidade foi gerado e exibido.
- **Gatilho exato:** Depois que a imagem do cartão é criada com sucesso e a janela de compartilhamento abre (falhas não disparam).
- **Status:** implementado no código · validação no GTM Preview / DebugView: pendente (fase GTM)

| Parâmetro | Tipo | Obrigatório | Valores permitidos | Descrição |
|---|---|---|---|---|
| `municipio_id` | string | sim | regex `^[0-9]{7}$` | Código IBGE do município do cartão. |
| `card_format` | string | sim | `png_1080x1350` | Formato do cartão gerado (tipo e tamanho da imagem). |

```js
window.dataLayer.push({
  "event": "generate_card",
  "event_id": "e2b6d8f4-9a1c-4b3e-8d7f-5c0e2a4b6d81",
  "schema_version": "1.0.0",
  "municipio_id": "2204600",
  "card_format": "png_1080x1350"
});
```

### `share`

- **Tipo:** recomendado GA4 · **evento-chave**
- **O que significa:** O cartão foi compartilhado (evento-chave / conversão do projeto).
- **Gatilho exato:** web_share: só quando o menu nativo conclui (cancelar não conta); whatsapp e download: clique no botão; copy_link: quando a cópia dá certo.
- **Status:** implementado no código · validação no GTM Preview / DebugView: pendente (fase GTM)

| Parâmetro | Tipo | Obrigatório | Valores permitidos | Descrição |
|---|---|---|---|---|
| `method` | string | sim | `web_share`, `whatsapp`, `download`, `copy_link` | Canal de compartilhamento: web_share = menu nativo do celular (Web Share API), whatsapp = link wa.me, download = baixou o PNG, copy_link = copiou o link. |
| `content_type` | string | sim | `cartao` | Tipo do conteúdo compartilhado; sempre 'cartao'. |
| `item_id` | string | sim | regex `^[0-9]{7}$` | Código IBGE do município do cartão. |

```js
window.dataLayer.push({
  "event": "share",
  "event_id": "7d3a9f1e-4c6b-4e2a-a8d5-0f9b3c7e1a62",
  "schema_version": "1.0.0",
  "method": "whatsapp",
  "content_type": "cartao",
  "item_id": "2204600"
});
```

### `data_unavailable`

- **Tipo:** personalizado
- **O que significa:** A tela mostrou um indicador sem dado (IDEB não divulgado ou etapa sem taxas de rendimento).
- **Gatilho exato:** Quando o aviso é renderizado na página (inclusive abaixo da dobra): IDEB não divulgado em qualquer das 3 etapas ao abrir o município, ou etapa/rede sem taxas de rendimento. Uma vez por município + indicador + etapa + motivo enquanto a página estiver aberta (re-renderizar por troca de filtro não repete).
- **Status:** implementado no código · validação no GTM Preview / DebugView: pendente (fase GTM)

| Parâmetro | Tipo | Obrigatório | Valores permitidos | Descrição |
|---|---|---|---|---|
| `indicador` | string | sim | `aprovacao`, `reprovacao`, `abandono`, `rendimento`, `ideb` | Indicador mostrado ou ausente. Em view_chart: a taxa do gráfico de rendimento ou 'ideb'. Em data_unavailable: 'rendimento' (taxas) ou 'ideb'. |
| `etapa` | string | sim | `ef_ai`, `ef_af`, `em` | Etapa de ensino: ef_ai = fundamental anos iniciais, ef_af = fundamental anos finais, em = ensino médio. |
| `motivo` | string | sim | `nao_divulgado`, `sem_registro`, `sem_dados` | Por que o dado não aparece: nao_divulgado = INEP publicou '-'; sem_registro = município fora da planilha do INEP; sem_dados = nenhuma taxa de rendimento no período para a etapa/rede. |

```js
window.dataLayer.push({
  "event": "data_unavailable",
  "event_id": "1c5e7a3f-8d2b-4f9c-b6e0-4a2d8f1c3e95",
  "schema_version": "1.0.0",
  "indicador": "ideb",
  "etapa": "ef_ai",
  "motivo": "nao_divulgado"
});
```

## 5. Dicionário de parâmetros

Cada parâmetro tem uma definição única, reutilizada entre eventos (evita dimensões duplicadas no GA4).

| Parâmetro | Tipo | Regras | Usado em | Dimensão personalizada GA4 | Definição |
|---|---|---|---|---|---|
| `card_format` | string | `png_1080x1350` | `generate_card` | sim | Formato do cartão gerado (tipo e tamanho da imagem). |
| `chart_id` | string | `rendimento`, `ideb` | `view_chart` | sim | Qual gráfico entrou na tela. |
| `comparacao` | string | `ativada`, `desativada` | `compare_toggle` | sim | Estado da comparação com estado e Brasil depois do clique. |
| `content_id` | string | regex `^[0-9]{7}$` | `select_content` | não | Código IBGE do município escolhido. |
| `content_type` | string | `municipio` | `select_content`, `share` | não | Tipo de conteúdo escolhido; sempre 'municipio'. |
| `etapa` | string | `ef_ai`, `ef_af`, `em` | `data_unavailable`, `view_chart` | sim | Etapa de ensino: ef_ai = fundamental anos iniciais, ef_af = fundamental anos finais, em = ensino médio. |
| `event_id` | string | regex `^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` | `change_filter`, `compare_toggle`, `data_unavailable`, `generate_card`, `search`, `select_content`, `share`, `view_chart` | não | Identificador único do push (UUID v4). Serve para deduplicar e, no futuro, reconciliar GA4 com o backend próprio. |
| `filter_name` | string | `etapa`, `rede`, `indicador` | `change_filter` | sim | Qual filtro foi alterado. |
| `filter_value` | string | `ef_ai`, `ef_af`, `em`, `total`, `publica`, `aprovacao`, `reprovacao`, `abandono` | `change_filter` | sim | Novo valor do filtro. |
| `indicador` | string | `aprovacao`, `reprovacao`, `abandono`, `rendimento`, `ideb` | `data_unavailable`, `view_chart` | sim | Indicador mostrado ou ausente. Em view_chart: a taxa do gráfico de rendimento ou 'ideb'. Em data_unavailable: 'rendimento' (taxas) ou 'ideb'. |
| `item_id` | string | regex `^[0-9]{7}$` | `share` | não | Código IBGE do município do cartão. |
| `method` | string | `web_share`, `whatsapp`, `download`, `copy_link` | `share` | não | Canal de compartilhamento: web_share = menu nativo do celular (Web Share API), whatsapp = link wa.me, download = baixou o PNG, copy_link = copiou o link. method é parâmetro do evento recomendado share e já existe como dimensão no GA4. |
| `motivo` | string | `nao_divulgado`, `sem_registro`, `sem_dados` | `data_unavailable` | sim | Por que o dado não aparece: nao_divulgado = INEP publicou '-'; sem_registro = município fora da planilha do INEP; sem_dados = nenhuma taxa de rendimento no período para a etapa/rede. |
| `municipio_id` | string | regex `^[0-9]{7}$` | `generate_card`, `view_chart` | sim | Código IBGE do município em tela. |
| `municipio_nome` | string | até 100 caracteres | `select_content` | sim | Nome do município como exibido no site (com acento). |
| `results_count` | integer | ≥ 0 | `search` | não | Quantos municípios a busca encontrou (0 = busca sem resultado). Registrar como métrica personalizada se quiser médias; para filtrar buscas sem resultado basta comparar com 0. |
| `schema_version` | string | `1.0.0` | `change_filter`, `compare_toggle`, `data_unavailable`, `generate_card`, `search`, `select_content`, `share`, `view_chart` | não | Versão deste contrato no momento do envio. Muda quando um evento ou parâmetro muda de forma incompatível. |
| `search_method` | string | `autocomplete`, `digitado` | `search` | sim | Como a busca foi confirmada: escolhendo uma sugestão da lista ou apertando Enter no texto digitado. |
| `search_term` | string | regex `^[^A-Z\u0080-\uffff]*$`; até 100 caracteres | `search` | não | Texto buscado, normalizado: minúsculas, sem acento e com espaços simples (mesma regra do pipeline). search_term é parâmetro reservado do GA4 (já aparece nos relatórios de busca), não precisa de dimensão personalizada. |

## 6. Dimensões personalizadas a registrar no GA4

Admin → Definições personalizadas → escopo **evento**. Total: **11** (limite: 50). Registrar antes de publicar: o registro não é retroativo nos relatórios padrão.

- `card_format`
- `chart_id`
- `comparacao`
- `etapa`
- `filter_name`
- `filter_value`
- `indicador`
- `motivo`
- `municipio_id`
- `municipio_nome`
- `search_method`
