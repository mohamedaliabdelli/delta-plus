<script setup>
import { useRouter } from 'vue-router'
import { auth, logout } from '../auth'

const router = useRouter()
function out() {
  logout()
  router.push('/login')
}
</script>

<template>
  <header class="bg-blue-900 text-white">
    <div class="mx-auto flex max-w-6xl items-center justify-between p-4">
      <nav class="flex items-center gap-6">
        <span class="text-lg font-semibold">Delta Plus Médical</span>
        <router-link to="/" class="text-sm hover:underline">Accueil</router-link>
        <router-link
          v-if="['admin', 'technicien'].includes(auth.user.role)"
          to="/equipments"
          class="text-sm hover:underline"
        >
          Matériel
        </router-link>
        <router-link to="/tickets" class="text-sm hover:underline">Tickets SAV</router-link>
        <router-link
          v-if="['admin', 'technicien'].includes(auth.user.role)"
          to="/monitoring"
          class="text-sm hover:underline"
        >
          Monitoring
        </router-link>
      </nav>
      <div class="flex items-center gap-4 text-sm">
        <span>{{ auth.user.email }}</span>
        <span class="rounded bg-blue-700 px-2 py-0.5 uppercase">{{ auth.user.role }}</span>
        <button class="rounded bg-white px-3 py-1 text-blue-900 hover:bg-blue-100" @click="out">
          Déconnexion
        </button>
      </div>
    </div>
  </header>
</template>