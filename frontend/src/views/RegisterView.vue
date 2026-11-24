<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { z } from 'zod'
import { AlertCircle } from 'lucide-vue-next'
import AuthLayout from '@/layouts/AuthLayout.vue'
import BaseInput from '@/components/common/BaseInput.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const errors = ref<{ email?: string; password?: string; confirmPassword?: string }>({})

const registerSchema = z
  .object({
    email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string().min(1, 'Please confirm your password'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

async function handleSubmit() {
  errors.value = {}
  authStore.clearError()

  const result = registerSchema.safeParse({
    email: email.value,
    password: password.value,
    confirmPassword: confirmPassword.value,
  })

  if (!result.success) {
    result.error.issues.forEach((issue) => {
      const field = issue.path[0] as 'email' | 'password' | 'confirmPassword'
      errors.value[field] = issue.message
    })
    return
  }

  const success = await authStore.register(email.value, password.value)
  if (success) {
    router.push('/dashboard')
  }
}
</script>

<template>
  <AuthLayout>
    <div class="bg-dock-surface border border-dock-border rounded-xl p-8 shadow-xl">
      <div class="mb-6">
        <h2 class="text-xl font-bold text-dock-text">Create Account</h2>
        <p class="text-xs text-dock-muted mt-1">
          Set up your primary DockScope platform administrator credentials.
        </p>
      </div>

      <!-- General Error Alert -->
      <div
        v-if="authStore.error"
        class="mb-6 p-3 bg-dock-danger/10 border border-dock-danger/30 rounded-lg flex items-center space-x-2 text-dock-danger text-xs"
      >
        <AlertCircle class="w-4 h-4 shrink-0" />
        <span>{{ authStore.error }}</span>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <BaseInput
          id="email"
          label="Email Address"
          type="email"
          v-model="email"
          placeholder="admin@dockscope.io"
          :error="errors.email"
          required
          autocomplete="email"
        />

        <BaseInput
          id="password"
          label="Password"
          type="password"
          v-model="password"
          placeholder="At least 8 characters"
          :error="errors.password"
          required
          autocomplete="new-password"
        />

        <BaseInput
          id="confirmPassword"
          label="Confirm Password"
          type="password"
          v-model="confirmPassword"
          placeholder="Repeat password"
          :error="errors.confirmPassword"
          required
          autocomplete="new-password"
        />

        <BaseButton
          type="submit"
          variant="primary"
          class="w-full mt-2"
          :loading="authStore.isLoading"
        >
          Create Administrator Account
        </BaseButton>
      </form>

      <div class="mt-6 pt-5 border-t border-dock-border text-center text-xs text-dock-muted">
        Already have an account?
        <RouterLink to="/login" class="text-dock-primary hover:underline font-medium ml-1">
          Sign In
        </RouterLink>
      </div>
    </div>
  </AuthLayout>
</template>
