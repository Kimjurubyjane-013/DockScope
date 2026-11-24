<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    variant?: 'success' | 'warning' | 'danger' | 'info' | 'neutral'
    size?: 'sm' | 'md'
    dot?: boolean
  }>(),
  {
    variant: 'info',
    size: 'sm',
    dot: false,
  }
)

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'success':
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
    case 'warning':
      return 'bg-amber-500/10 text-amber-400 border-amber-500/30'
    case 'danger':
      return 'bg-rose-500/10 text-rose-400 border-rose-500/30'
    case 'info':
      return 'bg-dock-primary/10 text-dock-primary border-dock-primary/30'
    case 'neutral':
    default:
      return 'bg-dock-muted/10 text-dock-muted border-dock-border'
  }
})

const dotColor = computed(() => {
  switch (props.variant) {
    case 'success':
      return 'bg-emerald-400'
    case 'warning':
      return 'bg-amber-400'
    case 'danger':
      return 'bg-rose-400'
    case 'info':
      return 'bg-dock-primary'
    case 'neutral':
    default:
      return 'bg-dock-muted'
  }
})
</script>

<template>
  <span
    :class="[
      'inline-flex items-center font-mono border rounded-full px-2.5 py-0.5 font-medium tracking-tight',
      size === 'sm' ? 'text-[11px]' : 'text-xs px-3 py-1',
      variantClasses,
    ]"
  >
    <span v-if="dot" :class="['w-1.5 h-1.5 rounded-full mr-1.5', dotColor]" />
    <slot />
  </span>
</template>
