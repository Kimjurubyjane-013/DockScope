<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Server, Boxes, Cpu, HardDrive, Info, ArrowRight } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import ActivityFeed from '@/components/dashboard/ActivityFeed.vue'
import InfrastructureStatus from '@/components/dashboard/InfrastructureStatus.vue'
import DockerEngineStatus from '@/components/dashboard/DockerEngineStatus.vue'
import { dockerApi } from '@/services/api'

const router = useRouter()
const containerCount = ref<number | null>(null)
const runningCount = ref<number | null>(null)

onMounted(async () => {
  try {
    const res = await dockerApi.listContainers()
    containerCount.value = res.total
    runningCount.value = res.items.filter((c) => c.state.toLowerCase() === 'running').length
  } catch {
    // Keep fallback preview when disconnected
  }
})
</script>

<template>
  <DefaultLayout>
    <AppHeader
      title="Infrastructure Dashboard"
      subtitle="Unified telemetry and monitoring preview across Docker nodes"
    />

    <div class="p-8 space-y-6">
      <!-- Milestone Active Banner -->
      <div class="p-4 rounded-lg bg-dock-surface border border-dock-border flex items-start space-x-3 text-xs">
        <Info class="w-4 h-4 text-dock-primary shrink-0 mt-0.5" />
        <div class="flex-1">
          <span class="font-semibold text-dock-text">Milestone 02.3 Active:</span>
          <span class="text-dock-muted ml-1">
            Docker Engine connection, Container Discovery, and Resource Monitoring active. Real container inventory and resource telemetry available.
          </span>
        </div>
        <button
          @click="router.push('/docker')"
          class="text-xs font-semibold text-dock-primary hover:underline shrink-0 flex items-center space-x-1"
        >
          <span>View Containers</span>
          <ArrowRight class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Real Docker Engine Connection Section -->
      <DockerEngineStatus
        :containers-override="containerCount !== null ? { total: containerCount, running: runningCount ?? 0 } : undefined"
      />

      <!-- Key Metrics Row -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          title="Total Hosts"
          value="1"
          unit="host"
          subtext="Local controller instance"
          :icon="Server"
          badgeText="Active"
          status="success"
          :isPreview="true"
        />

        <div class="cursor-pointer" @click="router.push('/docker')">
          <StatCard
            title="Containers"
            :value="containerCount !== null ? containerCount : 4"
            unit="containers"
            :subtext="runningCount !== null ? `${runningCount} running on host` : 'DockScope core stack'"
            :icon="Boxes"
            :badgeText="runningCount !== null ? (runningCount > 0 ? 'Discovered' : 'Idle') : 'Healthy'"
            :status="runningCount !== null ? (runningCount > 0 ? 'success' : 'info') : 'info'"
            :isPreview="containerCount === null"
          />
        </div>

        <StatCard
          title="CPU Usage"
          value="1.8"
          unit="%"
          subtext="4 Cores available"
          :icon="Cpu"
          badgeText="Nominal"
          status="success"
          :isPreview="true"
        />

        <StatCard
          title="Memory Usage"
          value="240"
          unit="MB"
          subtext="16 GB Total system RAM"
          :icon="HardDrive"
          badgeText="Optimal"
          status="success"
          :isPreview="true"
        />
      </div>

      <!-- Infrastructure Status & Activity Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <InfrastructureStatus />
        <ActivityFeed />
      </div>
    </div>
  </DefaultLayout>
</template>