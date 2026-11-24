<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  Boxes,
  Play,
  Square,
  Pause,
  Search,
  RefreshCw,
  Eye,
  Activity,
  Layers,
  Terminal,
  AlertCircle,
  HelpCircle,
  SlidersHorizontal,
  HardDrive,
  FolderGit2,
  Tag,
  CheckCircle2,
  Clock,
  Database,
  Filter,
} from 'lucide-vue-next'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseBadge from '@/components/common/BaseBadge.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import DockerEngineStatus from '@/components/dashboard/DockerEngineStatus.vue'
import ContainerDetailDrawer from '@/components/docker/ContainerDetailDrawer.vue'
import ImageDetailDrawer from '@/components/docker/ImageDetailDrawer.vue'
import VolumeDetailDrawer from '@/components/docker/VolumeDetailDrawer.vue'
import { dockerApi } from '@/services/api'
import type {
  ContainerSummary,
  ContainerDetail,
  ImageSummary,
  ImageDetail,
  VolumeSummary,
  VolumeDetail,
} from '@/types'
import { formatBytes, formatTimestamp } from '@/utils/formatters'

// Tab state
const activeTab = ref<'containers' | 'images' | 'volumes'>('containers')
const engineStatusRef = ref<InstanceType<typeof DockerEngineStatus> | null>(null)

