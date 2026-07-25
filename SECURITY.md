# Security Policy

## Supported versions

The NovelAI Image MCP project is pre-1.0 software. Only the latest minor
release line receives security fixes.

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | ✅ active development |
| < 0.1   | ❌ unsupported      |

Once a 1.0.0 release is cut, the policy will switch to supporting the latest
minor release plus the previous minor release with security-only updates.

## Reporting a vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, report them privately via one of these channels:

1. **GitHub Private Security Advisory** (preferred):
   <https://github.com/xinvxueyuan/NovelAI-Image-MCP/security/advisories/new>
2. **Email**: <security@xinvxueyuan.github.io>
   (PGP key fingerprint published in the advisory)

Please include:

- A description of the vulnerability and its impact
- Steps to reproduce (proof-of-concept, payload, or minimal repro)
- Affected versions (commit SHA or release tag)
- Suggested fix or mitigation, if any
- Whether you intend to publish details if no fix is issued (and the
  timeline you intend to follow)

## Response timeline

| Step | Target SLA |
|---|---|
| Acknowledge receipt | within 48 hours |
| Initial assessment + severity rating | within 5 business days |
| Fix or mitigation published | within 30 days (severity-dependent) |
| Public disclosure (after fix is released) | coordinated with reporter |

We follow a **coordinated disclosure** model. We will credit reporters in the
advisory unless they prefer to remain anonymous.

## Scope

This policy covers the **MCP server package** published from `apps/server/`
(including the `novelai-image-mcp` PyPI distribution and the GHCR container
image) and the **documentation site** built from `apps/docs/`.

The following are **out of scope**:

- Vulnerabilities in NovelAI's own API or infrastructure — report those to
  NovelAI directly.
- Issues in third-party dependencies — report those upstream; we will track
  and bump the affected version via Dependabot.
- Denial-of-service via the public streamable-http transport when no
  authentication is configured — that is expected behavior. Configure
  `MCP_HOST` to bind to `127.0.0.1` or front the server with a reverse proxy
  that enforces auth.

## Hardening checklist (for production deployments)

- [ ] Set `MCP_HOST=127.0.0.1` (never expose `0.0.0.0` without a reverse proxy)
- [ ] Front the streamable-http transport with TLS termination
- [ ] Use a dedicated NovelAI token (not your personal account) for the
      server's runtime credentials
- [ ] Run the container as a non-root user (the default `Dockerfile` already
      creates and switches to an `app` user)
- [ ] Mount `NOVELAI_OUTPUT_DIR` on a tmpfs or ephemeral volume if you don't
      need to persist generated images
- [ ] Rotate the NovelAI token periodically; revoke immediately if leaked
