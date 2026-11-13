<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import { auth } from '../auth'

const tickets = ref([])
const alerts = ref({ stock_bas: [], peremption_proche: [] })
const summary = ref(null)
const error = ref('')

const staff = computed(() => ['admin', 'technicien'].includes(auth.user?.role))

const statuses = [
  { key: 'ouvert', label: 'Ouverts', cls: 'text-red-600' },
  { key: 'affecte', label: 'Affectés', cls: 'text-orange-600' },
  { key: 'en_cours', label: 'En cours', cls: 'text-blue-700' },
  { key: 'resolu', label: 'Résolus', cls: 'text-green-700' },
  { key: 'clos', label: 'Clos', cls: 'text-slate-500' },
]

function count(s) {
  return tickets.value.filter((t) => t.status === s).length
}

onMounted(async () => {
  try {
    tickets.value = (await api.get('/tickets')).data
    if (staff.value) {
      const [a, s] = await Promise.all([
        api.get('/equipments/alerts'),
        api.get('/monitoring/summary'),
      ])
      alerts.value = a.data
      summary.value = s.data
    }
  } catch {
    error.value = "Impossible de joindre l'API"
  }
})
</script>

<template>
  <div v-if="auth.user">
    <h1 class="mb-1 text-2xl font-bold">Tableau de bord</h1>
    <p class="mb-6 text-sm text-slate-500">
      Connecté : {{ auth.user.email }} ({{ auth.user.role }})
    </p>

    <p v-if="error" class="mb-4 rounded bg-red-100 p-3 text-red-700">{{ error }}</p>

    <h2 class="mb-2 font-semibold">
      {{ auth.user.role === 'client' ? 'Mes tickets' : 'Tickets SAV' }}
    </h2>
    <div class="mb-6 grid grid-cols-2 gap-4 md:grid-cols-5">
      <router-link
        v-for="s in statuses"
        :key="s.key"
        to="/tickets"
        class="rounded-lg bg-white p-4 shadow hover:bg-slate-50"
      >
        <p class="text-sm text-slate-500">{{ s.label }}</p>
        <p class="text-3xl font-bold" :class="s.cls">{{ count(s.key) }}</p>
      </router-link>
    </div>

    <div v-if="staff">
      <h2 class="mb-2 font-semibold">Matériel</h2>
      <div class="mb-6 grid gap-4 md:grid-cols-2">
        <router-link to="/equipments" class="rounded-lg bg-white p-4 shadow hover:bg-slate-50">
          <p class="text-sm text-orange-600">Stock bas</p>
          <p class="text-3xl font-bold text-orange-600">{{ alerts.stock_bas.length }}</p>
        </router-link>
        <router-link to="/equipments" class="rounded-lg bg-white p-4 shadow hover:bg-slate-50">
          <p class="text-sm text-red-600">Péremption proche</p>
          <p class="text-3xl font-bold text-red-600">{{ alerts.peremption_proche.length }}</p>
        </router-link>
      </div>

      <h2 class="mb-2 font-semibold">Réseau</h2>
      <div v-if="summary" class="grid grid-cols-2 gap-4 md:grid-cols-4">
        <router-link to="/monitoring" class="rounded-lg bg-white p-4 shadow hover:bg-slate-50">
          <p class="text-sm text-slate-500">Équipements</p>
          <p class="text-3xl font-bold">{{ summary.total }}</p>
        </router-link>
        <router-link to="/monitoring" class="rounded-lg bg-white p-4 shadow hover:bg-slate-50">
          <p class="text-sm text-green-700">En ligne</p>
          <p class="text-3xl font-bold text-green-700">{{ summary.en_ligne }}</p>
        </router-link>
        <router-link to="/monitoring" class="rounded-lg bg-white p-4 shadow hover:bg-slate-50">
          <p class="text-sm text-orange-600">Alerte</p>
          <p class="text-3xl font-bold text-orange-600">{{ summary.alerte }}</p>
        </router-link>
        <router-link to="/monitoring" class="rounded-lg bg-white p-4 shadow hover:bg-slate-50">
          <p class="text-sm text-red-600">Hors ligne</p>
          <p class="text-3xl font-bold text-red-600">{{ summary.hors_ligne }}</p>
        </router-link>
      </div>
    </div>
  </div>
</template>