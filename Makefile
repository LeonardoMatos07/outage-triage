MODEL ?= claude-haiku-5-5
SPLIT ?= test

.PHONY: install lint types test nocomments check format up down eval triage-sample check-dataset

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
