import asyncio
from unittest.mock import MagicMock, patch
import pytest
from docker.errors import DockerException, NotFound
from httpx import AsyncClient

from app.schemas.docker import DockerConnectionStatus


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    reg_payload = {
        "email": "docker_tester@dockscope.io",
        "password": "SecurePassword123!",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)
    login_res = await client.post("/api/v1/auth/login", json=reg_payload)
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_docker_status_unauthenticated_fails(client: AsyncClient):
    """Ensure Docker status endpoint requires authentication."""
    response = await client.get("/api/v1/docker/status")
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_docker_status_connected_success(client: AsyncClient, auth_headers: dict):
    """Ensure successful Docker connection returns full read-only telemetry."""
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.version.return_value = {
        "Version": "29.9.3",
        "ApiVersion": "1.56",
        "MinAPIVersion": "1.24",
    }
    mock_client.info.return_value = {
        "OperatingSystem": "Docker Desktop",
        "OSType": "linux",
        "Architecture": "x86_64",
        "NCPU": 8,
        "MemTotal": 16777216000,
        "Containers": 5,
        "ContainersRunning": 3,
        "ContainersPaused": 0,
        "ContainersStopped": 2,
        "Images": 12,
    }

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "npipe:////./pipe/docker_engine")
        response = await client.get("/api/v1/docker/status", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == DockerConnectionStatus.CONNECTED
    assert data["endpoint"] == "npipe:////./pipe/docker_engine"
    assert data["error_message"] is None

    details = data["details"]
    assert details["version"] == "29.9.3"
    assert details["api_version"] == "1.56"
    assert details["os"] == "Docker Desktop"
    assert details["architecture"] == "x86_64"
    assert details["containers_total"] == 5
    assert details["containers_running"] == 3
    assert details["images_total"] == 12


@pytest.mark.asyncio
async def test_docker_status_daemon_unavailable(client: AsyncClient, auth_headers: dict):
    """Ensure unavailable socket/pipe returns 'unavailable' status with safe message."""
    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_client = MagicMock()
        mock_client.ping.side_effect = DockerException("The system cannot find the file specified.")
        mock_create.return_value = (mock_client, "npipe:////./pipe/docker_engine")

        response = await client.get("/api/v1/docker/status", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == DockerConnectionStatus.UNAVAILABLE
    assert data["details"] is None
    assert "not found" in data["error_message"].lower()


@pytest.mark.asyncio
async def test_docker_status_connection_refused(client: AsyncClient, auth_headers: dict):
    """Ensure connection refused returns 'disconnected' status."""
    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_client = MagicMock()
        mock_client.ping.side_effect = DockerException("Connection refused")
        mock_create.return_value = (mock_client, "unix:///var/run/docker.sock")

        response = await client.get("/api/v1/docker/status", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == DockerConnectionStatus.DISCONNECTED
    assert data["details"] is None
    assert "refused" in data["error_message"].lower()


@pytest.mark.asyncio
async def test_docker_status_timeout(client: AsyncClient, auth_headers: dict):
    """Ensure Docker probe timeout is handled gracefully without hanging."""
    from app.services.docker_service import DockerService

    async def mock_sleep():
        await asyncio.sleep(2.0)
        return MagicMock()

    # Create a service with 0.1s timeout
    fast_service = DockerService(timeout=0.05)

    with patch("app.api.v1.endpoints.docker.docker_service", fast_service):
        with patch.object(fast_service, "_sync_fetch_status") as mock_fetch:
            # Simulate a slow sync function
            import time

            def slow_call():
                time.sleep(0.2)

            mock_fetch.side_effect = slow_call

            response = await client.get("/api/v1/docker/status", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == DockerConnectionStatus.ERROR
    assert "timed out" in data["error_message"].lower()


@pytest.mark.asyncio
async def test_docker_status_unexpected_error(client: AsyncClient, auth_headers: dict):
    """Ensure unexpected daemon errors are caught and sanitized."""
    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.version.side_effect = RuntimeError("Fatal buffer corruption")
        mock_create.return_value = (mock_client, "test-socket")

        response = await client.get("/api/v1/docker/status", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == DockerConnectionStatus.ERROR
    assert data["details"] is None
    assert "unexpected" in data["error_message"].lower()


# ==============================================================================
# Container Discovery & Inspection Tests (M02.2)
# ==============================================================================

MOCK_CONTAINERS_RAW = [
    {
        "Id": "a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef",
        "Names": ["/production-postgres"],
        "Image": "postgres:16-alpine",
        "Created": 1700000000,
        "State": "running",
        "Status": "Up 3 hours (healthy)",
        "Ports": [
            {"IP": "127.0.0.1", "PrivatePort": 5432, "PublicPort": 5432, "Type": "tcp"},
        ],
        "Labels": {
            "com.docker.compose.project": "dockscope",
            "app.env": "production",
            "secret_token": "should-be-redacted",
            "db_password": "should-be-redacted",
        },
    },
    {
        "Id": "b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef12",
        "Names": ["/cache-redis"],
        "Image": "redis:7-alpine",
        "Created": 1700001000,
        "State": "exited",
        "Status": "Exited (0) 10 minutes ago",
        "Ports": [
            {"PrivatePort": 6379, "Type": "tcp"},
        ],
        "Labels": {
            "com.docker.compose.service": "cache",
        },
    },
]

MOCK_INSPECT_CONTAINER_RAW = {
    "Id": "a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef",
    "Name": "/production-postgres",
    "Created": "2026-11-20T10:00:00Z",
    "Image": "sha256:fedcba9876543210",
    "RestartCount": 2,
    "State": {
        "Status": "running",
        "Running": True,
        "StartedAt": "2026-11-20T10:00:05Z",
        "FinishedAt": "0001-01-01T00:00:00Z",
        "Health": {
            "Status": "healthy",
        },
    },
    "Config": {
        "Image": "postgres:16-alpine",
        "Cmd": ["postgres", "-c", "shared_buffers=256MB"],
        "Labels": {
            "com.docker.compose.project": "dockscope",
            "auth_token": "super-secret-must-not-leak",
            "public_tag": "v1.0",
        },
        "Env": [
            "POSTGRES_PASSWORD=SuperSecretDatabasePassword123!",
            "JWT_SECRET=UnsafeToken123456789",
        ],
    },
    "NetworkSettings": {
        "Ports": {
            "5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": "5432"}],
            "8080/tcp": None,
        },
        "Networks": {
            "dockscope-net": {"IPAddress": "172.20.0.3"},
        },
    },
    "Mounts": [
        {
            "Type": "volume",
            "Name": "postgres_data",
            "Source": "/var/lib/docker/volumes/postgres_data/_data",
            "Destination": "/var/lib/postgresql/data",
            "Mode": "rw",
            "RW": True,
        },
    ],
}


@pytest.mark.asyncio
async def test_list_containers_unauthenticated_fails(client: AsyncClient):
    """Ensure container listing requires authentication."""
    response = await client.get("/api/v1/docker/containers")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_container_unauthenticated_fails(client: AsyncClient):
    """Ensure container inspection requires authentication."""
    response = await client.get("/api/v1/docker/containers/any-container-id")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_containers_success(client: AsyncClient, auth_headers: dict):
    """Ensure listing containers returns sanitized summaries, ports, and counts."""
    mock_client = MagicMock()
    mock_client.api.containers.return_value = MOCK_CONTAINERS_RAW

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "npipe:////./pipe/docker_engine")
        response = await client.get("/api/v1/docker/containers", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    c1 = data["items"][0]
    assert c1["name"] == "production-postgres"
    assert c1["short_id"] == "a1b2c3d4e5f6"
    assert c1["state"] == "running"
    assert c1["status"] == "Up 3 hours (healthy)"
    assert len(c1["ports"]) == 1
    assert c1["ports"][0]["container_port"] == 5432
    assert c1["ports"][0]["host_port"] == 5432
    assert c1["ports"][0]["host_ip"] == "127.0.0.1"

    # Redaction verification: sensitive labels must be purged
    assert "com.docker.compose.project" in c1["labels"]
    assert "secret_token" not in c1["labels"]
    assert "db_password" not in c1["labels"]

    c2 = data["items"][1]
    assert c2["name"] == "cache-redis"
    assert c2["state"] == "exited"
    assert len(c2["ports"]) == 1
    assert c2["ports"][0]["container_port"] == 6379
    assert c2["ports"][0]["host_port"] is None


@pytest.mark.asyncio
async def test_list_containers_status_filter(client: AsyncClient, auth_headers: dict):
    """Ensure filtering by status works for running and stopped states."""
    mock_client = MagicMock()
    mock_client.api.containers.return_value = MOCK_CONTAINERS_RAW

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")

        # Test filter status=running
        res_running = await client.get("/api/v1/docker/containers?status=running", headers=auth_headers)
        assert res_running.status_code == 200
        items_running = res_running.json()["items"]
        assert len(items_running) == 1
        assert items_running[0]["name"] == "production-postgres"

        # Test filter status=stopped
        res_stopped = await client.get("/api/v1/docker/containers?status=stopped", headers=auth_headers)
        assert res_stopped.status_code == 200
        items_stopped = res_stopped.json()["items"]
        assert len(items_stopped) == 1
        assert items_stopped[0]["name"] == "cache-redis"


@pytest.mark.asyncio
async def test_list_containers_search(client: AsyncClient, auth_headers: dict):
    """Ensure searching by container name or image works properly."""
    mock_client = MagicMock()
    mock_client.api.containers.return_value = MOCK_CONTAINERS_RAW

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")

        # Search by container name
        res_search_name = await client.get("/api/v1/docker/containers?search=postgres", headers=auth_headers)
        assert res_search_name.status_code == 200
        assert len(res_search_name.json()["items"]) == 1

        # Search by image
        res_search_image = await client.get("/api/v1/docker/containers?search=redis", headers=auth_headers)
        assert res_search_image.status_code == 200
        assert len(res_search_image.json()["items"]) == 1

        # Search nonexistent
        res_none = await client.get("/api/v1/docker/containers?search=nonexistent_xyz", headers=auth_headers)
        assert res_none.status_code == 200
        assert len(res_none.json()["items"]) == 0


@pytest.mark.asyncio
async def test_list_containers_daemon_unavailable(client: AsyncClient, auth_headers: dict):
    """Ensure 503 is returned when Docker daemon is unreachable during container listing."""
    mock_client = MagicMock()
    mock_client.api.containers.side_effect = DockerException("Error connecting to Docker Engine pipe.")

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers", headers=auth_headers)

    assert response.status_code == 503
    assert "unreachable" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_container_detail_success(client: AsyncClient, auth_headers: dict):
    """Ensure container inspection returns detailed metadata and strictly omits environment variables."""
    mock_client = MagicMock()
    mock_client.api.inspect_container.return_value = MOCK_INSPECT_CONTAINER_RAW

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get(
            "/api/v1/docker/containers/a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "production-postgres"
    assert data["short_id"] == "a1b2c3d4e5f6"
    assert data["image"] == "postgres:16-alpine"
    assert data["command"] == "postgres -c shared_buffers=256MB"
    assert data["state"] == "running"
    assert data["health_status"] == "healthy"
    assert data["restart_count"] == 2
    assert "dockscope-net" in data["networks"]
    assert len(data["mounts"]) == 1
    assert data["mounts"][0]["destination"] == "/var/lib/postgresql/data"

    # Verify ports
    ports = data["ports"]
    assert len(ports) == 2
    assert any(p["container_port"] == 5432 and p["host_port"] == 5432 for p in ports)
    assert any(p["container_port"] == 8080 and p["host_port"] is None for p in ports)

    # STRICT SECURITY: Environment variables must NOT be in the schema or response
    assert "Env" not in data
    assert "env" not in data
    assert "SuperSecretDatabasePassword123!" not in str(data)

    # Redacted labels
    assert "auth_token" not in data["labels"]
    assert data["labels"]["public_tag"] == "v1.0"


@pytest.mark.asyncio
async def test_get_container_not_found(client: AsyncClient, auth_headers: dict):
    """Ensure nonexistent container returns HTTP 404."""
    mock_client = MagicMock()
    mock_client.api.inspect_container.side_effect = NotFound("No such container: unknown-container")

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers/unknown-container", headers=auth_headers)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_container_daemon_unavailable(client: AsyncClient, auth_headers: dict):
    """Ensure 503 is returned when Docker daemon is unreachable during container inspection."""
    mock_client = MagicMock()
    mock_client.api.inspect_container.side_effect = DockerException("Named pipe closed unexpectedly.")

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers/some-id", headers=auth_headers)

    assert response.status_code == 503
    assert "unreachable" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_container_count_reconciliation_and_all_states(client: AsyncClient, auth_headers: dict):
    """
    Regression test:
    Verify that GET /api/v1/docker/status and GET /api/v1/docker/containers
    report 100% consistent counts across all 5 container states:
    running, exited, paused, restarting, and created.
    """
    mock_containers = [
        {
            "Id": "c111111111111111111111111111111111111111111111111111111111111111",
            "Names": ["/app-running"],
            "Image": "nginx:alpine",
            "ImageID": "sha256:1111",
            "Command": "nginx -g 'daemon off;'",
            "Created": 1700000000,
            "State": "running",
            "Status": "Up 2 hours",
            "Ports": [],
            "Labels": {},
            "NetworkSettings": {"Networks": {}},
        },
        {
            "Id": "c222222222222222222222222222222222222222222222222222222222222222",
            "Names": ["/app-exited"],
            "Image": "alpine:latest",
            "ImageID": "sha256:2222",
            "Command": "sh",
            "Created": 1700000100,
            "State": "exited",
            "Status": "Exited (0) 10 minutes ago",
            "Ports": [],
            "Labels": {},
            "NetworkSettings": {"Networks": {}},
        },
        {
            "Id": "c33333333333333333333333333333333333333333333333333333333333333",
            "Names": ["/app-paused"],
            "Image": "redis:7-alpine",
            "ImageID": "sha256:3333",
            "Command": "redis-server",
            "Created": 1700000200,
            "State": "paused",
            "Status": "Up 1 hour (Paused)",
            "Ports": [],
            "Labels": {},
            "NetworkSettings": {"Networks": {}},
        },
        {
            "Id": "c44444444444444444444444444444444444444444444444444444444444444",
            "Names": ["/app-restarting"],
            "Image": "busybox:latest",
            "ImageID": "sha256:4444",
            "Command": "sh -c 'exit 1'",
            "Created": 1700000300,
            "State": "restarting",
            "Status": "Restarting (1) 2 seconds ago",
            "Ports": [],
            "Labels": {},
            "NetworkSettings": {"Networks": {}},
        },
        {
            "Id": "c55555555555555555555555555555555555555555555555555555555555555",
            "Names": ["/app-created"],
            "Image": "postgres:16-alpine",
            "ImageID": "sha256:5555",
            "Command": "postgres",
            "Created": 1700000400,
            "State": "created",
            "Status": "Created",
            "Ports": [],
            "Labels": {},
            "NetworkSettings": {"Networks": {}},
        },
    ]

    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.version.return_value = {
        "Version": "29.9.3",
        "ApiVersion": "1.56",
        "MinAPIVersion": "1.24",
    }
    mock_client.info.return_value = {
        "OperatingSystem": "Docker Desktop",
        "OSType": "linux",
        "Architecture": "x86_64",
        "NCPU": 8,
        "MemTotal": 16777216000,
        "Containers": 999,
        "ContainersRunning": 999,
        "ContainersPaused": 999,
        "ContainersStopped": 999,
        "Images": 5,
    }
    mock_client.api.containers.return_value = mock_containers

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "npipe:////./pipe/docker_engine")

        # 1. Test status reconciliation from authoritative container inventory
        res_status = await client.get("/api/v1/docker/status", headers=auth_headers)
        assert res_status.status_code == 200
        details = res_status.json()["details"]
        assert details["containers_total"] == 5
        assert details["containers_running"] == 1
        assert details["containers_paused"] == 1
        assert details["containers_stopped"] == 2

        # 2. Test list all containers
        res_all = await client.get("/api/v1/docker/containers", headers=auth_headers)
        assert res_all.status_code == 200
        data_all = res_all.json()
        assert data_all["total"] == 5
        states = {item["name"]: item["state"] for item in data_all["items"]}
        assert states["app-running"] == "running"
        assert states["app-exited"] == "exited"
        assert states["app-paused"] == "paused"
        assert states["app-restarting"] == "restarting"
        assert states["app-created"] == "created"

        # 3. Test status filter: running
        res_running = await client.get("/api/v1/docker/containers?status=running", headers=auth_headers)
        assert res_running.status_code == 200
        assert res_running.json()["total"] == 1
        assert res_running.json()["items"][0]["name"] == "app-running"

        # 4. Test status filter: stopped (includes exited and created, excludes running, paused, restarting)
        res_stopped = await client.get("/api/v1/docker/containers?status=stopped", headers=auth_headers)
        assert res_stopped.status_code == 200
        assert res_stopped.json()["total"] == 2
        stopped_names = {i["name"] for i in res_stopped.json()["items"]}
        assert stopped_names == {"app-exited", "app-created"}

        # 5. Test status filter: paused
        res_paused = await client.get("/api/v1/docker/containers?status=paused", headers=auth_headers)
        assert res_paused.status_code == 200
        assert res_paused.json()["total"] == 1
        assert res_paused.json()["items"][0]["name"] == "app-paused"

        # 6. Test status filter: restarting
        res_restarting = await client.get("/api/v1/docker/containers?status=restarting", headers=auth_headers)
        assert res_restarting.status_code == 200
        assert res_restarting.json()["total"] == 1
        assert res_restarting.json()["items"][0]["name"] == "app-restarting"

        # 7. Test status filter: created
        res_created = await client.get("/api/v1/docker/containers?status=created", headers=auth_headers)
        assert res_created.status_code == 200
        assert res_created.json()["total"] == 1
        assert res_created.json()["items"][0]["name"] == "app-created"

        # 8. Test status filter: exited
        res_exited = await client.get("/api/v1/docker/containers?status=exited", headers=auth_headers)
        assert res_exited.status_code == 200
        assert res_exited.json()["total"] == 1
        assert res_exited.json()["items"][0]["name"] == "app-exited"


MOCK_RAW_STATS_RUNNING = {
    "read": "2026-11-23T12:00:00Z",
    "cpu_stats": {
        "cpu_usage": {
            "total_usage": 200000000,
            "percpu_usage": [100000000, 100000000],
        },
        "system_cpu_usage": 1000000000,
        "online_cpus": 2,
    },
    "precpu_stats": {
        "cpu_usage": {
            "total_usage": 100000000,
            "percpu_usage": [50000000, 50000000],
        },
        "system_cpu_usage": 500000000,
    },
    "memory_stats": {
        "usage": 104857600,
        "limit": 1073741824,
        "stats": {
            "inactive_file": 20971520,
        },
    },
    "networks": {
        "eth0": {
            "rx_bytes": 1024,
            "tx_bytes": 2048,
        },
        "eth1": {
            "rx_bytes": 512,
            "tx_bytes": 512,
        },
    },
    "blkio_stats": {
        "io_service_bytes_recursive": [
            {"op": "read", "value": 4096},
            {"op": "write", "value": 8192},
        ],
    },
}


@pytest.mark.asyncio
async def test_container_stats_unauthenticated_fails(client: AsyncClient):
    """Ensure stats endpoint requires authentication."""
    response = await client.get("/api/v1/docker/containers/c1/stats")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_container_stats_running_success(client: AsyncClient, auth_headers: dict):
    """Ensure running container returns full calculated metrics."""
    mock_client = MagicMock()
    mock_client.api.inspect_container.return_value = {
        "Id": "c111111111111111111111111111111111111111111111111111111111111111",
        "Name": "/test-app",
        "State": {"Running": True, "Status": "running"},
        "HostConfig": {"Memory": 1073741824},
    }
    mock_client.api.stats.return_value = MOCK_RAW_STATS_RUNNING

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers/c1111/stats", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["container_id"] == "c111111111111111111111111111111111111111111111111111111111111111"
    assert data["name"] == "test-app"
    assert data["is_running"] is True
    assert data["cpu_percentage"] == 40.0
    assert data["cpu_usage_nanoseconds"] == 200000000
    assert data["system_cpu_usage_nanoseconds"] == 1000000000
    assert data["online_cpus"] == 2
    assert data["memory_usage_bytes"] == 83886080
    assert data["memory_limit_bytes"] == 1073741824
    assert data["memory_percentage"] == 7.81
    assert data["network_rx_bytes"] == 1536
    assert data["network_tx_bytes"] == 2560
    assert data["block_read_bytes"] == 4096
    assert data["block_write_bytes"] == 8192


@pytest.mark.asyncio
async def test_container_stats_stopped_container(client: AsyncClient, auth_headers: dict):
    """Ensure stopped container returns is_running=False with zero usage without hanging."""
    mock_client = MagicMock()
    mock_client.api.inspect_container.return_value = {
        "Id": "c222222222222222222222222222222222222222222222222222222222222222",
        "Name": "/stopped-app",
        "State": {"Running": False, "Status": "exited"},
        "HostConfig": {"Memory": 536870912},
    }

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers/c2222/stats", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["is_running"] is False
    assert data["cpu_percentage"] == 0.0
    assert data["memory_usage_bytes"] == 0
    assert data["memory_percentage"] == 0.0
    assert data["memory_limit_bytes"] == 536870912
    assert data["network_rx_bytes"] is None
    assert data["block_read_bytes"] is None
    mock_client.api.stats.assert_not_called()


@pytest.mark.asyncio
async def test_container_stats_not_found(client: AsyncClient, auth_headers: dict):
    """Ensure unknown container ID returns 404."""
    mock_client = MagicMock()
    mock_client.api.inspect_container.side_effect = NotFound("No such container: non-existent")

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers/non-existent/stats", headers=auth_headers)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_container_stats_daemon_unavailable(client: AsyncClient, auth_headers: dict):
    """Ensure 503 is returned when Docker daemon is unreachable during stats collection."""
    mock_client = MagicMock()
    mock_client.api.inspect_container.side_effect = DockerException("Pipe is broken")

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers/c1/stats", headers=auth_headers)

    assert response.status_code == 503
    assert "unreachable" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_container_stats_zero_cpu_delta(client: AsyncClient, auth_headers: dict):
    """Ensure zero CPU or system delta returns 0.0% CPU usage without division by zero."""
    zero_delta_stats = {
        "read": "2026-11-23T12:00:00Z",
        "cpu_stats": {
            "cpu_usage": {"total_usage": 100000000},
            "system_cpu_usage": 500000000,
            "online_cpus": 4,
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": 100000000},
            "system_cpu_usage": 500000000,
        },
        "memory_stats": {"usage": 50000000, "limit": 100000000},
    }
    mock_client = MagicMock()
    mock_client.api.inspect_container.return_value = {
        "Id": "c3",
        "Name": "/idle-app",
        "State": {"Running": True, "Status": "running"},
        "HostConfig": {},
    }
    mock_client.api.stats.return_value = zero_delta_stats

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers/c3/stats", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["cpu_percentage"] == 0.0


@pytest.mark.asyncio
async def test_container_stats_missing_memory_and_optional_metrics(client: AsyncClient, auth_headers: dict):
    """Ensure missing memory fields and missing network/blkio are handled safely."""
    minimal_stats = {
        "read": "2026-11-23T12:00:00Z",
        "cpu_stats": {},
        "precpu_stats": {},
        "memory_stats": {},
    }
    mock_client = MagicMock()
    mock_client.api.inspect_container.return_value = {
        "Id": "c4",
        "Name": "/minimal-app",
        "State": {"Running": True, "Status": "running"},
        "HostConfig": {},
    }
    mock_client.api.stats.return_value = minimal_stats

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers/c4/stats", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["cpu_percentage"] == 0.0
    assert data["memory_usage_bytes"] == 0
    assert data["memory_limit_bytes"] == 0
    assert data["memory_percentage"] == 0.0
    assert data["network_rx_bytes"] is None
    assert data["network_tx_bytes"] is None
    assert data["block_read_bytes"] is None
    assert data["block_write_bytes"] is None


# -------------------------------------------------------------
# M02.4 — Docker Images & Volumes Intelligence Tests
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_images_unauthenticated_fails(client: AsyncClient):
    """Ensure images listing requires authentication."""
    response = await client.get("/api/v1/docker/images")
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_list_images_success(client: AsyncClient, auth_headers: dict):
    """Ensure listing images returns mapped images with container correlation."""
    mock_client = MagicMock()
    mock_client.api.images.return_value = [
        {
            "Id": "sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "RepoTags": ["postgres:16-alpine", "postgres:latest"],
            "Size": 379000000,
            "VirtualSize": 379000000,
            "Created": 1700000000,
            "Labels": {"maintainer": "PostgreSQL"},
        },
        {
            "Id": "sha256:fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321",
            "RepoTags": ["<none>:<none>"],
            "Size": 150000000,
            "VirtualSize": 150000000,
            "Created": 1700001000,
            "Labels": {},
        },
    ]
    mock_client.api.containers.return_value = [
        {
            "Id": "c111111111111111111111111111111111111111111111111111111111111111",
            "Names": ["/dockscope-db"],
            "Image": "postgres:16-alpine",
            "ImageID": "sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "State": "running",
            "Status": "Up 2 hours",
        }
    ]

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/images", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # Verify first image
    pg_img = data["items"][0]
    assert pg_img["short_id"] == "1234567890ab"
    assert "postgres:16-alpine" in pg_img["repo_tags"]
    assert "postgres" in pg_img["repositories"]
    assert "16-alpine" in pg_img["tags"]
    assert pg_img["size_bytes"] == 379000000
    assert pg_img["containers_count"] == 1
    assert pg_img["is_dangling"] is False

    # Verify dangling image
    dangling_img = data["items"][1]
    assert dangling_img["is_dangling"] is True
    assert dangling_img["repo_tags"] == []
    assert dangling_img["containers_count"] == 0


@pytest.mark.asyncio
async def test_list_images_search_and_dangling_filters(client: AsyncClient, auth_headers: dict):
    """Ensure search and dangling filters work accurately."""
    mock_client = MagicMock()
    mock_client.api.images.return_value = [
        {
            "Id": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "RepoTags": ["dockscope-backend:latest"],
            "Size": 200000000,
            "Created": 1700000000,
        },
        {
            "Id": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
            "RepoTags": ["<none>:<none>"],
            "Size": 50000000,
            "Created": 1700000500,
        },
    ]
    mock_client.api.containers.return_value = []

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        
        # Test dangling=true
        res_dangling = await client.get("/api/v1/docker/images?dangling=true", headers=auth_headers)
        assert res_dangling.status_code == 200
        data_dangling = res_dangling.json()
        assert data_dangling["total"] == 1
        assert data_dangling["items"][0]["is_dangling"] is True

        # Test dangling=false
        res_named = await client.get("/api/v1/docker/images?dangling=false", headers=auth_headers)
        assert res_named.status_code == 200
        assert res_named.json()["total"] == 1
        assert res_named.json()["items"][0]["is_dangling"] is False

        # Test search query
        res_search = await client.get("/api/v1/docker/images?search=dockscope", headers=auth_headers)
        assert res_search.status_code == 200
        assert res_search.json()["total"] == 1
        assert res_search.json()["items"][0]["repo_tags"] == ["dockscope-backend:latest"]


@pytest.mark.asyncio
async def test_get_image_detail_success_and_sanitization(client: AsyncClient, auth_headers: dict):
    """Ensure inspecting an image returns safe metadata and excludes environment variables."""
    mock_client = MagicMock()
    mock_client.api.inspect_image.return_value = {
        "Id": "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "RepoTags": ["my-org/my-service:v1.0.0"],
        "Size": 450000000,
        "Created": "2026-11-23T10:00:00Z",
        "Architecture": "amd64",
        "Os": "linux",
        "Author": "DockScope Team",
        "Comment": "Production build",
        "DockerVersion": "24.0.7",
        "RootFS": {
            "Type": "layers",
            "Layers": [
                "sha256:layer11111111111111111111111111111111111111111111111111111111111",
                "sha256:layer22222222222222222222222222222222222222222222222222222222222",
            ],
        },
        "Config": {
            "Env": [
                "DATABASE_PASSWORD=supersecret",
                "SECRET_KEY=confidential_jwt_key",
                "PATH=/usr/local/bin:/usr/bin",
            ],
            "Labels": {
                "version": "1.0.0",
                "api_secret": "my-secret-token",
            },
        },
    }
    mock_client.api.containers.return_value = [
        {
            "Id": "c222222222222222222222222222222222222222222222222222222222222222",
            "Names": ["/my-service-app"],
            "Image": "my-org/my-service:v1.0.0",
            "ImageID": "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "State": "running",
            "Status": "Up 5 hours",
        }
    ]

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get(
            "/api/v1/docker/images/sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["short_id"] == "abcdef123456"
    assert data["architecture"] == "amd64"
    assert data["os"] == "linux"
    assert len(data["root_fs_layers"]) == 2
    assert len(data["containers"]) == 1
    assert data["containers"][0]["name"] == "my-service-app"

    # CRITICAL: Verify environment variables are NEVER in the schema/response
    assert "env" not in data
    assert "Env" not in data
    assert "Config" not in data
    # Verify sensitive labels are sanitized (completely omitted)
    assert "api_secret" not in data["labels"]
    assert data["labels"]["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_get_image_not_found(client: AsyncClient, auth_headers: dict):
    """Ensure non-existent image returns 404."""
    mock_client = MagicMock()
    mock_client.api.inspect_image.side_effect = NotFound("No such image: non-existent")

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/images/non-existent-img", headers=auth_headers)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_volumes_unauthenticated_fails(client: AsyncClient):
    """Ensure volumes listing requires authentication."""
    response = await client.get("/api/v1/docker/volumes")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_volumes_success(client: AsyncClient, auth_headers: dict):
    """Ensure listing volumes returns mapped volumes with container usage correlation."""
    mock_client = MagicMock()
    mock_client.api.volumes.return_value = {
        "Volumes": [
            {
                "Name": "pgdata_volume",
                "Driver": "local",
                "Scope": "local",
                "CreatedAt": "2026-11-20T08:00:00Z",
                "Labels": {"project": "dockscope"},
            },
            {
                "Name": "unused_cache",
                "Driver": "local",
                "Scope": "local",
                "CreatedAt": "2026-11-21T09:00:00Z",
                "Labels": {},
            },
        ]
    }
    mock_client.api.containers.return_value = [
        {
            "Id": "c33333333333333333333333333333333333333333333333333333333333333",
            "Names": ["/dockscope-db"],
            "State": "running",
            "Mounts": [
                {
                    "Type": "volume",
                    "Name": "pgdata_volume",
                    "Destination": "/var/lib/postgresql/data",
                    "Mode": "rw",
                    "RW": True,
                }
            ],
        }
    ]

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/volumes", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # Volume in use
    vol1 = next(v for v in data["items"] if v["name"] == "pgdata_volume")
    assert vol1["driver"] == "local"
    assert vol1["containers_count"] == 1
    assert vol1["is_in_use"] is True

    # Unused volume
    vol2 = next(v for v in data["items"] if v["name"] == "unused_cache")
    assert vol2["containers_count"] == 0
    assert vol2["is_in_use"] is False


@pytest.mark.asyncio
async def test_list_volumes_search_and_driver_filters(client: AsyncClient, auth_headers: dict):
    """Ensure search and driver query params filter volume results accurately."""
    mock_client = MagicMock()
    mock_client.api.volumes.return_value = {
        "Volumes": [
            {"Name": "vol-local-1", "Driver": "local", "Scope": "local"},
            {"Name": "vol-nfs-1", "Driver": "nfs", "Scope": "global"},
        ]
    }
    mock_client.api.containers.return_value = []

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")

        # Driver filter
        res_driver = await client.get("/api/v1/docker/volumes?driver=nfs", headers=auth_headers)
        assert res_driver.status_code == 200
        assert res_driver.json()["total"] == 1
        assert res_driver.json()["items"][0]["name"] == "vol-nfs-1"

        # Search filter
        res_search = await client.get("/api/v1/docker/volumes?search=local", headers=auth_headers)
        assert res_search.status_code == 200
        assert res_search.json()["total"] == 1
        assert res_search.json()["items"][0]["name"] == "vol-local-1"


@pytest.mark.asyncio
async def test_get_volume_detail_success_and_sanitization(client: AsyncClient, auth_headers: dict):
    """Ensure inspecting a volume returns details, container mount references, and sanitizes sensitive options."""
    mock_client = MagicMock()
    mock_client.api.inspect_volume.return_value = {
        "Name": "secure_data_vol",
        "Driver": "local",
        "Scope": "local",
        "CreatedAt": "2026-11-22T05:00:00Z",
        "Mountpoint": "/var/lib/docker/volumes/secure_data_vol/_data",
        "Options": {
            "device": "/dev/sdb1",
            "o": "size=10G",
            "auth_password": "supersecretpassword",
        },
        "Labels": {
            "env": "production",
            "secret_token": "token123",
        },
    }
    mock_client.api.containers.return_value = [
        {
            "Id": "c44444444444444444444444444444444444444444444444444444444444444",
            "Names": ["/data-processor"],
            "State": "running",
            "Mounts": [
                {
                    "Type": "volume",
                    "Name": "secure_data_vol",
                    "Destination": "/data",
                    "Mode": "ro",
                    "RW": False,
                }
            ],
        }
    ]

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/volumes/secure_data_vol", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "secure_data_vol"
    assert data["driver"] == "local"
    assert data["mountpoint"] == "/var/lib/docker/volumes/secure_data_vol/_data"
    assert data["containers_count"] == 1
    assert data["is_in_use"] is True

    # Check container mount details
    assert len(data["containers"]) == 1
    c_ref = data["containers"][0]
    assert c_ref["name"] == "data-processor"
    assert c_ref["destination"] == "/data"
    assert c_ref["mode"] == "ro"
    assert c_ref["read_only"] is True

    # Check sensitive sanitization
    assert "auth_password" not in data["options"]
    assert data["options"]["device"] == "/dev/sdb1"
    assert "secret_token" not in data["labels"]
    assert data["labels"]["env"] == "production"


@pytest.mark.asyncio
async def test_get_volume_not_found(client: AsyncClient, auth_headers: dict):
    """Ensure non-existent volume returns 404."""
    mock_client = MagicMock()
    mock_client.api.inspect_volume.side_effect = NotFound("No such volume: non-existent")

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/volumes/non-existent-vol", headers=auth_headers)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_images_and_volumes_daemon_unavailable(client: AsyncClient, auth_headers: dict):
    """Ensure 503 is returned when Docker daemon is unreachable during image/volume operations."""
    mock_client = MagicMock()
    mock_client.api.images.side_effect = DockerException("Socket unavailable")
    mock_client.api.volumes.side_effect = DockerException("Socket unavailable")

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")

        res_images = await client.get("/api/v1/docker/images", headers=auth_headers)
        assert res_images.status_code == 503
        assert "unreachable" in res_images.json()["detail"].lower()

        res_volumes = await client.get("/api/v1/docker/volumes", headers=auth_headers)
        assert res_volumes.status_code == 503
        assert "unreachable" in res_volumes.json()["detail"].lower()


# -------------------------------------------------------------
# M02.5 — Container Logs Intelligence Tests
# -------------------------------------------------------------

import struct


def _create_docker_frame(stream_type: int, payload: bytes) -> bytes:
    """Helper to generate standard Docker 8-byte multiplexed log frames."""
    header = struct.pack(">BxxxI", stream_type, len(payload))
    return header + payload


@pytest.mark.asyncio
async def test_get_container_logs_unauthenticated_fails(client: AsyncClient):
    """Ensure container logs endpoint requires authentication."""
    response = await client.get("/api/v1/docker/containers/c1/logs")
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_container_logs_running_multiplexed_success(client: AsyncClient, auth_headers: dict):
    """Ensure multiplexed stdout/stderr framing is parsed with timestamps and stream tagging."""
    stdout_data = b"2026-11-23T12:00:00.000000000Z Server listening on port 8080\n"
    stderr_data = b"2026-11-23T12:00:01.000000000Z [WARN] Failed connecting to replica\n"
    framed_payload = _create_docker_frame(1, stdout_data) + _create_docker_frame(2, stderr_data)

    mock_client = MagicMock()
    mock_client.api.inspect_container.return_value = {
        "Id": "c1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "Name": "/dockscope-api",
        "State": {"Running": True, "Status": "running"},
    }
    mock_client.api.logs.return_value = framed_payload

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get(
            "/api/v1/docker/containers/c1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef/logs",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["container_name"] == "dockscope-api"
    assert data["total_lines"] == 2
    assert len(data["lines"]) == 2

    # Check stdout line
    line1 = data["lines"][0]
    assert line1["stream"] == "stdout"
    assert line1["timestamp"] == "2026-11-23T12:00:00.000000000Z"
    assert line1["message"] == "Server listening on port 8080"

    # Check stderr line
    line2 = data["lines"][1]
    assert line2["stream"] == "stderr"
    assert line2["timestamp"] == "2026-11-23T12:00:01.000000000Z"
    assert line2["message"] == "[WARN] Failed connecting to replica"


@pytest.mark.asyncio
async def test_get_container_logs_stopped_container(client: AsyncClient, auth_headers: dict):
    """Ensure logs from stopped containers are retrieved safely without hanging."""
    mock_client = MagicMock()
    mock_client.api.inspect_container.return_value = {
        "Id": "stopped_c1",
        "Name": "/exited-job",
        "State": {"Running": False, "Status": "exited"},
    }
    mock_client.api.logs.return_value = _create_docker_frame(
        1, b"2026-11-23T11:59:59.000000000Z Batch processing completed with status 0\n"
    )

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers/stopped_c1/logs", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["container_name"] == "exited-job"
    assert data["total_lines"] == 1
    assert data["lines"][0]["message"] == "Batch processing completed with status 0"


@pytest.mark.asyncio
async def test_get_container_logs_not_found(client: AsyncClient, auth_headers: dict):
    """Ensure non-existent container ID returns 404."""
    mock_client = MagicMock()
    mock_client.api.inspect_container.side_effect = NotFound("No such container: unknown_c")

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers/unknown_c/logs", headers=auth_headers)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_container_logs_daemon_unavailable(client: AsyncClient, auth_headers: dict):
    """Ensure 503 is returned when Docker daemon is unreachable."""
    mock_client = MagicMock()
    mock_client.api.inspect_container.side_effect = DockerException("Pipe broken")

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers/c1/logs", headers=auth_headers)

    assert response.status_code == 503
    assert "unreachable" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_container_logs_sensitive_value_redaction(client: AsyncClient, auth_headers: dict):
    """Ensure sensitive tokens, passwords, bearer credentials, and connection strings are masked."""
    sensitive_lines = (
        b"2026-11-23T12:00:00Z Auth header: Bearer my-super-secret-jwt-token-1234567890\n"
        b"2026-11-23T12:00:01Z Database configuration password=MySecretPassword! host=db\n"
        b"2026-11-23T12:00:02Z Connecting to postgres://admin:TopSecretPass123@127.0.0.1:5432/dockscope\n"
        b"2026-11-23T12:00:03Z Loaded api_key: \"secret_api_key_xyz987\" for service\n"
    )
    framed = _create_docker_frame(1, sensitive_lines)

    mock_client = MagicMock()
    mock_client.api.inspect_container.return_value = {
        "Id": "c_sec",
        "Name": "/sec-app",
        "State": {"Running": True},
    }
    mock_client.api.logs.return_value = framed

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers/c_sec/logs", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["redaction_applied"] is True
    messages = [l["message"] for l in data["lines"]]

    # Verify Bearer token is redacted
    assert "Bearer [REDACTED]" in messages[0]
    assert "my-super-secret-jwt-token" not in messages[0]

    # Verify password= is redacted
    assert "password=[REDACTED]" in messages[1]
    assert "MySecretPassword!" not in messages[1]

    # Verify connection string credentials redacted
    assert "postgres://admin:[REDACTED]@127.0.0.1:5432/dockscope" in messages[2]
    assert "TopSecretPass123" not in messages[2]

    # Verify api_key is redacted
    assert "api_key: \"[REDACTED]\"" in messages[3]
    assert "secret_api_key_xyz987" not in messages[3]


@pytest.mark.asyncio
async def test_get_container_logs_malformed_utf8_and_binary(client: AsyncClient, auth_headers: dict):
    """Ensure malformed UTF-8 bytes and binary non-text chunks are safely decoded without crashing."""
    raw_binary = b"2026-11-23T12:00:00Z Binary payload \x80\x81\xff\xfe\x00\x01 status\n"
    framed = _create_docker_frame(1, raw_binary)

    mock_client = MagicMock()
    mock_client.api.inspect_container.return_value = {
        "Id": "c_bin",
        "Name": "/bin-app",
        "State": {"Running": True},
    }
    mock_client.api.logs.return_value = framed

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers/c_bin/logs", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_lines"] == 1
    assert "Binary payload" in data["lines"][0]["message"]


@pytest.mark.asyncio
async def test_get_container_logs_tail_maximum_validation(client: AsyncClient, auth_headers: dict):
    """Ensure tail parameter enforces strict bounds (1 <= tail <= 1000)."""
    # Over maximum (tail=1500)
    res_over = await client.get("/api/v1/docker/containers/c1/logs?tail=1500", headers=auth_headers)
    assert res_over.status_code == 422

    # Under minimum (tail=0)
    res_under = await client.get("/api/v1/docker/containers/c1/logs?tail=0", headers=auth_headers)
    assert res_under.status_code == 422


@pytest.mark.asyncio
async def test_get_container_logs_empty_output(client: AsyncClient, auth_headers: dict):
    """Ensure container with no logs returns 200 with empty list."""
    mock_client = MagicMock()
    mock_client.api.inspect_container.return_value = {
        "Id": "c_empty",
        "Name": "/empty-app",
        "State": {"Running": True},
    }
    mock_client.api.logs.return_value = b""

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers/c_empty/logs", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_lines"] == 0
    assert data["lines"] == []
    assert data["truncated"] is False


@pytest.mark.asyncio
async def test_get_container_logs_stream_filters(client: AsyncClient, auth_headers: dict):
    """Ensure stdout and stderr query flags pass to logs API correctly."""
    mock_client = MagicMock()
    mock_client.api.inspect_container.return_value = {
        "Id": "c_filter",
        "Name": "/filter-app",
        "State": {"Running": True},
    }
    mock_client.api.logs.return_value = _create_docker_frame(2, b"Error line only\n")

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")

        # stderr only
        res_stderr = await client.get(
            "/api/v1/docker/containers/c_filter/logs?stdout=false&stderr=true",
            headers=auth_headers,
        )
        assert res_stderr.status_code == 200
        assert res_stderr.json()["total_lines"] == 1
        assert res_stderr.json()["lines"][0]["stream"] == "stderr"

        # Both false -> returns empty immediately without querying daemon logs
        res_none = await client.get(
            "/api/v1/docker/containers/c_filter/logs?stdout=false&stderr=false",
            headers=auth_headers,
        )
        assert res_none.status_code == 200
        assert res_none.json()["total_lines"] == 0


@pytest.mark.asyncio
async def test_get_container_logs_bounded_size_and_truncation(client: AsyncClient, auth_headers: dict):
    """Ensure output exceeding requested tail limit is truncated and flagged."""
    many_lines = b"".join(f"Line {i}\n".encode("utf-8") for i in range(1, 20))
    framed = _create_docker_frame(1, many_lines)

    mock_client = MagicMock()
    mock_client.api.inspect_container.return_value = {
        "Id": "c_trunc",
        "Name": "/trunc-app",
        "State": {"Running": True},
    }
    mock_client.api.logs.return_value = framed

    with patch("app.services.docker_service.docker_service._create_client") as mock_create:
        mock_create.return_value = (mock_client, "test-socket")
        response = await client.get("/api/v1/docker/containers/c_trunc/logs?tail=5", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_lines"] == 5
    assert len(data["lines"]) == 5
    assert data["truncated"] is True
    assert data["lines"][-1]["message"] == "Line 19"
