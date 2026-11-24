<script setup lang="ts">
import { computed } from 'vue'
import { Loader2 } from 'lucide-vue-next'

const props = withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost'
    size?: 'sm' | 'md' | 'lg'
    loading?: boolean
    disabled?: boolean
    type?: 'button' | 'submit' | 'reset'
  }>(),
  {
    variant: 'primary',
    size: 'md',
    loading: false,
    disabled: false,
    type: 'button',
  }
)

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-dock-primary text-dock-bg font-semibold hover:bg-dock-primary-hover shadow-sm disabled:opacity-50 disabled:cursor-not-allowed'
    case 'secondary':
      return 'bg-dock-surface text-dock-text border border-dock-border hover:bg-dock-hover disabled:opacity-50 disabled:cursor-not-allowed'
    case 'outline':
      return 'bg-transparent text-dock-primary border border-dock-primary hover:bg-dock-primary/10 disabled:opacity-50 disabled:cursor-not-allowed'
    case 'danger':
      return 'bg-dock-danger/20 text-dock-danger border border-dock-danger/30 hover:bg-dock-danger/30 disabled:opacity-50 disabled:cursor-not-allowed'
    case 'ghost':
      return 'bg-transparent text-dock-muted hover:text-dock-text hover:bg-dock-surface disabled:opacity-50 disabled:cursor-not-allowed'
    default:
      return ''
  }
})

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'px-3 py-1.5 text-xs rounded'
    case 'lg':
      return 'px-6 py-3 text-base rounded-lg'
    case 'md':
    default:
      return 'px-4 py-2 text-sm rounded-md'
  }
})
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="[
      'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-dock-primary/50',
      variantClasses,
      sizeClasses,
    ]"
  >
    <Loader2 v-if="loading" class="w-4 h-4 mr-2 animate-spin" />
    <slot />
  </button>
</template>
