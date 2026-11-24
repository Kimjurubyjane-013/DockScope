<script setup lang="ts">
import { Radio } from 'lucide-vue-next'
</script>

<template>
  <div class="min-h-screen bg-dock-bg text-dock-text flex flex-col justify-center items-center px-4 py-12 selection:bg-dock-primary selection:text-dock-bg">
    <!-- Brand Header -->
    <div class="mb-8 text-center flex flex-col items-center">
      <div class="w-12 h-12 rounded-xl bg-dock-surface border border-dock-primary/40 flex items-center justify-center text-dock-primary shadow-lg mb-4">
        <Radio class="w-7 h-7 text-dock-primary animate-pulse" />
      </div>
      <h1 class="text-2xl font-bold tracking-tight text-dock-text">DockScope</h1>
      <p class="text-xs uppercase tracking-widest text-dock-muted mt-1 font-mono">
        Monitor. Analyze. Control.
      </p>
    </div>

    <!-- Auth Card Slot -->
    <div class="w-full max-w-md">
      <slot />
    </div>

    <!-- Security Notice Footer -->
    <footer class="mt-8 text-center text-xs text-dock-muted/70 font-mono">
      <span>Enterprise Docker & Linux Infrastructure Platform</span>
    </footer>
  </div>
</template>
