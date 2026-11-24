<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  Boxes,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Cpu,
  Layers,
  HardDrive,
} from 'lucide-vue-next'
import BaseBadge from '@/components/common/BaseBadge.vue'
import { dockerApi } from '@/services/api'
import type { DockerStatusResponse } from '@/types'
import { formatBytes } from '@/utils/formatters'

interface Props {
  containersOverride?: {
    total: number
    running: number
  } | null
}

const props = defineProps<Props>()

const statusData = ref<DockerStatusResponse | null>(null)
const isLoading = ref(false)
const requestError = ref<string | null>(null)

const displayContainersTotal = computed(() => {
  if (props.containersOverride && typeof props.containersOverride.total === 'number') {
    return props.containersOverride.total
  }
  return statusData.value?.details?.containers_total ?? 0
})

const displayContainersRunning = computed(() => {
  if (props.containersOverride && typeof props.containersOverride.running === 'number') {
    return props.containersOverride.running
  }
  return statusData.value?.details?.containers_running ?? 0
})

async function fetchStatus() {
  isLoading.value = true
  requestError.value = null
  try {
    statusData.value = await dockerApi.getStatus()
  } catch (err: unknown) {
    requestError.value = err instanceof Error ? err.message : 'Failed to query Docker Engine status'
    statusData.value = {
      status: 'error',
      details: null,
      error_message: requestError.value,
      endpoint: 'local socket/pipe',
      checked_at: new Date().toISOString(),
    }
  } finally {
    isLoading.value = false
  }
}

defineExpose({
  fetchStatus,
})

onMounted(() => {
  fetchStatus()
})

const badgeVariant = computed(() => {
  if (!statusData.value) return 'neutral'
  switch (statusData.value.status) {
    case 'connected':
      return 'success'
    case 'disconnected':
      return 'danger'
    case 'unavailable':
      return 'warning'
    case 'error':
      return 'danger'
    default:
      return 'neutral'
  }
})

const statusLabel = computed(() => {
  if (!statusData.value) return 'Checking...'
  switch (statusData.value.status) {
    case 'connected':
      return 'Connected'
    case 'disconnected':
      return 'Disconnected'
    case 'unavailable':
      return 'Unavailable'
    case 'error':
      return 'Error'
    default:
      return statusData.value.status
  }
})

const formattedTime = computed(() => {
  if (!statusData.value?.checked_at) return 'Never'
  try {
    return new Date(statusData.value.checked_at).toLocaleTimeString()
  } catch {
    return statusData.value.checked_at
  }
})
</script>

<template>
  <div class="bg-dock-surface border border-dock-border rounded-lg p-5">
    <!-- Header -->
    <div class="flex items-center justify-between pb-4 border-b border-dock-border/60">
      <div class="flex items-center space-x-3">
        <div class="p-2 rounded bg-dock-bg border border-dock-border text-dock-primary">
          <Boxes class="w-5 h-5" />
        </div>
        <div>
          <h3 class="text-sm font-semibold text-dock-text">Docker Engine Connection</h3>
          <p class="text-xs text-dock-muted">Local host daemon communication (M02.1 Read-Only)</p>
        </div>
      </div>

      <div class="flex items-center space-x-3">
        <BaseBadge :variant="badgeVariant" size="sm" dot>
          {{ statusLabel }}
        </BaseBadge>
        <button
          @click="fetchStatus"
          :disabled="isLoading"
          class="p-1.5 rounded bg-dock-bg border border-dock-border text-dock-muted hover:text-dock-text hover:border-dock-primary/50 transition-colors disabled:opacity-50"
          title="Refresh Docker Engine status"
        >
          <RefreshCw :class="['w-3.5 h-3.5', isLoading ? 'animate-spin text-dock-primary' : '']" />
        </button>
      </div>
    </div>

    <!-- Body -->
    <div class="mt-4">
      <!-- Error / Disconnected Banner -->
      <div
        v-if="statusData && statusData.status !== 'connected' && statusData.error_message"
        class="p-3 mb-4 rounded-md bg-dock-danger/10 border border-dock-danger/30 flex items-start space-x-2.5 text-xs text-dock-danger"
      >
        <AlertTriangle class="w-4 h-4 shrink-0 mt-0.5" />
        <div>
          <span class="font-semibold">Docker Daemon Offline or Unreachable:</span>
          <p class="mt-0.5 text-dock-muted/90">{{ statusData.error_message }}</p>
        </div>
      </div>

      <!-- Telemetry Grid (Connected State) -->
      <div v-if="statusData?.details" class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div class="p-3 rounded bg-dock-bg/50 border border-dock-border">
          <span class="text-dock-muted uppercase text-[10px] font-mono tracking-wider block">Engine Version</span>
          <span class="font-bold font-mono text-dock-text text-sm mt-0.5 block">
            {{ statusData.details.version || 'N/A' }}
          </span>
          <span class="text-[10px] text-dock-muted font-mono mt-0.5 block">
            API v{{ statusData.details.api_version || 'N/A' }}
          </span>
        </div>

        <div class="p-3 rounded bg-dock-bg/50 border border-dock-border">
          <span class="text-dock-muted uppercase text-[10px] font-mono tracking-wider block">Containers</span>
          <span class="font-bold font-mono text-dock-text text-sm mt-0.5 block">
            {{ displayContainersTotal }}
          </span>
          <span class="text-[10px] text-dock-success font-mono mt-0.5 block">
            {{ displayContainersRunning }} running
          </span>
        </div>

        <div class="p-3 rounded bg-dock-bg/50 border border-dock-border">
          <span class="text-dock-muted uppercase text-[10px] font-mono tracking-wider block">Images</span>
          <span class="font-bold font-mono text-dock-text text-sm mt-0.5 block">
            {{ statusData.details.images_total ?? 0 }}
          </span>
          <span class="text-[10px] text-dock-muted font-mono mt-0.5 block">Local cache</span>
        </div>

        <div class="p-3 rounded bg-dock-bg/50 border border-dock-border">
          <span class="text-dock-muted uppercase text-[10px] font-mono tracking-wider block">System Resources</span>
          <span class="font-bold font-mono text-dock-text text-sm mt-0.5 block">
            {{ statusData.details.cpus ? `${statusData.details.cpus} CPUs` : 'N/A' }}
          </span>
          <span class="text-[10px] text-dock-muted font-mono mt-0.5 block">
            {{ statusData.details.memory_total_bytes ? formatBytes(statusData.details.memory_total_bytes) : 'N/A' }}
          </span>
        </div>
      </div>

      <!-- Footer Info -->
      <div class="mt-4 pt-3 border-t border-dock-border/50 flex flex-wrap items-center justify-between text-[11px] text-dock-muted font-mono gap-2">
        <div class="flex items-center space-x-2">
          <span>Target:</span>
          <span class="px-1.5 py-0.5 rounded bg-dock-bg text-dock-text border border-dock-border">
            {{ statusData?.endpoint || 'Detecting...' }}
          </span>
        </div>
        <div class="flex items-center space-x-1.5">
          <span>Last Checked:</span>
          <span class="text-dock-text">{{ formattedTime }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
