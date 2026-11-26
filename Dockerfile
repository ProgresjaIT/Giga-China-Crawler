# Obraz dla serwera bez ekranu (agent-dashboard / mcp_loader): Python + zależności + Chromium z Patchright.
# bookworm, bo `patchright install --with-deps` zna jego pakiety systemowe.
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_COMPILE_BYTECODE=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PATH=/app/.venv/bin:$PATH \
    HOST=0.0.0.0 \
    PORT=8000
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
# Chromium i jego biblioteki systemowe; czytelne dla każdego, bo loader uruchamia kontener jako inny użytkownik
RUN patchright install --with-deps chromium && chmod -R a+rX /ms-playwright

COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["giga-china-crawler"]
