<script setup lang="ts">
import { ref } from 'vue'
import { User as UserIcon, Shield, Palette, Save, Check } from 'lucide-vue-next'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseInput from '@/components/common/BaseInput.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseBadge from '@/components/common/BaseBadge.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const selectedTheme = ref('infrastructure-dark')
const saveSuccess = ref(false)

function savePreferences() {
  saveSuccess.value = true
  setTimeout(() => {
    saveSuccess.value = false
  }, 2500)
}
</script>

<template>
  <DefaultLayout>
    <AppHeader
      title="Settings & Profile"
      subtitle="Account credentials, system preferences, and session controls"
    />

    <div class="p-8 max-w-4xl space-y-6">
      <!-- Profile Card -->
      <BaseCard title="Administrator Profile" subtitle="Your DockScope account credentials and system identity">
        <div class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <BaseInput
              label="Email Address"
              :modelValue="authStore.user?.email || 'admin@dockscope.io'"
              disabled
            />
            <BaseInput
              label="Account Identifier (UUID)"
              :modelValue="authStore.user?.id || '00000000-0000-0000-0000-000000000000'"
              disabled
            />
          </div>

          <div class="pt-2 flex items-center space-x-3 text-xs">
            <BaseBadge variant="success" size="sm" dot>Active Admin</BaseBadge>
            <span class="text-dock-muted font-mono text-[11px]">
              Created: {{ authStore.user?.created_at ? new Date(authStore.user.created_at).toLocaleDateString() : 'N/A' }}
            </span>
          </div>
        </div>
      </BaseCard>

      <!-- Theme Preferences Card -->
      <BaseCard title="Interface & Appearance" subtitle="Dashboard visual theme and display customization">
        <div class="space-y-4">
          <label class="text-xs font-medium text-dock-muted">Color Palette</label>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div
              @click="selectedTheme = 'infrastructure-dark'"
              :class="[
                'p-4 rounded-lg border cursor-pointer transition-all flex items-center justify-between',
                selectedTheme === 'infrastructure-dark'
                  ? 'bg-dock-bg border-dock-primary ring-1 ring-dock-primary/40'
                  : 'bg-dock-bg/50 border-dock-border hover:border-dock-border/80'
              ]"
            >
              <div class="flex items-center space-x-3">
                <div class="w-6 h-6 rounded bg-[#071827] border border-[#22D3EE] flex items-center justify-center">
                  <div class="w-2.5 h-2.5 rounded-full bg-[#22D3EE]" />
                </div>
                <div>
                  <h4 class="text-xs font-semibold text-dock-text">Infrastructure Dark (Default)</h4>
                  <p class="text-[10px] text-dock-muted">High-contrast navy with cyan accents</p>
                </div>
              </div>
              <Check v-if="selectedTheme === 'infrastructure-dark'" class="w-4 h-4 text-dock-primary" />
            </div>

            <div
              @click="selectedTheme = 'obsidian'"
              :class="[
                'p-4 rounded-lg border cursor-pointer transition-all flex items-center justify-between',
                selectedTheme === 'obsidian'
                  ? 'bg-dock-bg border-dock-primary ring-1 ring-dock-primary/40'
                  : 'bg-dock-bg/50 border-dock-border hover:border-dock-border/80'
              ]"
            >
              <div class="flex items-center space-x-3">
                <div class="w-6 h-6 rounded bg-[#0A0E17] border border-[#159FB5] flex items-center justify-center">
                  <div class="w-2.5 h-2.5 rounded-full bg-[#159FB5]" />
                </div>
                <div>
                  <h4 class="text-xs font-semibold text-dock-text">Deep Obsidian</h4>
                  <p class="text-[10px] text-dock-muted">True black for OLED panels</p>
                </div>
              </div>
              <Check v-if="selectedTheme === 'obsidian'" class="w-4 h-4 text-dock-primary" />
            </div>
          </div>
        </div>

        <template #footer>
          <div class="flex items-center justify-between">
            <span v-if="saveSuccess" class="text-xs text-dock-success flex items-center">
              <Check class="w-3.5 h-3.5 mr-1" /> Preferences saved
            </span>
            <span v-else class="text-[11px] text-dock-muted">Changes apply immediately to this browser session</span>
            <BaseButton size="sm" variant="primary" @click="savePreferences">
              <Save class="w-3.5 h-3.5 mr-1.5" />
              Save Preferences
            </BaseButton>
          </div>
        </template>
      </BaseCard>

      <!-- Security & Tokens -->
      <BaseCard title="Security Architecture" subtitle="Authentication protocol specifications for Milestone 01">
        <div class="space-y-3 text-xs text-dock-muted leading-relaxed">
          <p>
            <strong class="text-dock-text">Token Storage Standard:</strong> Access tokens are isolated within an
            <code class="px-1.5 py-0.5 rounded bg-dock-bg text-dock-primary font-mono text-[11px]">HttpOnly</code> cookie,
            preventing client-side JavaScript inspection and mitigating XSS token harvesting vectors.
          </p>
          <p>
            <strong class="text-dock-text">Password Hashing:</strong> Passwords are protected with memory-hard
            <code class="px-1.5 py-0.5 rounded bg-dock-bg text-dock-secondary font-mono text-[11px]">Argon2id</code>
            cryptographic parameters resistant to GPU brute-force cracking.
          </p>
        </div>
      </BaseCard>
    </div>
  </DefaultLayout>
</template>
