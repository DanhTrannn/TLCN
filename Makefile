SHELL := /bin/bash
COMPOSE := docker compose

.PHONY: help env core-up batch-up bi-up platform-up down logs ps generator-small validate reset

help:
	@printf '%s\n' \
	  'make env             Create .env from .env.example when missing' \
	  'make core-up         Start storefront, APIs and ecommerce MySQL' \
	  'make batch-up        Start MinIO, Spark and Airflow' \
	  'make bi-up           Start analytics MySQL and Superset' \
	  'make platform-up     Start all TLCN profiles' \
	  'make down            Stop containers without deleting volumes' \
	  'make logs            Follow all service logs' \
	  'make generator-small Run the deterministic small generator' \
	  'make validate        Run local structural checks' \
	  'make reset           Delete containers and persistent volumes'

env:
	@test -f .env || cp .env.example .env

core-up: env
	$(COMPOSE) --profile core up -d --build

batch-up: env
	$(COMPOSE) --profile batch up -d --build

bi-up: env
	$(COMPOSE) --profile bi up -d --build

platform-up: env
	$(COMPOSE) --profile core --profile batch --profile bi up -d --build

down:
	$(COMPOSE) --profile core --profile batch --profile bi down

logs:
	$(COMPOSE) --profile core --profile batch --profile bi logs -f

ps:
	$(COMPOSE) --profile core --profile batch --profile bi ps

generator-small: core-up
	$(COMPOSE) --profile tools run --rm generator run --config /app/configs/small.yml

validate:
	python3 scripts/validate_structure.py

reset:
	$(COMPOSE) --profile core --profile batch --profile bi --profile tools down -v --remove-orphans
