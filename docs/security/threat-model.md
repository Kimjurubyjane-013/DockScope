# Security Architecture & Threat Model

DockScope is designed with defense-in-depth principles for self-hosted and enterprise infrastructure environments.

## Threat Surface Analysis & Controls

### 1. Token Storage & XSS Mitigation
- Web client authentication does not persist JWTs in browser `localStorage` or `sessionStorage`.
- Sessions are governed through an `HttpOnly`, `SameSite=Lax` cookie (`dockscope_access_token`).
- JavaScript execution in the browser context cannot read or extract the active session token.

### 2. Password Hashing
- User passwords are processed with the memory-hard `Argon2id` algorithm (`argon2-cffi`).
- Default cost parameters: 64MB memory, 3 iterations, 4 parallelism lanes.
- Plaintext passwords are never logged, stored, or echoed across API responses.

### 3. Network Isolation
- PostgreSQL runs on loopback `127.0.0.1:5432` and the internal Docker bridge network (`dockscope_net`).
- Database ports are never exposed to public network interfaces.
- Only the Nginx reverse proxy exposes a public ingress port (`3000`).

### 4. Container Hardening
- Containers avoid privileged execution (`privileged: false`).
- Application Dockerfiles implement non-root service accounts (`dockscope:10001`).
- Minimal attack surface using Alpine and Debian-slim container foundations.

### 5. Docker Socket & Daemon Security Boundaries (Milestone 02.1)
- **Mounting Risks & Root Equivalence**: Mounting `/var/run/docker.sock` directly into containers effectively grants root-equivalent control over the host filesystem and kernel. Direct unauthenticated socket exposure is strictly prohibited.
- **Read-Only Scope**: In Milestone 02.1, the Docker integration service is restricted to read-only diagnostics (`ping`, `version`, `info`). Mutating operations (container create, start, stop, kill, exec, volume remove) are neither implemented nor permitted.
- **Authentication Protection**: The Docker Engine telemetry endpoint (`/api/v1/docker/status`) is strictly authenticated. Public or unauthenticated queries are rejected with `401 Unauthorized`.
- **Sensitive Data Redaction**: The Docker daemon configuration (`RegistryConfig`, `InsecureRegistryCIDRs`, `Labels`, plugins, authentication stores) is filtered out before returning responses to clients.
- **Windows + WSL2 + Docker Desktop Boundaries**: When running under Windows, the service accesses the local Docker Engine via Windows named pipes (`npipe:////./pipe/docker_engine`). For Dockerized backends, communication requires either an explicit read-only socket proxy or an outbound-only agent architecture (planned for Milestone 03).
