<script setup lang="ts">
import AppSidebar from '@/components/layout/AppSidebar.vue'
</script>

<template>
  <div class="flex min-h-screen bg-dock-bg text-dock-text">
    <AppSidebar />
    <main class="flex-1 flex flex-col min-w-0 overflow-y-auto">
      <slot />
    </main>
  </div>
</template>
