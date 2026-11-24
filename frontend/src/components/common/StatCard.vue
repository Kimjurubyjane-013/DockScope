<script setup lang="ts">
import { type Component } from 'vue'
import BaseBadge from './BaseBadge.vue'

defineProps<{
  title: string
  value: string | number
  unit?: string
  subtext?: string
  icon?: Component
  status?: 'success' | 'warning' | 'danger' | 'info' | 'neutral'
  badgeText?: string
  isPreview?: boolean
}>()
</script>

<template>
  <div class="bg-dock-surface border border-dock-border rounded-lg p-5 flex flex-col justify-between hover:border-dock-border/80 transition-colors">
    <div class="flex items-start justify-between">
      <div class="flex items-center space-x-3">
        <div v-if="icon" class="p-2.5 rounded-md bg-dock-bg border border-dock-border text-dock-primary">
          <component :is="icon" class="w-5 h-5" />
        </div>
        <div>
          <span class="text-xs uppercase tracking-wider font-medium text-dock-muted">{{ title }}</span>
          <div class="flex items-baseline space-x-1.5 mt-1">
            <span class="text-2xl font-bold font-mono text-dock-text">{{ value }}</span>
            <span v-if="unit" class="text-xs text-dock-muted font-mono">{{ unit }}</span>
          </div>
        </div>
      </div>
      <BaseBadge v-if="badgeText" :variant="status || 'neutral'" size="sm">
        {{ badgeText }}
      </BaseBadge>
    </div>

    <div class="mt-4 pt-3 border-t border-dock-border/50 flex items-center justify-between text-xs">
      <span class="text-dock-muted">{{ subtext || 'Infrastructure Metric' }}</span>
      <span v-if="isPreview" class="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-dock-bg text-dock-muted border border-dock-border/80">
        Preview
      </span>
    </div>
  </div>
</template>
