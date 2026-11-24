#!/usr/bin/env bash
# ==============================================================================
# DockScope Local Development Launcher (Bash)
# ==============================================================================
set -euo pipefail

echo "======================================================"
echo " DockScope Development Environment Launcher           "
echo "======================================================"

echo ""
echo "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000..."
(cd backend && python -m uvicorn app.main:app --reload --port 8000) &
BACKEND_PID=$!

trap "kill $BACKEND_PID 2>/dev/null || true" EXIT

echo "[2/2] Starting Vite Frontend on http://localhost:5173..."
npm run dev --prefix frontend
