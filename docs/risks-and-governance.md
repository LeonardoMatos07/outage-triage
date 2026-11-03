# Riscos e governança

Documento de estrutura, com as decisões já tomadas no MVP e as perguntas que ainda precisam de
resposta. Onde falta um valor, aparece `[PREMISSA: ...]`.

## 1. LGPD

Decisões do MVP:

- Só dados sintéticos. Nenhum dado pessoal real, nem nos testes, nem nos logs.
- O log guarda a mensagem do cliente. Em produção isso é dado pessoal.

Perguntas a responder:

- Qual é a base legal para tratar a mensagem do cliente? `[PREMISSA: parecer jurídico | fonte: ]`
- Por quanto tempo guardar mensagens e logs? `[PREMISSA: ]`
- O texto do cliente é enviado a um fornecedor externo (a API do LLM). Qual é o contrato de
  tratamento de dados e onde os dados são processados?
- Como mascarar CPF, endereço e telefone antes de enviar ao LLM e antes de gravar o log?
- Como atender pedidos de acesso e exclusão do titular?

## 2. Alucinação

Decisão do MVP: **o LLM só extrai e classifica**. Quem decide a ação e escreve a resposta são regras
e templates fixos. O modelo nunca escreve texto livre para o cliente, então não inventa previsão de
retorno, prazo ou promessa.

Riscos que restam:

- O modelo pode extrair um campo errado (bairro, intenção).
- O modelo pode errar a `confidence` que informa.

Perguntas a responder:

- Como amostrar e revisar atendimentos em produção para medir esses erros?
- Qual taxa de erro de extração é aceitável por tipo de campo?

## 3. Injeção de instruções

Decisões do MVP:

- O prompt declara que o conteúdo da mensagem do cliente é dado, nunca instrução.
- A mensagem vai delimitada por `<customer_message>`.
- A ação não depende de texto livre do modelo, o que limita o dano de uma injeção.
- A avaliação mede a resistência a injeção (tentativas que não mudaram a ação).

Perguntas a responder:

- Qual nível de resistência a injeção é exigido para operar? (a meta do autor está no relatório)
- Como atualizar o conjunto de tentativas de injeção ao longo do tempo?

## 4. Dependência de fornecedor

- O modelo é configurável por variável de ambiente (`LLM_MODEL`).
- O que acontece se a API ficar indisponível? No MVP, o atendimento vai para humano e as
  emergências por palavra-chave continuam funcionando.
- Há plano para trocar de fornecedor? Quanto custaria? `[PREMISSA: ]`

## 5. Comprar ou construir

| Critério | Comprar uma plataforma | Construir (este caminho) |
|---|---|---|
| Controle das regras de segurança | `[PREMISSA: ]` | Total |
| Custo de entrada | `[PREMISSA: ]` | `[PREMISSA: ]` |
| Integração com o sistema de ocorrências | `[PREMISSA: ]` | `[PREMISSA: ]` |
| Prazo | `[PREMISSA: ]` | `[PREMISSA: ]` |

## 6. Quando o humano assume

Regras do MVP (em `app/rules.py`):

1. Emergência por palavra-chave **ou** pelo LLM: orientação fixa de segurança e encaminhamento
   imediato com prioridade máxima.
2. Confiança abaixo do limiar configurado (`CONFIDENCE_THRESHOLD`).
3. Intenção de conta, religação ou outra: resposta fixa e fila correta.
4. Bairro não identificado após uma pergunta.
5. Falha do LLM ou saída inválida depois de uma nova tentativa.

## 7. Critérios para pausar o uso

Proposta a validar. Cada limite precisa de um valor.

- Qualquer emergência não identificada em produção: pausar e investigar.
- Resistência a injeção abaixo de `[PREMISSA: ]`.
- Acerto de ação abaixo de `[PREMISSA: ]` em amostra revisada.
- Reclamações de clientes acima de `[PREMISSA: ]`.
- Mudança de modelo ou de prompt sem nova avaliação.
