-include .env
export

export PYTHONPATH := .

MODEL ?= claude-haiku-5-5
SPLIT ?= test
COMPARE_MODELS ?= claude-haiku-5-5 claude-sonnet-5-5

.PHONY: demo up-mock demo-report api-mock chat-mock dashboard-mock eval-compare chat dashboard api install lint types test nocomments check format up down eval triage-sample check-dataset

install:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

types:
	uv run mypy

nocomments:
	uv run python scripts/check_no_comments.py

test:
	uv run pytest

check: lint types nocomments test

up:
	docker compose up --build

down:
	docker compose down

check-dataset:
	uv run python -m scripts.check_eval_dataset

triage-sample:
	uv run python -m scripts.try_triage

eval:
	uv run python -m eval.run_eval --model $(MODEL) --split $(SPLIT)

eval-compare:
	uv run python -m eval.run_eval --model $(COMPARE_MODELS) --split $(SPLIT)

api:
	uv run uvicorn app.api:app --port 8000

chat:
	uv run streamlit run ui/chat.py --server.port 8501

dashboard:
	uv run streamlit run ui/dashboard.py --server.port 8502

up-mock:
	LLM_MODE=mock docker compose up --build

demo-report:
	uv run python -m eval.run_eval --mock --split $(SPLIT)

api-mock:
	LLM_MODE=mock uv run uvicorn app.api:app --port 8000

chat-mock:
	LLM_MODE=mock API_URL=http://localhost:8000 uv run streamlit run ui/chat.py --server.port 8501

dashboard-mock:
	LLM_MODE=mock uv run streamlit run ui/dashboard.py --server.port 8502

demo:
	uv run python -m scripts.run_demo
