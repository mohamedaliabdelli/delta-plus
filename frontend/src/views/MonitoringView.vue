<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Tooltip, Legend,
} from 'chart.js'
import api from '../api'
import { auth } from '../auth'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

const summary = ref({ total: 0, en_ligne: 0, alerte: 0, hors_ligne: 0 })
const devices = ref([])
const alerts = ref([])
const metrics = ref([])
const selectedId = ref('')
const error = ref('')
const updatedAt = ref(null)
let timer = null

const color = {
  en_ligne: 'bg-green-100 text-green-700',
  alerte: 'bg-orange-100 text-orange-700',
  hors_ligne: 'bg-red-100 text-red-700',
}

const isAdmin = computed(() => auth.user?.role === 'admin')

function parse(d) {
  return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(d) ? d : d + 'Z')
}
const fmt = (d) => (d ? parse(d).toLocaleString('fr-FR') : '-')
const hour = (d) => parse(d).toLocaleTimeString('fr-FR')

function msg(e) {
  const d = e.response?.data?.detail
  return d ? (typeof d === 'string' ? d : JSON.stringify(d)) : 'Serveur injoignable'
}

async function loadMetrics() {
  if (!selectedId.value) return
  try {
    const { data } = await api.get(`/devices/${selectedId.value}/metrics`, { params: { limit: 40 } })
    metrics.value = [...data].reverse()
  } catch (e) {
    error.value = msg(e)
  }
}

async function load() {
  try {
    const [s, d, a] = await Promise.all([
      api.get('/monitoring/summary'),
      api.get('/devices'),
      api.get('/monitoring/alerts'),
    ])
    summary.value = s.data
    devices.value = d.data
    alerts.value = a.data
    if (!selectedId.value && d.data.length) selectedId.value = d.data[0]._id
    await loadMetrics()
    updatedAt.value = new Date()
    error.value = ''
  } catch (e) {
    error.value = msg(e)
  }
}

async function simulate(id) {
  if (!confirm('Simuler une panne ? Un ticket SAV sera créé automatiquement.')) return
  try {
    await api.post(`/devices/${id}/simulate-failure`)
    await load()
  } catch (e) {
    error.value = msg(e)
  }
}

watch(selectedId, loadMetrics)

const chartData = computed(() => ({
  labels: metrics.value.map((m) => hour(m.date)),
  datasets: [
    {
      label: 'Latence (ms)',
      data: metrics.value.map((m) => m.latency_ms),
      borderColor: '#1e3a8a',
      backgroundColor: '#1e3a8a',
      yAxisID: 'y',
      tension: 0.3,
    },
    {
      label: 'CPU (%)',
      data: metrics.value.map((m) => m.cpu),
      borderColor: '#ea580c',
      backgroundColor: '#ea580c',
      yAxisID: 'y1',
      tension: 0.3,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: { position: 'left', title: { display: true, text: 'ms' }, beginAtZero: true },
    y1: {
      position: 'right', title: { display: true, text: '%' },
      min: 0, max: 100, grid: { drawOnChartArea: false },
    },
  },
}

onMounted(() => {
  load()
  timer = setInterval(load, 30000)
})
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <div v-if="auth.user">
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold">Monitoring réseau</h1>
      <span class="text-xs text-slate-500">
        Actualisation toutes les 30 s · dernière : {{ updatedAt ? updatedAt.toLocaleTimeString('fr-FR') : '...' }}
      </span>
    </div>

    <p v-if="error" class="mb-4 rounded bg-red-100 p-3 text-red-700">{{ error }}</p>

    <!-- Résumé -->
    <div class="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
      <div class="rounded-lg bg-white p-4 shadow">
        <p class="text-sm text-slate-500">Total</p>
        <p class="text-3xl font-bold">{{ summary.total }}</p>
      </div>
      <div class="rounded-lg bg-white p-4 shadow">
        <p class="text-sm text-green-700">En ligne</p>
        <p class="text-3xl font-bold text-green-700">{{ summary.en_ligne }}</p>
      </div>
      <div class="rounded-lg bg-white p-4 shadow">
        <p class="text-sm text-orange-600">Alerte</p>
        <p class="text-3xl font-bold text-orange-600">{{ summary.alerte }}</p>
      </div>
      <div class="rounded-lg bg-white p-4 shadow">
        <p class="text-sm text-red-600">Hors ligne</p>
        <p class="text-3xl font-bold text-red-600">{{ summary.hors_ligne }}</p>
      </div>
    </div>

    <!-- Alertes -->
    <div class="mb-6 rounded-lg bg-white p-4 shadow">
      <h2 class="mb-2 font-semibold">Alertes en cours ({{ alerts.length }})</h2>
      <p v-if="!alerts.length" class="text-sm text-slate-500">Aucune alerte, tout est en ligne.</p>
      <ul class="space-y-1 text-sm">
        <li v-for="a in alerts" :key="a._id" class="flex items-center gap-2">
          <span class="rounded px-2 py-0.5 text-xs font-medium" :class="color[a.status]">{{ a.status }}</span>
          <strong>{{ a.name }}</strong> ({{ a.ip }}) · {{ a.establishment_name }}
        </li>
      </ul>
    </div>

    <!-- Équipements -->
    <div class="mb-6 overflow-x-auto rounded-lg bg-white shadow">
      <table class="w-full text-left text-sm">
        <thead class="bg-slate-50 text-slate-600">
          <tr>
            <th class="p-3">Nom</th><th class="p-3">IP</th><th class="p-3">Type</th>
            <th class="p-3">Établissement</th><th class="p-3">Statut</th>
            <th class="p-3">Dernière mesure</th><th class="p-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in devices" :key="d._id" class="cursor-pointer border-t hover:bg-slate-50"
              :class="{ 'bg-blue-50': d._id === selectedId }" @click="selectedId = d._id">
            <td class="p-3 font-medium">{{ d.name }}</td>
            <td class="p-3">{{ d.ip }}</td>
            <td class="p-3">{{ d.type }}</td>
            <td class="p-3">{{ d.establishment_name }}</td>
            <td class="p-3">
              <span class="rounded px-2 py-0.5 text-xs font-medium" :class="color[d.status]">{{ d.status }}</span>
            </td>
            <td class="p-3">{{ fmt(d.last_seen) }}</td>
            <td class="p-3">
              <button v-if="isAdmin" class="rounded bg-red-600 px-2 py-1 text-xs text-white hover:bg-red-700"
                      @click.stop="simulate(d._id)">
                Simuler une panne
              </button>
            </td>
          </tr>
          <tr v-if="!devices.length">
            <td colspan="7" class="p-4 text-center text-slate-500">Aucun équipement réseau</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Graphique -->
    <div class="rounded-lg bg-white p-4 shadow">
      <div class="mb-3 flex items-center justify-between">
        <h2 class="font-semibold">Latence et CPU</h2>
        <select v-model="selectedId" class="rounded border p-2 text-sm">
          <option v-for="d in devices" :key="d._id" :value="d._id">{{ d.name }}</option>
        </select>
      </div>
      <p v-if="!metrics.length" class="py-8 text-center text-sm text-slate-500">
        Aucune mesure pour le moment.
      </p>
      <div v-else class="h-72">
        <Line :data="chartData" :options="chartOptions" />
      </div>
    </div>
  </div>
</template>