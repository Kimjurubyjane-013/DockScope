from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from app.models.user import User
from app.schemas.docker import (
    ContainerDetail,
    ContainerListResponse,
    ContainerLogsResponse,
    ContainerStats,
    DockerStatusResponse,
    ImageDetail,
    ImageListResponse,
    VolumeDetail,
    VolumeListResponse,
)
from app.services.auth_service import get_current_user
from app.services.docker_service import (
    DockerContainerNotFoundException,
    DockerImageNotFoundException,
    DockerUnavailableException,
    DockerVolumeNotFoundException,
    docker_service,
)

router = APIRouter(prefix="/docker", tags=["Docker Integration"])


@router.get(
    "/status",
    response_model=DockerStatusResponse,
    summary="Get Local Docker Engine Connection Status",
)
async def get_docker_status(
    current_user: User = Depends(get_current_user),
) -> DockerStatusResponse:
    """
    Query the status and read-only telemetry of the local Docker Engine.
    Requires an authenticated session.
    Distinguishes: connected, disconnected, unavailable, error.
    """
    return await docker_service.get_docker_status()


@router.get(
    "/containers",
    response_model=ContainerListResponse,
    summary="Discover and List Docker Containers",
)
async def list_docker_containers(
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter containers by state (e.g. running, exited, stopped, paused)",
    ),
    search: Optional[str] = Query(
        None,
        description="Search containers by name, image, or container ID",
    ),
    current_user: User = Depends(get_current_user),
) -> ContainerListResponse:
    """
    Discover and list containers from the connected Docker Engine.
    Supports filtering by container state and substring searching by name/image/ID.
    Requires an authenticated session. Read-only operation.
    """
    try:
        return await docker_service.list_containers(status=status_filter, search=search)
    except DockerUnavailableException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Docker daemon is unreachable. Ensure Docker Engine is running: {exc}",
        )


@router.get(
    "/containers/{container_id}/stats",
    response_model=ContainerStats,
    summary="Get Container Resource Statistics",
)
async def get_container_resource_stats(
    container_id: str = Path(
        ...,
        description="Container ID or name",
    ),
    current_user: User = Depends(get_current_user),
) -> ContainerStats:
    """
    Retrieve one-shot resource utilization statistics for an individual container.
    Returns calculated CPU percentage, cache-adjusted memory metrics, network I/O,
    block I/O, and online CPUs.
    Gracefully handles stopped containers without blocking.
    Requires an authenticated session. Read-only operation.
    """
    try:
        return await docker_service.get_container_stats(container_id)
    except DockerContainerNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except DockerUnavailableException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Docker daemon is unreachable. Ensure Docker Engine is running: {exc}",
        )


@router.get(
    "/containers/{container_id}/logs",
    response_model=ContainerLogsResponse,
    summary="Get Bounded Container Logs",
)
async def get_container_logs(
    container_id: str = Path(
        ...,
        description="Container ID or name",
    ),
    tail: int = Query(
        100,
        ge=1,
        le=1000,
        description="Number of recent log lines to retrieve (max 1000)",
    ),
    timestamps: bool = Query(
        True,
        description="Whether to include timestamps extracted from log stream",
    ),
    stdout: bool = Query(
        True,
        description="Include standard output stream",
    ),
    stderr: bool = Query(
        True,
        description="Include standard error stream",
    ),
    since: Optional[str] = Query(
        None,
        description="Optional filter for logs since timestamp or relative time (e.g. 10m, 2026-11-23T10:00:00Z)",
    ),
    until: Optional[str] = Query(
        None,
        description="Optional filter for logs until timestamp or relative time",
    ),
    current_user: User = Depends(get_current_user),
) -> ContainerLogsResponse:
    """
    Retrieve bounded, sanitized container log entries with multiplexed stream parsing.
    Strictly read-only, non-streaming (stream=False), and protected with secret redaction.
    """
    try:
        return await docker_service.get_container_logs(
            container_id=container_id,
            tail=tail,
            timestamps=timestamps,
            stdout=stdout,
            stderr=stderr,
            since=since,
            until=until,
        )
    except DockerContainerNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except DockerUnavailableException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Docker daemon is unreachable. Ensure Docker Engine is running: {exc}",
        )


