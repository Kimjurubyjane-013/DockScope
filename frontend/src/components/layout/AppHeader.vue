<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Activity, Database, CheckCircle2, AlertTriangle } from 'lucide-vue-next'
import { healthApi } from '@/services/api'

defineProps<{
  title: string
  subtitle?: string
}>()

const apiStatus = ref<'online' | 'checking' | 'error'>('checking')
const dbStatus = ref<'connected' | 'checking' | 'error'>('checking')

async function checkSystemHealth() {
  try {
    const health = await healthApi.checkHealth()
    apiStatus.value = health.status === 'healthy' ? 'online' : 'error'
  } catch {
    apiStatus.value = 'error'
  }

  try {
    const ready = await healthApi.checkReady()
    dbStatus.value = ready.database === 'connected' ? 'connected' : 'error'
  } catch {
    dbStatus.value = 'error'
  }
}

onMounted(() => {
  checkSystemHealth()
})
</script>

<template>
  <header class="h-16 bg-dock-surface/60 backdrop-blur border-b border-dock-border px-8 flex items-center justify-between sticky top-0 z-10">
    <div>
      <h1 class="text-lg font-bold text-dock-text tracking-tight">{{ title }}</h1>
      <p v-if="subtitle" class="text-xs text-dock-muted">{{ subtitle }}</p>
    </div>

    <!-- System Status Badges -->
    <div class="flex items-center space-x-3 text-xs font-mono">
      <!-- API Status -->
      <div class="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-dock-bg border border-dock-border text-dock-muted">
        <Activity class="w-3.5 h-3.5 text-dock-primary" />
        <span>API:</span>
        <span
          :class="[
            'font-medium',
            apiStatus === 'online' ? 'text-dock-success' : apiStatus === 'checking' ? 'text-dock-muted' : 'text-dock-danger'
          ]"
        >
          {{ apiStatus }}
        </span>
      </div>

      <!-- DB Status -->
      <div class="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-dock-bg border border-dock-border text-dock-muted">
        <Database class="w-3.5 h-3.5 text-dock-secondary" />
        <span>DB:</span>
        <span
          :class="[
            'font-medium',
            dbStatus === 'connected' ? 'text-dock-success' : dbStatus === 'checking' ? 'text-dock-muted' : 'text-dock-danger'
          ]"
        >
          {{ dbStatus }}
        </span>
      </div>
    </div>
  </header>
</template>
