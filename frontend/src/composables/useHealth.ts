import { ref } from 'vue'
import { healthApi } from '@/services/api'
import type { HealthResponse, ReadyResponse } from '@/types'

export function useHealth() {
  const health = ref<HealthResponse | null>(null)
  const readiness = ref<ReadyResponse | null>(null)
  const isChecking = ref(false)
  const error = ref<string | null>(null)

  async function check() {
    isChecking.value = true
    error.value = null
    try {
      const [h, r] = await Promise.all([
        healthApi.checkHealth(),
        healthApi.checkReady(),
      ])
      health.value = h
      readiness.value = r
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : 'Health check failed'
    } finally {
      isChecking.value = false
    }
  }

  return {
    health,
    readiness,
    isChecking,
    error,
    check,
  }
}
