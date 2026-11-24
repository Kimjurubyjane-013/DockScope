# ==============================================================================
# DockScope Local Development Launcher (PowerShell)
# ==============================================================================
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " DockScope Development Environment Launcher           " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# 1. Start backend server in a background process from backend/ directory
Write-Host "`n[1/2] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
Start-Process -FilePath "backend/venv/Scripts/python.exe" -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000" -WorkingDirectory "backend"

# 2. Start frontend dev server
Write-Host "[2/2] Starting Vite Frontend on http://localhost:5173..." -ForegroundColor Green
npm run dev --prefix frontend
