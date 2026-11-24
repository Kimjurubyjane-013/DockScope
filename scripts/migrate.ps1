# ==============================================================================
# DockScope Database Migration Script (PowerShell)
# ==============================================================================
Write-Host "==> Running DockScope database migrations via Alembic..." -ForegroundColor Cyan
docker compose exec backend alembic upgrade head
if ($LASTEXITCODE -eq 0) {
    Write-Host "==> Migrations completed successfully." -ForegroundColor Green
} else {
    Write-Host "==> Migration failed. Inspect logs for details." -ForegroundColor Red
}
