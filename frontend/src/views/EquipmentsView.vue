<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import api from '../api'

const PAGE_SIZE = 25
const items = ref([])
const alerts = ref({ stock_bas: [], peremption_proche: [] })
const error = ref('')
const saving = ref(false)
const showForm = ref(false)

const search = ref('')
const category = ref('')
const lowOnly = ref(false)
const page = ref(1)

const empty = () => ({
  name: '', reference: '', serial_number: '', lot: '',
  categorie: '', conditionnement: '', prix_tnd: '',
  quantity: 1, min_stock: 1, expiry_date: '',
})
const form = reactive(empty())

const categories = computed(() =>
  [...new Set(items.value.map((e) => e.categorie).filter(Boolean))].sort(),
)

function isLow(e) {
  return e.quantity <= e.min_stock
}

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return items.value.filter((e) => {
    if (category.value && e.categorie !== category.value) return false
    if (lowOnly.value && !isLow(e)) return false
    if (!q) return true
    return (
      (e.name || '').toLowerCase().includes(q) ||
      (e.reference || '').toLowerCase().includes(q) ||
      (e.serial_number || '').toLowerCase().includes(q)
    )
  })
})

const pageCount = computed(() => Math.max(1, Math.ceil(filtered.value.length / PAGE_SIZE)))
const pageItems = computed(() =>
  filtered.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE),
)
const from = computed(() => (filtered.value.length ? (page.value - 1) * PAGE_SIZE + 1 : 0))
const to = computed(() => Math.min(page.value * PAGE_SIZE, filtered.value.length))

watch([search, category, lowOnly], () => {
  page.value = 1
})

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('fr-FR') : '-'
}

