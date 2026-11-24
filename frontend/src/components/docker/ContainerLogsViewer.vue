<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import {
  Terminal,
  RefreshCw,
  Copy,
  Check,
  Search,
  Filter,
  AlertCircle,
  Clock,
  Shield,
  Layers,
  FileText,
} from 'lucide-vue-next'
import { dockerApi } from '@/services/api'
import type { ContainerLogsResponse, LogEntry } from '@/types'

const props = defineProps<{
  containerId: string
  containerName?: string
}>()

const logsResponse = ref<ContainerLogsResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const copied = ref(false)

// Query parameters
const tail = ref<number>(100)
const showTimestamps = ref<boolean>(true)
const includeStdout = ref<boolean>(true)
const includeStderr = ref<boolean>(true)
const searchQuery = ref<string>('')

const tailOptions = [50, 100, 250, 500, 1000]

async function fetchLogs() {
  if (!props.containerId) return
  loading.value = true
  error.value = null
  try {
    logsResponse.value = await dockerApi.getContainerLogs(props.containerId, {
      tail: tail.value,
      timestamps: showTimestamps.value,
      stdout: includeStdout.value,
      stderr: includeStderr.value,
    })
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Failed to retrieve container logs from Docker Engine.'
  } finally {
    loading.value = false
  }
}

watch(
  () => props.containerId,
  (newId) => {
    if (newId) {
      fetchLogs()
    }
  },
  { immediate: true }
)

watch([tail, showTimestamps, includeStdout, includeStderr], () => {
  fetchLogs()
})

// Filtered log lines by search query
const filteredLines = computed<LogEntry[]>(() => {
  if (!logsResponse.value?.lines) return []
  if (!searchQuery.value.trim()) return logsResponse.value.lines
  const q = searchQuery.value.trim().toLowerCase()
  return logsResponse.value.lines.filter((entry) => {
    const msgMatch = entry.message.toLowerCase().includes(q)
    const tsMatch = entry.timestamp ? entry.timestamp.toLowerCase().includes(q) : false
    const streamMatch = entry.stream.toLowerCase().includes(q)
    return msgMatch || tsMatch || streamMatch
  })
})

// Copy plain text logs to clipboard
async function copyToClipboard() {
  if (!logsResponse.value?.lines) return
  const text = filteredLines.value
    .map((e) => {
      const parts: string[] = []
      if (showTimestamps.value && e.timestamp) parts.push(`[${e.timestamp}]`)
      parts.push(`[${e.stream.toUpperCase()}]`)
      parts.push(e.message)
      return parts.join(' ')
    })
    .join('\n')

  try {
    if (typeof navigator !== 'undefined' && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      await navigator.clipboard.writeText(text)
    } else if (typeof document !== 'undefined') {
      const textarea = document.createElement('textarea')
      textarea.value = text
      document.body.appendChild(textarea)
      textarea.select()
      try {
        document.execCommand('copy')
      } catch {
        // Fallback in environments where execCommand is restricted
      }
      document.body.removeChild(textarea)
    }
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch {
    copied.value = false
  }
}

function formatCollectedAt(iso?: string): string {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleTimeString()
  } catch {
    return iso
  }
}
</script>

