# syntax=docker/dockerfile:1.7

# ── Builder stage ────────────────────────────────────────────────────────────
# Slim image + build tools for any C-extension dependencies that lack
# pre-built wheels. The builder is discarded in the final image, so build
# tools do not affect the runtime image size.
FROM python:3.13-slim@sha256:7ba5f5888fbe0014ab9edb2278922995c2201fc3752c46b0be24763eb46fa9f3 AS requirements_stage

RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /wheel

RUN python -m pip install --user uv

COPY ./pyproject.toml ./uv.lock /wheel/

# Export only third-party runtime dependencies (no dev groups). --no-emit-project
# excludes the local ``-e .`` entry so the builder does not need README/license
# files; the source is copied into the runtime stage directly.
RUN python -m uv export --frozen --no-dev --all-extras --no-emit-project --no-hashes \
      --output-file requirements.txt

# Build wheels for offline installation in the runtime stage.
RUN python -m pip wheel --wheel-dir=/wheels --no-cache-dir --requirement ./requirements.txt


# ── Project build stage ─────────────────────────────────────────────────────
# Build the project wheel for installation in the runtime image.
FROM requirements_stage AS project_build
WORKDIR /build
COPY . /build/
RUN python -m uv build --wheel --no-sources --out-dir /dist


# ── Runtime stage ────────────────────────────────────────────────────────────
FROM python:3.13-slim@sha256:7ba5f5888fbe0014ab9edb2278922995c2201fc3752c46b0be24763eb46fa9f3

WORKDIR /app

# ── OCI labels ──
# Build args are passed by CI (.github/workflows/release.yml).
ARG VERSION=unknown
ARG VCS_REF=unknown
ARG CREATED=unknown
LABEL org.opencontainers.image.title="NovelAI Image MCP" \
  org.opencontainers.image.description="MCP server exposing NovelAI image generation as tools for AI agents" \
  org.opencontainers.image.version="${VERSION}" \
  org.opencontainers.image.revision="${VCS_REF}" \
  org.opencontainers.image.source="https://github.com/novelai-image-mcp/NovelAI-Image-MCP" \
  org.opencontainers.image.url="https://github.com/novelai-image-mcp/NovelAI-Image-MCP" \
  org.opencontainers.image.licenses="MIT" \
  org.opencontainers.image.documentation="https://github.com/novelai-image-mcp/NovelAI-Image-MCP#readme" \
  org.opencontainers.image.created="${CREATED}"

ENV TZ=Asia/Shanghai
ENV PYTHONPATH=/app
# Force unbuffered stdout/stderr so logs surface immediately in container
# orchestrators (docker logs / kubectl logs).
ENV PYTHONUNBUFFERED=1

# ── Non-root user ──
RUN groupadd --system app \
  && useradd --system --gid app --home-dir /app --shell /usr/sbin/nologin app \
  && chown -R app:app /app

# ── Install dependencies from pre-built wheels ──
COPY --from=requirements_stage /wheels /wheels
COPY --from=requirements_stage /wheel/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r /tmp/requirements.txt \
  && rm -rf /wheels /tmp/requirements.txt

# ── Install project wheel ──
COPY --from=project_build /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# ── Smoke-test support ──
# Build-time flag: when SMOKE_TEST=true the entrypoint runs docker/smoke-test.py
# instead of the production MCP server. The smoke-test image is built by CI
# (.github/workflows/ci.yml) to verify the image boots and tools register.
ARG SMOKE_TEST=false
ENV SMOKE_TEST=${SMOKE_TEST}
COPY --chown=app:app ./docker/smoke-test.py /app/docker/smoke-test.py

USER app

# ── Healthcheck ──
# Stdio transport has no listening port, so the healthcheck only runs the
# Python import sanity check. For streamable-http, override the healthcheck
# in docker-compose.yml to test the bind address (default 127.0.0.1:8000).
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import novelai_image_mcp; print(novelai_image_mcp.__version__)" || exit 1

# ── Entrypoint ──
# A conditional CMD is required because the CI smoke-test job invokes the
# image without a command override and selects the branch via SMOKE_TEST=true.
# The production branch uses ``exec`` so the MCP server receives process
# signals directly (equivalent to exec-form ENTRYPOINT).
CMD if [ "${SMOKE_TEST}" = "true" ]; then exec python /app/docker/smoke-test.py; else exec novelai-image-mcp serve; fi
