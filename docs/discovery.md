# Discovery

Documento de estrutura. As perguntas abaixo precisam ser respondidas por quem conhece a operação.
Nenhum número foi inventado: onde falta um valor, aparece `[PREMISSA: ...]` para preenchimento, com a
fonte ao lado.

> Contexto: Distribuidora Exemplo é uma empresa **fictícia**. Todos os dados deste repositório são
> sintéticos e as ocorrências são simuladas.

## 1. Problema

- Qual é o problema que a triagem automática resolve? (ex.: picos de mensagens durante falhas na rede)
- Quem sente esse problema hoje e como ele se manifesta?
- Quanto isso custa hoje? `[PREMISSA: volume de mensagens de falta de energia por mês | fonte: ]`
- Por que um LLM e não só um menu de opções ou regras fixas?

## 2. Personas

### Cliente

- O que ele quer quando escreve? Quais são as suas urgências reais?
- Em que situações ele escreve com medo (fio caído, faísca) e o que precisa ouvir primeiro?
- Que tipo de linguagem ele usa (erros de digitação, gírias, áudio transcrito)?

### Atendente

- Quais tarefas repetitivas ele faz hoje na triagem de uma mensagem?
- O que ele precisa receber da triagem para continuar sem refazer perguntas?
- O que faria ele desconfiar e deixar de usar a ferramenta?

### Centro de operação

- Que informação sobre ocorrências ativas existe, em que sistema e com que atraso?
- Como uma nova ocorrência suspeita (chamado marcado como "possível nova ocorrência") seria
  validada?
- Quem decide a prioridade de uma emergência?

## 3. Processo atual e futuro

### Atual (a descrever)

- Passo a passo desde a mensagem do cliente até a resolução. `[PREMISSA: mapear com a operação | fonte: ]`
- Onde estão os gargalos e as filas?

### Futuro (o que este MVP propõe)

1. Regras determinísticas de emergência por palavra-chave.
2. O LLM extrai e classifica a mensagem.
3. O bairro é normalizado contra a base.
4. Regras de decisão escolhem a ação.
5. Um template fixo gera a resposta ao cliente.
6. Tudo é registrado em log.

O LLM nunca escreve texto livre para o cliente.

## 4. Hipóteses

Cada hipótese precisa de um critério para ser confirmada ou refutada.

| Hipótese | Como o MVP testa | Critério |
|---|---|---|
| O LLM identifica emergências sem falhar | Recall de emergência no conjunto de teste | `[PREMISSA: meta do autor, hoje 100%]` |
| O LLM entende a intenção em mensagens reais | Acerto de intenção | `[PREMISSA: meta do autor]` |
| Uma fração relevante dos atendimentos se resolve sem humano | Taxa de resolução automática | `[PREMISSA: a definir com a operação]` |
| O custo por mensagem é baixo frente ao atendimento humano | Custo por mensagem do relatório | `[PREMISSA: custo do atendimento humano | fonte: ]` |

## 5. O que o MVP testa e o que não testa

### Testa

- Qualidade da extração e da classificação em mensagens sintéticas variadas.
- Segurança: emergências e tentativas de injeção de instruções.
- Custo e latência por mensagem em cada modelo.

### Não testa

- Integração com o sistema real de ocorrências.
- Canal real (WhatsApp) e volume de produção.
- Aceitação por clientes e atendentes reais.
- Mensagens reais: o conjunto de avaliação é sintético e escrito para este MVP.
- Áudio: as mensagens de "áudio" são texto já transcrito.
