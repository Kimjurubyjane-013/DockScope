import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import DockerEngineStatus from '@/components/dashboard/DockerEngineStatus.vue'
import { dockerApi } from '@/services/api'
import type { DockerStatusResponse } from '@/types'

vi.mock('@/services/api', () => ({
  dockerApi: {
    getStatus: vi.fn(),
  },
}))

describe('DockerEngineStatus.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders connected state with engine and API versions', async () => {
    const mockConnectedResponse: DockerStatusResponse = {
      status: 'connected',
      endpoint: 'npipe:////./pipe/docker_engine',
      checked_at: '2026-11-23T10:00:00Z',
      error_message: null,
      details: {
        version: '29.9.3',
        api_version: '1.56',
        min_api_version: '1.24',
        os: 'Docker Desktop',
        os_type: 'linux',
        architecture: 'x86_64',
        cpus: 8,
        memory_total_bytes: 16777216000,
        containers_total: 7,
        containers_running: 3,
        containers_paused: 0,
        containers_stopped: 4,
        images_total: 15,
      },
    }

    vi.mocked(dockerApi.getStatus).mockResolvedValueOnce(mockConnectedResponse)

    const wrapper = mount(DockerEngineStatus)
    await flushPromises()

    expect(wrapper.text()).toContain('Docker Engine Connection')
    expect(wrapper.text()).toContain('Connected')
    expect(wrapper.text()).toContain('29.9.3')
    expect(wrapper.text()).toContain('API v1.56')
    expect(wrapper.text()).toContain('7')
    expect(wrapper.text()).toContain('3 running')
    expect(wrapper.text()).toContain('npipe:////./pipe/docker_engine')
  })

  it('renders disconnected state with clear error message', async () => {
    const mockDisconnectedResponse: DockerStatusResponse = {
      status: 'disconnected',
      endpoint: 'unix:///var/run/docker.sock',
      checked_at: '2026-11-23T10:05:00Z',
      error_message: 'Docker daemon connection was refused. Ensure Docker service is active.',
      details: null,
    }

    vi.mocked(dockerApi.getStatus).mockResolvedValueOnce(mockDisconnectedResponse)

    const wrapper = mount(DockerEngineStatus)
    await flushPromises()

    expect(wrapper.text()).toContain('Disconnected')
    expect(wrapper.text()).toContain('Docker Daemon Offline or Unreachable')
    expect(wrapper.text()).toContain('Docker daemon connection was refused')
  })

  it('renders unavailable state when socket is missing', async () => {
    const mockUnavailableResponse: DockerStatusResponse = {
      status: 'unavailable',
      endpoint: 'default socket',
      checked_at: '2026-11-23T10:10:00Z',
      error_message: 'Docker daemon socket or pipe was not found. Is Docker Engine running?',
      details: null,
    }

    vi.mocked(dockerApi.getStatus).mockResolvedValueOnce(mockUnavailableResponse)

    const wrapper = mount(DockerEngineStatus)
    await flushPromises()

    expect(wrapper.text()).toContain('Unavailable')
    expect(wrapper.text()).toContain('socket or pipe was not found')
  })

  it('uses containersOverride prop when provided to guarantee count consistency', async () => {
    const mockConnectedResponse: DockerStatusResponse = {
      status: 'connected',
      endpoint: 'npipe:////./pipe/docker_engine',
      checked_at: '2026-11-23T10:00:00Z',
      error_message: null,
      details: {
        version: '29.9.3',
        api_version: '1.56',
        min_api_version: '1.24',
        os: 'Docker Desktop',
        os_type: 'linux',
        architecture: 'x86_64',
        cpus: 8,
        memory_total_bytes: 16777216000,
        containers_total: 999,
        containers_running: 999,
        containers_paused: 0,
        containers_stopped: 0,
        images_total: 15,
      },
    }

    vi.mocked(dockerApi.getStatus).mockResolvedValueOnce(mockConnectedResponse)

    const wrapper = mount(DockerEngineStatus, {
      props: {
        containersOverride: {
          total: 7,
          running: 1,
        },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('7')
    expect(wrapper.text()).toContain('1 running')
    expect(wrapper.text()).not.toContain('999')
  })
})
