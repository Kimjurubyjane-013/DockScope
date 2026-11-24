import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_health_ready_endpoint(client: AsyncClient, monkeypatch):
    from app.api.v1.endpoints import health

    async def mock_connected():
        return True

    monkeypatch.setattr(health, "check_db_connectivity", mock_connected)

    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_health_ready_endpoint_failure(client: AsyncClient, monkeypatch):
    from app.api.v1.endpoints import health

    async def mock_disconnected():
        return False

    monkeypatch.setattr(health, "check_db_connectivity", mock_disconnected)

    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == "Database connectivity check failed. PostgreSQL is unreachable."


@pytest.mark.asyncio
async def test_docs_endpoints_in_development(client: AsyncClient):
    # Standard Swagger UI
    res_docs = await client.get("/docs")
    assert res_docs.status_code == 200

    # OpenAPI JSON specification
    res_openapi = await client.get("/openapi.json")
    assert res_openapi.status_code == 200

    # Versioned alias redirects
    res_api_docs = await client.get("/api/v1/docs", follow_redirects=False)
    assert res_api_docs.status_code == 307
    assert res_api_docs.headers["location"] == "/docs"
