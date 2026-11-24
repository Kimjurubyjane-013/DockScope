import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    payload = {
        "email": "devops@dockscope.io",
        "password": "SecurePassword123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "devops@dockscope.io"
    assert "id" in data
    assert data["is_active"] is True
    assert "created_at" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client: AsyncClient):
    payload = {
        "email": "admin@dockscope.io",
        "password": "InitialPassword123!",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Attempt duplicate registration
    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_password_length(client: AsyncClient):
    payload = {
        "email": "short@dockscope.io",
        "password": "short",  # Less than 8 chars
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    reg_payload = {
        "email": "login_test@dockscope.io",
        "password": "MyStrongPassword456!",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201

    login_payload = {
        "email": "login_test@dockscope.io",
        "password": "MyStrongPassword456!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    # Verify HttpOnly cookie was set
    assert "dockscope_access_token" in response.cookies


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    reg_payload = {
        "email": "wrong_pw@dockscope.io",
        "password": "CorrectPassword123!",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "wrong_pw@dockscope.io",
        "password": "WrongPassword999!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    login_payload = {
        "email": "nonexistent@dockscope.io",
        "password": "SomePassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_protected_endpoint(client: AsyncClient):
    reg_payload = {
        "email": "auth_me@dockscope.io",
        "password": "PasswordForMe123!",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_res = await client.post("/api/v1/auth/login", json=reg_payload)
    token = login_res.json()["access_token"]

    # 1. Access with Authorization Bearer header
    headers = {"Authorization": f"Bearer {token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "auth_me@dockscope.io"

    # 2. Access with cookie
    client.cookies.set("dockscope_access_token", token)
    me_cookie_res = await client.get("/api/v1/auth/me")
    assert me_cookie_res.status_code == 200
    assert me_cookie_res.json()["email"] == "auth_me@dockscope.io"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_endpoint(client: AsyncClient):
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out."
