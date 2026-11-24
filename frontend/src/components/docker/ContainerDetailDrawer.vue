<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  X,
  Boxes,
  Terminal,
  Network,
  HardDrive,
  Clock,
  Shield,
  Layers,
  Activity,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  PauseCircle,
  RefreshCw,
  Cpu,
} from 'lucide-vue-next'
import type { ContainerDetail, ContainerStats } from '@/types'
import BaseBadge from '@/components/common/BaseBadge.vue'
import ContainerLogsViewer from '@/components/docker/ContainerLogsViewer.vue'
import { dockerApi } from '@/services/api'
import { formatBytes } from '@/utils/formatters'

const props = defineProps<{
  container: ContainerDetail | null
  isOpen: boolean
  loading?: boolean
  error?: string | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const activeTab = ref<'overview' | 'logs'>('overview')
const stats = ref<ContainerStats | null>(null)
const statsLoading = ref(false)
const statsError = ref<string | null>(null)

async function fetchStats() {
  if (!props.container?.id) return
  statsLoading.value = true
  statsError.value = null
  try {
    stats.value = await dockerApi.getContainerStats(props.container.id)
  } catch (err: unknown) {
    statsError.value = err instanceof Error ? err.message : 'Failed to collect container resource metrics.'
  } finally {
    statsLoading.value = false
  }
}

watch(
  () => props.container?.id,
  (newId) => {
    stats.value = null
    statsError.value = null
    activeTab.value = 'overview'
    if (newId) {
      fetchStats()
    }
  },
  { immediate: true }
)

const stateVariant = computed(() => {
  if (!props.container) return 'neutral'
  const state = props.container.state.toLowerCase()
  if (state === 'running') return 'success'
  if (state === 'paused') return 'warning'
  if (state === 'exited' || state === 'dead') return 'neutral'
  return 'info'
})

const healthVariant = computed(() => {
  if (!props.container?.health_status) return 'neutral'
  const h = props.container.health_status.toLowerCase()
  if (h === 'healthy') return 'success'
  if (h === 'unhealthy') return 'danger'
  if (h === 'starting') return 'warning'
  return 'neutral'
})

function formatTimestamp(ts?: string | null): string {
  if (!ts) return '—'
  try {
    const d = new Date(ts)
    if (isNaN(d.getTime())) return ts
    return d.toLocaleString()
  } catch {
    return ts
  }
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-hidden">
    <!-- Backdrop -->
    <div
      class="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
      @click="emit('close')"
    />

    <!-- Drawer Panel -->
    <div class="fixed inset-y-0 right-0 max-w-full flex pl-10">
      <div class="w-screen max-w-2xl bg-dock-surface border-l border-dock-border shadow-2xl flex flex-col">
        <!-- Drawer Header -->
        <div class="px-6 py-5 border-b border-dock-border flex items-center justify-between bg-dock-bg/50">
          <div class="flex items-center space-x-3 overflow-hidden">
            <div class="p-2 rounded-lg bg-dock-primary/10 border border-dock-primary/20 text-dock-primary shrink-0">
              <Boxes class="w-5 h-5" />
            </div>
            <div class="truncate">
              <div class="flex items-center space-x-2">
                <h2 class="text-base font-bold text-dock-text truncate" :title="container?.name">
                  {{ container?.name || 'Container Inspection' }}
                </h2>
                <BaseBadge v-if="container" :variant="stateVariant" size="sm" dot>
                  {{ container.state }}
                </BaseBadge>
                <BaseBadge v-if="container?.health_status" :variant="healthVariant" size="sm">
                  {{ container.health_status }}
                </BaseBadge>
              </div>
              <p class="text-xs font-mono text-dock-muted truncate mt-0.5">
                {{ container?.short_id || 'Inspecting...' }}
              </p>
            </div>
          </div>

          <button
            @click="emit('close')"
            class="p-2 rounded-lg text-dock-muted hover:text-dock-text hover:bg-dock-border/50 transition-colors"
            title="Close Drawer"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Drawer Navigation Sub-Tabs (M02.5) -->
        <div v-if="container" class="px-6 border-b border-dock-border flex items-center space-x-1 bg-dock-surface shrink-0">
          <button
            @click="activeTab = 'overview'"
            class="px-4 py-2.5 text-xs font-semibold border-b-2 flex items-center space-x-2 transition-colors"
            :class="activeTab === 'overview'
              ? 'border-dock-primary text-dock-primary bg-dock-primary/5'
              : 'border-transparent text-dock-muted hover:text-dock-text'"
          >
            <Boxes class="w-4 h-4" />
            <span>Overview & Telemetry</span>
          </button>

          <button
            @click="activeTab = 'logs'"
            class="px-4 py-2.5 text-xs font-semibold border-b-2 flex items-center space-x-2 transition-colors"
            :class="activeTab === 'logs'
              ? 'border-dock-primary text-dock-primary bg-dock-primary/5'
              : 'border-transparent text-dock-muted hover:text-dock-text'"
          >
            <Terminal class="w-4 h-4" />
            <span>Container Logs</span>
          </button>
        </div>

        <!-- Drawer Content -->
        <div class="flex-1 overflow-y-auto p-6 space-y-6">
          <!-- Loading State -->
          <div v-if="loading" class="py-16 text-center">
            <RefreshCw class="w-8 h-8 text-dock-primary animate-spin mx-auto mb-3" />
            <p class="text-sm text-dock-muted">Inspecting container telemetry...</p>
          </div>

          <!-- Error State -->
          <div v-else-if="error" class="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
            <div class="flex items-center space-x-2 font-semibold mb-1">
              <AlertCircle class="w-4 h-4" />
              <span>Inspection Error</span>
            </div>
            <p class="text-xs">{{ error }}</p>
          </div>

          <!-- Container Details View -->
          <template v-else-if="container">
            <!-- TAB 1: OVERVIEW & TELEMETRY -->
            <div v-show="activeTab === 'overview'" class="space-y-6">
              <!-- Security & Read-Only Notice -->
              <div class="p-3.5 rounded-lg bg-dock-bg border border-dock-border flex items-start space-x-3 text-xs">
                <Shield class="w-4 h-4 text-dock-primary shrink-0 mt-0.5" />
                <div class="leading-relaxed">
                  <span class="font-semibold text-dock-text">DockScope Read-Only Inspection:</span>
                  <span class="text-dock-muted ml-1">
                    Environment variables, API secrets, and sensitive credentials are encrypted and strictly omitted from telemetry per security guidelines.
                  </span>
                </div>
              </div>

            <!-- Live Resource Telemetry (Milestone 02.3) -->
            <div class="p-4 rounded-xl bg-dock-bg border border-dock-border space-y-3">
              <div class="flex items-center justify-between pb-3 border-b border-dock-border/60">
                <div class="flex items-center space-x-2.5">
                  <div class="p-1.5 rounded-md bg-dock-primary/10 text-dock-primary">
                    <Activity class="w-4 h-4" />
                  </div>
                  <div>
                    <h3 class="text-xs font-semibold text-dock-text">Resource Utilization (M02.3)</h3>
                    <p class="text-[10px] text-dock-muted">Real-time one-shot container metrics</p>
                  </div>
                </div>
                <div class="flex items-center space-x-2">
                  <span v-if="stats?.collected_at" class="text-[10px] font-mono text-dock-muted hidden sm:inline">
                    {{ formatTimestamp(stats.collected_at) }}
                  </span>
                  <button
                    @click="fetchStats"
                    :disabled="statsLoading"
                    class="px-2 py-1 rounded bg-dock-surface border border-dock-border text-dock-muted hover:text-dock-text hover:border-dock-primary/50 transition-colors disabled:opacity-50 inline-flex items-center space-x-1"
                    title="Refresh resource metrics"
                  >
                    <RefreshCw class="w-3 h-3" :class="{ 'animate-spin': statsLoading }" />
                    <span class="text-[10px]">Refresh</span>
                  </button>
                </div>
              </div>

              <!-- Loading State -->
              <div v-if="statsLoading && !stats" class="py-6 text-center">
                <RefreshCw class="w-5 h-5 text-dock-primary animate-spin mx-auto mb-2" />
                <span class="text-xs text-dock-muted">Querying Docker Engine stats...</span>
              </div>

              <!-- Error State -->
              <div v-else-if="statsError" class="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center justify-between">
                <div class="flex items-center space-x-2">
                  <AlertCircle class="w-4 h-4 shrink-0" />
                  <span>{{ statsError }}</span>
                </div>
                <button @click="fetchStats" class="underline hover:text-rose-300 shrink-0 ml-2">Retry</button>
              </div>

              <!-- Inactive / Stopped Container State -->
              <div v-else-if="stats && !stats.is_running" class="p-3 rounded-lg bg-dock-surface border border-dock-border text-xs text-dock-muted flex items-center space-x-2">
                <PauseCircle class="w-4 h-4 text-dock-muted shrink-0" />
                <span>Container is stopped. Resource telemetry is inactive.</span>
              </div>

              <!-- Active Telemetry Metrics Grid -->
              <div v-else-if="stats" class="grid grid-cols-2 gap-3">
                <!-- CPU Usage Card -->
                <div class="p-3 rounded-lg bg-dock-surface border border-dock-border space-y-1.5">
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] font-mono uppercase text-dock-muted">CPU Usage</span>
                    <span class="text-[10px] font-mono text-dock-muted">{{ stats.online_cpus }} Core{{ stats.online_cpus > 1 ? 's' : '' }}</span>
                  </div>
                  <div class="flex items-baseline space-x-1">
                    <span class="text-lg font-bold font-mono text-dock-text">{{ stats.cpu_percentage }}</span>
                    <span class="text-xs text-dock-muted font-mono">%</span>
                  </div>
                  <!-- CPU Progress Bar -->
                  <div class="w-full bg-dock-bg h-1.5 rounded-full overflow-hidden border border-dock-border/50">
                    <div
                      class="h-full rounded-full transition-all duration-300"
                      :class="stats.cpu_percentage > 85 ? 'bg-rose-500' : stats.cpu_percentage > 60 ? 'bg-amber-400' : 'bg-emerald-400'"
                      :style="{ width: `${Math.min(stats.cpu_percentage, 100)}%` }"
                    />
                  </div>
                </div>

                <!-- Memory Usage Card -->
                <div class="p-3 rounded-lg bg-dock-surface border border-dock-border space-y-1.5">
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] font-mono uppercase text-dock-muted">Memory</span>
                    <span class="text-[10px] font-mono text-dock-muted">{{ stats.memory_percentage }}%</span>
                  </div>
                  <div class="flex items-baseline space-x-1 truncate" :title="`${formatBytes(stats.memory_usage_bytes)} / ${stats.memory_limit_bytes > 0 ? formatBytes(stats.memory_limit_bytes) : 'No Limit'}`">
                    <span class="text-sm font-bold font-mono text-dock-text">{{ formatBytes(stats.memory_usage_bytes) }}</span>
                    <span class="text-[10px] text-dock-muted font-mono" v-if="stats.memory_limit_bytes > 0">
                      / {{ formatBytes(stats.memory_limit_bytes) }}
                    </span>
                  </div>
                  <!-- Memory Progress Bar -->
                  <div class="w-full bg-dock-bg h-1.5 rounded-full overflow-hidden border border-dock-border/50">
                    <div
                      class="h-full rounded-full transition-all duration-300"
                      :class="stats.memory_percentage > 85 ? 'bg-rose-500' : stats.memory_percentage > 60 ? 'bg-amber-400' : 'bg-dock-primary'"
                      :style="{ width: `${Math.min(stats.memory_percentage, 100)}%` }"
                    />
                  </div>
                </div>

                <!-- Network I/O Card -->
                <div class="p-3 rounded-lg bg-dock-surface border border-dock-border space-y-1">
                  <span class="text-[10px] font-mono uppercase text-dock-muted block">Network I/O</span>
                  <div class="flex items-center justify-between text-xs font-mono">
                    <span class="text-dock-muted text-[10px]">RX:</span>
                    <span class="text-dock-text font-semibold">
                      {{ stats.network_rx_bytes !== null && stats.network_rx_bytes !== undefined ? formatBytes(stats.network_rx_bytes) : '—' }}
                    </span>
                  </div>
                  <div class="flex items-center justify-between text-xs font-mono">
                    <span class="text-dock-muted text-[10px]">TX:</span>
                    <span class="text-dock-text font-semibold">
                      {{ stats.network_tx_bytes !== null && stats.network_tx_bytes !== undefined ? formatBytes(stats.network_tx_bytes) : '—' }}
                    </span>
                  </div>
                </div>

                <!-- Block I/O Card -->
                <div class="p-3 rounded-lg bg-dock-surface border border-dock-border space-y-1">
                  <span class="text-[10px] font-mono uppercase text-dock-muted block">Block I/O</span>
                  <div class="flex items-center justify-between text-xs font-mono">
                    <span class="text-dock-muted text-[10px]">Read:</span>
                    <span class="text-dock-text font-semibold">
                      {{ stats.block_read_bytes !== null && stats.block_read_bytes !== undefined ? formatBytes(stats.block_read_bytes) : '—' }}
                    </span>
                  </div>
                  <div class="flex items-center justify-between text-xs font-mono">
                    <span class="text-dock-muted text-[10px]">Write:</span>
                    <span class="text-dock-text font-semibold">
                      {{ stats.block_write_bytes !== null && stats.block_write_bytes !== undefined ? formatBytes(stats.block_write_bytes) : '—' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Overview Grid -->
            <div class="grid grid-cols-2 gap-4">
              <div class="p-4 rounded-lg bg-dock-bg border border-dock-border">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Image</span>
                <span class="text-xs font-mono text-dock-text break-all font-semibold">{{ container.image }}</span>
              </div>
              <div class="p-4 rounded-lg bg-dock-bg border border-dock-border">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Status</span>
                <span class="text-xs text-dock-text font-semibold">{{ container.status }}</span>
              </div>
              <div class="p-4 rounded-lg bg-dock-bg border border-dock-border">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Restarts</span>
                <span class="text-xs font-mono text-dock-text">{{ container.restart_count }} times</span>
              </div>
              <div class="p-4 rounded-lg bg-dock-bg border border-dock-border">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Created At</span>
                <span class="text-xs text-dock-text">{{ formatTimestamp(container.created_at) }}</span>
              </div>
              <div class="p-4 rounded-lg bg-dock-bg border border-dock-border">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Started At</span>
                <span class="text-xs text-dock-text">{{ formatTimestamp(container.started_at) }}</span>
              </div>
              <div class="p-4 rounded-lg bg-dock-bg border border-dock-border">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Finished At</span>
                <span class="text-xs text-dock-text">{{ formatTimestamp(container.finished_at) }}</span>
              </div>
            </div>

            <!-- Command -->
            <div class="space-y-2">
              <div class="flex items-center space-x-2 text-xs font-semibold text-dock-text">
                <Terminal class="w-4 h-4 text-dock-primary" />
                <span>Command Execution</span>
              </div>
              <div class="p-3 rounded-lg bg-dock-bg border border-dock-border">
                <code class="text-xs font-mono text-dock-secondary break-all">
                  {{ container.command || 'No command specified (default entrypoint)' }}
                </code>
              </div>
            </div>

            <!-- Port Mappings -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2 text-xs font-semibold text-dock-text">
                  <Activity class="w-4 h-4 text-dock-primary" />
                  <span>Port Bindings</span>
                </div>
                <span class="text-[11px] text-dock-muted font-mono">{{ container.ports.length }} mapped</span>
              </div>

              <div v-if="container.ports.length === 0" class="p-4 rounded-lg bg-dock-bg border border-dock-border text-center text-xs text-dock-muted">
                No published or exposed ports for this container.
              </div>

              <div v-else class="rounded-lg border border-dock-border overflow-hidden">
                <table class="w-full text-left text-xs">
                  <thead class="bg-dock-bg text-dock-muted uppercase font-mono text-[10px] border-b border-dock-border">
                    <tr>
                      <th class="py-2.5 px-3">Container Port</th>
                      <th class="py-2.5 px-3">Protocol</th>
                      <th class="py-2.5 px-3">Published Host Port</th>
                      <th class="py-2.5 px-3">Host Binding</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-dock-border font-mono text-[11px]">
                    <tr v-for="(p, idx) in container.ports" :key="idx" class="hover:bg-dock-bg/50">
                      <td class="py-2 px-3 text-dock-text font-bold">{{ p.container_port }}</td>
                      <td class="py-2 px-3 text-dock-muted uppercase">{{ p.protocol }}</td>
                      <td class="py-2 px-3">
                        <span v-if="p.host_port" class="text-emerald-400 font-semibold">{{ p.host_port }}</span>
                        <span v-else class="text-dock-muted italic text-[10px]">Unpublished (internal)</span>
                      </td>
                      <td class="py-2 px-3 text-dock-muted">{{ p.host_ip || '—' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Networks -->
            <div class="space-y-2">
              <div class="flex items-center space-x-2 text-xs font-semibold text-dock-text">
                <Network class="w-4 h-4 text-dock-primary" />
                <span>Connected Networks</span>
              </div>
              <div v-if="container.networks.length === 0" class="p-3 rounded-lg bg-dock-bg border border-dock-border text-xs text-dock-muted">
                No networks attached.
              </div>
              <div v-else class="flex flex-wrap gap-2">
                <span
                  v-for="net in container.networks"
                  :key="net"
                  class="px-2.5 py-1 rounded bg-dock-bg border border-dock-border font-mono text-xs text-dock-text"
                >
                  {{ net }}
                </span>
              </div>
            </div>

            <!-- Mounts and Storage -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2 text-xs font-semibold text-dock-text">
                  <HardDrive class="w-4 h-4 text-dock-primary" />
                  <span>Mounts & Volumes</span>
                </div>
                <span class="text-[11px] text-dock-muted font-mono">{{ container.mounts.length }} mounts</span>
              </div>

              <div v-if="container.mounts.length === 0" class="p-4 rounded-lg bg-dock-bg border border-dock-border text-center text-xs text-dock-muted">
                No mounts configured.
              </div>

              <div v-else class="space-y-2">
                <div
                  v-for="(m, idx) in container.mounts"
                  :key="idx"
                  class="p-3 rounded-lg bg-dock-bg border border-dock-border text-xs space-y-1"
                >
                  <div class="flex items-center justify-between">
                    <span class="font-mono text-dock-primary uppercase text-[10px] font-bold">{{ m.type }}</span>
                    <span class="text-[10px] font-mono text-dock-muted">{{ m.read_only ? 'Read-Only (ro)' : 'Read-Write (rw)' }}</span>
                  </div>
                  <div class="text-dock-text font-mono font-medium break-all">
                    {{ m.destination }}
                  </div>
                  <div v-if="m.source || m.name" class="text-[11px] text-dock-muted font-mono break-all">
                    Source: {{ m.source || m.name }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Labels -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2 text-xs font-semibold text-dock-text">
                  <Layers class="w-4 h-4 text-dock-primary" />
                  <span>Sanitized Labels</span>
                </div>
                <span class="text-[11px] text-dock-muted font-mono">{{ Object.keys(container.labels).length }} labels</span>
              </div>

              <div v-if="Object.keys(container.labels).length === 0" class="p-3 rounded-lg bg-dock-bg border border-dock-border text-xs text-dock-muted">
                No labels configured.
              </div>

              <div v-else class="space-y-1.5 max-h-48 overflow-y-auto rounded-lg border border-dock-border p-2 bg-dock-bg">
                <div
                  v-for="(v, k) in container.labels"
                  :key="k"
                  class="flex items-start justify-between text-[11px] font-mono py-1 px-1.5 rounded hover:bg-dock-surface"
                >
                  <span class="text-dock-muted mr-3 break-all">{{ k }}:</span>
                  <span class="text-dock-text font-medium text-right break-all">{{ v }}</span>
                </div>
              </div>
            </div>

            <!-- Full Container ID -->
            <div class="p-3 rounded-lg bg-dock-bg border border-dock-border">
              <span class="text-[10px] uppercase font-mono text-dock-muted block mb-1">Full Container Hash (SHA256)</span>
              <span class="text-[11px] font-mono text-dock-muted break-all select-all">{{ container.id }}</span>
            </div>
          </div>

          <!-- TAB 2: CONTAINER LOGS (M02.5) -->
          <div v-if="activeTab === 'logs'" class="space-y-4">
            <ContainerLogsViewer
              :container-id="container.id"
              :container-name="container.name"
            />
          </div>
        </template>
        </div>

        <!-- Drawer Footer -->
        <div class="px-6 py-4 border-t border-dock-border bg-dock-bg/50 flex justify-end">
          <button
            @click="emit('close')"
            class="px-4 py-2 text-xs font-medium text-dock-text bg-dock-surface border border-dock-border rounded-lg hover:border-dock-primary/40 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>