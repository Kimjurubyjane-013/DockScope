# DockScope

<div align="center">

**Monitor. Analyze. Control.**

An open-source, self-hosted platform for monitoring, understanding, securing, and managing Docker and Linux infrastructure through a unified web interface.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Frontend](https://img.shields.io/badge/Frontend-Vue_3_%7C_TypeScript_%7C_Vite-42b883.svg)](frontend/)
[![Backend](https://img.shields.io/badge/Backend-FastAPI_%7C_Python_3-009688.svg)](backend/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL_16-336791.svg)](docker-compose.yml)
[![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF.svg)](.github/workflows/ci.yml)

</div>

---

## 1. Project Overview

DockScope addresses the operational friction of distributed Docker and Linux server administration. Instead of juggling detached SSH sessions, command-line inspection tools, and fragmented telemetry dashboards, DockScope consolidates real-time host metrics, container lifecycles, and security posture into a single, high-contrast, responsive dashboard.

### Core Philosophy
- **Self-Hosted First**: You control your telemetry, database, and infrastructure data without third-party vendor lock-in.
- **Enterprise Security**: Argon2id password hashing, JWT authentication via HttpOnly cookies, internal network isolation, and non-root container sandboxing.
- **Modern Architecture**: Asynchronous Python backend (FastAPI + SQLAlchemy 2.x), responsive Vue 3 SPA, and Nginx reverse proxy.

---

## 2. Technology Stack

### Presentation Layer (Frontend)
- **Framework**: Vue 3 (Composition API with `<script setup lang="ts">`)
- **Language**: TypeScript
- **Bundler & Tooling**: Vite, Vitest, Vue Test Utils
- **Styling**: Tailwind CSS (custom dark infrastructure palette `#071827`, `#0D2233`, `#22D3EE`)
- **State & Routing**: Pinia, Vue Router
- **Icons**: Lucide Icons
- **Validation & HTTP**: Zod, Axios

### Application Layer (Backend)
- **Framework**: FastAPI (asynchronous ASGI)
- **Runtime**: Python 3.11+ / 3.14
- **Persistence & ORM**: PostgreSQL 16, SQLAlchemy 2.x (async), Psycopg 3
- **Migrations**: Alembic
- **Security**: Argon2id (`argon2-cffi`), PyJWT
- **Validation**: Pydantic v2, Pydantic Settings
- **Testing**: Pytest, Pytest-Asyncio, HTTPX

### Infrastructure & Deployment
- **Containerization**: Docker, Docker Compose
- **Web Ingress**: Nginx reverse proxy
- **Storage**: Persistent named Docker volume (`postgres_data`)

---

## 3. Architecture Overview

```
[ Browser / API Client ]
           │
           ▼
[ Nginx Reverse Proxy (:3000) ]
     │                   │
     │ /api/v1/*         │ /* (SPA)
     ▼                   ▼
[ FastAPI Backend ]  [ Vue 3 Frontend ]
     │
     ▼ (Internal Network)
[ PostgreSQL 16 DB ]
```

---

## 4. Prerequisites

- **Docker**: Engine version 24.0+
- **Docker Compose**: Version 2.20+
- *(Optional for bare-metal development)*:
  - Python 3.11+
  - Node.js 20+

---

## 5. Quickstart with Docker Compose

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dockscope/dockscope.git
   cd dockscope
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

3. **Build and start services:**
   ```bash
   docker compose up -d --build
   ```

4. **Apply initial database migrations:**
   ```bash
   # On Linux / macOS:
   ./scripts/migrate.sh
   # Or using PowerShell on Windows:
   ./scripts/migrate.ps1
   # Or directly with Docker Compose:
   docker compose exec backend alembic upgrade head
   ```

5. **Access the application:**
   - **Web UI**: [http://localhost:3000](http://localhost:3000)
   - **Interactive API Docs (Swagger)**: [http://localhost:3000/api/v1/docs](http://localhost:3000/api/v1/docs)
   - **Alternative API Docs (ReDoc)**: [http://localhost:3000/api/v1/redoc](http://localhost:3000/api/v1/redoc)

---

## 6. Local Development Commands

### Backend
```bash
# Set up virtual environment
python -m venv backend/venv
source backend/venv/bin/activate  # Windows: & backend/venv/Scripts/Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# Run migrations
alembic upgrade head

# Start API dev server with hot reload
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run backend tests
pytest backend/tests -v
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev

# Type check
npm run type-check

# Run unit tests
npm run test:unit

# Build for production
npm run build
```

---

## 7. Testing Suite Summary

### Backend Tests
- Application liveness healthcheck (`/api/v1/health`)
- PostgreSQL database connectivity check (`/api/v1/health/ready`)
- User registration with unique email validation
- Duplicate email prevention
- Password minimum length verification
- Password hashing with Argon2id
- Login and authentication token generation (JWT & HttpOnly cookie)
- Protected `/api/v1/auth/me` endpoint authorization checks
- Session termination (`/api/v1/auth/logout`)
- Docker Engine connection status (`/api/v1/docker/status`):
  - Authenticated session requirement
  - Connected state with version and telemetry details
  - Disconnected daemon handling
  - Unavailable socket/pipe detection
  - Timeout and unexpected error sanitization

### Frontend Tests
- Common UI components (`BaseButton`, `BaseInput`, `StatCard`)
- Docker Engine connection status component (`DockerEngineStatus`):
  - Connected state with live telemetry
  - Disconnected state with error alerts
  - Unavailable socket state
- Form validation schemas with Zod (email formats, password matching)
- Full production compilation and TypeScript strict verification

---

## 8. Current Status & Roadmap

| Milestone | Scope | Status |
| --------- | ----- | ------ |
| **Milestone 01** | **Professional Project Foundation** (Auth, DB, Vue 3, FastAPI, Docker, Nginx) | **Completed** |
| **Milestone 02.1** | **Docker Engine Connection** (Read-only daemon probe, versioning, status telemetry) | **Completed** |
| **Milestone 02.2** | Container Workload Observation (Live container listings, inspection, images) | Planned |
| **Milestone 02.3** | Container Lifecycle Controls (Start/stop/restart, log streaming) | Planned |
| **Milestone 03** | Linux Host Agent & Multi-Host Telemetry (Zero-dependency daemon, metrics) | Planned |
| **Milestone 04** | Security Intelligence & Vulnerability Scanner (CVE indexing, CIS benchmarks) | Planned |
| **Milestone 05** | Alerts, Notifications & Webhooks (Slack, Discord, Email, PagerDuty) | Planned |

---

## 9. Contributing

We welcome community contributions! Please review [CONTRIBUTING.md](CONTRIBUTING.md) and our [SECURITY.md](SECURITY.md) guidelines before opening a pull request.

---

## 10. License

DockScope is licensed under the **Apache License, Version 2.0**. See [LICENSE](LICENSE) for details.
