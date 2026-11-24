import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import VolumeDetailDrawer from '@/components/docker/VolumeDetailDrawer.vue'
import DockerView from '@/views/DockerView.vue'
import { dockerApi } from '@/services/api'
import type { VolumeListResponse, VolumeDetail, DockerStatusResponse } from '@/types'

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

const MOCK_STATUS_RESPONSE: DockerStatusResponse = {
  status: 'connected',
  endpoint: 'npipe:////./pipe/docker_engine',
  checked_at: '2026-11-23T10:00:00Z',
  details: {
    version: '29.9.3',
    api_version: '1.56',
    containers_total: 2,
    containers_running: 1,
    containers_stopped: 1,
    containers_paused: 0,
    images_total: 3,
  },
}

const MOCK_VOLUMES_RESPONSE: VolumeListResponse = {
  total: 2,
  items: [
    {
      name: 'dockscope_postgres_data',
      driver: 'local',
      scope: 'local',
      created_at: '2026-11-20T08:00:00Z',
      containers_count: 1,
      is_in_use: true,
      labels: { 'com.docker.compose.project': 'dockscope' },
    },
    {
      name: 'unused_cache_volume',
      driver: 'local',
      scope: 'local',
      created_at: '2026-11-21T09:00:00Z',
      containers_count: 0,
      is_in_use: false,
      labels: {},
    },
  ],
}

const MOCK_VOLUME_DETAIL: VolumeDetail = {
  name: 'dockscope_postgres_data',
  driver: 'local',
  scope: 'local',
  created_at: '2026-11-20T08:00:00Z',
  containers_count: 1,
  is_in_use: true,
  labels: { 'com.docker.compose.project': 'dockscope' },
  mountpoint: '/var/lib/docker/volumes/dockscope_postgres_data/_data',
  options: { device: '/dev/sda1' },
  containers: [
    {
      id: 'c111111111111111111111111111111111111111111111111111111111111111',
      short_id: 'c11111111111',
      name: 'dockscope-db',
      state: 'running',
      destination: '/var/lib/postgresql/data',
      mode: 'rw',
      read_only: false,
    },
  ],
}

describe('VolumeDetailDrawer.vue', () => {
  it('renders volume details and mounted containers correctly', () => {
    const wrapper = mount(VolumeDetailDrawer, {
      props: {
        volume: MOCK_VOLUME_DETAIL,
        isOpen: true,
        isLoading: false,
        error: null,
      },
    })

    expect(wrapper.text()).toContain('DockScope Read-Only Inspection')
    expect(wrapper.text()).toContain('dockscope_postgres_data')
    expect(wrapper.text()).toContain('/var/lib/docker/volumes/dockscope_postgres_data/_data')
    expect(wrapper.text()).toContain('dockscope-db')
    expect(wrapper.text()).toContain('/var/lib/postgresql/data')
    expect(wrapper.text()).toContain('device')
    expect(wrapper.text()).toContain('/dev/sda1')
  })

  it('renders unused volume indicator when no containers mount the volume', () => {
    const unusedVolume: VolumeDetail = {
      ...MOCK_VOLUME_DETAIL,
      name: 'unused_cache_volume',
      containers_count: 0,
      is_in_use: false,
      containers: [],
    }

    const wrapper = mount(VolumeDetailDrawer, {
      props: {
        volume: unusedVolume,
        isOpen: true,
        isLoading: false,
        error: null,
      },
    })

    expect(wrapper.text()).toContain('Unused')
    expect(wrapper.text()).toContain('No active or stopped containers are currently mounting this volume.')
  })

  it('renders error state safely', () => {
    const wrapper = mount(VolumeDetailDrawer, {
      props: {
        volume: null,
        isOpen: true,
        isLoading: false,
        error: 'Volume not found.',
      },
    })

    expect(wrapper.text()).toContain('Volume Inspection Error')
    expect(wrapper.text()).toContain('Volume not found.')
  })
})

describe('DockerView.vue - Volumes Tab', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(dockerApi.getStatus).mockResolvedValue(MOCK_STATUS_RESPONSE)
    vi.mocked(dockerApi.listContainers).mockResolvedValue({ total: 0, items: [] })
    vi.mocked(dockerApi.listImages).mockResolvedValue({ total: 0, items: [] })
    vi.mocked(dockerApi.listVolumes).mockResolvedValue(MOCK_VOLUMES_RESPONSE)
    vi.mocked(dockerApi.getVolume).mockResolvedValue(MOCK_VOLUME_DETAIL)
  })

  it('switches to Volumes tab and renders volume summary and table', async () => {
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

    // Click on Volumes Tab
    const volumesTabBtn = wrapper.findAll('button').find((b) => b.text().includes('Volumes'))
    expect(volumesTabBtn).toBeDefined()
    await volumesTabBtn!.trigger('click')
    await flushPromises()

    // Check Volumes Summary Cards
    expect(wrapper.text()).toContain('Total Volumes')
    expect(wrapper.text()).toContain('Mounted (In-Use)')
    expect(wrapper.text()).toContain('Local Driver')
    expect(wrapper.text()).toContain('Storage Drivers')

    // Check Volumes Table Content
    expect(wrapper.text()).toContain('dockscope_postgres_data')
    expect(wrapper.text()).toContain('unused_cache_volume')
    expect(wrapper.text()).toContain('local')
  })

  it('filters volumes by search query', async () => {
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

    // Switch to Volumes Tab
    const volumesTabBtn = wrapper.findAll('button').find((b) => b.text().includes('Volumes'))
    await volumesTabBtn!.trigger('click')
    await flushPromises()

    // Type in search box
    const searchInput = wrapper.find('input[placeholder*="Search volumes"]')
    expect(searchInput.exists()).toBe(true)
    await searchInput.setValue('postgres')

    expect(wrapper.text()).toContain('dockscope_postgres_data')
    expect(wrapper.text()).not.toContain('unused_cache_volume')
  })

  it('opens VolumeDetailDrawer when volume inspect button is clicked', async () => {
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

    // Switch to Volumes Tab
    const volumesTabBtn = wrapper.findAll('button').find((b) => b.text().includes('Volumes'))
    await volumesTabBtn!.trigger('click')
    await flushPromises()

    // Find and click the first volume inspect button
    const inspectBtn = wrapper.find('button[title*="Inspect volume"]')
    expect(inspectBtn.exists()).toBe(true)
    await inspectBtn.trigger('click')
    await flushPromises()

    expect(dockerApi.getVolume).toHaveBeenCalledWith(MOCK_VOLUMES_RESPONSE.items[0].name)
    expect(wrapper.text()).toContain('DockScope Read-Only Inspection')
  })
})
