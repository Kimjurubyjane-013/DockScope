import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import { authApi } from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isInitialized = ref(false)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!user.value)

  async function initAuth(): Promise<boolean> {
    if (isInitialized.value) return isAuthenticated.value

    isLoading.value = true
    try {
      // Guard with a 5-second timeout race so router navigation is never permanently blocked
      const timeoutPromise = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('Session verification timed out')), 5000)
      )
      user.value = await Promise.race([authApi.getMe(), timeoutPromise])
      return true
    } catch {
      user.value = null
      return false
    } finally {
      isLoading.value = false
      isInitialized.value = true
    }
  }

  async function login(email: string, password: string): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      await authApi.login({ email, password })
      // Fetch user profile after session cookie is established
      user.value = await authApi.getMe()
      return true
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : 'Login failed'
      user.value = null
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function register(email: string, password: string): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      await authApi.register({ email, password })
      // Automatically log in after registration
      return await login(email, password)
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : 'Registration failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function logout(): Promise<void> {
    try {
      await authApi.logout()
    } catch (e) {
      console.warn('Logout error:', e)
    } finally {
      user.value = null
      error.value = null
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    user,
    isAuthenticated,
    isInitialized,
    isLoading,
    error,
    initAuth,
    login,
    register,
    logout,
    clearError,
  }
})
