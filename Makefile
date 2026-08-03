.PHONY: install test lint run

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/

run:
	uvicorn src.main:app --reload --port 8080