@router.get(
    "/containers/{container_id}",
    response_model=ContainerDetail,
    summary="Inspect Docker Container",
)
async def get_docker_container(
    container_id: str = Path(
        ...,
        description="Container ID (full 64-char hash or 12-char prefix) or container name",
    ),
    current_user: User = Depends(get_current_user),
) -> ContainerDetail:
    """
    Inspect detailed telemetry of a specific Docker container.
    Returns network, port bindings, restart count, mounts, and health metadata.
    Strictly omits environment variables, sensitive tokens, or secrets.
    Requires an authenticated session. Read-only operation.
    """
    try:
        return await docker_service.get_container(container_id)
    except DockerContainerNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except DockerUnavailableException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Docker daemon is unreachable. Ensure Docker Engine is running: {exc}",
        )


# --- Docker Images Endpoints (M02.4) ---

@router.get(
    "/images",
    response_model=ImageListResponse,
    summary="List Cached Docker Images",
)
async def list_docker_images(
    search: Optional[str] = Query(
        None,
        description="Search images by repository name, tag, or image ID",
    ),
    dangling: Optional[bool] = Query(
        None,
        description="Filter dangling (<none>:<none>) images",
    ),
    current_user: User = Depends(get_current_user),
) -> ImageListResponse:
    """
    Retrieve list of cached Docker images from local Docker Engine.
    Correlates referencing containers count for each image without N+1 overhead.
    Strictly read-only.
    """
    try:
        return await docker_service.list_images(search=search, dangling=dangling)
    except DockerUnavailableException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Docker daemon is unreachable. Ensure Docker Engine is running: {exc}",
        )


@router.get(
    "/images/{image_id:path}",
    response_model=ImageDetail,
    summary="Inspect Docker Image Details",
)
async def get_docker_image(
    image_id: str = Path(
        ...,
        description="Docker image ID, short ID, or repository tag",
    ),
    current_user: User = Depends(get_current_user),
) -> ImageDetail:
    """
    Inspect detailed metadata for a single Docker image.
    Correlates linked container workloads, displays RootFS layers, and sanitizes labels.
    Strictly omits container environment variables or build secrets.
    """
    try:
        return await docker_service.get_image(image_id)
    except DockerImageNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except DockerUnavailableException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Docker daemon is unreachable. Ensure Docker Engine is running: {exc}",
        )


# --- Docker Volumes Endpoints (M02.4) ---

@router.get(
    "/volumes",
    response_model=VolumeListResponse,
    summary="List Docker Persistent Volumes",
)
async def list_docker_volumes(
    search: Optional[str] = Query(
        None,
        description="Search volumes by name",
    ),
    driver: Optional[str] = Query(
        None,
        description="Filter volumes by storage driver (e.g. local)",
    ),
    current_user: User = Depends(get_current_user),
) -> VolumeListResponse:
    """
    Retrieve list of Docker volumes configured on local host.
    Correlates active container mount counts without inspecting file contents.
    Strictly read-only.
    """
    try:
        return await docker_service.list_volumes(search=search, driver=driver)
    except DockerUnavailableException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Docker daemon is unreachable. Ensure Docker Engine is running: {exc}",
        )


@router.get(
    "/volumes/{volume_name:path}",
    response_model=VolumeDetail,
    summary="Inspect Docker Volume Details",
)
async def get_docker_volume(
    volume_name: str = Path(
        ...,
        description="Docker volume name",
    ),
    current_user: User = Depends(get_current_user),
) -> VolumeDetail:
    """
    Inspect detailed storage metadata for a Docker volume.
    Lists container mount points, mount mode, and sanitized driver options.
    Protects host privacy by never inspecting or reading file contents.
    """
    try:
        return await docker_service.get_volume(volume_name)
    except DockerVolumeNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except DockerUnavailableException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Docker daemon is unreachable. Ensure Docker Engine is running: {exc}",
        )
