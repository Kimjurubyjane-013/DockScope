<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue: string
    id?: string
    label?: string
    type?: string
    placeholder?: string
    error?: string
    disabled?: boolean
    required?: boolean
    autocomplete?: string
  }>(),
  {
    type: 'text',
    placeholder: '',
    disabled: false,
    required: false,
  }
)

defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()
</script>

<template>
  <div class="w-full flex flex-col space-y-1.5">
    <label v-if="label" :for="id" class="text-xs font-medium text-dock-muted">
      {{ label }}
      <span v-if="required" class="text-dock-danger">*</span>
    </label>
    <div class="relative">
      <input
        :id="id"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :autocomplete="autocomplete"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        :class="[
          'w-full px-3.5 py-2.5 bg-dock-bg border rounded-md text-dock-text text-sm transition-all focus:outline-none',
          error
            ? 'border-dock-danger focus:ring-1 focus:ring-dock-danger'
            : 'border-dock-border focus:border-dock-primary focus:ring-1 focus:ring-dock-primary/40',
          disabled ? 'opacity-50 cursor-not-allowed bg-dock-surface/50' : '',
        ]"
      />
      <div v-if="$slots.suffix" class="absolute inset-y-0 right-0 pr-3 flex items-center">
        <slot name="suffix" />
      </div>
    </div>
    <p v-if="error" class="text-xs text-dock-danger mt-1">{{ error }}</p>
  </div>
</template>