<template>
  <div class="space-y-4">
    <!-- Security & Bounded Log Policy Banner -->
    <div class="p-3.5 rounded-lg bg-dock-bg border border-dock-border flex items-start space-x-3 text-xs">
      <Shield class="w-4 h-4 text-dock-primary shrink-0 mt-0.5" />
      <div class="leading-relaxed">
        <span class="font-semibold text-dock-text">DockScope Logs Intelligence (M02.5):</span>
        <span class="text-dock-muted ml-1">
          Non-streaming one-shot retrieval with stream demuxing. Sensitive credentials, bearer tokens, and connection strings are automatically redacted.
        </span>
      </div>
    </div>

    <!-- Terminal Controls Toolbar -->
    <div class="p-3.5 rounded-xl bg-dock-surface border border-dock-border space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <!-- Stream Toggles & Tail Selector -->
        <div class="flex flex-wrap items-center gap-2">
          <!-- Tail limit -->
          <div class="flex items-center space-x-1.5 text-xs text-dock-muted font-mono">
            <span>Tail:</span>
            <select
              v-model="tail"
              :disabled="loading"
              class="px-2 py-1 text-xs bg-dock-bg border border-dock-border rounded-md text-dock-text focus:outline-none focus:border-dock-primary font-mono"
            >
              <option v-for="t in tailOptions" :key="t" :value="t">{{ t }} lines</option>
            </select>
          </div>

          <!-- Timestamps Toggle -->
          <button
            @click="showTimestamps = !showTimestamps"
            :disabled="loading"
            class="px-2.5 py-1 text-xs rounded-md border font-mono transition-colors flex items-center space-x-1"
            :class="showTimestamps
              ? 'bg-dock-primary/10 border-dock-primary/30 text-dock-primary'
              : 'bg-dock-bg border-dock-border text-dock-muted hover:text-dock-text'"
            title="Toggle timestamp display"
          >
            <Clock class="w-3.5 h-3.5" />
            <span>Timestamps</span>
          </button>

          <!-- stdout toggle -->
          <button
            @click="includeStdout = !includeStdout"
            :disabled="loading"
            class="px-2 py-1 text-xs rounded-md border font-mono transition-colors"
            :class="includeStdout
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 font-semibold'
              : 'bg-dock-bg border-dock-border text-dock-muted hover:text-dock-text'"
            title="Toggle stdout stream"
          >
            stdout
          </button>

          <!-- stderr toggle -->
          <button
            @click="includeStderr = !includeStderr"
            :disabled="loading"
            class="px-2 py-1 text-xs rounded-md border font-mono transition-colors"
            :class="includeStderr
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-400 font-semibold'
              : 'bg-dock-bg border-dock-border text-dock-muted hover:text-dock-text'"
            title="Toggle stderr stream"
          >
            stderr
          </button>
        </div>

        <!-- Action Buttons: Copy & Refresh -->
        <div class="flex items-center space-x-2">
          <button
            @click="copyToClipboard"
            :disabled="loading || filteredLines.length === 0"
            class="px-2.5 py-1 text-xs rounded-md bg-dock-bg border border-dock-border text-dock-muted hover:text-dock-text hover:border-dock-primary/50 transition-colors disabled:opacity-40 inline-flex items-center space-x-1"
            title="Copy logs to clipboard"
          >
            <Check v-if="copied" class="w-3.5 h-3.5 text-emerald-400" />
            <Copy v-else class="w-3.5 h-3.5" />
            <span>{{ copied ? 'Copied!' : 'Copy' }}</span>
          </button>

          <button
            @click="fetchLogs"
            :disabled="loading"
            class="px-2.5 py-1 text-xs rounded-md bg-dock-primary/10 border border-dock-primary/30 text-dock-primary hover:bg-dock-primary/20 transition-colors disabled:opacity-50 inline-flex items-center space-x-1"
            title="Refresh container logs"
          >
            <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': loading }" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      <!-- Search Input within Logs -->
      <div class="relative">
        <Search class="w-3.5 h-3.5 text-dock-muted absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Filter log output (regex or keyword)..."
          class="w-full pl-8 pr-20 py-1.5 text-xs bg-dock-bg border border-dock-border rounded-lg text-dock-text placeholder:text-dock-muted focus:outline-none focus:border-dock-primary font-mono transition-colors"
        />
        <div class="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center space-x-1.5 text-[10px] font-mono text-dock-muted">
          <span v-if="searchQuery">
            {{ filteredLines.length }} / {{ logsResponse?.total_lines || 0 }} lines
          </span>
          <span v-else-if="logsResponse">
            {{ logsResponse.total_lines }} lines
          </span>
        </div>
      </div>
    </div>

    <!-- Terminal Window Container -->
    <div class="rounded-xl border border-dock-border bg-[#080c16] overflow-hidden shadow-2xl flex flex-col font-mono">
      <!-- Terminal Window Bar -->
      <div class="px-4 py-2.5 bg-[#0e1626] border-b border-dock-border/70 flex items-center justify-between text-xs">
        <div class="flex items-center space-x-2">
          <!-- Terminal control dots -->
          <div class="flex items-center space-x-1.5 mr-2">
            <span class="w-2.5 h-2.5 rounded-full bg-rose-500/80 inline-block"></span>
            <span class="w-2.5 h-2.5 rounded-full bg-amber-500/80 inline-block"></span>
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500/80 inline-block"></span>
          </div>
          <Terminal class="w-3.5 h-3.5 text-dock-primary" />
          <span class="font-semibold text-dock-text text-[11px] tracking-wide">
            {{ containerName || 'container' }} &mdash; logs
          </span>
        </div>

        <div class="flex items-center space-x-3 text-[10px] text-dock-muted">
          <span v-if="logsResponse?.truncated" class="px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-400 font-bold">
            TRUNCATED (tail={{ tail }})
          </span>
          <span v-if="logsResponse?.collected_at">
            {{ formatCollectedAt(logsResponse.collected_at) }}
          </span>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading && !logsResponse" class="py-20 text-center space-y-3">
        <RefreshCw class="w-7 h-7 text-dock-primary animate-spin mx-auto" />
        <p class="text-xs text-dock-muted">Retrieving container log stream from Docker Engine...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="p-6 text-center space-y-3 my-4">
        <div class="p-3 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400 w-fit mx-auto">
          <AlertCircle class="w-6 h-6" />
        </div>
        <h4 class="text-xs font-semibold text-rose-300">Log Retrieval Error</h4>
        <p class="text-xs text-rose-400/80 max-w-md mx-auto">{{ error }}</p>
        <div>
          <button
            @click="fetchLogs"
            class="px-3 py-1.5 text-xs bg-dock-surface border border-dock-border rounded-lg text-dock-text hover:border-dock-primary/50 transition-colors"
          >
            Retry Log Query
          </button>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredLines.length === 0" class="py-16 text-center space-y-2">
        <FileText class="w-8 h-8 text-dock-muted mx-auto opacity-40" />
        <p class="text-xs text-dock-text font-semibold">No Log Output</p>
        <p class="text-[11px] text-dock-muted max-w-xs mx-auto">
          {{ searchQuery
            ? 'No log lines match your current search query.'
            : 'No logs have been recorded for this container workload yet.' }}
        </p>
        <div v-if="searchQuery" class="pt-2">
          <button @click="searchQuery = ''" class="text-xs text-dock-primary hover:underline">
            Clear search filter
          </button>
        </div>
      </div>

      <!-- Terminal Output Lines -->
      <div
        v-else
        class="max-h-[460px] overflow-y-auto p-3 text-xs space-y-0.5 divide-y divide-dock-border/10 select-text"
      >
        <div
          v-for="(line, idx) in filteredLines"
          :key="idx"
          class="flex items-start space-x-2 py-0.5 hover:bg-white/[0.03] rounded px-1 group"
        >
          <!-- Line number -->
          <span class="text-[10px] text-dock-muted/50 select-none w-8 text-right shrink-0 pt-0.5 font-mono">
            {{ idx + 1 }}
          </span>

          <!-- Timestamp -->
          <span
            v-if="showTimestamps && line.timestamp"
            class="text-[10px] text-dock-muted select-none shrink-0 pt-0.5 font-mono"
            :title="line.timestamp"
          >
            {{ line.timestamp }}
          </span>

          <!-- Stream Badge -->
          <span
            class="text-[9px] uppercase px-1 py-0.2 rounded font-bold shrink-0 select-none border"
            :class="line.stream === 'stderr'
              ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
              : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'"
          >
            {{ line.stream }}
          </span>

          <!-- Message Text -->
          <span
            class="text-dock-text break-all whitespace-pre-wrap font-mono flex-1 leading-relaxed"
            :class="line.stream === 'stderr' ? 'text-rose-200/90' : 'text-slate-200'"
          >{{ line.message }}</span>
        </div>
      </div>

      <!-- Terminal Status Footer -->
      <div class="px-4 py-2 bg-[#0a0f1d] border-t border-dock-border/60 flex items-center justify-between text-[10px] text-dock-muted font-mono">
        <div class="flex items-center space-x-2">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block"></span>
          <span>Redaction: Active (credentials & tokens masked)</span>
        </div>
        <div class="flex items-center space-x-3">
          <span>Lines: {{ filteredLines.length }} / {{ logsResponse?.total_lines || 0 }}</span>
          <span>Tail: {{ tail }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
