from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DockerConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class DockerEngineDetails(BaseModel):
    version: Optional[str] = Field(None, description="Docker Engine version (e.g. 29.9.3)")
    api_version: Optional[str] = Field(None, description="Docker Engine API version (e.g. 1.56)")
    min_api_version: Optional[str] = Field(None, description="Minimum supported API version")
    os: Optional[str] = Field(None, description="Operating system reported by daemon")
    os_type: Optional[str] = Field(None, description="OS type (linux/windows)")
    architecture: Optional[str] = Field(None, description="CPU architecture (e.g. x86_64, arm64)")
    cpus: Optional[int] = Field(None, description="Total CPU cores available to Docker")
    memory_total_bytes: Optional[int] = Field(None, description="Total memory available to Docker in bytes")
    containers_total: Optional[int] = Field(None, description="Total containers present")
    containers_running: Optional[int] = Field(None, description="Running containers count")
    containers_paused: Optional[int] = Field(None, description="Paused containers count")
    containers_stopped: Optional[int] = Field(None, description="Stopped containers count")
    images_total: Optional[int] = Field(None, description="Total image count")


class DockerStatusResponse(BaseModel):
    status: DockerConnectionStatus = Field(..., description="Connection status: connected, disconnected, unavailable, error")
    details: Optional[DockerEngineDetails] = Field(None, description="Docker Engine details when connected")
    error_message: Optional[str] = Field(None, description="Sanitized, human-readable error message when disconnected")
    endpoint: str = Field(..., description="Docker daemon connection target (e.g. local socket, npipe)")
    checked_at: datetime = Field(..., description="Timestamp of status check")


class PortMapping(BaseModel):
    container_port: int = Field(..., description="Container private port number")
    host_port: Optional[int] = Field(None, description="Published host public port number if mapped")
    protocol: str = Field("tcp", description="Protocol: tcp or udp")
    host_ip: Optional[str] = Field(None, description="Host IP the port is bound to (e.g. 127.0.0.1 or 0.0.0.0)")


class MountMetadata(BaseModel):
    type: str = Field(..., description="Mount type (volume, bind, tmpfs)")
    name: Optional[str] = Field(None, description="Volume name if volume mount")
    source: Optional[str] = Field(None, description="Source path or volume name on host")
    destination: str = Field(..., description="Target mount path inside container")
    mode: Optional[str] = Field(None, description="Mount mode (rw, ro)")
    read_only: bool = Field(False, description="Whether the mount is read-only")


class ContainerSummary(BaseModel):
    id: str = Field(..., description="Full 64-character container ID")
    short_id: str = Field(..., description="Short 12-character container ID prefix")
    name: str = Field(..., description="Container name without leading slash")
    image: str = Field(..., description="Container image name or repository tag")
    status: str = Field(..., description="Human-readable status string (e.g. 'Up 2 hours')")
    state: str = Field(..., description="Container state (running, exited, paused, created, dead)")
    created_at: Optional[str] = Field(None, description="Creation timestamp in ISO format")
    ports: list[PortMapping] = Field(default_factory=list, description="Parsed port mappings")
    labels: dict[str, str] = Field(default_factory=dict, description="Sanitized container labels")


class ContainerListResponse(BaseModel):
    items: list[ContainerSummary] = Field(default_factory=list, description="List of container summaries")
    total: int = Field(..., description="Total containers matching criteria")


class ContainerDetail(BaseModel):
    id: str = Field(..., description="Full 64-character container ID")
    short_id: str = Field(..., description="Short 12-character container ID prefix")
    name: str = Field(..., description="Container name without leading slash")
    image: str = Field(..., description="Container image name or repository tag")
    image_id: Optional[str] = Field(None, description="Docker image ID hash")
    command: Optional[str] = Field(None, description="Container execution command")
    state: str = Field(..., description="Container state (running, exited, paused, etc.)")
    status: str = Field(..., description="Human-readable container status")
    created_at: Optional[str] = Field(None, description="Container creation timestamp")
    started_at: Optional[str] = Field(None, description="Timestamp when container started")
    finished_at: Optional[str] = Field(None, description="Timestamp when container finished/exited")
    ports: list[PortMapping] = Field(default_factory=list, description="Parsed port mappings")
    restart_count: int = Field(0, description="Container restart count")
    health_status: Optional[str] = Field(None, description="Health status (healthy, unhealthy, starting) if configured")
    networks: list[str] = Field(default_factory=list, description="Names of connected Docker networks")
    mounts: list[MountMetadata] = Field(default_factory=list, description="Safe mount and volume metadata")
    labels: dict[str, str] = Field(default_factory=dict, description="Sanitized container labels")


class ContainerStats(BaseModel):
    container_id: str = Field(..., description="Container ID (64-character hash or short prefix)")
    name: str = Field(..., description="Container name without leading slash")
    is_running: bool = Field(..., description="Whether container is currently in running state")
    cpu_percentage: float = Field(0.0, description="Calculated CPU utilization percentage (0.0 to 100.0 * online_cpus)")
    cpu_usage_nanoseconds: int = Field(0, description="Total container CPU time consumed in nanoseconds")
    system_cpu_usage_nanoseconds: Optional[int] = Field(None, description="Total system CPU time consumed in nanoseconds")
    online_cpus: int = Field(1, description="Number of online CPU cores allocated or available")
    memory_usage_bytes: int = Field(0, description="Current memory consumption in bytes (cache-adjusted when available)")
    memory_limit_bytes: int = Field(0, description="Configured memory limit in bytes")
    memory_percentage: float = Field(0.0, description="Calculated memory usage percentage relative to limit (0.0 to 100.0)")
    network_rx_bytes: Optional[int] = Field(None, description="Total network received bytes across container interfaces")
    network_tx_bytes: Optional[int] = Field(None, description="Total network transmitted bytes across container interfaces")
    block_read_bytes: Optional[int] = Field(None, description="Total block I/O bytes read")
    block_write_bytes: Optional[int] = Field(None, description="Total block I/O bytes written")
    collected_at: str = Field(..., description="ISO 8601 collection timestamp")


