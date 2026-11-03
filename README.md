# Outage Triage

Protótipo de triagem de falta de energia por mensagem para uma distribuidora **fictícia**
("Distribuidora Exemplo"). Todos os dados são sintéticos e as ocorrências são simuladas.

> README provisório (Etapa 0). A versão final entra na Etapa 6.

## Decisão de governança

O LLM **só extrai e classifica** a mensagem. Quem decide a ação e escreve a resposta ao cliente
são regras determinísticas e templates fixos. O modelo nunca escreve texto livre para o cliente,
o que impede que ele invente previsão de retorno, prazo ou promessa.

## Como rodar

```
cp .env.example .env
make install
make check
make up
```

## Estado

Etapa 0: esqueleto, ferramentas de qualidade e CI.
