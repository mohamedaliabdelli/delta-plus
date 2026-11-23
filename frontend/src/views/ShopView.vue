<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '../api'
import { cart, addToCart, cartCount } from '../cart'

const PAGE_SIZE = 24
const products = ref([])
const search = ref('')
const category = ref('')
const page = ref(1)
const error = ref('')
const loading = ref(true)

const categories = computed(() =>
  [...new Set(products.value.map((p) => p.categorie).filter(Boolean))].sort(),
)

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return products.value.filter((p) => {
    if (category.value && p.categorie !== category.value) return false
    if (!q) return true
    return (
      (p.name || '').toLowerCase().includes(q) ||
      (p.reference || '').toLowerCase().includes(q)
    )
  })
})

const pageCount = computed(() => Math.max(1, Math.ceil(filtered.value.length / PAGE_SIZE)))
const pageItems = computed(() =>
  filtered.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE),
)

watch([search, category], () => {
  page.value = 1
})

function fmtPrice(v) {
  return Number(v).toLocaleString('fr-FR', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

function inCart(id) {
  return cart.items.find((i) => i.id === id)?.quantity || 0
}

onMounted(async () => {
  try {
    products.value = (await api.get('/shop/products')).data
  } catch {
    error.value = 'Impossible de charger la boutique'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold">Boutique</h1>
      <router-link to="/cart" class="rounded bg-blue-900 px-4 py-2 text-sm text-white hover:bg-blue-800">
        Panier ({{ cartCount }})
      </router-link>
    </div>

    <p v-if="error" class="mb-4 rounded bg-red-100 p-3 text-red-700">{{ error }}</p>

    <div class="mb-4 flex flex-wrap items-center gap-3 rounded-lg bg-white p-3 shadow">
      <input v-model="search" placeholder="Rechercher un article..."
             class="min-w-64 flex-1 rounded border p-2 text-sm" />
      <select v-model="category" class="rounded border p-2 text-sm">
        <option value="">Toutes les catégories</option>
        <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
      </select>
    </div>

    <p v-if="loading" class="p-6 text-center text-slate-500">Chargement...</p>

    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div v-for="p in pageItems" :key="p.id" class="flex flex-col rounded-lg bg-white p-4 shadow">
        <p class="font-mono text-xs text-slate-500">{{ p.reference }}</p>
        <p class="mt-1 flex-1 font-medium">{{ p.name }}</p>
        <p class="mt-1 text-xs text-slate-500">{{ p.categorie }} · {{ p.conditionnement }}</p>
        <div class="mt-3 flex items-end justify-between">
          <div>
            <p class="text-lg font-bold text-blue-900">{{ fmtPrice(p.prix_tnd) }} TND</p>
            <p class="text-xs" :class="p.stock > 0 ? 'text-green-700' : 'text-red-600'">
              {{ p.stock > 0 ? p.stock + ' en stock' : 'Rupture de stock' }}
            </p>
          </div>
          <button
            :disabled="p.stock <= 0 || inCart(p.id) >= p.stock"
            class="rounded bg-blue-900 px-3 py-2 text-sm text-white hover:bg-blue-800 disabled:opacity-40"
            @click="addToCart(p, 1)"
          >
            {{ inCart(p.id) ? 'Ajouter (' + inCart(p.id) + ')' : 'Ajouter' }}
          </button>
        </div>
      </div>
    </div>

    <p v-if="!loading && !pageItems.length" class="p-6 text-center text-slate-500">
      Aucun article trouvé
    </p>

    <div class="mt-4 flex items-center justify-between text-sm">
      <span class="text-slate-500">{{ filtered.length }} article(s)</span>
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