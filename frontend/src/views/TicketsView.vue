<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '../api'
import { auth } from '../auth'

const role = computed(() => auth.user?.role)
const tickets = ref([])
const equipments = ref([])
const establishments = ref([])
const technicians = ref([])
const filter = ref('')
const error = ref('')
const open = ref(null)
const saving = ref(false)
const drafts = reactive({})

const form = reactive({
  title: '', description: '', priority: 'normale',
  equipment_id: '', establishment_id: '',
})

const histId = ref('')
const history = ref(null)

const statusColor = {
  ouvert: 'bg-red-100 text-red-700',
  affecte: 'bg-orange-100 text-orange-700',
  en_cours: 'bg-blue-100 text-blue-700',
  resolu: 'bg-green-100 text-green-700',
  clos: 'bg-slate-200 text-slate-600',
}

function fmt(d) {
  if (!d) return '-'
  return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(d) ? d : d + 'Z').toLocaleString('fr-FR')
}

function msg(e) {
  const d = e.response?.data?.detail
  if (!d) return 'Serveur injoignable'
  return typeof d === 'string' ? d : JSON.stringify(d)
}

async function load() {
  try {
    const params = filter.value ? { status: filter.value } : {}
    const [t, eq, es] = await Promise.all([
      api.get('/tickets', { params }),
      api.get('/equipments'),
      api.get('/establishments'),
    ])
    tickets.value = t.data
    equipments.value = eq.data
    establishments.value = es.data
    t.data.forEach((x) => {
      if (!drafts[x._id]) drafts[x._id] = { tech: '', comment: '', action: '' }
    })
    if (role.value === 'admin') {
      technicians.value = (await api.get('/tickets/technicians')).data
    }
  } catch (e) {
    error.value = msg(e)
  }
}

async function run(fn) {
  error.value = ''
  try {
    await fn()
    await load()
  } catch (e) {
    error.value = msg(e)
  }
}

async function createTicket() {
  saving.value = true
  await run(async () => {
    await api.post('/tickets', { ...form })
    Object.assign(form, { title: '', description: '', priority: 'normale',
                          equipment_id: '', establishment_id: '' })
  })
  saving.value = false
}

const assign = (t) =>
  run(() => api.patch(`/tickets/${t._id}/assign`, { technician_id: Number(drafts[t._id].tech) }))

const setStatus = (t, status) =>
  run(async () => {
    await api.patch(`/tickets/${t._id}/status`, {
      status,
      comment: drafts[t._id].comment || null,
    })
    drafts[t._id].comment = ''
  })

const addAction = (t) =>
  run(async () => {
    await api.post(`/tickets/${t._id}/interventions`, { action: drafts[t._id].action })
    drafts[t._id].action = ''
  })

const closeTicket = (t) => run(() => api.post(`/tickets/${t._id}/close`))

async function loadHistory() {
  if (!histId.value) return
  try {
    history.value = (await api.get(`/establishments/${histId.value}/history`)).data
  } catch (e) {
    error.value = msg(e)
  }
}

const canWork = computed(() => ['admin', 'technicien'].includes(role.value))

onMounted(load)
</script>

