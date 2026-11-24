<script setup lang="ts">
import { Info, AlertCircle, CheckCircle2, ShieldAlert } from 'lucide-vue-next'
import type { ActivityEvent } from '@/types'

const sampleEvents: ActivityEvent[] = [
  {
    id: 'evt-1',
    timestamp: 'Just now',
    level: 'info',
    source: 'DockScope Core',
    message: 'Milestone 01 foundation initialized successfully.',
  },
  {
    id: 'evt-2',
    timestamp: '2 mins ago',
    level: 'success',
    source: 'PostgreSQL',
    message: 'Database schema migration 0001_initial_users verified.',
  },
  {
    id: 'evt-3',
    timestamp: '5 mins ago',
    level: 'info',
    source: 'Auth Service',
    message: 'Argon2id password hashing and JWT service configured.',
  },
  {
    id: 'evt-4',
    timestamp: 'Scheduled',
    level: 'warning',
    source: 'Docker Agent',
    message: 'Real Docker Engine integration planned for Milestone 02.',
  },
]
</script>

<template>
  <div class="bg-dock-surface border border-dock-border rounded-lg p-5">
    <div class="flex items-center justify-between pb-4 border-b border-dock-border/60">
      <div>
        <h3 class="text-sm font-semibold text-dock-text">Recent Activity</h3>
        <p class="text-xs text-dock-muted">Platform events and system lifecycle history</p>
      </div>
      <span class="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-dock-bg text-dock-muted border border-dock-border">
        Sample Preview
      </span>
    </div>

    <div class="mt-4 divide-y divide-dock-border/40">
      <div
        v-for="event in sampleEvents"
        :key="event.id"
        class="py-3 flex items-start space-x-3 text-xs"
      >
        <div class="mt-0.5 shrink-0">
          <CheckCircle2 v-if="event.level === 'success'" class="w-4 h-4 text-dock-success" />
          <AlertCircle v-else-if="event.level === 'warning'" class="w-4 h-4 text-dock-warning" />
          <ShieldAlert v-else-if="event.level === 'danger'" class="w-4 h-4 text-dock-danger" />
          <Info v-else class="w-4 h-4 text-dock-primary" />
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between mb-0.5">
            <span class="font-medium text-dock-text font-mono text-[11px]">{{ event.source }}</span>
            <span class="text-dock-muted text-[10px] font-mono">{{ event.timestamp }}</span>
          </div>
          <p class="text-dock-muted leading-relaxed truncate">{{ event.message }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
