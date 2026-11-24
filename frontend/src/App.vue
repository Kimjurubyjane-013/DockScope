<script setup lang="ts">
import { RouterView } from 'vue-router'
import { Radio } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

<template>
  <div id="dockscope-app" class="min-h-screen bg-dock-bg text-dock-text font-sans antialiased">
    <!-- Initial Loading State while checking authentication session -->
    <div
      v-if="!authStore.isInitialized"
      class="min-h-screen flex flex-col items-center justify-center space-y-4"
    >
      <div class="w-12 h-12 rounded-xl bg-dock-surface border border-dock-primary/40 flex items-center justify-center text-dock-primary shadow-lg animate-pulse">
        <Radio class="w-6 h-6 text-dock-primary" />
      </div>
      <p class="text-xs font-mono text-dock-muted uppercase tracking-widest">
        Initializing DockScope...
      </p>
    </div>

    <!-- Main Application Router View -->
    <RouterView v-else />
  </div>
</template>
