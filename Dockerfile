FROM python:3.13-slim AS backend
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"
COPY backend/ ./
RUN useradd --create-home beacon && chown -R beacon:beacon /app
USER beacon
EXPOSE 8000
CMD ["sh", "entrypoint.sh"]
