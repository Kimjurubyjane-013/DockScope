#!/usr/bin/env bash
# ==============================================================================
# DockScope Database Migration Script
# ==============================================================================
set -euo pipefail

echo "==> Running DockScope database migrations via Alembic..."
docker compose exec backend alembic upgrade head
echo "==> Migrations completed successfully."
