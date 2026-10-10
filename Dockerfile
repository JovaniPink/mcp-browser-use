# Build with Python 3.14 and copy the pinned uv binary from its versioned image.
# External images are pinned to reviewed manifest-list digests; Renovate refreshes them.
FROM python:3.14-slim-bookworm@sha256:82bc3c539b8813ada9d68c63b40158fa002f7f33de9bf3312a3dfdc0620dff56 AS uv
COPY --from=ghcr.io/astral-sh/uv:0.12.3@sha256:2d890623d310b57771ce840f0da5eed5fc6d657da05ffaa45d82797b53fa3abc /uv /uvx /bin/

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

CMD ["/app/.venv/bin/python", "-m", "pytest", "-q"]

FROM python:3.14-slim-bookworm@sha256:82bc3c539b8813ada9d68c63b40158fa002f7f33de9bf3312a3dfdc0620dff56

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
