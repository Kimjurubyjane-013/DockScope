<script setup lang="ts">
defineProps<{
  title?: string
  subtitle?: string
}>()
</script>

<template>
  <div class="bg-dock-surface border border-dock-border rounded-lg shadow-sm overflow-hidden flex flex-col">
    <div v-if="title || $slots.header" class="px-5 py-4 border-b border-dock-border/60 flex items-center justify-between">
      <div>
        <h3 v-if="title" class="text-sm font-semibold text-dock-text tracking-tight">{{ title }}</h3>
        <p v-if="subtitle" class="text-xs text-dock-muted mt-0.5">{{ subtitle }}</p>
      </div>
      <slot name="header-actions" />
    </div>

    <div class="p-5 flex-1">
      <slot />
    </div>

    <div v-if="$slots.footer" class="px-5 py-3 bg-dock-bg/40 border-t border-dock-border/60 text-xs text-dock-muted">
      <slot name="footer" />
    </div>
  </div>
</template>
