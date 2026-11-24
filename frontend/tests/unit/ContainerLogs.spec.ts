import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ContainerLogsViewer from '@/components/docker/ContainerLogsViewer.vue'
import ContainerDetailDrawer from '@/components/docker/ContainerDetailDrawer.vue'
import { dockerApi } from '@/services/api'
import type { ContainerDetail, ContainerLogsResponse } from '@/types'

vi.mock('@/services/api', () => ({
  dockerApi: {
    getContainerLogs: vi.fn(),
    getContainerStats: vi.fn(),
  },
}))

const MOCK_DETAIL: ContainerDetail = {
  id: 'c1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
  short_id: 'c1234567890a',
  name: 'dockscope-db',
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

const MOCK_LOGS_RESPONSE: ContainerLogsResponse = {
  container_id: 'c1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
  container_name: 'dockscope-db',
  total_lines: 3,
  lines: [
    {
      timestamp: '2026-11-23T12:00:00.000000000Z',
      stream: 'stdout',
      message: 'PostgreSQL database server initialized',
    },
    {
      timestamp: '2026-11-23T12:00:01.000000000Z',
      stream: 'stdout',
      message: 'Server accepting connections on port 5432',
    },
    {
      timestamp: '2026-11-23T12:00:02.000000000Z',
      stream: 'stderr',
      message: '[WARNING] Password authentication enabled: password=[REDACTED]',
    },
  ],
  truncated: false,
  parameters: {
    tail: 100,
    timestamps: true,
    stdout: true,
    stderr: true,
    since: null,
    until: null,
  },
  collected_at: '2026-11-23T12:00:05Z',
  redaction_applied: true,
}

describe('ContainerLogsViewer.vue (M02.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders log lines with timestamps, stream tags, and line numbers', async () => {
    vi.mocked(dockerApi.getContainerLogs).mockResolvedValue(MOCK_LOGS_RESPONSE)

    const wrapper = mount(ContainerLogsViewer, {
      props: {
        containerId: 'c1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
        containerName: 'dockscope-db',
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('dockscope-db — logs')
    expect(wrapper.text()).toContain('PostgreSQL database server initialized')
    expect(wrapper.text()).toContain('Server accepting connections on port 5432')
    expect(wrapper.text()).toContain('[WARNING] Password authentication enabled')
    expect(wrapper.text()).toContain('password=[REDACTED]')

    // Stream tags
    expect(wrapper.text()).toContain('stdout')
    expect(wrapper.text()).toContain('stderr')

    // Footer info
    expect(wrapper.text()).toContain('Redaction: Active')
    expect(wrapper.text()).toContain('Lines: 3 / 3')
  })

  it('filters log lines using search query', async () => {
    vi.mocked(dockerApi.getContainerLogs).mockResolvedValue(MOCK_LOGS_RESPONSE)

    const wrapper = mount(ContainerLogsViewer, {
      props: {
        containerId: 'c1',
        containerName: 'dockscope-db',
      },
    })

    await flushPromises()

    const searchInput = wrapper.find('input[placeholder*="Filter log output"]')
    expect(searchInput.exists()).toBe(true)

    // Search for "warning"
    await searchInput.setValue('warning')
    expect(wrapper.text()).toContain('[WARNING] Password authentication enabled')
    expect(wrapper.text()).not.toContain('PostgreSQL database server initialized')
    expect(wrapper.text()).toContain('1 / 3 lines')
  })

  it('changes tail parameter and queries backend', async () => {
    vi.mocked(dockerApi.getContainerLogs).mockResolvedValue(MOCK_LOGS_RESPONSE)

    const wrapper = mount(ContainerLogsViewer, {
      props: {
        containerId: 'c1',
        containerName: 'dockscope-db',
      },
    })

    await flushPromises()

    const tailSelect = wrapper.find('select')
    expect(tailSelect.exists()).toBe(true)
    await tailSelect.setValue('500')
    await flushPromises()

    expect(dockerApi.getContainerLogs).toHaveBeenCalledWith('c1', expect.objectContaining({ tail: 500 }))
  })

  it('handles copy to clipboard', async () => {
    vi.mocked(dockerApi.getContainerLogs).mockResolvedValue(MOCK_LOGS_RESPONSE)
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    })

    const wrapper = mount(ContainerLogsViewer, {
      props: {
        containerId: 'c1',
        containerName: 'dockscope-db',
      },
    })

    await flushPromises()

    const copyBtn = wrapper.find('button[title*="Copy logs"]')
    expect(copyBtn.exists()).toBe(true)
    await copyBtn.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Copied!')
  })

  it('renders empty log state when container has no logs', async () => {
    vi.mocked(dockerApi.getContainerLogs).mockResolvedValue({
      ...MOCK_LOGS_RESPONSE,
      total_lines: 0,
      lines: [],
    })

    const wrapper = mount(ContainerLogsViewer, {
      props: {
        containerId: 'c_empty',
        containerName: 'empty-container',
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('No Log Output')
    expect(wrapper.text()).toContain('No logs have been recorded for this container workload yet.')
  })

  it('renders error state and retry button on API failure', async () => {
    vi.mocked(dockerApi.getContainerLogs).mockRejectedValue(new Error('Docker daemon logs connection refused'))

    const wrapper = mount(ContainerLogsViewer, {
      props: {
        containerId: 'c_err',
        containerName: 'error-container',
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Log Retrieval Error')
    expect(wrapper.text()).toContain('Docker daemon logs connection refused')
    expect(wrapper.text()).toContain('Retry Log Query')
  })
})

describe('ContainerDetailDrawer.vue - Logs Tab Integration (M02.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(dockerApi.getContainerStats).mockResolvedValue({
      container_id: 'c1',
      name: 'dockscope-db',
      is_running: true,
      cpu_percentage: 5.0,
      cpu_usage_nanoseconds: 1000,
      online_cpus: 2,
      memory_usage_bytes: 50000000,
      memory_limit_bytes: 100000000,
      memory_percentage: 50.0,
      collected_at: '2026-11-23T12:00:00Z',
    })
    vi.mocked(dockerApi.getContainerLogs).mockResolvedValue(MOCK_LOGS_RESPONSE)
  })

  it('renders tab buttons and allows switching to Container Logs', async () => {
    const wrapper = mount(ContainerDetailDrawer, {
      props: {
        container: MOCK_DETAIL,
        isOpen: true,
      },
    })

    await flushPromises()

    // Verify sub-tab bar is present
    expect(wrapper.text()).toContain('Overview & Telemetry')
    expect(wrapper.text()).toContain('Container Logs')

    // Default overview tab is visible
    expect(wrapper.text()).toContain('Resource Utilization (M02.3)')
    expect(wrapper.text()).toContain('Connected Networks')

    // Switch to Container Logs Tab
    const logsTabBtn = wrapper.findAll('button').find((b) => b.text().includes('Container Logs'))
    expect(logsTabBtn).toBeDefined()
    await logsTabBtn!.trigger('click')
    await flushPromises()

    // Logs viewer is now mounted and active
    expect(wrapper.text()).toContain('dockscope-db — logs')
    expect(wrapper.text()).toContain('PostgreSQL database server initialized')
  })
})
