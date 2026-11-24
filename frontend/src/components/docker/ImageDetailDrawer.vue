<script setup lang="ts">
import { computed } from 'vue'
import {
  X,
  Layers,
  HardDrive,
  Cpu,
  Clock,
  Shield,
  Boxes,
  Tag,
  FolderGit2,
  AlertCircle,
  RefreshCw,
  Info,
} from 'lucide-vue-next'
import type { ImageDetail } from '@/types'
import BaseBadge from '@/components/common/BaseBadge.vue'
import { formatBytes, formatTimestamp } from '@/utils/formatters'

const props = defineProps<{
  image: ImageDetail | null
  isOpen: boolean
  loading?: boolean
  error?: string | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const primaryTitle = computed(() => {
  if (!props.image) return 'Image Inspection'
  if (props.image.repo_tags && props.image.repo_tags.length > 0) {
    return props.image.repo_tags[0]
  }
  return `<none>:${props.image.short_id}`
})
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
              <Layers class="w-5 h-5" />
            </div>
            <div class="truncate">
              <div class="flex items-center space-x-2">
                <h2 class="text-base font-bold text-dock-text truncate" :title="primaryTitle">
                  {{ primaryTitle }}
                </h2>
                <BaseBadge v-if="image?.is_dangling" variant="warning" size="sm">
                  Dangling
                </BaseBadge>
                <BaseBadge v-else-if="image" variant="success" size="sm">
                  Tagged
                </BaseBadge>
              </div>
              <p class="text-xs font-mono text-dock-muted truncate mt-0.5">
                {{ image?.id || 'Inspecting...' }}
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
            <p class="text-sm text-dock-muted">Inspecting Docker image metadata...</p>
          </div>

          <!-- Error State -->
          <div v-else-if="error" class="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
            <div class="flex items-center space-x-2 font-semibold mb-1">
              <AlertCircle class="w-4 h-4" />
              <span>Image Inspection Error</span>
            </div>
            <p class="text-xs">{{ error }}</p>
          </div>

          <!-- Image Details View -->
          <template v-else-if="image">
            <!-- Security & Read-Only Notice -->
            <div class="p-3.5 rounded-lg bg-dock-bg border border-dock-border flex items-start space-x-3 text-xs">
              <Shield class="w-4 h-4 text-dock-primary shrink-0 mt-0.5" />
              <div class="leading-relaxed">
                <span class="font-semibold text-dock-text">DockScope Read-Only Inspection:</span>
                <span class="text-dock-muted ml-1">
                  Image build arguments, container environment layers, and sensitive tokens are strictly omitted per security guidelines.
                </span>
              </div>
            </div>

            <!-- Overview Grid -->
            <div class="grid grid-cols-2 gap-4">
              <div class="p-4 rounded-lg bg-dock-bg border border-dock-border">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Image Size</span>
                <span class="text-sm font-bold font-mono text-dock-text">{{ formatBytes(image.size_bytes) }}</span>
                <span v-if="image.virtual_size_bytes && image.virtual_size_bytes !== image.size_bytes" class="text-[10px] text-dock-muted block mt-0.5">
                  Virtual: {{ formatBytes(image.virtual_size_bytes) }}
                </span>
              </div>

              <div class="p-4 rounded-lg bg-dock-bg border border-dock-border">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Referencing Containers</span>
                <span class="text-sm font-bold font-mono text-dock-text">{{ image.containers_count }} workload{{ image.containers_count === 1 ? '' : 's' }}</span>
                <span class="text-[10px] text-dock-muted block mt-0.5">
                  {{ image.containers_count > 0 ? 'Active in container inventory' : 'Unused image cache' }}
                </span>
              </div>

              <div class="p-4 rounded-lg bg-dock-bg border border-dock-border">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Architecture / OS</span>
                <span class="text-xs font-mono text-dock-text font-semibold">
                  {{ image.architecture || 'unknown' }} / {{ image.os || 'linux' }}
                </span>
              </div>

              <div class="p-4 rounded-lg bg-dock-bg border border-dock-border">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Created At</span>
                <span class="text-xs text-dock-text font-semibold">
                  {{ image.created_at ? formatTimestamp(image.created_at) : '—' }}
                </span>
              </div>

              <div v-if="image.author" class="p-4 rounded-lg bg-dock-bg border border-dock-border col-span-2">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Author</span>
                <span class="text-xs font-mono text-dock-text break-all">{{ image.author }}</span>
              </div>

              <div v-if="image.comment" class="p-4 rounded-lg bg-dock-bg border border-dock-border col-span-2">
                <span class="text-[11px] font-medium text-dock-muted uppercase tracking-wider block mb-1">Comment</span>
                <span class="text-xs text-dock-text">{{ image.comment }}</span>
              </div>
            </div>

            <!-- Repository Tags -->
            <div class="space-y-2">
              <div class="flex items-center space-x-2 text-xs font-semibold text-dock-text">
                <Tag class="w-4 h-4 text-dock-primary" />
                <span>Repository Tags</span>
              </div>

              <div v-if="image.repo_tags.length === 0" class="p-3 rounded-lg bg-dock-bg border border-dock-border text-xs text-dock-muted italic">
                No repository tags (&lt;none&gt;:&lt;none&gt; dangling image)
              </div>
              <div v-else class="flex flex-wrap gap-2">
                <span
                  v-for="rt in image.repo_tags"
                  :key="rt"
                  class="px-2.5 py-1 rounded bg-dock-bg border border-dock-border font-mono text-xs text-dock-text"
                >
                  {{ rt }}
                </span>
              </div>
            </div>

            <!-- Container Relationships -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2 text-xs font-semibold text-dock-text">
                  <Boxes class="w-4 h-4 text-dock-primary" />
                  <span>Referencing Containers</span>
                </div>
                <span class="text-[11px] text-dock-muted font-mono">{{ image.containers.length }} linked</span>
              </div>

              <div v-if="image.containers.length === 0" class="p-4 rounded-lg bg-dock-bg border border-dock-border text-center text-xs text-dock-muted">
                No running or stopped containers currently use this image.
              </div>

              <div v-else class="rounded-lg border border-dock-border overflow-hidden">
                <table class="w-full text-left text-xs">
                  <thead class="bg-dock-bg text-dock-muted uppercase font-mono text-[10px] border-b border-dock-border">
                    <tr>
                      <th class="py-2.5 px-3">Container Name</th>
                      <th class="py-2.5 px-3">Short ID</th>
                      <th class="py-2.5 px-3">State</th>
                      <th class="py-2.5 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-dock-border font-mono text-[11px]">
                    <tr v-for="c in image.containers" :key="c.id" class="hover:bg-dock-bg/50">
                      <td class="py-2 px-3 text-dock-text font-bold">{{ c.name }}</td>
                      <td class="py-2 px-3 text-dock-muted">{{ c.short_id }}</td>
                      <td class="py-2 px-3">
                        <span
                          class="px-1.5 py-0.5 rounded text-[10px] font-semibold"
                          :class="c.state === 'running' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-dock-bg text-dock-muted'"
                        >
                          {{ c.state }}
                        </span>
                      </td>
                      <td class="py-2 px-3 text-dock-muted text-[10px]">{{ c.status }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- RootFS Layers -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2 text-xs font-semibold text-dock-text">
                  <HardDrive class="w-4 h-4 text-dock-primary" />
                  <span>Filesystem Layer Hashes</span>
                </div>
                <span class="text-[11px] text-dock-muted font-mono">{{ image.root_fs_layers.length }} layers</span>
              </div>

              <div v-if="image.root_fs_layers.length === 0" class="p-3 rounded-lg bg-dock-bg border border-dock-border text-xs text-dock-muted">
                No layer metadata reported.
              </div>
              <div v-else class="space-y-1 max-h-40 overflow-y-auto rounded-lg border border-dock-border p-2 bg-dock-bg font-mono text-[10px] text-dock-muted">
                <div v-for="(layer, idx) in image.root_fs_layers" :key="idx" class="truncate py-0.5 hover:text-dock-text">
                  <span class="text-dock-primary mr-1">[{{ idx + 1 }}]</span> {{ layer }}
                </div>
              </div>
            </div>

            <!-- Labels -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2 text-xs font-semibold text-dock-text">
                  <Tag class="w-4 h-4 text-dock-primary" />
                  <span>Sanitized Image Labels</span>
                </div>
                <span class="text-[11px] text-dock-muted font-mono">{{ Object.keys(image.labels).length }} labels</span>
              </div>

              <div v-if="Object.keys(image.labels).length === 0" class="p-3 rounded-lg bg-dock-bg border border-dock-border text-xs text-dock-muted">
                No labels on this image.
              </div>
              <div v-else class="space-y-1.5 max-h-40 overflow-y-auto rounded-lg border border-dock-border p-2 bg-dock-bg">
                <div
                  v-for="(v, k) in image.labels"
                  :key="k"
                  class="flex items-start justify-between text-[11px] font-mono py-1 px-1.5 rounded hover:bg-dock-surface"
                >
                  <span class="text-dock-muted mr-3 break-all">{{ k }}:</span>
                  <span class="text-dock-text font-medium text-right break-all">{{ v }}</span>
                </div>
              </div>
            </div>

            <!-- Full Image ID -->
            <div class="p-3 rounded-lg bg-dock-bg border border-dock-border">
              <span class="text-[10px] uppercase font-mono text-dock-muted block mb-1">Full Image Hash (SHA256)</span>
              <span class="text-[11px] font-mono text-dock-muted break-all select-all">{{ image.id }}</span>
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
