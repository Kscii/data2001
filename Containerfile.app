FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY configs ./configs
COPY sql ./sql
COPY src ./src

RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:${PATH}"
ENV DATA2001_CONFIG="/app/configs/example.yaml"

EXPOSE 8050

CMD ["gunicorn", "data2001.task4.dashboard_wsgi:server", "--bind", "0.0.0.0:8050", "--workers", "2", "--threads", "4", "--timeout", "120"]
