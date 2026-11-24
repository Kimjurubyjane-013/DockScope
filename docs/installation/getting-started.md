# Installation & Getting Started

## Prerequisites

- **Docker**: Engine version 24.0+
- **Docker Compose**: Version 2.20+
- (For local non-container development):
  - Python 3.11+
  - Node.js 20+

## Quickstart with Docker Compose

1. Clone the repository and navigate to the project root:
   ```bash
   git clone https://github.com/dockscope/dockscope.git
   cd dockscope
   ```

2. Copy the sample environment configuration:
   ```bash
   cp .env.example .env
   ```

3. Launch the container stack:
   ```bash
   docker compose up -d --build
   ```

4. Execute database migrations:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

5. Open your web browser at:
   ```text
   http://localhost:3000
   ```

6. Register your initial administrator credentials and access the dashboard!
