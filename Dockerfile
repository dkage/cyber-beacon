FROM oven/bun:1.3 AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/bun.lock ./
RUN bun install --frozen-lockfile
COPY frontend/ ./
RUN bun run build

FROM python:3.13-slim AS backend
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"
COPY backend/ ./
COPY --from=frontend /frontend/build /frontend/build
ENV FRONTEND_DIR=/frontend/build
RUN useradd --create-home beacon && chown -R beacon:beacon /app
USER beacon
EXPOSE 8000
CMD ["sh", "entrypoint.sh"]
