# Plano de adoção

Documento de estrutura. Onde falta um valor, aparece `[PREMISSA: ...]`.

## 1. Piloto

- Qual escopo? Sugestão a validar: uma região, só falta de energia, com atendente revisando.
- Duração e volume do piloto: `[PREMISSA: ]`
- Quem aprova o início? Quem pode interromper?
- O piloto roda em modo sombra (a triagem roda, mas o atendente decide) antes de responder clientes?
- Qual versão do prompt, do modelo e das listas de emergência vai para o piloto? Tudo versionado.

## 2. Treinamento dos atendentes

- O que o atendente precisa entender: o que a triagem faz, o que não faz e quando ele assume.
- Como ler o resumo de triagem (campos extraídos, motivo do encaminhamento, prioridade).
- Como reportar um erro da triagem de forma rápida.
- Duração e formato do treinamento: `[PREMISSA: ]`

## 3. Comunicação

- Cliente: como avisar que o atendimento inicial é automático e como pedir um atendente?
- Equipe: como apresentar a mudança sem parecer substituição?
- Centro de operação: como tratar chamados marcados como "possível nova ocorrência"?

## 4. KPIs de adoção

Cada KPI precisa de um valor-alvo e de uma fonte de medição.

| KPI | Alvo | Fonte |
|---|---|---|
| Taxa de resolução automática | `[PREMISSA: ]` | Log de atendimentos |
| Recall de emergência em amostra revisada | `[PREMISSA: ]` | Revisão por amostragem |
| Satisfação do cliente | `[PREMISSA: ]` | `[PREMISSA: ]` |
| Atendentes que usam o resumo da triagem | `[PREMISSA: ]` | `[PREMISSA: ]` |

## 5. Critérios para escalar ou encerrar

Escalar quando:

- as metas de avaliação forem atingidas no conjunto de teste e confirmadas em amostra real
  `[PREMISSA: definir limites | fonte: ]`;
- nenhuma emergência tiver sido perdida no piloto;
- o custo por mensagem estiver dentro do orçamento `[PREMISSA: ]`.

Encerrar ou refazer quando:

- qualquer critério de pausa de `risks-and-governance.md` se repetir sem correção;
- o ganho medido ficar abaixo do custo `[PREMISSA: ]`.

## 6. Reaproveitamento em outras distribuidoras

- O que é específico da Distribuidora Exemplo: lista de bairros, base de ocorrências, templates.
- O que é reaproveitável: regras de segurança, esquema de triagem, avaliação, painel.
- Quanto trabalho para adaptar a cada nova distribuidora? `[PREMISSA: ]`
