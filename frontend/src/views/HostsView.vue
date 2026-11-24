<script setup lang="ts">
import { Server, Terminal, Shield, Plus } from 'lucide-vue-next'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BaseButton from '@/components/common/BaseButton.vue'
</script>

<template>
  <DefaultLayout>
    <AppHeader
      title="Hosts & Infrastructure"
      subtitle="Manage Linux servers, edge nodes, and Docker hosts"
    />

    <div class="p-8">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-base font-semibold text-dock-text">Registered Infrastructure Nodes</h2>
          <p class="text-xs text-dock-muted">Connect bare-metal or cloud instances using the lightweight DockScope Agent</p>
        </div>
        <BaseButton variant="secondary" size="sm" disabled>
          <Plus class="w-3.5 h-3.5 mr-1.5" />
          Add Host
        </BaseButton>
      </div>

      <EmptyState
        :icon="Server"
        title="No Remote Hosts Connected"
        description="Multi-host registration and remote Linux telemetry will be implemented in Milestone 03. You will be able to enroll nodes via a single curl command or SSH keypair."
        milestone="Milestone 03"
        actionLabel="View Agent Architecture"
      >
        <template #extra>
          <div class="w-full bg-dock-bg border border-dock-border rounded-lg p-3 my-4 text-left font-mono text-xs text-dock-muted overflow-x-auto">
            <span class="text-dock-primary">$</span> curl -sSL https://get.dockscope.io/agent | sudo sh -s -- --token [NODE_TOKEN]
          </div>
        </template>
      </EmptyState>
    </div>
  </DefaultLayout>
</template>