function fmtPrice(v) {
  if (v === null || v === undefined) return '-'
  return Number(v).toLocaleString('fr-FR', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

function resetFilters() {
  search.value = ''
  category.value = ''
  lowOnly.value = false
}

async function load() {
  try {
    const [a, b] = await Promise.all([api.get('/equipments'), api.get('/equipments/alerts')])
    items.value = [...a.data].sort((x, y) =>
      (x.reference || '~').localeCompare(y.reference || '~'),
    )
    alerts.value = b.data
    error.value = ''
  } catch {
    error.value = 'Impossible de charger le matériel'
  }
}

async function add() {
  error.value = ''
  saving.value = true
  try {
    await api.post('/equipments', {
      name: form.name,
      reference: form.reference || null,
      serial_number: form.serial_number || null,
      lot: form.lot || null,
      categorie: form.categorie || null,
      conditionnement: form.conditionnement || null,
      prix_tnd: form.prix_tnd !== '' ? Number(form.prix_tnd) : null,
      quantity: Number(form.quantity),
      min_stock: Number(form.min_stock),
      expiry_date: form.expiry_date ? form.expiry_date + 'T00:00:00' : null,
    })
    Object.assign(form, empty())
    showForm.value = false
    await load()
  } catch (e) {
    error.value = e.response?.data?.detail
      ? JSON.stringify(e.response.data.detail)
      : "Erreur lors de l'ajout"
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold">
        Matériel médical
        <span class="text-base font-normal text-slate-500">({{ items.length }} articles)</span>
      </h1>
      <button class="rounded bg-blue-900 px-4 py-2 text-sm text-white hover:bg-blue-800"
              @click="showForm = !showForm">
        {{ showForm ? 'Fermer' : 'Ajouter un équipement' }}
      </button>
    </div>

    <p v-if="error" class="mb-4 rounded bg-red-100 p-3 text-red-700">{{ error }}</p>

    <!-- Alertes -->
    <div class="mb-6 grid gap-4 md:grid-cols-2">
      <div class="rounded-lg bg-white p-4 shadow">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold text-orange-600">Stock bas ({{ alerts.stock_bas.length }})</h2>
          <button class="text-sm text-blue-800 hover:underline"
                  @click="lowOnly = !lowOnly">
            {{ lowOnly ? 'Tout afficher' : 'Voir dans le tableau' }}
          </button>
        </div>
        <p class="text-sm text-slate-500">Articles dont la quantité est inférieure ou égale au stock minimum.</p>
      </div>
      <div class="rounded-lg bg-white p-4 shadow">
        <h2 class="mb-1 font-semibold text-red-600">
          Péremption proche ({{ alerts.peremption_proche.length }})
        </h2>
        <p v-if="!alerts.peremption_proche.length" class="text-sm text-slate-500">Aucune alerte</p>
        <ul class="max-h-20 overflow-y-auto text-sm">
          <li v-for="e in alerts.peremption_proche" :key="e._id">
            {{ e.name }} : expire le {{ fmtDate(e.expiry_date) }}
          </li>
        </ul>
      </div>
    </div>

    <!-- Formulaire d'ajout -->
    <form v-if="showForm" class="mb-6 rounded-lg bg-white p-4 shadow" @submit.prevent="add">
      <h2 class="mb-3 font-semibold">Ajouter un équipement</h2>
      <div class="grid gap-3 md:grid-cols-4">
        <label class="text-sm text-slate-600 md:col-span-2">Nom
          <input v-model="form.name" required class="mt-1 w-full rounded border p-2" />
        </label>
        <label class="text-sm text-slate-600">Référence
          <input v-model="form.reference" class="mt-1 w-full rounded border p-2" />
        </label>
        <label class="text-sm text-slate-600">N° de série
          <input v-model="form.serial_number" class="mt-1 w-full rounded border p-2" />
        </label>
        <label class="text-sm text-slate-600">Catégorie
          <input v-model="form.categorie" list="cats" class="mt-1 w-full rounded border p-2" />
          <datalist id="cats">
            <option v-for="c in categories" :key="c" :value="c" />
          </datalist>
        </label>
        <label class="text-sm text-slate-600">Conditionnement
          <input v-model="form.conditionnement" class="mt-1 w-full rounded border p-2" />
        </label>
        <label class="text-sm text-slate-600">Prix (TND)
          <input v-model="form.prix_tnd" type="number" min="0" step="0.001" class="mt-1 w-full rounded border p-2" />
        </label>
        <label class="text-sm text-slate-600">Lot
          <input v-model="form.lot" class="mt-1 w-full rounded border p-2" />
        </label>
        <label class="text-sm text-slate-600">Quantité
          <input v-model="form.quantity" type="number" min="0" class="mt-1 w-full rounded border p-2" />
        </label>
        <label class="text-sm text-slate-600">Stock minimum
          <input v-model="form.min_stock" type="number" min="0" class="mt-1 w-full rounded border p-2" />
        </label>
        <label class="text-sm text-slate-600">Date de péremption
          <input v-model="form.expiry_date" type="date" class="mt-1 w-full rounded border p-2" />
        </label>
        <div class="flex items-end">
          <button :disabled="saving"
                  class="w-full rounded bg-blue-900 p-2 text-white hover:bg-blue-800 disabled:opacity-50">
            {{ saving ? 'Ajout...' : 'Enregistrer' }}
          </button>
        </div>
      </div>
    </form>

    <!-- Filtres -->
    <div class="mb-3 flex flex-wrap items-center gap-3 rounded-lg bg-white p-3 shadow">
      <input v-model="search" placeholder="Rechercher (nom, référence)..."
             class="min-w-64 flex-1 rounded border p-2 text-sm" />
      <select v-model="category" class="rounded border p-2 text-sm">
        <option value="">Toutes les catégories</option>
        <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
      </select>
      <label class="flex items-center gap-2 text-sm">
        <input v-model="lowOnly" type="checkbox" /> Stock bas uniquement
      </label>
      <button class="text-sm text-blue-800 hover:underline" @click="resetFilters">Réinitialiser</button>
    </div>

    <!-- Tableau -->
    <div class="overflow-x-auto rounded-lg bg-white shadow">
      <table class="w-full text-left text-sm">
        <thead class="bg-slate-50 text-slate-600">
          <tr>
            <th class="p-3">Référence</th>
            <th class="p-3">Désignation</th>
            <th class="p-3">Catégorie</th>
            <th class="p-3">Conditionnement</th>
            <th class="p-3 text-right">Qté</th>
            <th class="p-3 text-right">Min</th>
            <th class="p-3 text-right">Prix (TND)</th>
            <th class="p-3">Péremption</th>
            <th class="p-3">Statut</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in pageItems" :key="e._id" class="border-t"
              :class="isLow(e) ? 'bg-red-50' : ''">
            <td class="whitespace-nowrap p-3 font-mono text-xs">{{ e.reference || '-' }}</td>
            <td class="p-3">{{ e.name }}</td>
            <td class="p-3">{{ e.categorie || '-' }}</td>
            <td class="p-3">{{ e.conditionnement || '-' }}</td>
            <td class="p-3 text-right font-semibold" :class="isLow(e) ? 'text-red-600' : ''">
              {{ e.quantity }}
            </td>
            <td class="p-3 text-right">{{ e.min_stock }}</td>
            <td class="whitespace-nowrap p-3 text-right">{{ fmtPrice(e.prix_tnd) }}</td>
            <td class="p-3">{{ fmtDate(e.expiry_date) }}</td>
            <td class="p-3">{{ e.statut }}</td>
          </tr>
          <tr v-if="!pageItems.length">
            <td colspan="9" class="p-4 text-center text-slate-500">Aucun équipement trouvé</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="mt-3 flex items-center justify-between text-sm">
      <span class="text-slate-500">{{ from }}–{{ to }} sur {{ filtered.length }}</span>
      <div class="flex items-center gap-2">
        <button :disabled="page <= 1" class="rounded border bg-white px-3 py-1 disabled:opacity-40"
                @click="page--">
          Précédent
        </button>
        <span>Page {{ page }} / {{ pageCount }}</span>
        <button :disabled="page >= pageCount" class="rounded border bg-white px-3 py-1 disabled:opacity-40"
                @click="page++">
          Suivant
        </button>
      </div>
    </div>
  </div>
</template>