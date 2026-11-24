<script setup lang="ts">
import { computed } from 'vue'
import {
  X,
  HardDrive,
  Clock,
  Shield,
  Boxes,
  Tag,
  AlertCircle,
  RefreshCw,
  Folder,
  Layers,
  Settings,
} from 'lucide-vue-next'
import type { VolumeDetail } from '@/types'
import BaseBadge from '@/components/common/BaseBadge.vue'
import { formatTimestamp } from '@/utils/formatters'

const props = defineProps<{
  volume: VolumeDetail | null
  isOpen: boolean
  loading?: boolean
  error?: string | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()
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
              <HardDrive class="w-5 h-5" />
            </div>
            <div class="truncate">
              <div class="flex items-center space-x-2">
                <h2 class="text-base font-bold text-dock-text truncate" :title="volume?.name">
                  {{ volume?.name || 'Volume Inspection' }}
                </h2>
                <BaseBadge v-if="volume?.is_in_use" variant="success" size="sm">
                  In Use
                </BaseBadge>
                <BaseBadge v-else-if="volume" variant="neutral" size="sm">
                  Unused
                </BaseBadge>
              </div>
              <p class="text-xs font-mono text-dock-muted truncate mt-0.5">
                Driver: {{ volume?.driver || 'local' }} | Scope: {{ volume?.scope || 'local' }}
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

        <!-- Drawer Content -->
        <div class="flex-1 overflow-y-auto p-6 space-y-6">
          <!-- Loading State -->
          <div v-if="loading" class="py-16 text-center">
            <RefreshCw class="w-8 h-8 text-dock-primary animate-spin mx-auto mb-3" />
            <p class="text-sm text-dock-muted">Inspecting Docker volume metadata...</p>
          </div>

          <!-- Error State -->
          <div v-else-if="error" class="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
            <div class="flex items-center space-x-2 font-semibold mb-1">
              <AlertCircle class="w-4 h-4" />
              <span>Volume Inspection Error</span>
            </div>
            <p class="text-xs">{{ error }}</p>
          </div>

          <!-- Volume Details View -->
          <template v-else-if="volume">
            <!-- Security & Read-Only Notice -->
            <div class="p-3.5 rounded-lg bg-dock-bg border border-dock-border flex items-start space-x-3 text-xs">
              <Shield class="w-4 h-4 text-dock-primary shrink-0 mt-0.5" />
              <div class="leading-relaxed">
                <span class="font-semibold text-dock-text">DockScope Read-Only Inspection:</span>
                <span class="text-dock-muted ml-1">
                  Volume file contents are not inspected or mounted, and host file paths are sanitized per storage privacy guidelines.
                </span>
              </div>
            </div>

            <!-- Overview Grid -->
            <div class="grid grid-cols-2 gap-4">
              <div class="p-4 rounded-lg bg-dock-bg border border-dock-border">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Driver</span>
                <span class="text-sm font-bold font-mono text-dock-text">{{ volume.driver }}</span>
              </div>

              <div class="p-4 rounded-lg bg-dock-bg border border-dock-border">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Scope</span>
                <span class="text-sm font-bold font-mono text-dock-text uppercase">{{ volume.scope }}</span>
              </div>

              <div class="p-4 rounded-lg bg-dock-bg border border-dock-border">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Containers Referencing</span>
                <span class="text-sm font-bold font-mono text-dock-text">{{ volume.containers_count }} workload{{ volume.containers_count === 1 ? '' : 's' }}</span>
                <span class="text-[10px] text-dock-muted block mt-0.5">
                  {{ volume.is_in_use ? 'Mounted by active containers' : 'Available for attachment' }}
                </span>
              </div>

              <div class="p-4 rounded-lg bg-dock-bg border border-dock-border">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Created At</span>
                <span class="text-xs text-dock-text font-semibold">
                  {{ volume.created_at ? formatTimestamp(volume.created_at) : '—' }}
                </span>
              </div>
            </div>

            <!-- Mountpoint Path -->
            <div class="space-y-2">
              <div class="flex items-center space-x-2 text-xs font-semibold text-dock-text">
                <Folder class="w-4 h-4 text-dock-primary" />
                <span>Host Storage Mountpoint</span>
              </div>
              <div class="p-3 rounded-lg bg-dock-bg border border-dock-border">
                <code class="text-xs font-mono text-dock-text break-all select-all">
                  {{ volume.mountpoint || 'Default Docker storage driver path' }}
                </code>
              </div>
            </div>

            <!-- Referencing Containers & Mount Destinations -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2 text-xs font-semibold text-dock-text">
                  <Boxes class="w-4 h-4 text-dock-primary" />
                  <span>Referencing Containers & Mount Targets</span>
                </div>
                <span class="text-[11px] text-dock-muted font-mono">{{ volume.containers.length }} mounted</span>
              </div>

              <div v-if="volume.containers.length === 0" class="p-4 rounded-lg bg-dock-bg border border-dock-border text-center text-xs text-dock-muted">
                No active or stopped containers are currently mounting this volume.
              </div>

              <div v-else class="rounded-lg border border-dock-border overflow-hidden">
                <table class="w-full text-left text-xs">
                  <thead class="bg-dock-bg text-dock-muted uppercase font-mono text-[10px] border-b border-dock-border">
                    <tr>
                      <th class="py-2.5 px-3">Container</th>
                      <th class="py-2.5 px-3">Container Target Path</th>
                      <th class="py-2.5 px-3">Mode</th>
                      <th class="py-2.5 px-3">State</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-dock-border font-mono text-[11px]">
                    <tr v-for="c in volume.containers" :key="c.id" class="hover:bg-dock-bg/50">
                      <td class="py-2.5 px-3 text-dock-text font-bold">
                        {{ c.name }}
                        <span class="text-[10px] text-dock-muted block font-normal">{{ c.short_id }}</span>
                      </td>
                      <td class="py-2.5 px-3 text-dock-text break-all">
                        {{ c.destination }}
                      </td>
                      <td class="py-2.5 px-3">
                        <span
                          class="px-1.5 py-0.5 rounded text-[10px] uppercase font-semibold"
                          :class="c.read_only ? 'bg-amber-500/10 text-amber-400' : 'bg-dock-primary/10 text-dock-primary'"
                        >
                          {{ c.mode || (c.read_only ? 'ro' : 'rw') }}
                        </span>
                      </td>
                      <td class="py-2.5 px-3">
                        <span
                          class="px-1.5 py-0.5 rounded text-[10px]"
                          :class="c.state === 'running' ? 'bg-emerald-500/10 text-emerald-400 font-semibold' : 'bg-dock-bg text-dock-muted'"
                        >
                          {{ c.state }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Driver Options -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2 text-xs font-semibold text-dock-text">
                  <Settings class="w-4 h-4 text-dock-primary" />
                  <span>Driver Options</span>
                </div>
                <span class="text-[11px] text-dock-muted font-mono">{{ Object.keys(volume.options).length }} options</span>
              </div>

              <div v-if="Object.keys(volume.options).length === 0" class="p-3 rounded-lg bg-dock-bg border border-dock-border text-xs text-dock-muted">
                No custom driver options configured (default driver defaults).
              </div>
              <div v-else class="space-y-1.5 rounded-lg border border-dock-border p-2 bg-dock-bg">
                <div
                  v-for="(v, k) in volume.options"
                  :key="k"
                  class="flex items-start justify-between text-[11px] font-mono py-1 px-1.5 rounded hover:bg-dock-surface"
                >
                  <span class="text-dock-muted mr-3 break-all">{{ k }}:</span>
                  <span class="text-dock-text font-medium text-right break-all">{{ v }}</span>
                </div>
              </div>
            </div>

            <!-- Sanitized Labels -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2 text-xs font-semibold text-dock-text">
                  <Tag class="w-4 h-4 text-dock-primary" />
                  <span>Sanitized Volume Labels</span>
                </div>
                <span class="text-[11px] text-dock-muted font-mono">{{ Object.keys(volume.labels).length }} labels</span>
              </div>

              <div v-if="Object.keys(volume.labels).length === 0" class="p-3 rounded-lg bg-dock-bg border border-dock-border text-xs text-dock-muted">
                No labels attached to this volume.
              </div>
              <div v-else class="space-y-1.5 max-h-40 overflow-y-auto rounded-lg border border-dock-border p-2 bg-dock-bg">
                <div
                  v-for="(v, k) in volume.labels"
                  :key="k"
                  class="flex items-start justify-between text-[11px] font-mono py-1 px-1.5 rounded hover:bg-dock-surface"
                >
                  <span class="text-dock-muted mr-3 break-all">{{ k }}:</span>
                  <span class="text-dock-text font-medium text-right break-all">{{ v }}</span>
                </div>
              </div>
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
