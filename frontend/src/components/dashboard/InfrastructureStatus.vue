<script setup lang="ts">
import { Server, Database, Boxes, ShieldCheck, Activity } from 'lucide-vue-next'
import BaseBadge from '@/components/common/BaseBadge.vue'

const services = [
  {
    name: 'DockScope API',
    component: 'FastAPI Backend',
    status: 'Operational',
    variant: 'success' as const,
    detail: 'REST /api/v1 active',
    icon: Activity,
  },
  {
    name: 'Primary Database',
    component: 'PostgreSQL 16',
    status: 'Connected',
    variant: 'success' as const,
    detail: 'Persistent volume mounted',
    icon: Database,
  },
  {
    name: 'Docker Daemon Service',
    component: 'Engine Connector',
    status: 'Milestone 02',
    variant: 'info' as const,
    detail: 'Planned extension point',
    icon: Boxes,
  },
  {
    name: 'Security Engine',
    component: 'CVE & Audit Scanner',
    status: 'Milestone 04',
    variant: 'neutral' as const,
    detail: 'Planned extension point',
    icon: ShieldCheck,
  },
]
</script>

<template>
  <div class="bg-dock-surface border border-dock-border rounded-lg p-5">
    <div class="flex items-center justify-between pb-4 border-b border-dock-border/60">
      <div>
        <h3 class="text-sm font-semibold text-dock-text">Infrastructure Status</h3>
        <p class="text-xs text-dock-muted">Platform services and architectural subsystems</p>
      </div>
      <BaseBadge variant="success" size="sm" dot>Core Active</BaseBadge>
    </div>

    <div class="mt-4 space-y-3">
      <div
        v-for="svc in services"
        :key="svc.name"
        class="p-3 rounded-lg bg-dock-bg/50 border border-dock-border flex items-center justify-between text-xs"
      >
        <div class="flex items-center space-x-3">
          <div class="p-2 rounded bg-dock-surface border border-dock-border text-dock-primary">
            <component :is="svc.icon" class="w-4 h-4" />
          </div>
          <div>
            <h4 class="font-semibold text-dock-text">{{ svc.name }}</h4>
            <p class="text-dock-muted text-[11px] font-mono">{{ svc.detail }}</p>
          </div>
        </div>
        <BaseBadge :variant="svc.variant" size="sm">
          {{ svc.status }}
        </BaseBadge>
      </div>
    </div>
  </div>
</template>
