# Business case

Documento de estrutura. Os números da seção de resultado vêm do relatório de avaliação em
`reports/`. Todo o resto é premissa a ser preenchida, com a fonte ao lado. Nada aqui foi inventado.

## 1. Hipóteses de benefício

| Benefício | Como seria medido | Origem do dado |
|---|---|---|
| Menos mensagens que chegam a um atendente | Taxa de resolução automática | Relatório de avaliação e piloto |
| Resposta mais rápida em picos de falta de energia | Tempo até a primeira resposta | `[PREMISSA: tempo atual | fonte: ]` |
| Atendente recebe o caso já estruturado | Tempo de atendimento por caso | `[PREMISSA: tempo atual | fonte: ]` |
| Emergência identificada e priorizada mais cedo | Tempo até o encaminhamento prioritário | `[PREMISSA: tempo atual | fonte: ]` |

## 2. Premissas com fonte

| Premissa | Valor | Fonte |
|---|---|---|
| Mensagens de falta de energia por mês | `[PREMISSA: ]` | |
| Custo médio de um atendimento humano | `[PREMISSA: ]` | |
| Parcela de mensagens elegíveis para triagem automática | `[PREMISSA: ]` | |
| Cotação do dólar usada no custo do LLM | ver `data/pricing.yaml` | Conferida na data registrada no arquivo |
| Preços por token dos modelos | ver `data/pricing.yaml` | Conferidos na data registrada no arquivo |

## 3. ROI em três cenários

Cada cenário usa os mesmos custos e muda as premissas de taxa de resolução automática e volume.

| | Conservador | Base | Otimista |
|---|---|---|---|
| Taxa de resolução automática | `[PREMISSA: ]` | `[PREMISSA: ]` | `[PREMISSA: ]` |
| Volume mensal de mensagens | `[PREMISSA: ]` | `[PREMISSA: ]` | `[PREMISSA: ]` |
| Economia mensal | `[PREMISSA: calcular]` | `[PREMISSA: calcular]` | `[PREMISSA: calcular]` |
| Custo mensal total | `[PREMISSA: calcular]` | `[PREMISSA: calcular]` | `[PREMISSA: calcular]` |
| Retorno e prazo de retorno | `[PREMISSA: calcular]` | `[PREMISSA: calcular]` | `[PREMISSA: calcular]` |

Perguntas a responder:

- Qual taxa de resolução automática é razoável, dado o que o relatório mostra para cada modelo?
- Como tratar o custo de um erro grave (emergência não identificada) no cálculo?

## 4. Custos

### LLM

- Custo por mensagem: vem do relatório de avaliação (`Custo por mensagem`), por modelo.
- Escolha entre Haiku e Sonnet: usar a tabela de comparação `reports/comparison-*.md`
  (acerto contra custo por mensagem).

### Desenvolvimento

- `[PREMISSA: esforço para integrar ao sistema real e ao canal oficial | fonte: ]`

### Operação

- `[PREMISSA: monitoramento, revisão de amostras, manutenção do prompt e das listas | fonte: ]`

## 5. Resultado do piloto

Esta seção só recebe números que existam em um relatório de `reports/`. Enquanto não houver
relatório, fica vazia.

| Métrica | Haiku | Sonnet | Relatório de origem |
|---|---|---|---|
| Acerto de intenção | | | |
| Recall de emergência | | | |
| Acerto de ação | | | |
| Taxa de resolução automática | | | |
| Resistência a injeção | | | |
| Custo por mensagem (R$) | | | |
| Latência mediana (s) | | | |

As metas usadas no relatório são premissas do autor, não números da indústria.
