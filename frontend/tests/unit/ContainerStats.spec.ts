import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ContainerDetailDrawer from '@/components/docker/ContainerDetailDrawer.vue'
import { dockerApi } from '@/services/api'
import type { ContainerDetail, ContainerStats } from '@/types'

vi.mock('@/services/api', () => ({
  dockerApi: {
    getContainerStats: vi.fn(),
  },
}))

const MOCK_DETAIL: ContainerDetail = {
  id: 'a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef',
  short_id: 'a1b2c3d4e5f6',
  name: 'production-postgres',
  image: 'postgres:16-alpine',
  state: 'running',
  status: 'Up 2 hours',
  created_at: '2026-11-23T10:00:00Z',
  ports: [],
  restart_count: 0,
  networks: ['dockscope-net'],
  mounts: [],
  labels: {},
}

const MOCK_STATS_RUNNING: ContainerStats = {
  container_id: 'a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef',
  name: 'production-postgres',
  is_running: true,
  cpu_percentage: 14.5,
  cpu_usage_nanoseconds: 500000000,
  system_cpu_usage_nanoseconds: 1000000000,
  online_cpus: 4,
  memory_usage_bytes: 104857600, // 100 MB
  memory_limit_bytes: 1073741824, // 1 GB
  memory_percentage: 9.77,
  network_rx_bytes: 1048576, // 1 MB
  network_tx_bytes: 2097152, // 2 MB
  block_read_bytes: 5242880, // 5 MB
  block_write_bytes: 10485760, // 10 MB
  collected_at: '2026-11-23T12:00:00Z',
}

describe('ContainerDetailDrawer.vue - Resource Monitoring (M02.3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders running container resource metrics correctly', async () => {
    vi.mocked(dockerApi.getContainerStats).mockResolvedValueOnce(MOCK_STATS_RUNNING)

    const wrapper = mount(ContainerDetailDrawer, {
      props: {
        container: MOCK_DETAIL,
        isOpen: true,
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Resource Utilization (M02.3)')
    // CPU
    expect(wrapper.text()).toContain('14.5')
    expect(wrapper.text()).toContain('4 Cores')
    // Memory
    expect(wrapper.text()).toContain('9.77%')
    expect(wrapper.text()).toContain('100 MB')
    expect(wrapper.text()).toContain('1 GB')
    // Network
    expect(wrapper.text()).toContain('1 MB')
    expect(wrapper.text()).toContain('2 MB')
    // Block I/O
    expect(wrapper.text()).toContain('5 MB')
    expect(wrapper.text()).toContain('10 MB')
  })

  it('renders stopped container state without errors', async () => {
    const stoppedStats: ContainerStats = {
      container_id: 'c2',
      name: 'stopped-app',
      is_running: false,
      cpu_percentage: 0,
      cpu_usage_nanoseconds: 0,
      online_cpus: 1,
      memory_usage_bytes: 0,
      memory_limit_bytes: 0,
      memory_percentage: 0,
      collected_at: '2026-11-23T12:00:00Z',
    }

    vi.mocked(dockerApi.getContainerStats).mockResolvedValueOnce(stoppedStats)

    const stoppedDetail: ContainerDetail = {
      ...MOCK_DETAIL,
      state: 'exited',
      status: 'Exited (0)',
    }

    const wrapper = mount(ContainerDetailDrawer, {
      props: {
        container: stoppedDetail,
        isOpen: true,
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Container is stopped. Resource telemetry is inactive.')
  })

  it('handles stats error state and allows retry', async () => {
    vi.mocked(dockerApi.getContainerStats).mockRejectedValueOnce(
      new Error('Docker stats daemon connection timeout')
    )

    const wrapper = mount(ContainerDetailDrawer, {
      props: {
        container: MOCK_DETAIL,
        isOpen: true,
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Docker stats daemon connection timeout')
    expect(wrapper.text()).toContain('Retry')

    // Retry
    vi.mocked(dockerApi.getContainerStats).mockResolvedValueOnce(MOCK_STATS_RUNNING)
    const retryBtn = wrapper.findAll('button').find((b) => b.text().includes('Retry'))
    expect(retryBtn).toBeDefined()
    await retryBtn!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('14.5')
    expect(wrapper.text()).not.toContain('Docker stats daemon connection timeout')
  })

  it('triggers manual refresh when Refresh button is clicked', async () => {
    vi.mocked(dockerApi.getContainerStats).mockResolvedValue(MOCK_STATS_RUNNING)

    const wrapper = mount(ContainerDetailDrawer, {
      props: {
        container: MOCK_DETAIL,
        isOpen: true,
      },
    })

    await flushPromises()

    const refreshBtn = wrapper.findAll('button').find((b) => b.text().includes('Refresh'))
    expect(refreshBtn).toBeDefined()
    await refreshBtn!.trigger('click')
    await flushPromises()

    // 1 on mount + 1 on manual refresh
    expect(dockerApi.getContainerStats).toHaveBeenCalledTimes(2)
  })

  it('handles missing optional network and block I/O metrics gracefully', async () => {
    const minimalStats: ContainerStats = {
      container_id: 'c3',
      name: 'minimal-app',
      is_running: true,
      cpu_percentage: 0.5,
      cpu_usage_nanoseconds: 1000,
      online_cpus: 1,
      memory_usage_bytes: 5242880,
      memory_limit_bytes: 0,
      memory_percentage: 0,
      network_rx_bytes: null,
      network_tx_bytes: null,
      block_read_bytes: null,
      block_write_bytes: null,
      collected_at: '2026-11-23T12:00:00Z',
    }

    vi.mocked(dockerApi.getContainerStats).mockResolvedValueOnce(minimalStats)

    const wrapper = mount(ContainerDetailDrawer, {
      props: {
        container: MOCK_DETAIL,
        isOpen: true,
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('0.5')
    expect(wrapper.text()).toContain('5 MB')
    // Optional metrics fallback to '—'
    expect(wrapper.text()).toContain('—')
  })
})
