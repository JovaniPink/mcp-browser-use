# Build with Python 3.14 and copy the pinned uv binary from its versioned image.
FROM python:3.14-slim-bookworm AS uv
COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/

RUN apt-get update \
  && apt-get install --yes --no-install-recommends build-essential \
  && rm -rf /var/lib/apt/lists/*

# Install the project into /app
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --frozen --no-install-project --no-dev --no-editable

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev --no-editable

FROM uv AS test

RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --dev --no-editable

CMD ["uv", "run", "--frozen", "pytest", "-q"]

FROM python:3.14-slim-bookworm

WORKDIR /app

RUN apt-get update \
  && apt-get install --yes --no-install-recommends \
    ca-certificates \
    chromium \
    fonts-liberation \
  && rm -rf /var/lib/apt/lists/* \
  && useradd --create-home --uid 10001 appuser
COPY --from=uv --chown=appuser:appuser /app/.venv /app/.venv

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
ENV BROWSER_USE_HEADLESS=true
ENV CHROME_PATH=/usr/bin/chromium

USER appuser
ENTRYPOINT ["mcp-browser-use"]
