# Outage Triage

Protótipo de triagem de falta de energia por mensagem para uma distribuidora **fictícia**
("Distribuidora Exemplo"). Um LLM entende a mensagem do cliente, regras determinísticas decidem o que
fazer e uma avaliação mede se funciona. O repositório serve de **evidência** para um business case,
não é um produto completo.

> Todos os dados são sintéticos. As ocorrências são simuladas e nenhuma marca, nome ou dado de
> distribuidora real é usado.

## Problema

Em falhas na rede, a distribuidora recebe rajadas de mensagens de clientes. Cada mensagem precisa
ser lida, classificada (falta de energia, conta, religação, outro), localizada em um bairro e
priorizada, e algumas são emergências (fio caído, faísca, fogo, choque) que não podem esperar. A
pergunta que este repositório tenta responder com evidência: **um LLM consegue fazer essa triagem
com segurança, e a que custo?**

## Demonstração

`[DEMO: adicionar GIF ou imagens do chat (make chat) e do painel (make dashboard) | gravar após
rodar a avaliação com a chave da API]`

O chat mostra a resposta ao cliente e, ao lado, os detalhes técnicos da decisão (ação, fila,
prioridade, protocolo). Toda tela avisa que as ocorrências são simuladas.

## Como funciona

```
mensagem
  -> regras de emergência por palavra-chave (determinísticas)
  -> LLM extrai a triagem (intenção, bairro, escopo, confiança)
  -> normalização do bairro (rapidfuzz)
  -> regras de decisão
  -> template de resposta
  -> registro no log
```

| Situação | Ação |
|---|---|
| Emergência (palavra-chave **ou** LLM) | Orientação fixa de segurança e encaminhamento imediato com prioridade máxima |
| Bairro com ocorrência ativa | Informa a ocorrência conhecida, com protocolo e previsão cadastrada |
| Bairro sem ocorrência, só a casa do cliente | Abre chamado individual e orienta a verificar o disjuntor |
| Bairro sem ocorrência, rua ou área | Abre chamado e marca como possível nova ocorrência |
| Bairro não identificado | Pergunta uma vez; na segunda falha, vai para humano |
| Confiança baixa, conta, religação, outro, falha do LLM | Encaminha para humano na fila certa |

## Decisões de governança

- **O LLM só extrai e classifica.** Quem decide a ação e escreve a resposta ao cliente são regras e
  templates fixos. O modelo nunca escreve texto livre para o cliente, então não inventa previsão de
  retorno, prazo ou promessa.
- **Emergência é a regra mais forte.** A detecção é um OU entre palavras-chave determinísticas e o
  LLM. Ela vale mesmo se o LLM falhar ou ficar fora do ar.
- **A mensagem do cliente é dado, não instrução.** O prompt e a delimitação da mensagem reduzem o
  risco de injeção, e a avaliação mede a resistência a tentativas de injeção.
- **Dúvida vai para humano.** Baixa confiança e saída inválida do modelo encaminham para um
  atendente.
- **Só dados sintéticos.** Nenhum dado pessoal real, nem em testes, nem em logs.
- **Código sem comentários.** O código se explica pelos nomes e pela estrutura. O script
  `scripts/check_no_comments.py` reprova comentários e *docstrings* em `app/`, `ui/`, `eval/`,
  `scripts/` e `tests/`.

Veja também [docs/risks-and-governance.md](docs/risks-and-governance.md).

## Resultados

Ainda não há relatório de avaliação com o modelo real. A avaliação precisa da chave da API e roda
sob confirmação, porque faz muitas chamadas.

`[RESULTADO: preencher com os números de reports/eval-*.md depois de rodar make eval-compare SPLIT=dev
e, no fim, make eval-compare SPLIT=test]`

O que a avaliação mede (`eval/metrics.py`):

| Métrica | Meta (premissa do autor) |
|---|---|
| Acerto de intenção, com matriz de confusão | acima de 90% |
| **Recall de emergência** (regras OU LLM) | **100%** |
| Precisão de emergência | acompanhar |
| Acerto de bairro | acima de 85% |
| Acerto de ação | acima de 85% |
| Taxa de resolução automática | métrica de negócio |
| Resistência a injeção | 100% |
| Custo por mensagem e latência (mediana e p95) | acompanhar |

As metas são **premissas do autor**, não números da indústria.

### Conjunto de avaliação

- 150 mensagens sintéticas em português, com erros de digitação, gírias, caixa alta, áudio
  transcrito, mensagens irritadas, duas intenções, só ponto de referência e 8 tentativas de injeção.
- `data/eval/dev.jsonl` (50) serve para ajustar o prompt. `data/eval/test.jsonl` (100) só é rodado
  no final, para a medição.
- A avaliação só usa linhas com `label_status = "reviewed"` e informa quantas ignorou.
- Se o recall de emergência ficar abaixo de 100%, os casos são mostrados antes de qualquer ajuste
  de prompt.

## Como rodar

Requisitos: Python 3.12, [uv](https://docs.astral.sh/uv/), Docker e `make`.

```
cp .env.example .env
make install
make check
```

Preencha `ANTHROPIC_API_KEY` no `.env` (o arquivo não vai para o git). O modelo é configurável em
`LLM_MODEL` (padrão `claude-haiku-5-5`).

| Comando | O que faz |
|---|---|
| `make check` | Lint, tipos, checagem de comentários e testes (nenhum chama a API) |
| `make up` | Sobe API (`:8000`), chat (`:8501`) e painel (`:8502`) com Docker Compose |
| `make triage-sample` | Roda 3 mensagens de exemplo no LLM real |
| `make check-dataset` | Confere distribuição e variedade do conjunto de avaliação |
| `make eval MODEL=claude-haiku-5-5 SPLIT=dev` | Avalia um modelo e grava `reports/eval-*.md` e `.json` |
| `make eval-compare SPLIT=dev` | Avalia Haiku e Sonnet e grava também a comparação |

A avaliação pede confirmação antes de fazer mais de 20 chamadas. Preços por token e cotação do dólar
estão em `data/pricing.yaml`, com a data em que foram conferidos.

## Estrutura

```
app/        triagem: esquema, LLM, regras, ocorrências, respostas, pipeline, API
templates/  textos em português (respostas, relatório, interface)
ui/         chat e painel em Streamlit
eval/       conjunto de avaliação, métricas, relatórios, execução
data/       bairros, ocorrências simuladas, palavras-chave, preços, avaliação
reports/    relatórios de avaliação versionados
docs/       documentação de negócio
```

## Limitações

- Conjunto de avaliação sintético e pequeno: ele mostra tendência, não prova desempenho com
  clientes reais.
- Rótulos escritos e revisados por uma pessoa, sem dupla revisão.
- Ocorrências simuladas, sem integração com um sistema real de ocorrências.
- Chat simulado, sem canal real (WhatsApp) e sem áudio.
- Conta, religação e outros assuntos são apenas encaminhados, não resolvidos.
- Os números de negócio dependem de premissas ainda não preenchidas em [docs/](docs/).
