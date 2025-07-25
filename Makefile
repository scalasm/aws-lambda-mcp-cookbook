.PHONY: dev lint mypy-lint complex coverage pre-commit sort deploy destroy deps unit infra-tests integration e2e coverage-tests docs lint-docs build format format-fix pr watch update-deps
PYTHON := ".venv/bin/python3"
.ONESHELL:  # run all commands in a single shell, ensuring it runs within a local virtual env

OPENAPI_DIR := ./docs/swagger
CURRENT_OPENAPI := $(OPENAPI_DIR)/openapi.json
LATEST_OPENAPI := openapi_latest.json


dev:
	pip install --upgrade pip pre-commit poetry
	pre-commit install
# ensures poetry creates a local virtualenv (.venv)
	poetry config --local virtualenvs.in-project true
	poetry install --no-root
	npm ci

format:
	poetry run ruff check . --fix

format-fix:
	poetry run ruff format .

lint: format
	@echo "Running mypy"
	$(MAKE) mypy-lint

complex:
	@echo "Running Radon"
	poetry run radon cc -e 'tests/*,cdk.out/*,node_modules/*' .
	@echo "Running xenon"
	poetry run xenon --max-absolute B --max-modules A --max-average A -e 'tests/*,.venv/*,cdk.out/*,node_modules/*,service/*' .

pre-commit:
	poetry run pre-commit run -a --show-diff-on-failure

mypy-lint:
	poetry run mypy --pretty service cdk tests docs/examples

deps:
	poetry export --only=dev --format=requirements.txt > dev_requirements.txt
	poetry export --without=dev --format=requirements.txt > lambda_requirements.txt

unit:
	poetry run pytest tests/unit  --cov-config=.coveragerc --cov=service --cov-report xml

build: deps
	mkdir -p .build/lambdas ; cp -r service .build/lambdas
	cp run.sh .build/lambdas/
	mkdir -p .build/common_layer ; poetry export --without=dev --format=requirements.txt > .build/common_layer/requirements.txt

infra-tests: build
	poetry run pytest tests/infrastructure

integration:
	poetry run pytest tests/integration  --cov-config=.coveragerc --cov=service --cov-report xml

e2e:
	poetry run pytest tests/e2e  --cov-config=.coveragerc --cov=service --cov-report xml

pr: deps format pre-commit complex lint lint-docs unit deploy coverage-tests e2e

coverage-tests:
	poetry run pytest tests/unit tests/integration  --cov-config=.coveragerc --cov=service --cov-report xml

deploy: build
	npx cdk deploy --app="${PYTHON} ${PWD}/app.py" --require-approval=never

destroy:
	npx cdk destroy --app="${PYTHON} ${PWD}/app.py" --force

docs:
	poetry run mkdocs serve

lint-docs:
	docker run -v ${PWD}:/markdown 06kellyjac/markdownlint-cli --fix "docs"

watch:
	npx cdk watch

update-deps:
	@echo "Updating Poetry dependencies..."
	poetry update
	@echo "Updating pre-commit hooks..."
	pre-commit autoupdate
	@echo "Fetching latest CDK version from npm..."
	$(eval LATEST_CDK_VERSION := $(shell npm view aws-cdk version))
	@echo "Found CDK version: $(LATEST_CDK_VERSION)"
	@echo "Updating package.json with latest CDK version..."
	node -e "const fs = require('fs'); const pkg = JSON.parse(fs.readFileSync('package.json')); pkg.dependencies['aws-cdk'] = '$(LATEST_CDK_VERSION)'; fs.writeFileSync('package.json', JSON.stringify(pkg, null, 4));"
	npm i --package-lock-only
	@echo "Installing npm dependencies..."
	npm install
	@echo "All dependencies updated successfully!"
