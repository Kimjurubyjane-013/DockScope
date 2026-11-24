import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import ContainerDetailDrawer from '@/components/docker/ContainerDetailDrawer.vue'
import DockerView from '@/views/DockerView.vue'
import { dockerApi } from '@/services/api'
import type { ContainerListResponse, ContainerDetail, DockerStatusResponse } from '@/types'

// Mock Router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/docker', component: { template: '<div>Docker</div>' } },
  ],
})

vi.mock('@/services/api', () => ({
  dockerApi: {
    getStatus: vi.fn(),
    listContainers: vi.fn(),
    getContainer: vi.fn(),
    getContainerStats: vi.fn(),
    listImages: vi.fn(),
    getImage: vi.fn(),
    listVolumes: vi.fn(),
    getVolume: vi.fn(),
  },
}))

const MOCK_CONTAINERS_RESPONSE: ContainerListResponse = {
  total: 2,
  items: [
    {
      id: 'a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef',
      short_id: 'a1b2c3d4e5f6',
      name: 'dockscope-db',
      image: 'postgres:16-alpine',
      status: 'Up 2 hours (healthy)',
      state: 'running',
      created_at: '2026-11-23T10:00:00Z',
      ports: [
        {
          container_port: 5432,
          host_port: 5432,
          protocol: 'tcp',
          host_ip: '127.0.0.1',
        },
      ],
      labels: {
        'com.docker.compose.project': 'dockscope',
      },
    },
    {
      id: 'b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef12',
      short_id: 'b2c3d4e5f678',
      name: 'dockscope-redis',
      image: 'redis:alpine',
      status: 'Exited (0) 1 hour ago',
      state: 'exited',
      created_at: '2026-11-23T09:00:00Z',
      ports: [
        {
          container_port: 6379,
          host_port: null,
          protocol: 'tcp',
          host_ip: null,
        },
      ],
      labels: {},
    },
  ],
}

const MOCK_CONTAINER_DETAIL: ContainerDetail = {
  id: 'a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef',
  short_id: 'a1b2c3d4e5f6',
  name: 'dockscope-db',
  image: 'postgres:16-alpine',
  image_id: 'sha256:fedcba987654',
  command: 'postgres -c shared_buffers=256MB',
  state: 'running',
  status: 'Up (healthy)',
  created_at: '2026-11-23T10:00:00Z',
  started_at: '2026-11-23T10:00:05Z',
  finished_at: null,
  ports: [
    {
      container_port: 5432,
      host_port: 5432,
      protocol: 'tcp',
      host_ip: '127.0.0.1',
    },
  ],
  restart_count: 3,
  health_status: 'healthy',
  networks: ['dockscope-net'],
  mounts: [
    {
      type: 'volume',
      name: 'dockscope_postgres_data',
      source: '/var/lib/docker/volumes/dockscope_postgres_data/_data',
      destination: '/var/lib/postgresql/data',
      mode: 'rw',
      read_only: false,
    },
  ],
  labels: {
    'com.docker.compose.project': 'dockscope',
  },
}

const MOCK_STATUS_RESPONSE: DockerStatusResponse = {
  status: 'connected',
  endpoint: 'npipe:////./pipe/docker_engine',
  checked_at: '2026-11-23T10:00:00Z',
  error_message: null,
  details: {
    version: '29.9.3',
    api_version: '1.56',
    containers_total: 2,
    containers_running: 1,
    containers_stopped: 1,
    containers_paused: 0,
  },
}