// -------------------------------------------------------------
// Containers State
// -------------------------------------------------------------
const containers = ref<ContainerSummary[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const statusFilter = ref<string>('all')
const searchQuery = ref<string>('')

// Container Drawer
const selectedContainer = ref<ContainerDetail | null>(null)
const isDrawerOpen = ref(false)
const drawerLoading = ref(false)
const drawerError = ref<string | null>(null)

// Container Statistics
const stats = computed(() => {
  const total = containers.value.length
  let running = 0
  let stopped = 0
  let paused = 0
  let restarting = 0
  let created = 0
  let exited = 0

  for (const c of containers.value) {
    const s = (c.state || '').toLowerCase()
    if (s === 'running') running++
    else if (s === 'paused') paused++
    else if (s === 'restarting') restarting++
    else if (s === 'created') {
      created++
      stopped++
    } else {
      exited++
      stopped++
    }
  }

  return { total, running, stopped, paused, restarting, created, exited }
})

// Filtered Containers
const filteredContainers = computed(() => {
  return containers.value.filter((c) => {
    if (statusFilter.value !== 'all') {
      const s = (c.state || '').toLowerCase()
      if (statusFilter.value === 'running' && s !== 'running') return false
      if (statusFilter.value === 'paused' && s !== 'paused') return false
      if (statusFilter.value === 'stopped' && (s === 'running' || s === 'paused' || s === 'restarting')) return false
      if (statusFilter.value === 'restarting' && s !== 'restarting') return false
      if (statusFilter.value === 'created' && s !== 'created') return false
    }

    if (searchQuery.value.trim()) {
      const q = searchQuery.value.trim().toLowerCase()
      const matchName = c.name.toLowerCase().includes(q)
      const matchImage = c.image.toLowerCase().includes(q)
      const matchId = c.short_id.toLowerCase().includes(q) || c.id.toLowerCase().includes(q)
      if (!matchName && !matchImage && !matchId) return false
    }

    return true
  })
})

async function fetchContainers() {
  loading.value = true
  error.value = null
  try {
    const res = await dockerApi.listContainers()
    containers.value = res.items
  } catch (err: unknown) {
    containers.value = []
    error.value = err instanceof Error ? err.message : 'Failed to retrieve containers from Docker Engine.'
  } finally {
    loading.value = false
  }
}

async function inspectContainer(containerId: string) {
  isDrawerOpen.value = true
  drawerLoading.value = true
  drawerError.value = null
  selectedContainer.value = null

  try {
    const detail = await dockerApi.getContainer(containerId)
    selectedContainer.value = detail
  } catch (err: unknown) {
    drawerError.value = err instanceof Error ? err.message : `Failed to inspect container ${containerId}`
  } finally {
    drawerLoading.value = false
  }
}

function closeDrawer() {
  isDrawerOpen.value = false
  selectedContainer.value = null
  drawerError.value = null
}

// -------------------------------------------------------------
// Images State (M02.4)
// -------------------------------------------------------------
const images = ref<ImageSummary[]>([])
const imagesLoading = ref(false)
const imagesError = ref<string | null>(null)
const imageSearchQuery = ref('')
const imageDanglingFilter = ref<'all' | 'tagged' | 'dangling'>('all')

const selectedImage = ref<ImageDetail | null>(null)
const isImageDrawerOpen = ref(false)
const imageDrawerLoading = ref(false)
const imageDrawerError = ref<string | null>(null)

const imageStats = computed(() => {
  const total = images.value.length
  let dangling = 0
  let inUse = 0
  let totalBytes = 0

  for (const img of images.value) {
    if (img.is_dangling) dangling++
    if (img.containers_count > 0) inUse++
    totalBytes += img.size_bytes || 0
  }

  return { total, dangling, inUse, totalBytes }
})

const filteredImages = computed(() => {
  return images.value.filter((img) => {
    if (imageDanglingFilter.value === 'dangling' && !img.is_dangling) return false
    if (imageDanglingFilter.value === 'tagged' && img.is_dangling) return false

    if (imageSearchQuery.value.trim()) {
      const q = imageSearchQuery.value.trim().toLowerCase()
      const matchId = img.id.toLowerCase().includes(q) || img.short_id.toLowerCase().includes(q)
      const matchTag = img.repo_tags.some((t) => t.toLowerCase().includes(q))
      const matchRepo = img.repositories.some((r) => r.toLowerCase().includes(q))
      if (!matchId && !matchTag && !matchRepo) return false
    }

    return true
  })
})

async function fetchImages() {
  imagesLoading.value = true
  imagesError.value = null
  try {
    const res = await dockerApi.listImages()
    images.value = res.items
  } catch (err: unknown) {
    images.value = []
    imagesError.value = err instanceof Error ? err.message : 'Failed to retrieve Docker images.'
  } finally {
    imagesLoading.value = false
  }
}

async function inspectImage(imageId: string) {
  isImageDrawerOpen.value = true
  imageDrawerLoading.value = true
  imageDrawerError.value = null
  selectedImage.value = null

  try {
    const detail = await dockerApi.getImage(imageId)
    selectedImage.value = detail
  } catch (err: unknown) {
    imageDrawerError.value = err instanceof Error ? err.message : `Failed to inspect image ${imageId}`
  } finally {
    imageDrawerLoading.value = false
  }
}

function closeImageDrawer() {
  isImageDrawerOpen.value = false
  selectedImage.value = null
  imageDrawerError.value = null
}

// -------------------------------------------------------------
// Volumes State (M02.4)
// -------------------------------------------------------------
const volumes = ref<VolumeSummary[]>([])
const volumesLoading = ref(false)
const volumesError = ref<string | null>(null)
const volumeSearchQuery = ref('')
const volumeDriverFilter = ref('all')

const selectedVolume = ref<VolumeDetail | null>(null)
const isVolumeDrawerOpen = ref(false)
const volumeDrawerLoading = ref(false)
const volumeDrawerError = ref<string | null>(null)

const volumeStats = computed(() => {
  const total = volumes.value.length
  let inUse = 0
  let localDriver = 0
  const drivers = new Set<string>()

  for (const v of volumes.value) {
    if (v.is_in_use) inUse++
    if (v.driver === 'local') localDriver++
    if (v.driver) drivers.add(v.driver)
  }

  return { total, inUse, localDriver, driverCount: drivers.size }
})

const availableDrivers = computed(() => {
  const set = new Set<string>()
  for (const v of volumes.value) {
    if (v.driver) set.add(v.driver)
  }
  return Array.from(set)
})

const filteredVolumes = computed(() => {
  return volumes.value.filter((v) => {
    if (volumeDriverFilter.value !== 'all' && v.driver !== volumeDriverFilter.value) {
      return false
    }

    if (volumeSearchQuery.value.trim()) {
      const q = volumeSearchQuery.value.trim().toLowerCase()
      if (!v.name.toLowerCase().includes(q)) return false
    }

    return true
  })
})

async function fetchVolumes() {
  volumesLoading.value = true
  volumesError.value = null
  try {
    const res = await dockerApi.listVolumes()
    volumes.value = res.items
  } catch (err: unknown) {
    volumes.value = []
    volumesError.value = err instanceof Error ? err.message : 'Failed to retrieve Docker volumes.'
  } finally {
    volumesLoading.value = false
  }
}

async function inspectVolume(volumeName: string) {
  isVolumeDrawerOpen.value = true
  volumeDrawerLoading.value = true
  volumeDrawerError.value = null
  selectedVolume.value = null

  try {
    const detail = await dockerApi.getVolume(volumeName)
    selectedVolume.value = detail
  } catch (err: unknown) {
    volumeDrawerError.value = err instanceof Error ? err.message : `Failed to inspect volume ${volumeName}`
  } finally {
    volumeDrawerLoading.value = false
  }
}

function closeVolumeDrawer() {
  isVolumeDrawerOpen.value = false
  selectedVolume.value = null
  volumeDrawerError.value = null
}

// -------------------------------------------------------------
// Coordinated Lifecycle & Helpers
// -------------------------------------------------------------
async function refreshAll() {
  await Promise.allSettled([
    fetchContainers(),
    fetchImages(),
    fetchVolumes(),
    engineStatusRef.value?.fetchStatus?.(),
  ])
}

function getStateBadgeVariant(state: string): 'success' | 'warning' | 'danger' | 'info' | 'neutral' {
  switch (state.toLowerCase()) {
    case 'running':
      return 'success'
    case 'paused':
      return 'warning'
    case 'restarting':
      return 'info'
    case 'exited':
    case 'dead':
    default:
      return 'neutral'
  }
}

function formatCreatedAt(ts?: string | null): string {
  if (!ts) return '—'
  try {
    const d = new Date(ts)
    if (isNaN(d.getTime())) return ts
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return ts
  }
}

onMounted(() => {
  refreshAll()
})
</script>

<template>
  <DefaultLayout>
    <AppHeader
      title="Docker Workloads & Discovery"
      subtitle="Discover, inspect, and monitor containers, images, and volumes on the connected Docker Engine"
    />

    <div class="p-8 space-y-6">
      <!-- Milestone Header Banner -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 class="text-base font-semibold text-dock-text">Container Discovery & Inspection</h2>
          <p class="text-xs text-dock-muted">Real-time non-mutating inventory, resource telemetry, and storage intelligence</p>
        </div>
        <div class="flex items-center space-x-2">
          <BaseBadge variant="info" size="sm">Milestone 02.4: Images & Volumes Intelligence</BaseBadge>
          <BaseBadge variant="neutral" size="sm">Read-Only Safety</BaseBadge>
        </div>
      </div>

      <!-- Docker Engine Status Accordion/Banner -->
      <DockerEngineStatus
        ref="engineStatusRef"
        :containers-override="{ total: stats.total, running: stats.running }"
      />

      <!-- Navigation Tabs: Containers, Images, Volumes -->
      <div class="flex items-center space-x-1 border-b border-dock-border">
        <button
          @click="activeTab = 'containers'"
          class="px-4 py-2.5 text-xs font-semibold border-b-2 flex items-center space-x-2 transition-colors"
          :class="activeTab === 'containers'
            ? 'border-dock-primary text-dock-primary bg-dock-primary/5'
            : 'border-transparent text-dock-muted hover:text-dock-text'"
        >
          <Boxes class="w-4 h-4" />
          <span>Containers</span>
          <span class="px-1.5 py-0.5 rounded-full text-[10px] bg-dock-bg border border-dock-border text-dock-text font-mono">
            {{ containers.length }}
          </span>
        </button>

        <button
          @click="activeTab = 'images'"
          class="px-4 py-2.5 text-xs font-semibold border-b-2 flex items-center space-x-2 transition-colors"
          :class="activeTab === 'images'
            ? 'border-dock-primary text-dock-primary bg-dock-primary/5'
            : 'border-transparent text-dock-muted hover:text-dock-text'"
        >
          <Layers class="w-4 h-4" />
          <span>Images</span>
          <span class="px-1.5 py-0.5 rounded-full text-[10px] bg-dock-bg border border-dock-border text-dock-text font-mono">
            {{ images.length }}
          </span>
        </button>

        <button
          @click="activeTab = 'volumes'"
          class="px-4 py-2.5 text-xs font-semibold border-b-2 flex items-center space-x-2 transition-colors"
          :class="activeTab === 'volumes'
            ? 'border-dock-primary text-dock-primary bg-dock-primary/5'
            : 'border-transparent text-dock-muted hover:text-dock-text'"
        >
          <HardDrive class="w-4 h-4" />
          <span>Volumes</span>
          <span class="px-1.5 py-0.5 rounded-full text-[10px] bg-dock-bg border border-dock-border text-dock-text font-mono">
            {{ volumes.length }}
          </span>
        </button>
      </div>

      <!-- ======================================================= -->
      <!-- TAB 1: CONTAINERS VIEW                                  -->
      <!-- ======================================================= -->
      <div v-if="activeTab === 'containers'" class="space-y-6">
        <!-- Container Statistics Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="p-4 rounded-xl bg-dock-surface border border-dock-border flex items-center justify-between">
            <div>
              <span class="text-xs font-medium text-dock-muted uppercase tracking-wider block">Total Containers</span>
              <span class="text-2xl font-bold text-dock-text mt-1 block font-mono">{{ stats.total }}</span>
            </div>
            <div class="p-3 rounded-lg bg-dock-bg border border-dock-border text-dock-primary">
              <Boxes class="w-5 h-5" />
            </div>
          </div>

          <div class="p-4 rounded-xl bg-dock-surface border border-dock-border flex items-center justify-between">
            <div>
              <span class="text-xs font-medium text-dock-muted uppercase tracking-wider block">Running</span>
              <span class="text-2xl font-bold text-emerald-400 mt-1 block font-mono">{{ stats.running }}</span>
              <span v-if="stats.restarting > 0" class="text-[10px] text-dock-muted block mt-0.5">
                {{ stats.restarting }} restarting
              </span>
            </div>
            <div class="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Play class="w-5 h-5" />
            </div>
          </div>

          <div class="p-4 rounded-xl bg-dock-surface border border-dock-border flex items-center justify-between">
            <div>
              <span class="text-xs font-medium text-dock-muted uppercase tracking-wider block">Stopped / Exited</span>
              <span class="text-2xl font-bold text-dock-muted mt-1 block font-mono">{{ stats.stopped }}</span>
              <span v-if="stats.created > 0 || stats.exited > 0" class="text-[10px] text-dock-muted block mt-0.5">
                {{ stats.exited }} exited{{ stats.created > 0 ? `, ${stats.created} created` : '' }}
              </span>
            </div>
            <div class="p-3 rounded-lg bg-dock-bg border border-dock-border text-dock-muted">
              <Square class="w-5 h-5" />
            </div>
          </div>

          <div class="p-4 rounded-xl bg-dock-surface border border-dock-border flex items-center justify-between">
            <div>
              <span class="text-xs font-medium text-dock-muted uppercase tracking-wider block">Paused</span>
              <span class="text-2xl font-bold text-amber-400 mt-1 block font-mono">{{ stats.paused }}</span>
            </div>
            <div class="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <Pause class="w-5 h-5" />
            </div>
          </div>
        </div>

        <!-- Main Containers Card -->
        <BaseCard
          title="Discovered Containers"
          subtitle="Active and stopped containers reported by Docker Engine"
        >
          <template #header-actions>
            <div class="flex items-center space-x-2">
              <BaseButton
                size="sm"
                variant="outline"
                :loading="loading"
                @click="refreshAll"
              >
                <template #icon>
                  <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': loading }" />
                </template>
                Refresh
              </BaseButton>
            </div>
          </template>

          <!-- Filters & Search Toolbar -->
          <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pb-5 border-b border-dock-border">
            <!-- Search Bar -->
            <div class="relative flex-1 max-w-md">
              <Search class="w-4 h-4 text-dock-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search by container name, image, or ID..."
                class="w-full pl-9 pr-3 py-1.5 text-xs bg-dock-bg border border-dock-border rounded-lg text-dock-text placeholder:text-dock-muted focus:outline-none focus:border-dock-primary transition-colors"
              />
            </div>

            <!-- Status Filter Tabs -->
            <div class="flex items-center space-x-1 bg-dock-bg p-1 rounded-lg border border-dock-border self-start sm:self-auto">
              <button
                v-for="filter in [
                  { label: 'All', value: 'all' },
                  { label: 'Running', value: 'running' },
                  { label: 'Stopped', value: 'stopped' },
                  { label: 'Paused', value: 'paused' },
                ]"
                :key="filter.value"
                @click="statusFilter = filter.value"
                class="px-2.5 py-1 text-xs rounded font-medium transition-colors"
                :class="statusFilter === filter.value
                  ? 'bg-dock-surface text-dock-primary border border-dock-border shadow-sm'
                  : 'text-dock-muted hover:text-dock-text'"
              >
                {{ filter.label }}
              </button>
            </div>
          </div>

          <!-- Daemon Unreachable / Error Alert -->
          <div v-if="error" class="p-6 rounded-xl bg-rose-500/10 border border-rose-500/20 text-center my-4">
            <AlertCircle class="w-8 h-8 text-rose-400 mx-auto mb-2" />
            <h4 class="text-sm font-semibold text-rose-300">Docker Daemon Unavailable</h4>
            <p class="text-xs text-rose-400/80 mt-1 max-w-md mx-auto">{{ error }}</p>
            <div class="mt-4">
              <BaseButton size="sm" variant="outline" @click="fetchContainers">
                Retry Connection
              </BaseButton>
            </div>
          </div>

          <!-- Loading State -->
          <div v-else-if="loading && containers.length === 0" class="py-16 text-center">
            <RefreshCw class="w-8 h-8 text-dock-primary animate-spin mx-auto mb-3" />
            <p class="text-sm text-dock-muted">Discovering containers on Docker Engine...</p>
          </div>

          <!-- Empty State -->
          <div v-else-if="filteredContainers.length === 0" class="py-16 text-center">
            <Boxes class="w-10 h-10 text-dock-muted mx-auto mb-3 opacity-50" />
            <h4 class="text-sm font-semibold text-dock-text">No Containers Found</h4>
            <p class="text-xs text-dock-muted mt-1 max-w-xs mx-auto">
              {{ searchQuery || statusFilter !== 'all'
                ? 'No containers match the selected filters or search query.'
                : 'There are no active or stopped containers on this Docker host.' }}
            </p>
            <div v-if="searchQuery || statusFilter !== 'all'" class="mt-4">
              <button
                @click="searchQuery = ''; statusFilter = 'all'"
                class="text-xs text-dock-primary hover:underline"
              >
                Clear filters
              </button>
            </div>
          </div>

          <!-- Containers Table -->
          <div v-else class="overflow-x-auto -mx-6 -mb-6 mt-4">
            <table class="w-full text-left text-xs">
              <thead class="bg-dock-bg text-dock-muted uppercase font-mono text-[10px] border-b border-dock-border">
                <tr>
                  <th class="py-3 px-6">Name / ID</th>
                  <th class="py-3 px-4">Image</th>
                  <th class="py-3 px-4">State & Status</th>
                  <th class="py-3 px-4">Port Bindings</th>
                  <th class="py-3 px-4">Created</th>
                  <th class="py-3 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-dock-border">
                <tr
                  v-for="container in filteredContainers"
                  :key="container.id"
                  class="hover:bg-dock-bg/40 transition-colors group"
                >
                  <!-- Container Name & Short ID -->
                  <td class="py-3.5 px-6">
                    <div class="flex items-center space-x-2">
                      <span class="font-semibold text-dock-text text-xs tracking-tight">
                        {{ container.name }}
                      </span>
                    </div>
                    <span class="font-mono text-[11px] text-dock-muted block mt-0.5">
                      {{ container.short_id }}
                    </span>
                  </td>

                  <!-- Image -->
                  <td class="py-3.5 px-4 font-mono text-[11px] text-dock-text max-w-xs truncate" :title="container.image">
                    {{ container.image }}
                  </td>

                  <!-- State Badge & Status -->
                  <td class="py-3.5 px-4">
                    <div class="flex items-center space-x-2">
                      <BaseBadge :variant="getStateBadgeVariant(container.state)" size="sm" dot>
                        {{ container.state }}
                      </BaseBadge>
                    </div>
                    <span class="text-[11px] text-dock-muted block mt-1 truncate max-w-xs" :title="container.status">
                      {{ container.status }}
                    </span>
                  </td>

                  <!-- Port Bindings -->
                  <td class="py-3.5 px-4">
                    <div v-if="container.ports.length === 0" class="text-dock-muted italic text-[11px]">
                      None
                    </div>
                    <div v-else class="flex flex-wrap gap-1 max-w-xs">
                      <span
                        v-for="(p, pIdx) in container.ports.slice(0, 3)"
                        :key="pIdx"
                        class="px-1.5 py-0.5 rounded text-[10px] font-mono border border-dock-border bg-dock-bg"
                        :class="p.host_port ? 'text-emerald-400 border-emerald-500/20' : 'text-dock-muted'"
                      >
                        <template v-if="p.host_port">
                          {{ p.host_port }}:{{ p.container_port }}
                        </template>
                        <template v-else>
                          {{ p.container_port }}/{{ p.protocol }}
                        </template>
                      </span>
                      <span
                        v-if="container.ports.length > 3"
                        class="px-1 py-0.5 text-[10px] text-dock-muted font-mono"
                      >
                        +{{ container.ports.length - 3 }} more
                      </span>
                    </div>
                  </td>

                  <!-- Created Timestamp -->
                  <td class="py-3.5 px-4 text-dock-muted text-[11px] font-mono whitespace-nowrap">
                    {{ formatCreatedAt(container.created_at) }}
                  </td>

                  <!-- Actions: Inspect -->
                  <td class="py-3.5 px-6 text-right whitespace-nowrap">
                    <button
                      @click="inspectContainer(container.id)"
                      class="px-2.5 py-1 text-xs font-medium text-dock-primary hover:text-white bg-dock-primary/10 hover:bg-dock-primary border border-dock-primary/20 rounded-md transition-all inline-flex items-center space-x-1"
                      title="Inspect container telemetry"
                    >
                      <Eye class="w-3.5 h-3.5" />
                      <span>Inspect</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </BaseCard>
      </div>

      <!-- ======================================================= -->
      <!-- TAB 2: IMAGES VIEW (M02.4)                              -->
      <!-- ======================================================= -->
      <div v-else-if="activeTab === 'images'" class="space-y-6">
        <!-- Image Statistics Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="p-4 rounded-xl bg-dock-surface border border-dock-border flex items-center justify-between">
            <div>
              <span class="text-xs font-medium text-dock-muted uppercase tracking-wider block">Total Images</span>
              <span class="text-2xl font-bold text-dock-text mt-1 block font-mono">{{ imageStats.total }}</span>
            </div>
            <div class="p-3 rounded-lg bg-dock-bg border border-dock-border text-dock-primary">
              <Layers class="w-5 h-5" />
            </div>
          </div>

          <div class="p-4 rounded-xl bg-dock-surface border border-dock-border flex items-center justify-between">
            <div>
              <span class="text-xs font-medium text-dock-muted uppercase tracking-wider block">In Use</span>
              <span class="text-2xl font-bold text-emerald-400 mt-1 block font-mono">{{ imageStats.inUse }}</span>
              <span class="text-[10px] text-dock-muted block mt-0.5">Referenced by containers</span>
            </div>
            <div class="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <CheckCircle2 class="w-5 h-5" />
            </div>
          </div>

          <div class="p-4 rounded-xl bg-dock-surface border border-dock-border flex items-center justify-between">
            <div>
              <span class="text-xs font-medium text-dock-muted uppercase tracking-wider block">Dangling</span>
              <span class="text-2xl font-bold text-amber-400 mt-1 block font-mono">{{ imageStats.dangling }}</span>
              <span class="text-[10px] text-dock-muted block mt-0.5">Untagged layers</span>
            </div>
            <div class="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <Tag class="w-5 h-5" />
            </div>
          </div>

          <div class="p-4 rounded-xl bg-dock-surface border border-dock-border flex items-center justify-between">
            <div>
              <span class="text-xs font-medium text-dock-muted uppercase tracking-wider block">Total Size</span>
              <span class="text-2xl font-bold text-dock-text mt-1 block font-mono">{{ formatBytes(imageStats.totalBytes) }}</span>
              <span class="text-[10px] text-dock-muted block mt-0.5">Local cache disk footprint</span>
            </div>
            <div class="p-3 rounded-lg bg-dock-bg border border-dock-border text-dock-muted">
              <HardDrive class="w-5 h-5" />
            </div>
          </div>
        </div>

        <!-- Images Table Card -->
        <BaseCard
          title="Docker Image Cache"
          subtitle="Cached container images, repositories, and workload relationships"
        >
          <template #header-actions>
            <div class="flex items-center space-x-2">
              <BaseButton
                size="sm"
                variant="outline"
                :loading="imagesLoading"
                @click="fetchImages"
              >
                <template #icon>
                  <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': imagesLoading }" />
                </template>
                Refresh Images
              </BaseButton>
            </div>
          </template>

          <!-- Search & Filter Toolbar -->
          <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pb-5 border-b border-dock-border">
            <div class="relative flex-1 max-w-md">
              <Search class="w-4 h-4 text-dock-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                v-model="imageSearchQuery"
                type="text"
                placeholder="Search images by repository, tag, or ID..."
                class="w-full pl-9 pr-3 py-1.5 text-xs bg-dock-bg border border-dock-border rounded-lg text-dock-text placeholder:text-dock-muted focus:outline-none focus:border-dock-primary transition-colors"
              />
            </div>

            <!-- Dangling Filter Tabs -->
            <div class="flex items-center space-x-1 bg-dock-bg p-1 rounded-lg border border-dock-border self-start sm:self-auto">
              <button
                v-for="tab in [
                  { label: 'All Images', value: 'all' },
                  { label: 'Tagged Only', value: 'tagged' },
                  { label: 'Dangling', value: 'dangling' },
                ]"
                :key="tab.value"
                @click="imageDanglingFilter = tab.value as any"
                class="px-2.5 py-1 text-xs rounded font-medium transition-colors"
                :class="imageDanglingFilter === tab.value
                  ? 'bg-dock-surface text-dock-primary border border-dock-border shadow-sm'
                  : 'text-dock-muted hover:text-dock-text'"
              >
                {{ tab.label }}
              </button>
            </div>
          </div>

          <!-- Error Alert -->
          <div v-if="imagesError" class="p-6 rounded-xl bg-rose-500/10 border border-rose-500/20 text-center my-4">
            <AlertCircle class="w-8 h-8 text-rose-400 mx-auto mb-2" />
            <h4 class="text-sm font-semibold text-rose-300">Images Discovery Failed</h4>
            <p class="text-xs text-rose-400/80 mt-1 max-w-md mx-auto">{{ imagesError }}</p>
            <div class="mt-4">
              <BaseButton size="sm" variant="outline" @click="fetchImages">
                Retry Connection
              </BaseButton>
            </div>
          </div>

          <!-- Loading State -->
          <div v-else-if="imagesLoading && images.length === 0" class="py-16 text-center">
            <RefreshCw class="w-8 h-8 text-dock-primary animate-spin mx-auto mb-3" />
            <p class="text-sm text-dock-muted">Discovering images on Docker Engine...</p>
          </div>

          <!-- Empty State -->
          <div v-else-if="filteredImages.length === 0" class="py-16 text-center">
            <Layers class="w-10 h-10 text-dock-muted mx-auto mb-3 opacity-50" />
            <h4 class="text-sm font-semibold text-dock-text">No Images Found</h4>
            <p class="text-xs text-dock-muted mt-1 max-w-xs mx-auto">
              {{ imageSearchQuery || imageDanglingFilter !== 'all'
                ? 'No images match the selected search or dangling filter.'
                : 'There are no images stored in the local Docker image cache.' }}
            </p>
          </div>

          <!-- Images Table -->
          <div v-else class="overflow-x-auto -mx-6 -mb-6 mt-4">
            <table class="w-full text-left text-xs">
              <thead class="bg-dock-bg text-dock-muted uppercase font-mono text-[10px] border-b border-dock-border">
                <tr>
                  <th class="py-3 px-6">Repository & Tag</th>
                  <th class="py-3 px-4">Image ID</th>
                  <th class="py-3 px-4">Size</th>
                  <th class="py-3 px-4">Containers</th>
                  <th class="py-3 px-4">Created</th>
                  <th class="py-3 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-dock-border">
                <tr
                  v-for="img in filteredImages"
                  :key="img.id"
                  class="hover:bg-dock-bg/40 transition-colors group"
                >
                  <!-- Repo & Tag -->
                  <td class="py-3.5 px-6">
                    <div v-if="img.repo_tags.length === 0" class="flex items-center space-x-1.5">
                      <span class="text-dock-muted font-mono italic text-xs">&lt;none&gt;:&lt;none&gt;</span>
                      <BaseBadge variant="warning" size="sm">dangling</BaseBadge>
                    </div>
                    <div v-else class="space-y-1">
                      <span class="font-semibold text-dock-text text-xs tracking-tight block">
                        {{ img.repo_tags[0] }}
                      </span>
                      <div v-if="img.repo_tags.length > 1" class="flex flex-wrap gap-1">
                        <span
                          v-for="t in img.repo_tags.slice(1)"
                          :key="t"
                          class="px-1.5 py-0.2 rounded text-[10px] font-mono bg-dock-bg border border-dock-border text-dock-muted"
                        >
                          {{ t }}
                        </span>
                      </div>
                    </div>
                  </td>

                  <!-- Image ID -->
                  <td class="py-3.5 px-4 font-mono text-[11px] text-dock-text">
                    {{ img.short_id }}
                  </td>

                  <!-- Size -->
                  <td class="py-3.5 px-4 font-mono text-[11px] text-dock-text">
                    {{ formatBytes(img.size_bytes) }}
                  </td>

                  <!-- Containers Referencing -->
                  <td class="py-3.5 px-4">
                    <span
                      class="px-2 py-0.5 rounded-full text-[11px] font-mono font-semibold"
                      :class="img.containers_count > 0 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-dock-bg text-dock-muted border border-dock-border'"
                    >
                      {{ img.containers_count }} container{{ img.containers_count === 1 ? '' : 's' }}
                    </span>
                  </td>

                  <!-- Created Timestamp -->
                  <td class="py-3.5 px-4 text-dock-muted text-[11px] font-mono whitespace-nowrap">
                    {{ formatCreatedAt(img.created_at) }}
                  </td>

                  <!-- Actions: Inspect -->
                  <td class="py-3.5 px-6 text-right whitespace-nowrap">
                    <button
                      @click="inspectImage(img.id)"
                      class="px-2.5 py-1 text-xs font-medium text-dock-primary hover:text-white bg-dock-primary/10 hover:bg-dock-primary border border-dock-primary/20 rounded-md transition-all inline-flex items-center space-x-1"
                      title="Inspect image metadata"
                    >
                      <Eye class="w-3.5 h-3.5" />
                      <span>Inspect</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </BaseCard>
      </div>

      <!-- ======================================================= -->
      <!-- TAB 3: VOLUMES VIEW (M02.4)                            -->
      <!-- ======================================================= -->
      <div v-else-if="activeTab === 'volumes'" class="space-y-6">
        <!-- Volume Statistics Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="p-4 rounded-xl bg-dock-surface border border-dock-border flex items-center justify-between">
            <div>
              <span class="text-xs font-medium text-dock-muted uppercase tracking-wider block">Total Volumes</span>
              <span class="text-2xl font-bold text-dock-text mt-1 block font-mono">{{ volumeStats.total }}</span>
            </div>
            <div class="p-3 rounded-lg bg-dock-bg border border-dock-border text-dock-primary">
              <HardDrive class="w-5 h-5" />
            </div>
          </div>

          <div class="p-4 rounded-xl bg-dock-surface border border-dock-border flex items-center justify-between">
            <div>
              <span class="text-xs font-medium text-dock-muted uppercase tracking-wider block">Mounted (In-Use)</span>
              <span class="text-2xl font-bold text-emerald-400 mt-1 block font-mono">{{ volumeStats.inUse }}</span>
              <span class="text-[10px] text-dock-muted block mt-0.5">Attached to containers</span>
            </div>
            <div class="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <CheckCircle2 class="w-5 h-5" />
            </div>
          </div>

          <div class="p-4 rounded-xl bg-dock-surface border border-dock-border flex items-center justify-between">
            <div>
              <span class="text-xs font-medium text-dock-muted uppercase tracking-wider block">Local Driver</span>
              <span class="text-2xl font-bold text-dock-text mt-1 block font-mono">{{ volumeStats.localDriver }}</span>
              <span class="text-[10px] text-dock-muted block mt-0.5">Host storage backend</span>
            </div>
            <div class="p-3 rounded-lg bg-dock-bg border border-dock-border text-dock-primary">
              <Database class="w-5 h-5" />
            </div>
          </div>

          <div class="p-4 rounded-xl bg-dock-surface border border-dock-border flex items-center justify-between">
            <div>
              <span class="text-xs font-medium text-dock-muted uppercase tracking-wider block">Storage Drivers</span>
              <span class="text-2xl font-bold text-dock-muted mt-1 block font-mono">{{ volumeStats.driverCount }}</span>
              <span class="text-[10px] text-dock-muted block mt-0.5">Active volume plugins</span>
            </div>
            <div class="p-3 rounded-lg bg-dock-bg border border-dock-border text-dock-muted">
              <SlidersHorizontal class="w-5 h-5" />
            </div>
          </div>
        </div>

        <!-- Volumes Table Card -->
        <BaseCard
          title="Docker Persistent Volumes"
          subtitle="Storage volumes, driver engines, and container mount relationships"
        >
          <template #header-actions>
            <div class="flex items-center space-x-2">
              <BaseButton
                size="sm"
                variant="outline"
                :loading="volumesLoading"
                @click="fetchVolumes"
              >
                <template #icon>
                  <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': volumesLoading }" />
                </template>
                Refresh Volumes
              </BaseButton>
            </div>
          </template>

          <!-- Search & Driver Filter Toolbar -->
          <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pb-5 border-b border-dock-border">
            <div class="relative flex-1 max-w-md">
              <Search class="w-4 h-4 text-dock-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                v-model="volumeSearchQuery"
                type="text"
                placeholder="Search volumes by name..."
                class="w-full pl-9 pr-3 py-1.5 text-xs bg-dock-bg border border-dock-border rounded-lg text-dock-text placeholder:text-dock-muted focus:outline-none focus:border-dock-primary transition-colors"
              />
            </div>

            <!-- Driver Filter Select -->
            <div class="flex items-center space-x-2 self-start sm:self-auto">
              <Filter class="w-3.5 h-3.5 text-dock-muted" />
              <select
                v-model="volumeDriverFilter"
                class="px-2.5 py-1 text-xs bg-dock-bg border border-dock-border rounded-lg text-dock-text focus:outline-none focus:border-dock-primary"
              >
                <option value="all">All Drivers</option>
                <option v-for="d in availableDrivers" :key="d" :value="d">{{ d }}</option>
              </select>
            </div>
          </div>

          <!-- Error Alert -->
          <div v-if="volumesError" class="p-6 rounded-xl bg-rose-500/10 border border-rose-500/20 text-center my-4">
            <AlertCircle class="w-8 h-8 text-rose-400 mx-auto mb-2" />
            <h4 class="text-sm font-semibold text-rose-300">Volumes Discovery Failed</h4>
            <p class="text-xs text-rose-400/80 mt-1 max-w-md mx-auto">{{ volumesError }}</p>
            <div class="mt-4">
              <BaseButton size="sm" variant="outline" @click="fetchVolumes">
                Retry Connection
              </BaseButton>
            </div>
          </div>

          <!-- Loading State -->
          <div v-else-if="volumesLoading && volumes.length === 0" class="py-16 text-center">
            <RefreshCw class="w-8 h-8 text-dock-primary animate-spin mx-auto mb-3" />
            <p class="text-sm text-dock-muted">Discovering volumes on Docker Engine...</p>
          </div>

          <!-- Empty State -->
          <div v-else-if="filteredVolumes.length === 0" class="py-16 text-center">
            <HardDrive class="w-10 h-10 text-dock-muted mx-auto mb-3 opacity-50" />
            <h4 class="text-sm font-semibold text-dock-text">No Volumes Found</h4>
            <p class="text-xs text-dock-muted mt-1 max-w-xs mx-auto">
              {{ volumeSearchQuery || volumeDriverFilter !== 'all'
                ? 'No volumes match the selected search or driver filter.'
                : 'There are no persistent volumes configured on this host.' }}
            </p>
          </div>

          <!-- Volumes Table -->
          <div v-else class="overflow-x-auto -mx-6 -mb-6 mt-4">
            <table class="w-full text-left text-xs">
              <thead class="bg-dock-bg text-dock-muted uppercase font-mono text-[10px] border-b border-dock-border">
                <tr>
                  <th class="py-3 px-6">Volume Name</th>
                  <th class="py-3 px-4">Driver</th>
                  <th class="py-3 px-4">Scope</th>
                  <th class="py-3 px-4">Mount Usage</th>
                  <th class="py-3 px-4">Created</th>
                  <th class="py-3 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-dock-border">
                <tr
                  v-for="vol in filteredVolumes"
                  :key="vol.name"
                  class="hover:bg-dock-bg/40 transition-colors group"
                >
                  <!-- Volume Name -->
                  <td class="py-3.5 px-6">
                    <span class="font-semibold text-dock-text text-xs tracking-tight block truncate max-w-xs" :title="vol.name">
                      {{ vol.name }}
                    </span>
                  </td>

                  <!-- Driver -->
                  <td class="py-3.5 px-4 font-mono text-[11px] text-dock-text">
                    {{ vol.driver }}
                  </td>

                  <!-- Scope -->
                  <td class="py-3.5 px-4 font-mono text-[11px] text-dock-muted uppercase">
                    {{ vol.scope }}
                  </td>

                  <!-- Containers Referencing -->
                  <td class="py-3.5 px-4">
                    <span
                      class="px-2 py-0.5 rounded-full text-[11px] font-mono font-semibold"
                      :class="vol.is_in_use ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-dock-bg text-dock-muted border border-dock-border'"
                    >
                      {{ vol.containers_count }} container{{ vol.containers_count === 1 ? '' : 's' }}
                    </span>
                  </td>

                  <!-- Created Timestamp -->
                  <td class="py-3.5 px-4 text-dock-muted text-[11px] font-mono whitespace-nowrap">
                    {{ formatCreatedAt(vol.created_at) }}
                  </td>

                  <!-- Actions: Inspect -->
                  <td class="py-3.5 px-6 text-right whitespace-nowrap">
                    <button
                      @click="inspectVolume(vol.name)"
                      class="px-2.5 py-1 text-xs font-medium text-dock-primary hover:text-white bg-dock-primary/10 hover:bg-dock-primary border border-dock-primary/20 rounded-md transition-all inline-flex items-center space-x-1"
                      title="Inspect volume metadata"
                    >
                      <Eye class="w-3.5 h-3.5" />
                      <span>Inspect</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </BaseCard>
      </div>

      <!-- Scope & Security Boundary Notice -->
      <BaseCard title="DockScope Workload Management Roadmap" subtitle="Security boundary and upcoming execution capabilities">
        <div class="space-y-4 text-xs text-dock-muted leading-relaxed">
          <p>
            <strong class="text-dock-text">Read-Only Safety Guarantee:</strong> Milestone 02.4 expands DockScope with comprehensive
            images and volumes discovery, layer inspection, and container mount correlation. As mandated by project safety standards,
            mutations (pull, build, push, prune, delete, create, mount) remain strictly disabled.
          </p>

          <div class="grid grid-cols-1 md:grid-cols-4 gap-3 pt-2">
            <div class="p-3 rounded-lg bg-dock-bg border border-dock-border">
              <div class="flex items-center space-x-2 text-dock-text font-semibold mb-1">
                <Activity class="w-4 h-4 text-dock-primary" />
                <span>M02.1: Engine Connection</span>
              </div>
              <p class="text-[11px] text-dock-muted">
                Socket verification, API versioning, daemon health, host resource allocation.
              </p>
              <span class="inline-block mt-2 text-[10px] font-mono text-dock-success">Completed & Verified</span>
            </div>

            <div class="p-3 rounded-lg bg-dock-bg border border-dock-border">
              <div class="flex items-center space-x-2 text-dock-text font-semibold mb-1">
                <Boxes class="w-4 h-4 text-dock-secondary" />
                <span>M02.2: Container Discovery</span>
              </div>
              <p class="text-[11px] text-dock-muted">
                Real container inventory, detail drawer, network inspection, and mount discovery.
              </p>
              <span class="inline-block mt-2 text-[10px] font-mono text-dock-success">Completed & Verified</span>
            </div>

            <div class="p-3 rounded-lg bg-dock-bg border border-dock-border">
              <div class="flex items-center space-x-2 text-dock-text font-semibold mb-1">
                <Activity class="w-4 h-4 text-dock-primary" />
                <span>M02.3: Resource Monitoring</span>
              </div>
              <p class="text-[11px] text-dock-muted">
                One-shot CPU %, memory usage, limits, network RX/TX, and disk I/O metrics.
              </p>
              <span class="inline-block mt-2 text-[10px] font-mono text-dock-success">Completed & Verified</span>
            </div>

            <div class="p-3 rounded-lg bg-dock-bg border border-dock-border">
              <div class="flex items-center space-x-2 text-dock-text font-semibold mb-1">
                <Layers class="w-4 h-4 text-emerald-400" />
                <span>M02.4: Images & Volumes</span>
              </div>
              <p class="text-[11px] text-dock-muted">
                Image cache, dangling layers, storage volumes, and container relationship intelligence.
              </p>
              <span class="inline-block mt-2 text-[10px] font-mono text-dock-success">Active & Implemented</span>
            </div>
          </div>
        </div>
      </BaseCard>
    </div>

    <!-- Container Inspection Detail Drawer -->
    <ContainerDetailDrawer
      :container="selectedContainer"
      :is-open="isDrawerOpen"
      :loading="drawerLoading"
      :error="drawerError"
      @close="closeDrawer"
    />

    <!-- Image Inspection Detail Drawer (M02.4) -->
    <ImageDetailDrawer
      :image="selectedImage"
      :is-open="isImageDrawerOpen"
      :loading="imageDrawerLoading"
      :error="imageDrawerError"
      @close="closeImageDrawer"
    />

    <!-- Volume Inspection Detail Drawer (M02.4) -->
    <VolumeDetailDrawer
      :volume="selectedVolume"
      :is-open="isVolumeDrawerOpen"
      :loading="volumeDrawerLoading"
      :error="volumeDrawerError"
      @close="closeVolumeDrawer"
    />
  </DefaultLayout>
</template>
