# DockScope System Architecture

## Overview

DockScope is engineered as an open-source, modular, self-hosted platform for monitoring, analyzing, securing, and managing Docker and Linux infrastructure through a single unified web interface.

```
                              [ Browser Client ]
                                      │
                                      ▼
                      [ Nginx Ingress Proxy :3000 ]
                       ├── /api/* ───────────────┐
                       └── /* (SPA Static)       ▼
                              │           [ FastAPI Backend :8000 ]
                              ▼                  │
                     [ Vue 3 Frontend ]          ├── SQLAlchemy 2.x ──► [ PostgreSQL 16 ]
                                                 │
                                                 └── Read-Only ───────► [ Local Docker Engine ]
                                                                        (Named Pipe / Socket)
```

## Architectural Layers

### 1. Ingress Tier (Nginx)
- Single entrypoint on port `3000`.
- Routes `/api/` traffic directly to the asynchronous FastAPI application server.
- Serves the compiled Vue 3 Single Page Application with HTTP caching and gzip compression.
- Sets standard security headers (`X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`, `Referrer-Policy`).

### 2. Presentation Tier (Frontend)
- **Framework**: Vue 3 with TypeScript, Vite build tool.
- **State Management**: Pinia.
- **Styling**: Tailwind CSS with customized high-contrast dark theme.
- **Routing**: Vue Router with authentication guards.
- **Validation**: Zod schema validation for forms.

### 3. Application Tier (Backend)
- **Framework**: FastAPI (asynchronous Python 3).
- **ORM & Database**: SQLAlchemy 2.0 async engine with Alembic migrations.
- **Security**: Argon2id password hashing and PyJWT tokens.
- **Authentication**: Dual-mode session handling:
  - `HttpOnly` secure cookie for web browser interaction (XSS mitigation).
  - Standard `Authorization: Bearer <token>` for API and CLI consumers.

### 4. Data Tier (PostgreSQL)
- Relational schema with UUID primary keys.
- Named persistent volume `postgres_data` preserving state across container recycles.
- Isolated to loopback/internal container network (`127.0.0.1:5432`).

### 5. Docker Engine Integration Tier (Milestone 02.1 — Read-Only)
- **Local Daemon Communication**: Detects local Docker Engine via Windows named pipe (`npipe:////./pipe/docker_engine`, `npipe:////./pipe/dockerDesktopLinuxEngine`) or Unix domain socket (`unix:///var/run/docker.sock`).
- **Strict Read-Only Enforcement**: Restricted exclusively to non-mutating status probes, API version negotiation, and aggregated resource telemetry (`client.ping()`, `client.version()`, `client.info()`). No lifecycle commands or socket write operations are exposed.
- **Asynchronous Execution & Timeout Protection**: Daemon queries run in worker threads with timeout bounds (`asyncio.timeout(3.0)`), guaranteeing the REST API is never blocked by an unresponsive engine.
- **Redaction of Sensitive Configuration**: Daemon credentials, registries, plugin configurations, and raw socket handles are stripped from responses.
