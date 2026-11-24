<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { z } from 'zod'
import { AlertCircle, Lock, Mail } from 'lucide-vue-next'
import AuthLayout from '@/layouts/AuthLayout.vue'
import BaseInput from '@/components/common/BaseInput.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const errors = ref<{ email?: string; password?: string }>({})

const loginSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

async function handleSubmit() {
  errors.value = {}
  authStore.clearError()

  const result = loginSchema.safeParse({
    email: email.value,
    password: password.value,
  })

  if (!result.success) {
    result.error.issues.forEach((issue) => {
      const field = issue.path[0] as 'email' | 'password'
      errors.value[field] = issue.message
    })
    return
  }

  const success = await authStore.login(email.value, password.value)
  if (success) {
    router.push('/dashboard')
  }
}
</script>

<template>
  <AuthLayout>
    <div class="bg-dock-surface border border-dock-border rounded-xl p-8 shadow-xl">
      <div class="mb-6">
        <h2 class="text-xl font-bold text-dock-text">Sign In</h2>
        <p class="text-xs text-dock-muted mt-1">
          Access your DockScope infrastructure control center.
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
          placeholder="••••••••"
          :error="errors.password"
          required
          autocomplete="current-password"
        />

        <BaseButton
          type="submit"
          variant="primary"
          class="w-full mt-2"
          :loading="authStore.isLoading"
        >
          Sign In
        </BaseButton>
      </form>

      <div class="mt-6 pt-5 border-t border-dock-border text-center text-xs text-dock-muted">
        Don't have an administrator account?
        <RouterLink to="/register" class="text-dock-primary hover:underline font-medium ml-1">
          Register
        </RouterLink>
      </div>
    </div>
  </AuthLayout>
</template>
