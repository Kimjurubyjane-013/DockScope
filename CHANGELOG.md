# Changelog

All notable changes to **DockScope** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-11-23

### Added
- **Milestone 02.1: Docker Engine Connection (Read-Only)**
- Backend `DockerService` integration querying local Docker Engine via Windows named pipe or Unix socket.
- Authenticated `GET /api/v1/docker/status` endpoint reporting connection states (`connected`, `disconnected`, `unavailable`, `error`).
- Read-only telemetry extraction: Engine version, API version, system architecture, CPU count, total memory, and container counts.
- Daemon timeout protection and safe error sanitization preventing secret or config leakage.
- Frontend `DockerEngineStatus.vue` dashboard component with real-time status indicators, version displays, and manual refresh controls.
- Integrated Docker status into Dashboard and Docker Workloads views.
- Comprehensive backend Pytest suite covering connected, disconnected, unavailable, timeout, and authentication scenarios.
- Frontend Vitest unit test suite covering connected and disconnected states.

## [0.1.0] - 2026-11-22

### Added
- **Milestone 01: Professional Project Foundation**
- Complete modular directory architecture for frontend, backend, agent, deployment, and documentation.
- FastAPI backend with asynchronous SQLAlchemy 2.0 ORM and Alembic database migrations.
- Argon2id password hashing and JWT token management with secure HttpOnly cookies.
- Authentication endpoints: `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/logout`, `/api/v1/auth/me`.
- Health and database readiness check endpoints: `/api/v1/health`, `/api/v1/health/ready`.
- Vue 3 + TypeScript + Vite frontend with Tailwind CSS infrastructure theme.
- Frontend views: Login, Registration, Dashboard, Hosts, Docker, Security, and Settings.
- Zod form validation and Vitest test suite.
- Comprehensive Pytest backend test suite covering auth flows and health checks.
- Multi-stage Dockerfile configurations, Nginx ingress reverse proxy, and docker-compose orchestration.
- Open-source Apache-2.0 licensing, CI workflows, and developer documentation.