# --- Docker Images Schemas (M02.4) ---

class ImageContainerReference(BaseModel):
    id: str = Field(..., description="Container ID")
    short_id: str = Field(..., description="Short container ID (12 chars)")
    name: str = Field(..., description="Container name")
    state: str = Field(..., description="Container state (running, exited, etc.)")
    status: str = Field(..., description="Container status description")


class ImageSummary(BaseModel):
    id: str = Field(..., description="Full image ID (e.g. sha256:...)")
    short_id: str = Field(..., description="Short 12-char image ID prefix")
    repo_tags: list[str] = Field(default_factory=list, description="Repository tags (e.g. ['postgres:16-alpine'])")
    repositories: list[str] = Field(default_factory=list, description="Repository names without tag")
    tags: list[str] = Field(default_factory=list, description="Tag identifiers")
    size_bytes: int = Field(0, description="Image virtual/disk size in bytes")
    virtual_size_bytes: Optional[int] = Field(None, description="Virtual size in bytes if available")
    created_at: Optional[str] = Field(None, description="ISO 8601 creation timestamp")
    containers_count: int = Field(0, description="Number of containers referencing this image")
    is_dangling: bool = Field(False, description="Whether the image is dangling (<none>:<none>)")
    labels: dict[str, str] = Field(default_factory=dict, description="Sanitized image labels")


class ImageListResponse(BaseModel):
    items: list[ImageSummary] = Field(default_factory=list, description="List of Docker images")
    total: int = Field(..., description="Total images matching filter")


class ImageDetail(ImageSummary):
    architecture: Optional[str] = Field(None, description="CPU architecture (e.g. amd64, arm64)")
    os: Optional[str] = Field(None, description="Operating system (e.g. linux)")
    author: Optional[str] = Field(None, description="Image author metadata")
    comment: Optional[str] = Field(None, description="Image commit comment")
    docker_version: Optional[str] = Field(None, description="Docker version used to build image")
    root_fs_layers: list[str] = Field(default_factory=list, description="Root filesystem layer diff IDs")
    containers: list[ImageContainerReference] = Field(default_factory=list, description="Containers referencing this image")


# --- Docker Volumes Schemas (M02.4) ---

class VolumeContainerReference(BaseModel):
    id: str = Field(..., description="Container ID")
    short_id: str = Field(..., description="Short container ID (12 chars)")
    name: str = Field(..., description="Container name")
    state: str = Field(..., description="Container state")
    destination: str = Field(..., description="Mount destination path inside container")
    mode: Optional[str] = Field(None, description="Mount mode (rw, ro)")
    read_only: bool = Field(False, description="Whether the volume is mounted read-only")


class VolumeSummary(BaseModel):
    name: str = Field(..., description="Volume name")
    driver: str = Field("local", description="Volume driver (e.g. local)")
    scope: str = Field("local", description="Volume scope (local, global)")
    created_at: Optional[str] = Field(None, description="ISO 8601 creation timestamp if available")
    containers_count: int = Field(0, description="Number of containers using this volume")
    is_in_use: bool = Field(False, description="Whether the volume is referenced by at least one container")
    labels: dict[str, str] = Field(default_factory=dict, description="Sanitized volume labels")


class VolumeListResponse(BaseModel):
    items: list[VolumeSummary] = Field(default_factory=list, description="List of Docker volumes")
    total: int = Field(..., description="Total volumes matching filter")


class VolumeDetail(VolumeSummary):
    mountpoint: Optional[str] = Field(None, description="Safe mountpoint path on host")
    options: dict[str, str] = Field(default_factory=dict, description="Sanitized driver options")
    containers: list[VolumeContainerReference] = Field(default_factory=list, description="Containers mounting this volume")


# --- Container Logs Schemas (M02.5) ---

class LogStreamType(str, Enum):
    STDOUT = "stdout"
    STDERR = "stderr"
    SYSTEM = "system"


class LogEntry(BaseModel):
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp extracted from log stream if enabled")
    stream: LogStreamType = Field(LogStreamType.STDOUT, description="Log stream source (stdout, stderr, system)")
    message: str = Field(..., description="Redacted and safely decoded log line message")


class ContainerLogsParameters(BaseModel):
    tail: int = Field(..., description="Requested tail limit")
    timestamps: bool = Field(..., description="Whether timestamps were requested from daemon")
    stdout: bool = Field(..., description="Whether stdout stream was included")
    stderr: bool = Field(..., description="Whether stderr stream was included")
    since: Optional[str] = Field(None, description="Since filter value if provided")
    until: Optional[str] = Field(None, description="Until filter value if provided")


class ContainerLogsResponse(BaseModel):
    container_id: str = Field(..., description="Container ID")
    container_name: str = Field(..., description="Container name")
    total_lines: int = Field(..., description="Total log entries returned in this response")
    lines: list[LogEntry] = Field(default_factory=list, description="Ordered list of log entries")
    truncated: bool = Field(False, description="Whether output was truncated due to size/tail limits")
    parameters: ContainerLogsParameters = Field(..., description="Parameters applied to this logs query")
    collected_at: str = Field(..., description="ISO 8601 timestamp when logs were retrieved")
    redaction_applied: bool = Field(True, description="Whether sensitive credential redaction was applied")
