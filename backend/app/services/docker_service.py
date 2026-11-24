import asyncio
import os
import re
import struct
import sys
from datetime import datetime, timezone
from typing import Any, Optional, Tuple
import docker
from docker.errors import DockerException, NotFound

from app.core.config import settings
from app.core.logging import logger
from app.schemas.docker import (
    ContainerDetail,
    ContainerListResponse,
    ContainerLogsParameters,
    ContainerLogsResponse,
    ContainerStats,
    ContainerSummary,
    DockerConnectionStatus,
    DockerEngineDetails,
    DockerStatusResponse,
    ImageContainerReference,
    ImageDetail,
    ImageListResponse,
    ImageSummary,
    LogEntry,
    LogStreamType,
    MountMetadata,
    PortMapping,
    VolumeContainerReference,
    VolumeDetail,
    VolumeListResponse,
    VolumeSummary,
)


class DockerUnavailableException(Exception):
    """Raised when the Docker daemon is unreachable, disconnected, or times out."""
    pass


class DockerContainerNotFoundException(Exception):
    """Raised when a specific container ID or name is not found."""
    pass


class DockerImageNotFoundException(Exception):
    """Raised when a specific image ID or tag is not found."""
    pass


class DockerVolumeNotFoundException(Exception):
    """Raised when a specific volume name is not found."""
    pass


SENSITIVE_LABEL_KEYWORDS = ("password", "secret", "token", "key", "auth", "credential", "private")

# Timestamp pattern: 2026-11-23T12:00:00.123456789Z or 2026-11-23T12:00:00Z
TIMESTAMP_REGEX = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))\s+(.*)$",
    re.DOTALL,
)

