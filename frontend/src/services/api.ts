import axios from 'axios'
import type {
  User,
  AuthResponse,
  HealthResponse,
  ReadyResponse,
  DockerStatusResponse,
  ContainerListResponse,
  ContainerDetail,
  ContainerStats,
  ImageListResponse,
  ImageDetail,
  VolumeListResponse,
  VolumeDetail,
  ContainerLogsResponse,
} from '@/types'

export const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 10000, // 10-second request timeout prevents hanging on stalled connections
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enables HttpOnly cookie transmission
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = 'An unexpected error occurred'
    if (error.response?.data?.detail) {
      if (typeof error.response.data.detail === 'string') {
        message = error.response.data.detail
      } else if (Array.isArray(error.response.data.detail)) {
        message = error.response.data.detail.map((d: { msg: string }) => d.msg).join(', ')
      }
    } else if (error.message) {
      message = error.message
    }
    return Promise.reject(new Error(message))
  }
)

export const authApi = {
  async register(payload: { email: string; password: string }): Promise<User> {
    const response = await apiClient.post<User>('/auth/register', payload)
    return response.data
  },

  async login(payload: { email: string; password: string }): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', payload)
    return response.data
  },

  async logout(): Promise<void> {
    await apiClient.post('/auth/logout')
  },

  async getMe(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me')
    return response.data
  },
}

export const healthApi = {
  async checkHealth(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>('/health')
    return response.data
  },

  async checkReady(): Promise<ReadyResponse> {
    const response = await apiClient.get<ReadyResponse>('/health/ready')
    return response.data
  },
}

export const dockerApi = {
  async getStatus(): Promise<DockerStatusResponse> {
    const response = await apiClient.get<DockerStatusResponse>('/docker/status')
    return response.data
  },

  async listContainers(params?: { status?: string; search?: string }): Promise<ContainerListResponse> {
    const response = await apiClient.get<ContainerListResponse>('/docker/containers', { params })
    return response.data
  },

  async getContainer(id: string): Promise<ContainerDetail> {
    const response = await apiClient.get<ContainerDetail>(`/docker/containers/${id}`)
    return response.data
  },

  async getContainerStats(id: string): Promise<ContainerStats> {
    const response = await apiClient.get<ContainerStats>(`/docker/containers/${id}/stats`)
    return response.data
  },

  async listImages(params?: { search?: string; dangling?: boolean }): Promise<ImageListResponse> {
    const response = await apiClient.get<ImageListResponse>('/docker/images', { params })
    return response.data
  },

  async getImage(id: string): Promise<ImageDetail> {
    const response = await apiClient.get<ImageDetail>(`/docker/images/${encodeURIComponent(id)}`)
    return response.data
  },

  async listVolumes(params?: { search?: string; driver?: string }): Promise<VolumeListResponse> {
    const response = await apiClient.get<VolumeListResponse>('/docker/volumes', { params })
    return response.data
  },

  async getVolume(name: string): Promise<VolumeDetail> {
    const response = await apiClient.get<VolumeDetail>(`/docker/volumes/${encodeURIComponent(name)}`)
    return response.data
  },

  async getContainerLogs(
    id: string,
    params?: {
      tail?: number
      timestamps?: boolean
      stdout?: boolean
      stderr?: boolean
      since?: string
      until?: string
    }
  ): Promise<ContainerLogsResponse> {
    const response = await apiClient.get<ContainerLogsResponse>(`/docker/containers/${encodeURIComponent(id)}/logs`, {
      params,
    })
    return response.data
  },
}
