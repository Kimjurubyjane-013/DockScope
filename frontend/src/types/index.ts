export interface User {
  id: string
  email: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface HealthResponse {
  status: string
  version: string
  environment: string
  timestamp: string
}

export interface ReadyResponse {
  status: string
  database: string
  timestamp: string
}

export interface InfrastructureMetric {
  title: string
  value: string | number
  unit?: string
  change?: string
  trend?: 'up' | 'down' | 'neutral'
  status?: 'healthy' | 'warning' | 'critical' | 'info'
  subtext?: string
}

export interface ActivityEvent {
  id: string
  timestamp: string
  level: 'info' | 'warning' | 'success' | 'danger'
  source: string
  message: string
}

export type DockerStatusType = 'connected' | 'disconnected' | 'unavailable' | 'error'

export interface DockerEngineDetails {
  version?: string | null
  api_version?: string | null
  min_api_version?: string | null
  os?: string | null
  os_type?: string | null
  architecture?: string | null
  cpus?: number | null
  memory_total_bytes?: number | null
  containers_total?: number | null
  containers_running?: number | null
  containers_paused?: number | null
  containers_stopped?: number | null
  images_total?: number | null
}

export interface DockerStatusResponse {
  status: DockerStatusType
  details?: DockerEngineDetails | null
  error_message?: string | null
  endpoint: string
  checked_at: string
}

export interface PortMapping {
  container_port: number
  host_port?: number | null
  protocol: string
  host_ip?: string | null
}

export interface MountMetadata {
  type: string
  name?: string | null
  source?: string | null
  destination: string
  mode?: string | null
  read_only: boolean
}

export interface ContainerSummary {
  id: string
  short_id: string
  name: string
  image: string
  status: string
  state: string
  created_at?: string | null
  ports: PortMapping[]
  labels: Record<string, string>
}

export interface ContainerListResponse {
  items: ContainerSummary[]
  total: number
}

export interface ContainerDetail {
  id: string
  short_id: string
  name: string
  image: string
  image_id?: string | null
  command?: string | null
  state: string
  status: string
  created_at?: string | null
  started_at?: string | null
  finished_at?: string | null
  ports: PortMapping[]
  restart_count: number
  health_status?: string | null
  networks: string[]
  mounts: MountMetadata[]
  labels: Record<string, string>
}

export interface ContainerStats {
  container_id: string
  name: string
  is_running: boolean
  cpu_percentage: number
  cpu_usage_nanoseconds: number
  system_cpu_usage_nanoseconds?: number | null
  online_cpus: number
  memory_usage_bytes: number
  memory_limit_bytes: number
  memory_percentage: number
  network_rx_bytes?: number | null
  network_tx_bytes?: number | null
  block_read_bytes?: number | null
  block_write_bytes?: number | null
  collected_at: string
}

// --- Docker Images Types (M02.4) ---

export interface ImageContainerReference {
  id: string
  short_id: string
  name: string
  state: string
  status: string
}

export interface ImageSummary {
  id: string
  short_id: string
  repo_tags: string[]
  repositories: string[]
  tags: string[]
  size_bytes: number
  virtual_size_bytes?: number | null
  created_at?: string | null
  containers_count: number
  is_dangling: boolean
  labels: Record<string, string>
}

export interface ImageListResponse {
  items: ImageSummary[]
  total: number
}

export interface ImageDetail extends ImageSummary {
  architecture?: string | null
  os?: string | null
  author?: string | null
  comment?: string | null
  docker_version?: string | null
  root_fs_layers: string[]
  containers: ImageContainerReference[]
}

// --- Docker Volumes Types (M02.4) ---

export interface VolumeContainerReference {
  id: string
  short_id: string
  name: string
  state: string
  destination: string
  mode?: string | null
  read_only: boolean
}

export interface VolumeSummary {
  name: string
  driver: string
  scope: string
  created_at?: string | null
  containers_count: number
  is_in_use: boolean
  labels: Record<string, string>
}

export interface VolumeListResponse {
  items: VolumeSummary[]
  total: number
}

export interface VolumeDetail extends VolumeSummary {
  mountpoint?: string | null
  options: Record<string, string>
  containers: VolumeContainerReference[]
}

// --- Container Logs Types (M02.5) ---

export type LogStreamType = 'stdout' | 'stderr' | 'system'

export interface LogEntry {
  timestamp?: string | null
  stream: LogStreamType
  message: string
}

export interface ContainerLogsParameters {
  tail: number
  timestamps: boolean
  stdout: boolean
  stderr: boolean
  since?: string | null
  until?: string | null
}

export interface ContainerLogsResponse {
  container_id: string
  container_name: string
  total_lines: number
  lines: LogEntry[]
  truncated: boolean
  parameters: ContainerLogsParameters
  collected_at: string
  redaction_applied: boolean
}
