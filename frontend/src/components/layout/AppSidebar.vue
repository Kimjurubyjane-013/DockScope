<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  LayoutDashboard,
  Server,
  Boxes,
  Shield,
  Settings as SettingsIcon,
  LogOut,
  Radio,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Hosts', path: '/hosts', icon: Server, badge: 'M03' },
  { name: 'Docker', path: '/docker', icon: Boxes, badge: 'M02' },
  { name: 'Security', path: '/security', icon: Shield, badge: 'M04' },
  { name: 'Settings', path: '/settings', icon: SettingsIcon },
]

const currentPath = computed(() => route.path)

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <aside class="w-64 bg-dock-surface border-r border-dock-border flex flex-col justify-between h-screen sticky top-0 shrink-0">
    <div>
      <!-- Brand Logo -->
      <div class="h-16 px-6 border-b border-dock-border flex items-center space-x-3">
        <div class="w-8 h-8 rounded-lg bg-dock-bg border border-dock-primary/40 flex items-center justify-center text-dock-primary">
          <Radio class="w-5 h-5 text-dock-primary animate-pulse" />
        </div>
        <div>
          <span class="font-bold tracking-tight text-dock-text text-base">DockScope</span>
          <span class="block text-[10px] text-dock-muted uppercase tracking-wider font-mono">v0.1.0-alpha</span>
        </div>
      </div>

      <!-- Navigation Links -->
      <nav class="p-3 space-y-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium transition-colors',
            currentPath === item.path
              ? 'bg-dock-hover text-dock-primary border-l-2 border-dock-primary font-semibold'
              : 'text-dock-muted hover:text-dock-text hover:bg-dock-hover/60',
          ]"
        >
          <div class="flex items-center space-x-3">
            <component :is="item.icon" class="w-4 h-4" />
            <span>{{ item.name }}</span>
          </div>
          <span
            v-if="item.badge"
            class="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-dock-bg text-dock-muted border border-dock-border"
          >
            {{ item.badge }}
          </span>
        </RouterLink>
      </nav>
    </div>

    <!-- User / Session Footer -->
    <div class="p-4 border-t border-dock-border bg-dock-bg/50">
      <div class="flex items-center justify-between">
        <div class="truncate mr-2">
          <p class="text-xs font-semibold text-dock-text truncate">
            {{ authStore.user?.email || 'Authenticated User' }}
          </p>
          <p class="text-[10px] text-dock-muted flex items-center mt-0.5">
            <span class="w-1.5 h-1.5 rounded-full bg-dock-success mr-1.5" />
            Active Session
          </p>
        </div>
        <button
          @click="handleLogout"
          title="Sign out"
          class="p-2 text-dock-muted hover:text-dock-danger hover:bg-dock-surface rounded-md transition-colors"
        >
          <LogOut class="w-4 h-4" />
        </button>
      </div>
    </div>
  </aside>
</template>
