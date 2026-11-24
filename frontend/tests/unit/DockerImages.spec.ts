import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import ImageDetailDrawer from '@/components/docker/ImageDetailDrawer.vue'
import DockerView from '@/views/DockerView.vue'
import { dockerApi } from '@/services/api'
import type { ImageListResponse, ImageDetail, DockerStatusResponse } from '@/types'

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

const MOCK_IMAGES_RESPONSE: ImageListResponse = {
  total: 2,
  items: [
    {
      id: 'sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
      short_id: '1234567890ab',
      repo_tags: ['postgres:16-alpine', 'postgres:latest'],
      repositories: ['postgres'],
      tags: ['16-alpine', 'latest'],
      size_bytes: 379000000,
      virtual_size_bytes: 379000000,
      created_at: '2026-11-20T10:00:00Z',
      containers_count: 1,
      is_dangling: false,
      labels: { maintainer: 'PostgreSQL' },
    },
    {
      id: 'sha256:fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321',
      short_id: 'fedcba098765',
      repo_tags: [],
      repositories: [],
      tags: [],
      size_bytes: 52000000,
      virtual_size_bytes: 52000000,
      created_at: '2026-11-21T11:00:00Z',
      containers_count: 0,
      is_dangling: true,
      labels: {},
    },
  ],
}

const MOCK_IMAGE_DETAIL: ImageDetail = {
  id: 'sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
  short_id: '1234567890ab',
  repo_tags: ['postgres:16-alpine', 'postgres:latest'],
  repositories: ['postgres'],
  tags: ['16-alpine', 'latest'],
  size_bytes: 379000000,
  virtual_size_bytes: 379000000,
  created_at: '2026-11-20T10:00:00Z',
  containers_count: 1,
  is_dangling: false,
  labels: { maintainer: 'PostgreSQL' },
  architecture: 'amd64',
  os: 'linux',
  author: 'DockScope Team',
  comment: 'Official build',
  docker_version: '24.0.7',
  root_fs_layers: [
    'sha256:layer11111111111111111111111111111111111111111111111111111111111',
    'sha256:layer22222222222222222222222222222222222222222222222222222222222',
  ],
  containers: [
    {
      id: 'c111111111111111111111111111111111111111111111111111111111111111',
      short_id: 'c11111111111',
      name: 'dockscope-db',
      state: 'running',
      status: 'Up 2 hours',
    },
  ],
}

describe('ImageDetailDrawer.vue', () => {
  it('renders image details and correlated containers correctly', () => {
    const wrapper = mount(ImageDetailDrawer, {
      props: {
        image: MOCK_IMAGE_DETAIL,
        isOpen: true,
        isLoading: false,
        error: null,
      },
    })

    expect(wrapper.text()).toContain('DockScope Read-Only Inspection')
    expect(wrapper.text()).toContain('postgres:16-alpine')
    expect(wrapper.text()).toContain('amd64')
    expect(wrapper.text()).toContain('linux')
    expect(wrapper.text()).toContain('Filesystem Layer Hashes')
    expect(wrapper.text()).toContain('Referencing Containers')
    expect(wrapper.text()).toContain('dockscope-db')
    expect(wrapper.text()).toContain('maintainer')
    expect(wrapper.text()).toContain('PostgreSQL')
  })

  it('renders dangling image indicator when image has no repo tags', () => {
    const danglingDetail: ImageDetail = {
      ...MOCK_IMAGE_DETAIL,
      repo_tags: [],
      repositories: [],
      tags: [],
      is_dangling: true,
      containers_count: 0,
      containers: [],
    }

    const wrapper = mount(ImageDetailDrawer, {
      props: {
        image: danglingDetail,
        isOpen: true,
        isLoading: false,
        error: null,
      },
    })

    expect(wrapper.text()).toContain('Dangling')
    expect(wrapper.text()).toContain('dangling image')
    expect(wrapper.text()).toContain('No running or stopped containers currently use this image.')
  })

  it('renders error state safely', () => {
    const wrapper = mount(ImageDetailDrawer, {
      props: {
        image: null,
        isOpen: true,
        isLoading: false,
        error: 'Image not found.',
      },
    })

    expect(wrapper.text()).toContain('Image Inspection Error')
    expect(wrapper.text()).toContain('Image not found.')
  })
})

describe('DockerView.vue - Images Tab', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(dockerApi.getStatus).mockResolvedValue(MOCK_STATUS_RESPONSE)
    vi.mocked(dockerApi.listContainers).mockResolvedValue({ total: 0, items: [] })
    vi.mocked(dockerApi.listImages).mockResolvedValue(MOCK_IMAGES_RESPONSE)
    vi.mocked(dockerApi.getImage).mockResolvedValue(MOCK_IMAGE_DETAIL)
    vi.mocked(dockerApi.listVolumes).mockResolvedValue({ total: 0, items: [] })
  })

  it('switches to Images tab and renders image summary and table', async () => {
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

    // Click on Images Tab
    const imagesTabBtn = wrapper.findAll('button').find((b) => b.text().includes('Images'))
    expect(imagesTabBtn).toBeDefined()
    await imagesTabBtn!.trigger('click')
    await flushPromises()

    // Check Images Summary Cards
    expect(wrapper.text()).toContain('Total Images')
    expect(wrapper.text()).toContain('In Use')
    expect(wrapper.text()).toContain('Dangling')
    expect(wrapper.text()).toContain('Total Size')

    // Check Images Table Content
    expect(wrapper.text()).toContain('postgres:16-alpine')
    expect(wrapper.text()).toContain('1234567890ab')
    expect(wrapper.text()).toContain('fedcba098765')
    expect(wrapper.text()).toContain('dangling')
  })

  it('filters images by search term', async () => {
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

    // Switch to Images Tab
    const imagesTabBtn = wrapper.findAll('button').find((b) => b.text().includes('Images'))
    await imagesTabBtn!.trigger('click')
    await flushPromises()

    // Type in search box
    const searchInput = wrapper.find('input[placeholder*="Search images"]')
    expect(searchInput.exists()).toBe(true)
    await searchInput.setValue('postgres')

    expect(wrapper.text()).toContain('postgres')
    expect(wrapper.text()).not.toContain('fedcba098765')
  })

  it('opens ImageDetailDrawer when image inspect button is clicked', async () => {
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

    // Switch to Images Tab
    const imagesTabBtn = wrapper.findAll('button').find((b) => b.text().includes('Images'))
    await imagesTabBtn!.trigger('click')
    await flushPromises()

    // Find and click the inspect button for the first image
    const inspectBtn = wrapper.find('button[title*="Inspect image"]')
    expect(inspectBtn.exists()).toBe(true)
    await inspectBtn.trigger('click')
    await flushPromises()

    expect(dockerApi.getImage).toHaveBeenCalledWith(MOCK_IMAGES_RESPONSE.items[0].id)
    expect(wrapper.text()).toContain('DockScope Read-Only Inspection')
  })
})
