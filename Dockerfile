# syntax=docker/dockerfile:1.7

# ---- Build stage: install deps into a virtualenv with uv ----
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv

WORKDIR /app

# Layer 1: dependencies (cached unless lock file changes)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Layer 2: project source
COPY backend ./backend
COPY alembic ./alembic
COPY alembic.ini ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# ---- Runtime stage: slim image with only the venv and the source ----
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/app/.venv/bin:$PATH \
    PYTHONPATH=/app

WORKDIR /app

# Non-root user for the runtime container
RUN groupadd --system app && useradd --system --gid app --home /app app

COPY --from=builder --chown=app:app /app /app

USER app

EXPOSE 8000

# Default command runs the FastAPI server.
# The `worker` service in compose overrides this to run procrastinate instead.
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