# Common sensitive patterns to redact:
REDACTION_PATTERNS = [
    # Authorization header / Bearer token
    (re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*"), r"\1[REDACTED]"),
    # Basic auth base64
    (re.compile(r"(?i)\b(basic\s+)[A-Za-z0-9\+/=]{10,}"), r"\1[REDACTED]"),
    # Key-value secrets (e.g. password=..., secret: "...", token='...')
    (
        re.compile(
            r"(?i)\b(password|passwd|pwd|secret|token|api_?key|auth_?token|access_?token|client_?secret|private_?key)(\s*[:=]\s*)(['\"]?)([^'\"\s,;\\]+)\3"
        ),
        r"\1\2\3[REDACTED]\3",
    ),
    # Connection string passwords (e.g. postgres://user:password@host)
    (
        re.compile(r"([a-zA-Z][a-zA-Z0-9+.-]*://[^:]+:)([^@\s]+)(@)"),
        r"\1[REDACTED]\3",
    ),
    # JWT tokens
    (
        re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+\b"),
        "[REDACTED_JWT]",
    ),
    # Private Key blocks
    (
        re.compile(r"-----BEGIN (?:[A-Z0-9_-]+ )?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z0-9_-]+ )?PRIVATE KEY-----"),
        "[REDACTED_PRIVATE_KEY]",
    ),
]


class DockerService:
    """
    Read-only service for monitoring and inspecting the local Docker Engine.
    Strictly isolated from mutating Docker commands (lifecycle/management).
    """

    def __init__(
        self,
        host: Optional[str] = None,
        timeout: Optional[float] = None,
        max_concurrent_stats: int = 10,
    ):
        self.host = host or settings.DOCKER_HOST
        self.timeout = timeout or settings.DOCKER_TIMEOUT_SECONDS
        self._stats_semaphore = asyncio.Semaphore(max_concurrent_stats)
        self._logs_semaphore = asyncio.Semaphore(max_concurrent_stats)

    def _create_client(self) -> Tuple[docker.DockerClient, str]:
        """
        Instantiate Docker client with safe platform fallbacks.
        Returns a tuple of (DockerClient, endpoint_label).
        """
        timeout_int = int(self.timeout)

        # 1. Explicit host configured
        if self.host:
            client = docker.DockerClient(base_url=self.host, timeout=timeout_int)
            return client, self.host

        # 2. Try standard environment detection
        try:
            client = docker.from_env(timeout=timeout_int)
            endpoint = os.environ.get("DOCKER_HOST") or (
                "npipe:////./pipe/docker_engine" if sys.platform == "win32" else "unix:///var/run/docker.sock"
            )
            return client, endpoint
        except DockerException:
            pass

        # 3. Windows Docker Desktop specific fallback
        if sys.platform == "win32":
            desktop_pipe = "npipe:////./pipe/dockerDesktopLinuxEngine"
            client = docker.DockerClient(base_url=desktop_pipe, timeout=timeout_int)
            return client, desktop_pipe

        # 4. Default Unix socket
        unix_socket = "unix:///var/run/docker.sock"
        client = docker.DockerClient(base_url=unix_socket, timeout=timeout_int)
        return client, unix_socket

    def _sync_fetch_status(self) -> DockerStatusResponse:
        """
        Synchronously probe the Docker daemon, retrieve version and basic info.
        Redacts any sensitive configuration.
        """
        now = datetime.now(timezone.utc)
        endpoint_label = "unknown"

        try:
            client, endpoint_label = self._create_client()
        except Exception as exc:
            logger.warning(f"Docker client creation failed: {exc}")
            return DockerStatusResponse(
                status=DockerConnectionStatus.UNAVAILABLE,
                endpoint=self.host or "default socket",
                error_message="Docker client could not be initialized. Ensure Docker is installed.",
                checked_at=now,
            )

        try:
            # 1. Ping test
            if not client.ping():
                return DockerStatusResponse(
                    status=DockerConnectionStatus.DISCONNECTED,
                    endpoint=endpoint_label,
                    error_message="Docker daemon responded negatively to ping check.",
                    checked_at=now,
                )

            # 2. Version inspection
            version_data = client.version() or {}

            # 3. Basic daemon info (read-only telemetry)
            info_data = client.info() or {}

            # Authoritative count reconciliation:
            # Query actual container inventory to resolve daemon counter desynchronization
            # (e.g. unstarted created containers or failed start attempts inflating ContainersRunning)
            c_total = info_data.get("Containers")
            c_running = info_data.get("ContainersRunning")
            c_paused = info_data.get("ContainersPaused")
            c_stopped = info_data.get("ContainersStopped")

            try:
                raw_containers = client.api.containers(all=True)
                if isinstance(raw_containers, list):
                    c_total = len(raw_containers)
                    c_running = sum(1 for c in raw_containers if isinstance(c, dict) and str(c.get("State", "")).lower() == "running")
                    c_paused = sum(1 for c in raw_containers if isinstance(c, dict) and str(c.get("State", "")).lower() == "paused")
                    c_stopped = sum(1 for c in raw_containers if isinstance(c, dict) and str(c.get("State", "")).lower() in ("exited", "dead", "created"))
            except Exception as e:
                logger.debug(f"Could not query containers list for count reconciliation: {e}")

            details = DockerEngineDetails(
                version=version_data.get("Version"),
                api_version=version_data.get("ApiVersion"),
                min_api_version=version_data.get("MinAPIVersion"),
                os=info_data.get("OperatingSystem"),
                os_type=info_data.get("OSType"),
                architecture=info_data.get("Architecture"),
                cpus=info_data.get("NCPU"),
                memory_total_bytes=info_data.get("MemTotal"),
                containers_total=c_total,
                containers_running=c_running,
                containers_paused=c_paused,
                containers_stopped=c_stopped,
                images_total=info_data.get("Images"),
            )

            return DockerStatusResponse(
                status=DockerConnectionStatus.CONNECTED,
                details=details,
                endpoint=endpoint_label,
                checked_at=now,
            )

        except DockerException as exc:
            err_str = str(exc).lower()
            logger.warning(f"Docker daemon connection error ({endpoint_label}): {exc}")

            if "permission denied" in err_str or "access is denied" in err_str:
                status = DockerConnectionStatus.UNAVAILABLE
                msg = "Access to Docker socket/pipe was denied. Check permissions."
            elif "not found" in err_str or "cannot find the file" in err_str or "no such file" in err_str:
                status = DockerConnectionStatus.UNAVAILABLE
                msg = "Docker daemon socket or pipe was not found. Is Docker Engine running?"
            elif "connection refused" in err_str or "refused" in err_str:
                status = DockerConnectionStatus.DISCONNECTED
                msg = "Docker daemon connection was refused. Ensure Docker service is active."
            else:
                status = DockerConnectionStatus.ERROR
                msg = f"Docker daemon communication failed: {str(exc)[:120]}"

            return DockerStatusResponse(
                status=status,
                endpoint=endpoint_label,
                error_message=msg,
                checked_at=now,
            )
        except Exception as exc:
            logger.error(f"Unexpected error while querying Docker daemon: {exc}")
            return DockerStatusResponse(
                status=DockerConnectionStatus.ERROR,
                endpoint=endpoint_label,
                error_message="Unexpected internal error while communicating with Docker Engine.",
                checked_at=now,
            )
        finally:
            try:
                client.close()
            except Exception:
                pass

    @staticmethod
    def _clean_timestamp(ts: Any) -> Optional[str]:
        if not ts:
            return None
        if isinstance(ts, (int, float)):
            try:
                return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            except Exception:
                return None
        if isinstance(ts, str):
            if ts.startswith("0001-01-01"):
                return None
            return ts
        return None

    @staticmethod
    def _parse_port_mappings(raw_ports: Any) -> list[PortMapping]:
        mappings: list[PortMapping] = []
        if not raw_ports:
            return mappings

        if isinstance(raw_ports, list):
            for item in raw_ports:
                if not isinstance(item, dict):
                    continue
                container_port = item.get("PrivatePort")
                if not container_port:
                    continue
                host_port = item.get("PublicPort")
                protocol = str(item.get("Type", "tcp")).lower()
                host_ip = item.get("IP") or None
                mappings.append(PortMapping(
                    container_port=container_port,
                    host_port=host_port,
                    protocol=protocol,
                    host_ip=host_ip,
                ))
        elif isinstance(raw_ports, dict):
            for port_proto, bindings in raw_ports.items():
                parts = str(port_proto).split("/")
                try:
                    container_port = int(parts[0])
                except (ValueError, IndexError):
                    continue
                protocol = parts[1].lower() if len(parts) > 1 else "tcp"
                if bindings and isinstance(bindings, list):
                    for binding in bindings:
                        if not isinstance(binding, dict):
                            continue
                        host_ip = binding.get("HostIp") or None
                        host_port = None
                        if binding.get("HostPort"):
                            try:
                                host_port = int(binding["HostPort"])
                            except (ValueError, TypeError):
                                pass
                        mappings.append(PortMapping(
                            container_port=container_port,
                            host_port=host_port,
                            protocol=protocol,
                            host_ip=host_ip,
                        ))
                else:
                    mappings.append(PortMapping(
                        container_port=container_port,
                        host_port=None,
                        protocol=protocol,
                        host_ip=None,
                    ))

        mappings.sort(key=lambda p: (p.container_port, p.host_port or 0))
        return mappings

    @staticmethod
    def _parse_mounts(raw_mounts: Any) -> list[MountMetadata]:
        mounts: list[MountMetadata] = []
        if not raw_mounts or not isinstance(raw_mounts, list):
            return mounts

        for m in raw_mounts:
            if not isinstance(m, dict):
                continue
            dest = m.get("Destination", "")
            if not dest:
                continue
            mounts.append(MountMetadata(
                type=m.get("Type", "unknown"),
                name=m.get("Name"),
                source=m.get("Source"),
                destination=dest,
                mode=m.get("Mode"),
                read_only=not m.get("RW", True),
            ))
        return mounts

    @staticmethod
    def _sanitize_labels(raw_labels: Any) -> dict[str, str]:
        if not raw_labels or not isinstance(raw_labels, dict):
            return {}
        sanitized: dict[str, str] = {}
        for k, v in raw_labels.items():
            if not isinstance(k, str):
                continue
            lower_k = k.lower()
            if any(keyword in lower_k for keyword in SENSITIVE_LABEL_KEYWORDS):
                continue
            sanitized[k] = str(v)
        return sanitized

    def _sync_list_containers(
        self,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> ContainerListResponse:
        """
        Synchronously list Docker containers using the low-level APIClient.
        Supports status filtering and container name/image search.
        """
        try:
            client, _ = self._create_client()
        except Exception as exc:
            logger.warning(f"Failed to create Docker client: {exc}")
            raise DockerUnavailableException(f"Cannot initialize Docker client: {exc}") from exc

        try:
            raw_list = client.api.containers(all=True)
        except DockerException as exc:
            logger.warning(f"Docker API containers query failed: {exc}")
            raise DockerUnavailableException(f"Docker daemon query failed: {exc}") from exc
        finally:
            try:
                client.close()
            except Exception:
                pass

        items: list[ContainerSummary] = []
        for entry in raw_list:
            cid = entry.get("Id", "")
            short_id = cid[:12] if len(cid) >= 12 else cid
            names = entry.get("Names") or []
            name = names[0].lstrip("/") if names else short_id
            image = entry.get("Image", "")
            state = entry.get("State", "unknown")
            status_str = entry.get("Status", state)

            created_val = entry.get("Created")
            created_at = None
            if isinstance(created_val, (int, float)):
                created_at = datetime.fromtimestamp(created_val, tz=timezone.utc).isoformat()
            elif isinstance(created_val, str):
                created_at = created_val

            ports = self._parse_port_mappings(entry.get("Ports"))
            labels = self._sanitize_labels(entry.get("Labels"))

            # Status filter
            if status_filter:
                sf = status_filter.strip().lower()
                if sf == "stopped":
                    if state.lower() in ("running", "restarting", "paused"):
                        continue
                elif sf != state.lower():
                    continue

            # Search filter (name, image, short_id, full id)
            if search:
                q = search.strip().lower()
                if not (q in name.lower() or q in image.lower() or q in short_id.lower() or q in cid.lower()):
                    continue

            items.append(ContainerSummary(
                id=cid,
                short_id=short_id,
                name=name,
                image=image,
                status=status_str,
                state=state,
                created_at=created_at,
                ports=ports,
                labels=labels,
            ))

        return ContainerListResponse(items=items, total=len(items))

    def _sync_get_container(self, container_id: str) -> ContainerDetail:
        """
        Synchronously inspect a specific Docker container.
        Strictly omits environment variables, sensitive tokens, or secrets.
        """
        try:
            client, _ = self._create_client()
        except Exception as exc:
            logger.warning(f"Failed to create Docker client: {exc}")
            raise DockerUnavailableException(f"Cannot initialize Docker client: {exc}") from exc

        try:
            insp = client.api.inspect_container(container_id)
        except NotFound as exc:
            raise DockerContainerNotFoundException(f"Container '{container_id}' was not found.") from exc
        except DockerException as exc:
            logger.warning(f"Docker API inspect_container failed for '{container_id}': {exc}")
            raise DockerUnavailableException(f"Docker daemon query failed: {exc}") from exc
        finally:
            try:
                client.close()
            except Exception:
                pass

        cid = insp.get("Id", container_id)
        short_id = cid[:12] if len(cid) >= 12 else cid
        name = insp.get("Name", "").lstrip("/") or short_id
        config = insp.get("Config") or {}
        state_obj = insp.get("State") or {}

        image = config.get("Image") or insp.get("Image", "unknown")
        image_id = insp.get("Image")

        cmd_raw = config.get("Cmd")
        if isinstance(cmd_raw, list):
            command = " ".join(cmd_raw)
        elif isinstance(cmd_raw, str):
            command = cmd_raw
        else:
            command = None

        state = state_obj.get("Status", "unknown")
        health_status = state_obj.get("Health", {}).get("Status") if isinstance(state_obj.get("Health"), dict) else None
        status_str = f"Up ({health_status})" if (state == "running" and health_status) else state

        created_at = self._clean_timestamp(insp.get("Created"))
        started_at = self._clean_timestamp(state_obj.get("StartedAt"))
        finished_at = self._clean_timestamp(state_obj.get("FinishedAt"))

        net_settings = insp.get("NetworkSettings") or {}
        ports = self._parse_port_mappings(net_settings.get("Ports"))

        networks_raw = net_settings.get("Networks") or {}
        networks = list(networks_raw.keys()) if isinstance(networks_raw, dict) else []

        mounts = self._parse_mounts(insp.get("Mounts"))
        labels = self._sanitize_labels(config.get("Labels"))
        restart_count = int(insp.get("RestartCount", 0))

        # IMPORTANT: Environment variables (config.get('Env')) are strictly NOT included.

        return ContainerDetail(
            id=cid,
            short_id=short_id,
            name=name,
            image=image,
            image_id=image_id,
            command=command,
            state=state,
            status=status_str,
            created_at=created_at,
            started_at=started_at,
            finished_at=finished_at,
            ports=ports,
            restart_count=restart_count,
            health_status=health_status,
            networks=networks,
            mounts=mounts,
            labels=labels,
        )

    def _sync_get_container_stats(self, container_id: str) -> ContainerStats:
        """
        Synchronously collect one-shot resource statistics for a single container.
        
        CPU Percentage Calculation:
            cpu_delta = cpu_stats.cpu_usage.total_usage - precpu_stats.cpu_usage.total_usage
            system_delta = cpu_stats.system_cpu_usage - precpu_stats.system_cpu_usage
            online_cpus = cpu_stats.online_cpus or len(percpu_usage) or 1
            cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0 (if system_delta > 0 and cpu_delta > 0)
            
        Memory Usage Definition:
            Raw memory usage (usage) minus inactive file memory / cache when available:
            In cgroups v1: cache or total_inactive_file
            In cgroups v2: inactive_file
            If usage > cache, used_memory = usage - cache; else used_memory = usage.
            memory_percent = (used_memory / limit) * 100.0 (if limit > 0)
            
        Safety:
            - Stopped containers return non-running status with zero metrics without waiting or hanging.
            - Handles missing/zero deltas gracefully.
            - Strictly non-streaming (stream=False).
            - Omits any secrets or environment variables.
        """
        try:
            client, _ = self._create_client()
        except Exception as exc:
            logger.warning(f"Failed to create Docker client for stats: {exc}")
            raise DockerUnavailableException(f"Cannot initialize Docker client: {exc}") from exc

        try:
            insp = client.api.inspect_container(container_id)
        except NotFound as exc:
            try:
                client.close()
            except Exception:
                pass
            raise DockerContainerNotFoundException(f"Container '{container_id}' was not found.") from exc
        except DockerException as exc:
            try:
                client.close()
            except Exception:
                pass
            logger.warning(f"Docker API inspect_container failed for stats '{container_id}': {exc}")
            raise DockerUnavailableException(f"Docker daemon query failed: {exc}") from exc

        cid = insp.get("Id", container_id)
        short_id = cid[:12] if len(cid) >= 12 else cid
        name = insp.get("Name", "").lstrip("/") or short_id
        is_running = bool(insp.get("State", {}).get("Running", False))
        now_iso = datetime.now(timezone.utc).isoformat()

        # Handle stopped / inactive containers safely without hanging
        if not is_running:
            try:
                client.close()
            except Exception:
                pass
            memory_limit = 0
            host_config = insp.get("HostConfig") or {}
            if isinstance(host_config.get("Memory"), (int, float)):
                memory_limit = int(host_config["Memory"])
            return ContainerStats(
                container_id=cid,
                name=name,
                is_running=False,
                cpu_percentage=0.0,
                cpu_usage_nanoseconds=0,
                system_cpu_usage_nanoseconds=None,
                online_cpus=1,
                memory_usage_bytes=0,
                memory_limit_bytes=memory_limit,
                memory_percentage=0.0,
                network_rx_bytes=None,
                network_tx_bytes=None,
                block_read_bytes=None,
                block_write_bytes=None,
                collected_at=now_iso,
            )

        try:
            raw_stats = client.api.stats(container_id, stream=False)
        except NotFound as exc:
            raise DockerContainerNotFoundException(f"Container '{container_id}' was not found.") from exc
        except DockerException as exc:
            logger.warning(f"Docker API stats failed for '{container_id}': {exc}")
            raise DockerUnavailableException(f"Docker stats collection failed: {exc}") from exc
        finally:
            try:
                client.close()
            except Exception:
                pass

        # 1. CPU metrics
        cpu_stats = raw_stats.get("cpu_stats") or {}
        precpu_stats = raw_stats.get("precpu_stats") or {}

        cpu_usage_raw = cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
        cpu_usage = int(cpu_usage_raw) if isinstance(cpu_usage_raw, (int, float)) else 0

        precpu_usage_raw = precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
        precpu_usage = int(precpu_usage_raw) if isinstance(precpu_usage_raw, (int, float)) else 0
        cpu_delta = cpu_usage - precpu_usage

        system_cpu_usage = cpu_stats.get("system_cpu_usage")
        precpu_system_usage = precpu_stats.get("system_cpu_usage")

        system_delta = 0
        if isinstance(system_cpu_usage, (int, float)) and isinstance(precpu_system_usage, (int, float)):
            system_delta = int(system_cpu_usage) - int(precpu_system_usage)

        online_cpus = cpu_stats.get("online_cpus")
        if not isinstance(online_cpus, int) or online_cpus <= 0:
            percpu = cpu_stats.get("cpu_usage", {}).get("percpu_usage")
            online_cpus = len(percpu) if isinstance(percpu, list) and percpu else 1

        cpu_percent = 0.0
        if system_delta > 0 and cpu_delta > 0:
            cpu_percent = round((cpu_delta / system_delta) * online_cpus * 100.0, 2)

        # 2. Memory metrics (cache-adjusted)
        mem_stats = raw_stats.get("memory_stats") or {}
        raw_usage = mem_stats.get("usage", 0)
        usage = int(raw_usage) if isinstance(raw_usage, (int, float)) else 0

        stats_map = mem_stats.get("stats") or {}
        cache = 0
        if isinstance(stats_map, dict):
            cache_val = (
                stats_map.get("inactive_file")
                or stats_map.get("total_inactive_file")
                or stats_map.get("cache")
                or 0
            )
            if isinstance(cache_val, (int, float)):
                cache = int(cache_val)

        if usage > cache:
            memory_usage_bytes = usage - cache
        else:
            memory_usage_bytes = usage

        raw_limit = mem_stats.get("limit", 0)
        memory_limit_bytes = int(raw_limit) if isinstance(raw_limit, (int, float)) else 0

        memory_percentage = 0.0
        if memory_limit_bytes > 0 and memory_usage_bytes > 0:
            memory_percentage = round((memory_usage_bytes / memory_limit_bytes) * 100.0, 2)

        # 3. Network metrics
        network_rx_bytes = None
        network_tx_bytes = None
        networks = raw_stats.get("networks")
        if isinstance(networks, dict) and networks:
            rx_acc = 0
            tx_acc = 0
            for iface_stats in networks.values():
                if isinstance(iface_stats, dict):
                    rx_val = iface_stats.get("rx_bytes", 0)
                    tx_val = iface_stats.get("tx_bytes", 0)
                    if isinstance(rx_val, (int, float)):
                        rx_acc += int(rx_val)
                    if isinstance(tx_val, (int, float)):
                        tx_acc += int(tx_val)
            network_rx_bytes = rx_acc
            network_tx_bytes = tx_acc

        # 4. Block I/O metrics
        block_read_bytes = None
        block_write_bytes = None
        blkio = raw_stats.get("blkio_stats") or {}
        io_entries = blkio.get("io_service_bytes_recursive") or blkio.get("io_serviced_recursive")
        if isinstance(io_entries, list) and io_entries:
            read_acc = 0
            write_acc = 0
            has_blkio = False
            for entry in io_entries:
                if isinstance(entry, dict):
                    op = str(entry.get("op", "")).lower()
                    val = entry.get("value", 0)
                    if isinstance(val, (int, float)):
                        has_blkio = True
                        if op == "read":
                            read_acc += int(val)
                        elif op == "write":
                            write_acc += int(val)
            if has_blkio:
                block_read_bytes = read_acc
                block_write_bytes = write_acc

        collected_at = str(raw_stats.get("read") or now_iso)

        return ContainerStats(
            container_id=cid,
            name=name,
            is_running=True,
            cpu_percentage=cpu_percent,
            cpu_usage_nanoseconds=cpu_usage,
            system_cpu_usage_nanoseconds=int(system_cpu_usage) if isinstance(system_cpu_usage, (int, float)) else None,
            online_cpus=online_cpus,
            memory_usage_bytes=memory_usage_bytes,
            memory_limit_bytes=memory_limit_bytes,
            memory_percentage=memory_percentage,
            network_rx_bytes=network_rx_bytes,
            network_tx_bytes=network_tx_bytes,
            block_read_bytes=block_read_bytes,
            block_write_bytes=block_write_bytes,
            collected_at=collected_at,
        )

    async def list_containers(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> ContainerListResponse:
        """
        Asynchronously retrieve container list with optional status and search filters.
        """
        try:
            async with asyncio.timeout(self.timeout):
                return await asyncio.to_thread(self._sync_list_containers, status, search)
        except asyncio.TimeoutError as exc:
            raise DockerUnavailableException(
                f"Docker container listing timed out after {self.timeout} seconds."
            ) from exc

    async def get_container(self, container_id: str) -> ContainerDetail:
        """
        Asynchronously inspect a container by ID or name.
        """
        try:
            async with asyncio.timeout(self.timeout):
                return await asyncio.to_thread(self._sync_get_container, container_id)
        except asyncio.TimeoutError as exc:
            raise DockerUnavailableException(
                f"Docker container inspection timed out after {self.timeout} seconds."
            ) from exc

    async def get_container_stats(self, container_id: str) -> ContainerStats:
        """
        Asynchronously retrieve one-shot resource statistics for a container.
        Enforces concurrency limit via semaphore and strict request timeout.
        """
        try:
            async with self._stats_semaphore:
                async with asyncio.timeout(self.timeout):
                    return await asyncio.to_thread(self._sync_get_container_stats, container_id)
        except asyncio.TimeoutError as exc:
            raise DockerUnavailableException(
                f"Docker container stats timed out after {self.timeout} seconds."
            ) from exc

    def _sync_list_images(
        self,
        search: Optional[str] = None,
        dangling: Optional[bool] = None,
    ) -> ImageListResponse:
        """
        Synchronously list Docker images from the local image cache.
        Correlates each image with container references without N+1 calls.
        """
        try:
            client, _ = self._create_client()
        except Exception as exc:
            logger.warning(f"Failed to create Docker client for images: {exc}")
            raise DockerUnavailableException(f"Cannot initialize Docker client: {exc}") from exc

        try:
            raw_images = client.api.images()
            raw_containers = client.api.containers(all=True)
        except DockerException as exc:
            logger.warning(f"Docker API images query failed: {exc}")
            raise DockerUnavailableException(f"Docker daemon query failed: {exc}") from exc
        finally:
            try:
                client.close()
            except Exception:
                pass

        # Build container references map for images
        from collections import defaultdict
        image_id_to_containers = defaultdict(list)
        tag_to_containers = defaultdict(list)

        for c in raw_containers:
            cid = c.get("Id", "")
            short_id = cid[:12] if len(cid) >= 12 else cid
            names = c.get("Names") or []
            cname = names[0].lstrip("/") if names else short_id
            cstate = c.get("State", "unknown")
            cstatus = c.get("Status", cstate)
            ref = ImageContainerReference(
                id=cid,
                short_id=short_id,
                name=cname,
                state=cstate,
                status=cstatus,
            )
            c_img_id = c.get("ImageID", "")
            if c_img_id:
                image_id_to_containers[c_img_id].append(ref)
            c_img_tag = c.get("Image", "")
            if c_img_tag:
                tag_to_containers[c_img_tag].append(ref)

        items: list[ImageSummary] = []
        for img in raw_images:
            raw_id = img.get("Id", "")
            short_id = raw_id.replace("sha256:", "")[:12]
            raw_repo_tags = img.get("RepoTags") or []

            # Dangling detection: repo_tags empty or contains only <none>:<none>
            clean_tags = [t for t in raw_repo_tags if t != "<none>:<none>"]
            is_dangling = not clean_tags

            # Filter dangling if requested
            if dangling is not None:
                if dangling and not is_dangling:
                    continue
                if not dangling and is_dangling:
                    continue

            # Extract repositories and tags
            repositories = list(dict.fromkeys([t.rsplit(":", 1)[0] for t in clean_tags if ":" in t]))
            tags = list(dict.fromkeys([t.rsplit(":", 1)[1] for t in clean_tags if ":" in t]))

            # Correlate containers
            matched_containers: dict[str, ImageContainerReference] = {}
            for ref in image_id_to_containers.get(raw_id, []):
                matched_containers[ref.id] = ref
            for k, v_list in image_id_to_containers.items():
                if k.startswith(raw_id) or raw_id.startswith(k):
                    for ref in v_list:
                        matched_containers[ref.id] = ref
            for tag in clean_tags:
                for ref in tag_to_containers.get(tag, []):
                    matched_containers[ref.id] = ref

            containers_count = len(matched_containers)

            # Search filter
            if search:
                q = search.strip().lower()
                id_match = q in raw_id.lower() or q in short_id.lower()
                tag_match = any(q in t.lower() for t in clean_tags)
                repo_match = any(q in r.lower() for r in repositories)
                if not (id_match or tag_match or repo_match):
                    continue

            size_bytes = int(img.get("Size", 0))
            v_size = img.get("VirtualSize")
            virtual_size_bytes = int(v_size) if v_size is not None else None
            created_at = self._clean_timestamp(img.get("Created"))
            labels = self._sanitize_labels(img.get("Labels"))

            items.append(ImageSummary(
                id=raw_id,
                short_id=short_id,
                repo_tags=clean_tags,
                repositories=repositories,
                tags=tags,
                size_bytes=size_bytes,
                virtual_size_bytes=virtual_size_bytes,
                created_at=created_at,
                containers_count=containers_count,
                is_dangling=is_dangling,
                labels=labels,
            ))

        return ImageListResponse(items=items, total=len(items))

    def _sync_get_image(self, image_id: str) -> ImageDetail:
        """
        Synchronously inspect a Docker image and correlate container references.
        Strictly omits environment variables, sensitive tokens, or secrets.
        """
        try:
            client, _ = self._create_client()
        except Exception as exc:
            logger.warning(f"Failed to create Docker client for image inspect: {exc}")
            raise DockerUnavailableException(f"Cannot initialize Docker client: {exc}") from exc

        try:
            insp = client.api.inspect_image(image_id)
            raw_containers = client.api.containers(all=True)
        except NotFound as exc:
            raise DockerImageNotFoundException(f"Image '{image_id}' was not found.") from exc
        except DockerException as exc:
            logger.warning(f"Docker API inspect_image failed for '{image_id}': {exc}")
            raise DockerUnavailableException(f"Docker daemon query failed: {exc}") from exc
        finally:
            try:
                client.close()
            except Exception:
                pass

        raw_id = insp.get("Id", image_id)
        short_id = raw_id.replace("sha256:", "")[:12]
        raw_repo_tags = insp.get("RepoTags") or []
        clean_tags = [t for t in raw_repo_tags if t != "<none>:<none>"]
        is_dangling = not clean_tags

        repositories = list(dict.fromkeys([t.rsplit(":", 1)[0] for t in clean_tags if ":" in t]))
        tags = list(dict.fromkeys([t.rsplit(":", 1)[1] for t in clean_tags if ":" in t]))

        # Correlate containers
        matched_containers: dict[str, ImageContainerReference] = {}
        for c in raw_containers:
            cid = c.get("Id", "")
            short_cid = cid[:12] if len(cid) >= 12 else cid
            names = c.get("Names") or []
            cname = names[0].lstrip("/") if names else short_cid
            cstate = c.get("State", "unknown")
            cstatus = c.get("Status", cstate)
            ref = ImageContainerReference(
                id=cid,
                short_id=short_cid,
                name=cname,
                state=cstate,
                status=cstatus,
            )

            c_img_id = c.get("ImageID", "")
            c_img_tag = c.get("Image", "")
            if (
                c_img_id == raw_id
                or raw_id.startswith(c_img_id)
                or c_img_id.startswith(raw_id)
                or c_img_tag in clean_tags
                or c_img_tag == raw_id
                or c_img_tag == short_id
            ):
                matched_containers[cid] = ref

        containers_list = list(matched_containers.values())
        size_bytes = int(insp.get("Size", 0))
        v_size = insp.get("VirtualSize")
        virtual_size_bytes = int(v_size) if v_size is not None else None
        created_at = self._clean_timestamp(insp.get("Created"))

        architecture = insp.get("Architecture")
        os_name = insp.get("Os")
        author = insp.get("Author") or None
        comment = insp.get("Comment") or None
        docker_version = insp.get("DockerVersion") or None

        root_fs_layers = (insp.get("RootFS") or {}).get("Layers") or []
        # Config labels sanitized - STRICTLY NO Config.Env
        config = insp.get("Config") or {}
        labels = self._sanitize_labels(config.get("Labels"))

        return ImageDetail(
            id=raw_id,
            short_id=short_id,
            repo_tags=clean_tags,
            repositories=repositories,
            tags=tags,
            size_bytes=size_bytes,
            virtual_size_bytes=virtual_size_bytes,
            created_at=created_at,
            containers_count=len(containers_list),
            is_dangling=is_dangling,
            labels=labels,
            architecture=architecture,
            os=os_name,
            author=author,
            comment=comment,
            docker_version=docker_version,
            root_fs_layers=root_fs_layers,
            containers=containers_list,
        )

    def _sync_list_volumes(
        self,
        search: Optional[str] = None,
        driver: Optional[str] = None,
    ) -> VolumeListResponse:
        """
        Synchronously list Docker volumes and correlate container usage.
        """
        try:
            client, _ = self._create_client()
        except Exception as exc:
            logger.warning(f"Failed to create Docker client for volumes: {exc}")
            raise DockerUnavailableException(f"Cannot initialize Docker client: {exc}") from exc

        try:
            vol_data = client.api.volumes()
            raw_vols = vol_data.get("Volumes") or []
            raw_containers = client.api.containers(all=True)
        except DockerException as exc:
            logger.warning(f"Docker API volumes query failed: {exc}")
            raise DockerUnavailableException(f"Docker daemon query failed: {exc}") from exc
        finally:
            try:
                client.close()
            except Exception:
                pass

        # Build volume to containers correlation
        from collections import defaultdict
        vol_containers_map = defaultdict(list)
        for c in raw_containers:
            cid = c.get("Id", "")
            short_cid = cid[:12] if len(cid) >= 12 else cid
            names = c.get("Names") or []
            cname = names[0].lstrip("/") if names else short_cid
            cstate = c.get("State", "unknown")

            for m in c.get("Mounts") or []:
                if m.get("Type") == "volume":
                    vname = m.get("Name")
                    if vname:
                        vol_containers_map[vname].append(VolumeContainerReference(
                            id=cid,
                            short_id=short_cid,
                            name=cname,
                            state=cstate,
                            destination=m.get("Destination", ""),
                            mode=m.get("Mode"),
                            read_only=not m.get("RW", True),
                        ))

        items: list[VolumeSummary] = []
        for v in raw_vols:
            name = v.get("Name", "")
            drv = v.get("Driver", "local")
            scope = v.get("Scope", "local")
            created_at = self._clean_timestamp(v.get("CreatedAt"))

            if driver and drv.lower() != driver.strip().lower():
                continue

            if search and search.strip().lower() not in name.lower():
                continue

            c_refs = vol_containers_map.get(name, [])
            containers_count = len(c_refs)
            is_in_use = containers_count > 0
            labels = self._sanitize_labels(v.get("Labels"))

            items.append(VolumeSummary(
                name=name,
                driver=drv,
                scope=scope,
                created_at=created_at,
                containers_count=containers_count,
                is_in_use=is_in_use,
                labels=labels,
            ))

        return VolumeListResponse(items=items, total=len(items))

    def _sync_get_volume(self, volume_name: str) -> VolumeDetail:
        """
        Synchronously inspect a Docker volume and list container mount references.
        Protects host privacy and sanitizes driver options.
        """
        try:
            client, _ = self._create_client()
        except Exception as exc:
            logger.warning(f"Failed to create Docker client for volume inspect: {exc}")
            raise DockerUnavailableException(f"Cannot initialize Docker client: {exc}") from exc

        try:
            insp = client.api.inspect_volume(volume_name)
            raw_containers = client.api.containers(all=True)
        except NotFound as exc:
            raise DockerVolumeNotFoundException(f"Volume '{volume_name}' was not found.") from exc
        except DockerException as exc:
            logger.warning(f"Docker API inspect_volume failed for '{volume_name}': {exc}")
            raise DockerUnavailableException(f"Docker daemon query failed: {exc}") from exc
        finally:
            try:
                client.close()
            except Exception:
                pass

        name = insp.get("Name", volume_name)
        drv = insp.get("Driver", "local")
        scope = insp.get("Scope", "local")
        created_at = self._clean_timestamp(insp.get("CreatedAt"))
        mountpoint = insp.get("Mountpoint")

        # Sanitize driver options
        raw_options = insp.get("Options") or {}
        sanitized_options: dict[str, str] = {}
        if isinstance(raw_options, dict):
            for k, v in raw_options.items():
                if not any(kw in str(k).lower() for kw in SENSITIVE_LABEL_KEYWORDS):
                    sanitized_options[str(k)] = str(v)

        labels = self._sanitize_labels(insp.get("Labels"))

        # Find container references
        containers_list: list[VolumeContainerReference] = []
        for c in raw_containers:
            cid = c.get("Id", "")
            short_cid = cid[:12] if len(cid) >= 12 else cid
            names = c.get("Names") or []
            cname = names[0].lstrip("/") if names else short_cid
            cstate = c.get("State", "unknown")

            for m in c.get("Mounts") or []:
                if m.get("Type") == "volume" and m.get("Name") == name:
                    containers_list.append(VolumeContainerReference(
                        id=cid,
                        short_id=short_cid,
                        name=cname,
                        state=cstate,
                        destination=m.get("Destination", ""),
                        mode=m.get("Mode"),
                        read_only=not m.get("RW", True),
                    ))

        return VolumeDetail(
            name=name,
            driver=drv,
            scope=scope,
            created_at=created_at,
            containers_count=len(containers_list),
            is_in_use=len(containers_list) > 0,
            labels=labels,
            mountpoint=mountpoint,
            options=sanitized_options,
            containers=containers_list,
        )

    async def list_images(
        self,
        search: Optional[str] = None,
        dangling: Optional[bool] = None,
    ) -> ImageListResponse:
        """
        Asynchronously retrieve Docker images list with optional search and dangling filters.
        """
        try:
            async with asyncio.timeout(self.timeout):
                return await asyncio.to_thread(self._sync_list_images, search, dangling)
        except asyncio.TimeoutError as exc:
            raise DockerUnavailableException(
                f"Docker image listing timed out after {self.timeout} seconds."
            ) from exc

    async def get_image(self, image_id: str) -> ImageDetail:
        """
        Asynchronously inspect a Docker image and its container relationships.
        """
        try:
            async with asyncio.timeout(self.timeout):
                return await asyncio.to_thread(self._sync_get_image, image_id)
        except asyncio.TimeoutError as exc:
            raise DockerUnavailableException(
                f"Docker image inspection timed out after {self.timeout} seconds."
            ) from exc

    async def list_volumes(
        self,
        search: Optional[str] = None,
        driver: Optional[str] = None,
    ) -> VolumeListResponse:
        """
        Asynchronously retrieve Docker volumes list with optional search and driver filters.
        """
        try:
            async with asyncio.timeout(self.timeout):
                return await asyncio.to_thread(self._sync_list_volumes, search, driver)
        except asyncio.TimeoutError as exc:
            raise DockerUnavailableException(
                f"Docker volume listing timed out after {self.timeout} seconds."
            ) from exc

    async def get_volume(self, volume_name: str) -> VolumeDetail:
        """
        Asynchronously inspect a Docker volume and its container relationships.
        """
        try:
            async with asyncio.timeout(self.timeout):
                return await asyncio.to_thread(self._sync_get_volume, volume_name)
        except asyncio.TimeoutError as exc:
            raise DockerUnavailableException(
                f"Docker volume inspection timed out after {self.timeout} seconds."
            ) from exc

    @staticmethod
    def _redact_secrets(message: str) -> str:
        redacted = message
        for pattern, replacement in REDACTION_PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        return redacted

    @staticmethod
    def _extract_timestamp(line: str, timestamps_requested: bool) -> Tuple[Optional[str], str]:
        if timestamps_requested:
            match = TIMESTAMP_REGEX.match(line)
            if match:
                return match.group(1), match.group(2)
        return None, line

    @staticmethod
    def _parse_demux_logs(
        raw_data: Any,
        timestamps: bool,
        default_stream: LogStreamType = LogStreamType.STDOUT,
    ) -> list[LogEntry]:
        if not raw_data:
            return []

        entries: list[LogEntry] = []

        if isinstance(raw_data, str):
            for line in raw_data.splitlines():
                line = line.rstrip("\r")
                if not line.strip() and not line:
                    continue
                ts, msg = DockerService._extract_timestamp(line, timestamps)
                entries.append(LogEntry(
                    timestamp=ts,
                    stream=default_stream,
                    message=DockerService._redact_secrets(msg),
                ))
            return entries

        if not isinstance(raw_data, (bytes, bytearray)):
            return []

        data = bytes(raw_data)
        # Check if multiplexed: 8-byte headers: stream_type (1 or 2), 3 zero bytes, 4-byte length
        is_multiplexed = False
        if len(data) >= 8 and data[0] in (1, 2) and data[1:4] == b"\x00\x00\x00":
            first_frame_len = struct.unpack(">I", data[4:8])[0]
            if first_frame_len <= len(data) - 8:
                is_multiplexed = True

        if is_multiplexed:
            offset = 0
            n = len(data)
            while offset + 8 <= n:
                stream_type_byte = data[offset]
                if data[offset+1:offset+4] != b"\x00\x00\x00":
                    break
                frame_len = struct.unpack(">I", data[offset+4:offset+8])[0]
                frame_data = data[offset+8 : offset+8+frame_len]
                offset += 8 + frame_len

                stream = LogStreamType.STDOUT if stream_type_byte == 1 else LogStreamType.STDERR if stream_type_byte == 2 else LogStreamType.SYSTEM
                text = frame_data.decode("utf-8", errors="replace")
                for line in text.splitlines():
                    line = line.rstrip("\r")
                    if not line.strip() and not line:
                        continue
                    ts, msg = DockerService._extract_timestamp(line, timestamps)
                    entries.append(LogEntry(
                        timestamp=ts,
                        stream=stream,
                        message=DockerService._redact_secrets(msg),
                    ))

            if offset < n:
                trailing = data[offset:].decode("utf-8", errors="replace")
                for line in trailing.splitlines():
                    line = line.rstrip("\r")
                    if not line.strip() and not line:
                        continue
                    ts, msg = DockerService._extract_timestamp(line, timestamps)
                    entries.append(LogEntry(
                        timestamp=ts,
                        stream=default_stream,
                        message=DockerService._redact_secrets(msg),
                    ))
        else:
            text = data.decode("utf-8", errors="replace")
            for line in text.splitlines():
                line = line.rstrip("\r")
                if not line.strip() and not line:
                    continue
                ts, msg = DockerService._extract_timestamp(line, timestamps)
                entries.append(LogEntry(
                    timestamp=ts,
                    stream=default_stream,
                    message=DockerService._redact_secrets(msg),
                ))

        return entries

    def _sync_get_container_logs(
        self,
        container_id: str,
        tail: int = 100,
        timestamps: bool = True,
        stdout: bool = True,
        stderr: bool = True,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> ContainerLogsResponse:
        """
        Synchronously retrieve bounded, redacted container logs from Docker daemon.
        Strictly bounded: stream=False, tail <= 1000, max buffer limits.
        """
        if not stdout and not stderr:
            return ContainerLogsResponse(
                container_id=container_id,
                container_name=container_id,
                total_lines=0,
                lines=[],
                truncated=False,
                parameters=ContainerLogsParameters(
                    tail=tail,
                    timestamps=timestamps,
                    stdout=stdout,
                    stderr=stderr,
                    since=since,
                    until=until,
                ),
                collected_at=datetime.now(timezone.utc).isoformat(),
                redaction_applied=True,
            )

        try:
            client, _ = self._create_client()
        except Exception as exc:
            logger.warning(f"Failed to create Docker client for container logs: {exc}")
            raise DockerUnavailableException(f"Cannot initialize Docker client: {exc}") from exc

        try:
            insp = client.api.inspect_container(container_id)
            cid = insp.get("Id", container_id)
            cname = insp.get("Name", "").lstrip("/") or cid[:12]

            logs_kwargs: dict[str, Any] = {
                "stdout": stdout,
                "stderr": stderr,
                "stream": False,
                "timestamps": timestamps,
                "tail": tail,
            }
            if since:
                logs_kwargs["since"] = since
            if until:
                logs_kwargs["until"] = until

            raw_logs = client.api.logs(container_id, **logs_kwargs)
        except NotFound as exc:
            raise DockerContainerNotFoundException(f"Container '{container_id}' was not found.") from exc
        except DockerException as exc:
            logger.warning(f"Docker API logs query failed for '{container_id}': {exc}")
            raise DockerUnavailableException(f"Docker daemon query failed: {exc}") from exc
        finally:
            try:
                client.close()
            except Exception:
                pass

        default_stream = LogStreamType.STDOUT if stdout else LogStreamType.STDERR
        all_entries = self._parse_demux_logs(raw_logs, timestamps, default_stream)

        truncated = False
        if len(all_entries) > tail:
            all_entries = all_entries[-tail:]
            truncated = True

        return ContainerLogsResponse(
            container_id=cid,
            container_name=cname,
            total_lines=len(all_entries),
            lines=all_entries,
            truncated=truncated,
            parameters=ContainerLogsParameters(
                tail=tail,
                timestamps=timestamps,
                stdout=stdout,
                stderr=stderr,
                since=since,
                until=until,
            ),
            collected_at=datetime.now(timezone.utc).isoformat(),
            redaction_applied=True,
        )

    async def get_container_logs(
        self,
        container_id: str,
        tail: int = 100,
        timestamps: bool = True,
        stdout: bool = True,
        stderr: bool = True,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> ContainerLogsResponse:
        """
        Asynchronously retrieve bounded container logs with concurrency limiting and strict timeout.
        """
        try:
            async with self._logs_semaphore:
                async with asyncio.timeout(self.timeout):
                    return await asyncio.to_thread(
                        self._sync_get_container_logs,
                        container_id,
                        tail,
                        timestamps,
                        stdout,
                        stderr,
                        since,
                        until,
                    )
        except asyncio.TimeoutError as exc:
            raise DockerUnavailableException(
                f"Docker container logs request timed out after {self.timeout} seconds."
            ) from exc

    async def get_docker_status(self) -> DockerStatusResponse:
        """
        Asynchronously retrieve Docker Engine status using an executor thread
        with strict timeout enforcement.
        """
        now = datetime.now(timezone.utc)
        try:
            async with asyncio.timeout(self.timeout):
                return await asyncio.to_thread(self._sync_fetch_status)
        except asyncio.TimeoutError:
            logger.warning(f"Docker status check timed out after {self.timeout}s")
            return DockerStatusResponse(
                status=DockerConnectionStatus.ERROR,
                endpoint=self.host or "default socket",
                error_message=f"Connection to Docker Engine timed out after {self.timeout} seconds.",
                checked_at=now,
            )


# Default singleton service instance
docker_service = DockerService()
