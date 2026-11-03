# Como isso escalaria

Quatro pontos, um parágrafo cada. São direções a validar, não decisões tomadas.

## Fila de mensagens

Hoje cada mensagem é processada de forma síncrona pelo endpoint `POST /v1/triage`. Em volume real,
picos de falta de energia gerariam rajadas de mensagens, e o ideal seria receber as mensagens do
canal em uma fila, processá-las com consumidores independentes e absorver os picos sem perder
nenhuma. O repositório `relay` explora esse tipo de padrão de fila de mensagens e pode servir de
referência para a arquitetura. `[PREMISSA: volume de pico esperado | fonte: ]`

## Integração com o sistema real de ocorrências

A base de ocorrências do MVP é um SQLite populado com dados simulados. Em produção, `app/outages.py`
passaria a consultar o sistema real, com atenção ao atraso dos dados, à indisponibilidade do
sistema (a regra seria encaminhar a um humano) e ao modo de abrir chamados e de marcar uma possível
nova ocorrência. `[PREMISSA: sistema e forma de integração | fonte: ]`

## WhatsApp oficial

O canal do MVP é um chat simulado. Um canal oficial exigiria a API oficial do provedor, o
tratamento de mídia (áudio hoje é só texto transcrito), regras de janela de conversa e modelos de
mensagem aprovados, além de revisar a base legal do tratamento de dados do cliente.
`[PREMISSA: provedor e custo do canal | fonte: ]`

## Monitoramento do modelo em produção

O log do MVP já registra modelo, tokens, custo estimado e latência. Em produção seria preciso
acompanhar a taxa de encaminhamento a humano, a distribuição de confiança, as emergências
sinalizadas e uma amostra de atendimentos revisada por pessoas, e rodar de novo a avaliação a cada
mudança de modelo, de prompt ou das listas de palavras-chave. `[PREMISSA: processo e responsável | fonte: ]`
