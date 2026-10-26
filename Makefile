.PHONY: all up start down stop restart ps logs status seed typecheck help

all: up

help:
	@echo "D&K E-Commerce Lakehouse Platform Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make up          Start full platform services (fastest launcher)"
	@echo "  make down        Stop all platform containers"
	@echo "  make restart     Restart all platform containers"
	@echo "  make ps          Show container status"
	@echo "  make logs        Follow container logs in real time"
	@echo "  make seed        Seed multi-domain demo scenarios into MySQL"
	@echo "  make typecheck   Run Next.js storefront TypeScript check"
	@echo ""

up: start

start:
	@./scripts/start_all.sh

down: stop

stop:
	@./scripts/stop_all.sh

restart: stop start

ps:
	@docker compose --profile core --profile batch --profile streaming ps

status: ps

logs:
	@docker compose --profile core --profile batch --profile streaming logs -f

seed:
	@uv run --locked --package ecommerce-api -- python database/seeds/seed_demo_scenarios.py

typecheck:
	@npm --prefix apps/storefront run typecheck
