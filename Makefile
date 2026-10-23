.PHONY: install test lint run lock evals docker

install:
	pip install -r requirements-dev.txt

test:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/ -v

lint:
	ruff check src/ tests/

run:
	uvicorn src.main:app --reload --port 8080

evals:
	python -m src.eval.run_evals

docker:
	docker build -t renewal-risk-agent . && docker run --rm -p 8080:8080 --env-file .env renewal-risk-agent

# Regenerate both lock files after editing requirements*.in (needs uv).
lock:
	uv pip compile -p 3.11 requirements-dev.in -o requirements-dev.txt
	uv pip compile -p 3.11 requirements.in -c requirements-dev.txt -o requirements.txt
