import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from '@/App.vue'
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import DockerView from '@/views/DockerView.vue'
import { useAuthStore } from '@/stores/auth'
import { authApi, dockerApi, healthApi } from '@/services/api'

vi.mock('@/services/api', () => ({
  authApi: {
    getMe: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
  },
  healthApi: {
    checkHealth: vi.fn().mockResolvedValue({ status: 'healthy', version: '0.1.0' }),
    checkReady: vi.fn().mockResolvedValue({ status: 'ready', database: 'connected' }),
  },
  dockerApi: {
    getStatus: vi.fn().mockResolvedValue({
      status: 'connected',
      endpoint: 'npipe:////./pipe/docker_engine',
      checked_at: '2026-11-23T10:00:00Z',
      details: { version: '29.9.3', api_version: '1.56', containers_total: 4, containers_running: 2, containers_stopped: 2, containers_paused: 0 },
    }),
    listContainers: vi.fn().mockResolvedValue({
      total: 2,
      items: [
        { id: 'c1', short_id: 'c1short', name: 'dockscope-db', image: 'postgres:16-alpine', state: 'running', status: 'Up 2 hours', ports: [], labels: {} },
        { id: 'c2', short_id: 'c2short', name: 'dockscope-redis', image: 'redis:alpine', state: 'exited', status: 'Exited (0)', ports: [], labels: {} },
      ],
    }),
    getContainer: vi.fn().mockResolvedValue({
      id: 'c1', short_id: 'c1short', name: 'dockscope-db', image: 'postgres:16-alpine', state: 'running', status: 'Up', restart_count: 0, networks: [], mounts: [], ports: [], labels: {},
    }),
    listImages: vi.fn().mockResolvedValue({ total: 0, items: [] }),
    listVolumes: vi.fn().mockResolvedValue({ total: 0, items: [] }),
  },
}))

describe('DockScope End-to-End Navigation Flow', () => {
  let router: any

  beforeEach(() => {
    vi.clearAllMocks()
    const pinia = createPinia()
    setActivePinia(pinia)

    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', redirect: '/dashboard' },
        { path: '/login', name: 'login', component: LoginView, meta: { guestOnly: true } },
        { path: '/register', name: 'register', component: { template: '<div>Register</div>' }, meta: { guestOnly: true } },
        { path: '/dashboard', name: 'dashboard', component: DashboardView, meta: { requiresAuth: true } },
        { path: '/docker', name: 'docker', component: DockerView, meta: { requiresAuth: true } },
        { path: '/hosts', name: 'hosts', component: { template: '<div>Hosts</div>' }, meta: { requiresAuth: true } },
        { path: '/security', name: 'security', component: { template: '<div>Security</div>' }, meta: { requiresAuth: true } },
        { path: '/settings', name: 'settings', component: { template: '<div>Settings</div>' }, meta: { requiresAuth: true } },
      ],
    })

    router.beforeEach(async (to: any, from: any, next: any) => {
      const authStore = useAuthStore()
      if (!authStore.isInitialized) {
        await authStore.initAuth()
      }
      if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        next({ name: 'login', query: { redirect: to.fullPath } })
      } else if (to.meta.guestOnly && authStore.isAuthenticated) {
        next({ name: 'dashboard' })
      } else {
        next()
      }
    })
  })

  it('unauthenticated navigation to / redirects to /login and renders Login UI visibly', async () => {
    vi.mocked(authApi.getMe).mockRejectedValueOnce(new Error('Unauthorized'))

    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), router],
      },
    })

    router.push('/')
    await router.isReady()
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('login')
    expect(wrapper.text()).toContain('DockScope')
    expect(wrapper.text()).toContain('Sign In')
    expect(wrapper.find('input[type="email"]').exists()).toBe(true)
    expect(wrapper.find('input[type="password"]').exists()).toBe(true)
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true)
  })

  it('authenticated user renders Dashboard with metrics, connection status, and infrastructure feed', async () => {
    const mockUser = { id: 'u1', email: 'admin@dockscope.io', is_active: true, created_at: '', updated_at: '' }
    vi.mocked(authApi.getMe).mockResolvedValueOnce(mockUser)

    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), router],
      },
    })

    router.push('/dashboard')
    await router.isReady()
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('dashboard')
    expect(wrapper.text()).toContain('Infrastructure Dashboard')
    expect(wrapper.text()).toContain('Docker Engine Connection')
    expect(wrapper.text()).toContain('Connected')
    expect(wrapper.text()).toContain('Total Hosts')
    expect(wrapper.text()).toContain('Containers')
    expect(wrapper.text()).toContain('CPU Usage')
  })

  it('navigates from Dashboard to Docker view and renders discovered containers', async () => {
    const mockUser = { id: 'u1', email: 'admin@dockscope.io', is_active: true, created_at: '', updated_at: '' }
    vi.mocked(authApi.getMe).mockResolvedValueOnce(mockUser)

    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), router],
      },
    })

    router.push('/dashboard')
    await router.isReady()
    await flushPromises()

    router.push('/docker')
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('docker')
    expect(wrapper.text()).toContain('Container Discovery & Inspection')
    expect(wrapper.text()).toContain('dockscope-db')
    expect(wrapper.text()).toContain('dockscope-redis')
  })

  it('handles backend timeout gracefully without locking into blank screen', async () => {
    // When authApi.getMe rejects with an error or timeout
    vi.mocked(authApi.getMe).mockRejectedValueOnce(new Error('Session verification timed out'))

    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), router],
      },
    })

    router.push('/')
    await router.isReady()
    await flushPromises()

    // Gracefully settles on login view instead of blank screen
    expect(router.currentRoute.value.name).toBe('login')
    expect(wrapper.text()).toContain('Sign In')
  })
})
