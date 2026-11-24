<script setup lang="ts">
import { ShieldCheck, ShieldAlert, FileText, Lock } from 'lucide-vue-next'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
</script>

<template>
  <DefaultLayout>
    <AppHeader
      title="Security & Compliance"
      subtitle="Vulnerability scanner, CIS benchmarks, and misconfiguration auditing"
    />

    <div class="p-8">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-base font-semibold text-dock-text">Security Posture</h2>
          <p class="text-xs text-dock-muted">Automated container image CVE detection and daemon hardening</p>
        </div>
      </div>

      <EmptyState
        :icon="ShieldCheck"
        title="Automated Vulnerability Scanning Planned"
        description="The DockScope security intelligence engine (Trivy/Clair vulnerability indexing, exposed secrets scanning, and CIS Docker Benchmark compliance audits) will be introduced in Milestone 04."
        milestone="Milestone 04"
        actionLabel="Review Security Policies"
      >
        <template #extra>
          <div class="w-full max-w-md my-4 space-y-2 text-left">
            <div class="flex items-center justify-between p-2.5 rounded bg-dock-bg border border-dock-border text-xs">
              <span class="text-dock-text">Image Vulnerability Scanner</span>
              <span class="text-[10px] font-mono text-dock-muted">Planned M04</span>
            </div>
            <div class="flex items-center justify-between p-2.5 rounded bg-dock-bg border border-dock-border text-xs">
              <span class="text-dock-text">CIS Docker Benchmarks</span>
              <span class="text-[10px] font-mono text-dock-muted">Planned M04</span>
            </div>
            <div class="flex items-center justify-between p-2.5 rounded bg-dock-bg border border-dock-border text-xs">
              <span class="text-dock-text">Rootless & Secret Exposure Checks</span>
              <span class="text-[10px] font-mono text-dock-muted">Planned M04</span>
            </div>
          </div>
        </template>
      </EmptyState>
    </div>
  </DefaultLayout>
</template>
