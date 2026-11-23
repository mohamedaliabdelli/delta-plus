<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import { auth } from '../auth'

const orders = ref([])
const filter = ref('')
const open = ref(null)
const error = ref('')

const isAdmin = computed(() => auth.user?.role === 'admin')

const color = {
  payee: 'bg-blue-100 text-blue-700',
  expediee: 'bg-orange-100 text-orange-700',
  livree: 'bg-green-100 text-green-700',
  annulee: 'bg-slate-200 text-slate-600',
}

function fmt(d) {
  if (!d) return '-'
  return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(d) ? d : d + 'Z').toLocaleString('fr-FR')
}

function fmtPrice(v) {
  return Number(v).toLocaleString('fr-FR', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

function msg(e) {
  const d = e.response?.data?.detail
  return d ? (typeof d === 'string' ? d : JSON.stringify(d)) : 'Serveur injoignable'
}

async function load() {
  try {
    const params = filter.value ? { status: filter.value } : {}
    orders.value = (await api.get('/orders', { params })).data
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

const setStatus = (o, status) => run(() => api.patch(`/orders/${o._id}/status`, { status }))
const cancel = (o) => {
  if (!confirm('Annuler cette commande ? Le paiement sera remboursé (simulation).')) return
  return run(() => api.post(`/orders/${o._id}/cancel`))
}

onMounted(load)
</script>

<template>
  <div v-if="auth.user">
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold">{{ isAdmin ? 'Commandes' : 'Mes commandes' }}</h1>
      <select v-model="filter" class="rounded border bg-white p-2 text-sm" @change="load">
        <option value="">Tous les statuts</option>
        <option v-for="s in ['payee', 'expediee', 'livree', 'annulee']" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>

    <p v-if="error" class="mb-4 rounded bg-red-100 p-3 text-red-700">{{ error }}</p>

    <p v-if="!orders.length" class="rounded-lg bg-white p-6 text-center text-slate-500 shadow">
      Aucune commande
    </p>

    <div v-for="o in orders" :key="o._id" class="mb-3 rounded-lg bg-white shadow">
      <div class="flex cursor-pointer items-center justify-between p-4"
           @click="open = open === o._id ? null : o._id">
        <div>
          <p class="font-semibold">{{ o.number }}</p>
          <p class="text-sm text-slate-500">
            {{ fmt(o.created_at) }}<span v-if="isAdmin"> · {{ o.customer_email }}</span>
          </p>
        </div>
        <div class="flex items-center gap-4">
          <span class="font-semibold">{{ fmtPrice(o.total_tnd) }} TND</span>
          <span class="rounded px-2 py-0.5 text-xs font-medium" :class="color[o.status]">{{ o.status }}</span>
        </div>
      </div>

      <div v-if="open === o._id" class="space-y-4 border-t p-4 text-sm">
        <table class="w-full text-left">
          <thead class="text-slate-500">
            <tr><th class="py-1">Article</th><th class="text-right">Prix</th>
                <th class="text-right">Qté</th><th class="text-right">Total</th></tr>
          </thead>
          <tbody>
            <tr v-for="l in o.lines" :key="l.equipment_id" class="border-t">
              <td class="py-1">{{ l.name }} <span class="text-xs text-slate-500">({{ l.reference }})</span></td>
              <td class="text-right">{{ fmtPrice(l.unit_price) }}</td>
              <td class="text-right">{{ l.quantity }}</td>
              <td class="text-right">{{ fmtPrice(l.line_total) }}</td>
            </tr>
          </tbody>
        </table>

        <p><strong>Livraison :</strong> {{ o.address }}, {{ o.city }}<span v-if="o.phone"> · {{ o.phone }}</span></p>
        <p>
          <strong>Paiement :</strong> carte •••• {{ o.payment.card_last4 }} ·
          {{ o.payment.status }} · {{ o.payment.transaction_id }}
        </p>

        <div class="flex flex-wrap gap-2">
          <button v-if="isAdmin && o.status === 'payee'" class="rounded bg-orange-600 px-3 py-2 text-white"
                  @click="setStatus(o, 'expediee')">
            Marquer expédiée
          </button>
          <button v-if="isAdmin && o.status === 'expediee'" class="rounded bg-green-700 px-3 py-2 text-white"
                  @click="setStatus(o, 'livree')">
            Marquer livrée
          </button>
          <button v-if="o.status === 'payee'" class="rounded bg-red-600 px-3 py-2 text-white"
                  @click="cancel(o)">
            Annuler la commande
          </button>
        </div>

        <div>
          <p class="mb-1 font-semibold">Historique</p>
          <ul class="space-y-1 border-l-2 border-blue-200 pl-3">
            <li v-for="(ev, k) in o.events" :key="k">
              <span class="text-slate-500">{{ fmt(ev.date) }}</span>
              · <strong>{{ ev.author_email }}</strong> : {{ ev.action }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>