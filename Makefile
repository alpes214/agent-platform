.PHONY: help dev dev-down dev-logs backend-dev frontend-dev prod prod-build prod-down prod-logs tunnel tunnel-stop

help:
	@echo "Dev (local):"
	@echo "  make tunnel       SSH-forward remote TEI (8080) and Ollama (11434) to localhost"
	@echo "  make tunnel-stop  kill the autossh tunnel"
	@echo "  make dev          start Postgres in compose"
	@echo "  make dev-down     stop Postgres"
	@echo "  make dev-logs     tail Postgres logs"
	@echo "  make backend-dev  run uvicorn with .env.dev sourced (auto-reload)"
	@echo "  make frontend-dev run Next.js dev server on http://localhost:3000"
	@echo ""
	@echo "Prod (server):"
	@echo "  make prod-build   build images and bring up full stack (postgres + app + cloudflared)"
	@echo "  make prod         bring up full stack without rebuild"
	@echo "  make prod-down    stop full stack"
	@echo "  make prod-logs    tail logs for full stack"

# --- Dev (local): Postgres only in compose; FastAPI + Next.js run natively. ---

dev:
	docker compose --env-file .env.dev up -d postgres

dev-down:
	docker compose --env-file .env.dev down

dev-logs:
	docker compose --env-file .env.dev logs -f

# Run the FastAPI dev server natively with .env.dev sourced into the shell.
# Wrapping in `bash -c` so the env stays exported across the chained commands;
# default make shell may be /bin/sh which lacks `source`.
backend-dev:
	@bash -c 'set -a && source .env.dev && set +a && \
	  exec uv run uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000'

# Run the Next.js dev server on http://localhost:3000 (defaults to FastAPI on :8000).
frontend-dev:
	cd frontend && npm run dev

# --- Prod (server): full stack in compose. ---

prod:
	docker compose --env-file .env.prod --profile app --profile public up -d

prod-build:
	docker compose --env-file .env.prod --profile app --profile public up -d --build

prod-down:
	docker compose --env-file .env.prod --profile app --profile public down

prod-logs:
	docker compose --env-file .env.prod --profile app --profile public logs -f

# --- SSH tunnel to remote host for TEI + Ollama. ---

tunnel:
	autossh -M 0 -f -N \
	  -L 8080:127.0.0.1:8080 \
	  -L 11434:127.0.0.1:11434 \
	  ubuntu-server
	@echo "Tunnel up. Check with: ss -tln 2>/dev/null | grep -E '8080|11434' || lsof -iTCP -sTCP:LISTEN -P -n | grep -E '8080|11434'"

tunnel-stop:
	@pkill -f 'autossh.*ubuntu-server' && echo "Tunnel stopped." || echo "No autossh tunnel running."