<template>
  <div v-if="auth.user">
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold">Tickets SAV</h1>
      <select v-model="filter" class="rounded border bg-white p-2 text-sm" @change="load">
        <option value="">Tous les statuts</option>
        <option v-for="s in ['ouvert','affecte','en_cours','resolu','clos']" :key="s" :value="s">
          {{ s }}
        </option>
      </select>
    </div>

    <p v-if="error" class="mb-4 rounded bg-red-100 p-3 text-red-700">{{ error }}</p>

    <!-- Création (client, admin) -->
    <form v-if="['client','admin'].includes(role)"
          class="mb-6 rounded-lg bg-white p-4 shadow" @submit.prevent="createTicket">
      <h2 class="mb-3 font-semibold">Déclarer une panne</h2>
      <div class="grid gap-3 md:grid-cols-2">
        <input v-model="form.title" placeholder="Titre" required class="rounded border p-2" />
        <select v-model="form.priority" class="rounded border p-2">
          <option v-for="p in ['basse','normale','haute','critique']" :key="p" :value="p">
            Priorité : {{ p }}
          </option>
        </select>
        <select v-model="form.equipment_id" required class="rounded border p-2">
          <option value="" disabled>Équipement</option>
          <option v-for="e in equipments" :key="e._id" :value="e._id">
            {{ e.name }} ({{ e.serial_number }})
          </option>
        </select>
        <select v-model="form.establishment_id" required class="rounded border p-2">
          <option value="" disabled>Établissement</option>
          <option v-for="s in establishments" :key="s._id" :value="s._id">{{ s.name }}</option>
        </select>
        <textarea v-model="form.description" placeholder="Description de la panne" required
                  class="rounded border p-2 md:col-span-2" rows="2"></textarea>
      </div>
      <button :disabled="saving"
              class="mt-3 rounded bg-blue-900 px-4 py-2 text-white hover:bg-blue-800 disabled:opacity-50">
        {{ saving ? 'Envoi...' : 'Créer le ticket' }}
      </button>
    </form>

    <!-- Liste -->
    <p v-if="!tickets.length" class="rounded-lg bg-white p-6 text-center text-slate-500 shadow">
      Aucun ticket
    </p>

    <div v-for="t in tickets" :key="t._id" class="mb-3 rounded-lg bg-white shadow">
      <div class="flex cursor-pointer items-center justify-between p-4"
           @click="open = open === t._id ? null : t._id">
        <div>
          <p class="font-semibold">{{ t.title }}</p>
          <p class="text-sm text-slate-500">
            {{ t.equipment_name }} · {{ t.establishment_name }} · priorité {{ t.priority }}
          </p>
        </div>
        <div class="flex items-center gap-3">
          <span v-if="t.assigned_email" class="text-xs text-slate-500">→ {{ t.assigned_email }}</span>
          <span class="rounded px-2 py-0.5 text-xs font-medium" :class="statusColor[t.status]">
            {{ t.status }}
          </span>
        </div>
      </div>

      <div v-if="open === t._id && drafts[t._id]" class="space-y-4 border-t p-4 text-sm">
        <p>{{ t.description }}</p>
        <p class="text-slate-500">Créé par {{ t.created_by_email }} le {{ fmt(t.created_at) }}</p>

        <!-- Affectation (admin) -->
        <div v-if="role === 'admin' && t.status !== 'clos'" class="flex gap-2">
          <select v-model="drafts[t._id].tech" class="rounded border p-2">
            <option value="" disabled>Technicien</option>
            <option v-for="u in technicians" :key="u.id" :value="u.id">{{ u.email }}</option>
          </select>
          <button :disabled="!drafts[t._id].tech"
                  class="rounded bg-blue-900 px-3 py-2 text-white disabled:opacity-50"
                  @click="assign(t)">
            Affecter
          </button>
        </div>

        <!-- Traitement (technicien, admin) -->
        <div v-if="canWork && t.status !== 'clos' && t.status !== 'ouvert'" class="space-y-2">
          <div class="flex flex-wrap gap-2">
            <button v-if="t.status === 'affecte'"
                    class="rounded bg-blue-700 px-3 py-2 text-white" @click="setStatus(t, 'en_cours')">
              Démarrer
            </button>
            <button v-if="t.status === 'resolu'"
                    class="rounded bg-orange-600 px-3 py-2 text-white" @click="setStatus(t, 'en_cours')">
              Rouvrir
            </button>
            <button v-if="t.status === 'resolu'"
                    class="rounded bg-slate-700 px-3 py-2 text-white" @click="closeTicket(t)">
              Clôturer
            </button>
          </div>
          <div v-if="t.status === 'en_cours'" class="flex flex-wrap gap-2">
            <input v-model="drafts[t._id].action" placeholder="Action effectuée"
                   class="flex-1 rounded border p-2" />
            <button :disabled="!drafts[t._id].action"
                    class="rounded bg-blue-900 px-3 py-2 text-white disabled:opacity-50"
                    @click="addAction(t)">
              Ajouter
            </button>
          </div>
          <div v-if="t.status === 'en_cours'" class="flex flex-wrap gap-2">
            <input v-model="drafts[t._id].comment" placeholder="Commentaire de résolution (facultatif)"
                   class="flex-1 rounded border p-2" />
            <button class="rounded bg-green-700 px-3 py-2 text-white" @click="setStatus(t, 'resolu')">
              Marquer résolu
            </button>
          </div>
        </div>

        <!-- Historique du ticket -->
        <div>
          <p class="mb-1 font-semibold">Interventions</p>
          <ul class="space-y-1 border-l-2 border-blue-200 pl-3">
            <li v-for="(i, k) in t.interventions" :key="k">
              <span class="text-slate-500">{{ fmt(i.date) }}</span>
              · <strong>{{ i.author_email }}</strong> : {{ i.action }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Historique par établissement (admin, technicien) -->
    <div v-if="canWork" class="mt-8 rounded-lg bg-white p-4 shadow">
      <h2 class="mb-3 font-semibold">Historique par établissement</h2>
      <div class="flex gap-2">
        <select v-model="histId" class="rounded border p-2">
          <option value="" disabled>Établissement</option>
          <option v-for="s in establishments" :key="s._id" :value="s._id">{{ s.name }}</option>
        </select>
        <button class="rounded bg-blue-900 px-3 py-2 text-white" @click="loadHistory">Afficher</button>
      </div>
      <div v-if="history" class="mt-3 text-sm">
        <p class="mb-2">
          <strong>{{ history.establishment }}</strong> :
          {{ history.tickets_total }} ticket(s), {{ history.tickets_clos }} clos
        </p>
        <ul class="max-h-64 space-y-1 overflow-y-auto">
          <li v-for="(ev, k) in history.events" :key="k">
            <span class="text-slate-500">{{ fmt(ev.date) }}</span>
            · {{ ev.ticket }} ({{ ev.equipment }}) · {{ ev.by }} : {{ ev.action }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>