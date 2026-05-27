.PHONY: help backend-dev frontend-dev up build down logs \
        admin-status admin-reset-all admin-reset-failed admin-reset-doc admin-reingest admin-reingest-all admin-vacuum

help:
	@echo "Dev (local — runs natively against managed Groq / Voyage / Neon):"
	@echo "  make backend-dev  run uvicorn with .env.dev sourced (auto-reload)"
	@echo "  make frontend-dev run Next.js dev server on http://localhost:3000"
	@echo ""
	@echo "Prod (VPS — docker compose reads ./.env; brings up fastapi + caddy):"
	@echo "  make build  build image + bring up the stack"
	@echo "  make up     bring up without rebuild"
	@echo "  make down   stop the stack"
	@echo "  make logs   tail logs"
	@echo ""
	@echo "Admin (corpus management — runs inside ks-fastapi):"
	@echo "  make admin-status / admin-reset-all / admin-reset-failed"
	@echo "  make admin-reset-doc DOC=<uuid> / admin-reingest DOC=<uuid> / admin-reingest-all / admin-vacuum"

# --- Dev (local): FastAPI + Next.js run natively against managed services. ---

backend-dev:
	@bash -c 'set -a && source .env.dev && set +a && \
	  exec uv run uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000'

frontend-dev:
	cd frontend && npm run dev

# --- Prod (VPS): fastapi + caddy via compose (reads ./.env). ---

up:
	docker compose up -d

build:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

# --- Admin (corpus management — runs inside ks-fastapi) ---

EXEC := docker compose exec -T fastapi python scripts/admin.py

admin-status:
	@$(EXEC) status

admin-reset-all:
	@$(EXEC) reset-all

admin-reset-failed:
	@$(EXEC) reset-failed

admin-reset-doc:
	@if [ -z "$(DOC)" ]; then echo "usage: make admin-reset-doc DOC=<uuid>"; exit 1; fi
	@$(EXEC) reset-doc $(DOC)

admin-reingest:
	@if [ -z "$(DOC)" ]; then echo "usage: make admin-reingest DOC=<uuid>"; exit 1; fi
	@$(EXEC) reingest $(DOC)

admin-reingest-all:
	@$(EXEC) reingest-all

admin-vacuum:
	@$(EXEC) vacuum-staging