describe('ContainerDetailDrawer.vue', () => {
  it('renders container inspection details when open', () => {
    const wrapper = mount(ContainerDetailDrawer, {
      props: {
        container: MOCK_CONTAINER_DETAIL,
        isOpen: true,
      },
    })

    expect(wrapper.text()).toContain('dockscope-db')
    expect(wrapper.text()).toContain('a1b2c3d4e5f6')
    expect(wrapper.text()).toContain('postgres:16-alpine')
    expect(wrapper.text()).toContain('postgres -c shared_buffers=256MB')
    expect(wrapper.text()).toContain('healthy')
    expect(wrapper.text()).toContain('dockscope-net')
    expect(wrapper.text()).toContain('/var/lib/postgresql/data')
    expect(wrapper.text()).toContain('3 times')
    expect(wrapper.text()).toContain('5432')
  })

  it('emits close event when close button is clicked', async () => {
    const wrapper = mount(ContainerDetailDrawer, {
      props: {
        container: MOCK_CONTAINER_DETAIL,
        isOpen: true,
      },
    })

    const closeBtn = wrapper.find('button[title="Close Drawer"]')
    expect(closeBtn.exists()).toBe(true)
    await closeBtn.trigger('click')

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('renders loading state when loading prop is true', () => {
    const wrapper = mount(ContainerDetailDrawer, {
      props: {
        container: null,
        isOpen: true,
        loading: true,
      },
    })

    expect(wrapper.text()).toContain('Inspecting container telemetry')
  })

  it('renders error state when error prop is provided', () => {
    const wrapper = mount(ContainerDetailDrawer, {
      props: {
        container: null,
        isOpen: true,
        error: 'Container was not found.',
      },
    })

    expect(wrapper.text()).toContain('Inspection Error')
    expect(wrapper.text()).toContain('Container was not found.')
  })
})

describe('DockerView.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(dockerApi.getStatus).mockResolvedValue(MOCK_STATUS_RESPONSE)
    vi.mocked(dockerApi.listContainers).mockResolvedValue(MOCK_CONTAINERS_RESPONSE)
    vi.mocked(dockerApi.getContainer).mockResolvedValue(MOCK_CONTAINER_DETAIL)
    vi.mocked(dockerApi.listImages).mockResolvedValue({ total: 0, items: [] })
    vi.mocked(dockerApi.listVolumes).mockResolvedValue({ total: 0, items: [] })
  })

  it('renders discovered containers and summary counts', async () => {
    const wrapper = mount(DockerView, {
      global: {
        plugins: [router],
        stubs: {
          DefaultLayout: { template: '<div><slot /></div>' },
          AppHeader: { template: '<div><slot /></div>' },
          DockerEngineStatus: { template: '<div class="docker-status">Status</div>' },
        },
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Container Discovery & Inspection')
    expect(wrapper.text()).toContain('dockscope-db')
    expect(wrapper.text()).toContain('dockscope-redis')
    expect(wrapper.text()).toContain('postgres:16-alpine')
    expect(wrapper.text()).toContain('redis:alpine')

    // Stats
    expect(wrapper.text()).toContain('Total Containers')
    expect(wrapper.text()).toContain('Running')
    expect(wrapper.text()).toContain('Stopped / Exited')
  })

  it('filters containers by search query', async () => {
    const wrapper = mount(DockerView, {
      global: {
        plugins: [router],
        stubs: {
          DefaultLayout: { template: '<div><slot /></div>' },
          AppHeader: { template: '<div><slot /></div>' },
          DockerEngineStatus: true,
        },
      },
    })

    await flushPromises()

    const searchInput = wrapper.find('input[placeholder*="Search by container name"]')
    expect(searchInput.exists()).toBe(true)

    await searchInput.setValue('postgres')
    expect(wrapper.text()).toContain('dockscope-db')
    expect(wrapper.text()).not.toContain('dockscope-redis')
  })

  it('filters containers by status tab', async () => {
    const wrapper = mount(DockerView, {
      global: {
        plugins: [router],
        stubs: {
          DefaultLayout: { template: '<div><slot /></div>' },
          AppHeader: { template: '<div><slot /></div>' },
          DockerEngineStatus: true,
        },
      },
    })

    await flushPromises()

    // Click 'Running' filter tab
    const buttons = wrapper.findAll('button')
    const runningBtn = buttons.find((b) => b.text() === 'Running')
    expect(runningBtn).toBeDefined()
    await runningBtn!.trigger('click')

    expect(wrapper.text()).toContain('dockscope-db')
    expect(wrapper.text()).not.toContain('dockscope-redis')
  })

  it('handles Docker daemon connection error gracefully', async () => {
    vi.mocked(dockerApi.listContainers).mockRejectedValueOnce(
      new Error('Docker daemon is unreachable. Ensure Docker Engine is running.')
    )

    const wrapper = mount(DockerView, {
      global: {
        plugins: [router],
        stubs: {
          DefaultLayout: { template: '<div><slot /></div>' },
          AppHeader: { template: '<div><slot /></div>' },
          DockerEngineStatus: true,
        },
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Docker Daemon Unavailable')
    expect(wrapper.text()).toContain('Retry Connection')
  })

  it('opens inspection drawer when Inspect button is clicked', async () => {
    const wrapper = mount(DockerView, {
      global: {
        plugins: [router],
        stubs: {
          DefaultLayout: { template: '<div><slot /></div>' },
          AppHeader: { template: '<div><slot /></div>' },
          DockerEngineStatus: true,
        },
      },
    })

    await flushPromises()

    const inspectBtns = wrapper.findAll('button').filter((b) => b.text().includes('Inspect'))
    expect(inspectBtns.length).toBeGreaterThan(0)
    await inspectBtns[0].trigger('click')

    expect(dockerApi.getContainer).toHaveBeenCalledWith(MOCK_CONTAINERS_RESPONSE.items[0].id)
  })

  it('correctly calculates counts and displays subtext for all 5 container states', async () => {
    const fiveStateContainers: ContainerListResponse = {
      total: 5,
      items: [
        {
          id: 'c1',
          short_id: 'c1',
          name: 'app-running',
          image: 'nginx:alpine',
          status: 'Up 2 hours',
          state: 'running',
          created_at: '2026-11-23T10:00:00Z',
          ports: [],
          labels: {},
        },
        {
          id: 'c2',
          short_id: 'c2',
          name: 'app-exited',
          image: 'alpine:latest',
          status: 'Exited (0)',
          state: 'exited',
          created_at: '2026-11-23T09:00:00Z',
          ports: [],
          labels: {},
        },
        {
          id: 'c3',
          short_id: 'c3',
          name: 'app-paused',
          image: 'redis:alpine',
          status: 'Up (Paused)',
          state: 'paused',
          created_at: '2026-11-23T08:00:00Z',
          ports: [],
          labels: {},
        },
        {
          id: 'c4',
          short_id: 'c4',
          name: 'app-restarting',
          image: 'busybox:latest',
          status: 'Restarting',
          state: 'restarting',
          created_at: '2026-11-23T07:00:00Z',
          ports: [],
          labels: {},
        },
        {
          id: 'c5',
          short_id: 'c5',
          name: 'app-created',
          image: 'postgres:alpine',
          status: 'Created',
          state: 'created',
          created_at: '2026-11-23T06:00:00Z',
          ports: [],
          labels: {},
        },
      ],
    }

    vi.mocked(dockerApi.listContainers).mockResolvedValueOnce(fiveStateContainers)

    const wrapper = mount(DockerView, {
      global: {
        plugins: [router],
        stubs: {
          DefaultLayout: { template: '<div><slot /></div>' },
          AppHeader: { template: '<div><slot /></div>' },
          DockerEngineStatus: true,
        },
      },
    })

    await flushPromises()

    // Total: 5
    expect(wrapper.text()).toContain('Total Containers')
    // Running: 1 running, 1 restarting
    expect(wrapper.text()).toContain('1 restarting')
    // Stopped/Exited: 1 exited, 1 created -> 2 stopped
    expect(wrapper.text()).toContain('1 exited, 1 created')
    // Paused: 1
    expect(wrapper.text()).toContain('Paused')

    // Test filter 'Stopped' includes exited and created, excludes running, paused, restarting
    const buttons = wrapper.findAll('button')
    const stoppedBtn = buttons.find((b) => b.text() === 'Stopped')
    expect(stoppedBtn).toBeDefined()
    await stoppedBtn!.trigger('click')

    expect(wrapper.text()).toContain('app-exited')
    expect(wrapper.text()).toContain('app-created')
    expect(wrapper.text()).not.toContain('app-running')
    expect(wrapper.text()).not.toContain('app-paused')
    expect(wrapper.text()).not.toContain('app-restarting')
  })
})
