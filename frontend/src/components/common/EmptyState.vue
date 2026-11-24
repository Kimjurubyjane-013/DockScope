<script setup lang="ts">
import { type Component } from 'vue'
import BaseBadge from './BaseBadge.vue'

defineProps<{
  icon?: Component
  title: string
  description: string
  milestone?: string
  actionLabel?: string
}>()

defineEmits<{
  (e: 'action'): void
}>()
</script>

<template>
  <div class="bg-dock-surface border border-dock-border rounded-xl p-10 text-center flex flex-col items-center justify-center max-w-xl mx-auto my-8">
    <div v-if="icon" class="p-4 rounded-xl bg-dock-bg border border-dock-border text-dock-primary mb-4">
      <component :is="icon" class="w-8 h-8" />
    </div>

    <BaseBadge v-if="milestone" variant="info" size="sm" class="mb-3">
      Planned for {{ milestone }}
    </BaseBadge>

    <h3 class="text-base font-semibold text-dock-text tracking-tight mb-2">{{ title }}</h3>
    <p class="text-sm text-dock-muted max-w-md leading-relaxed mb-6">{{ description }}</p>

    <slot name="extra" />

    <button
      v-if="actionLabel"
      @click="$emit('action')"
      class="px-4 py-2 text-xs font-medium text-dock-primary border border-dock-primary/40 rounded-md hover:bg-dock-primary/10 transition-colors"
    >
      {{ actionLabel }}
    </button>
  </div>
</template>
