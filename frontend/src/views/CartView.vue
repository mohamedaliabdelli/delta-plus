<script setup>
import { reactive, ref } from 'vue'
import api from '../api'
import { cart, setQty, removeFromCart, clearCart, cartTotal } from '../cart'

const saving = ref(false)
const error = ref('')
const done = ref(null)

const empty = () => ({
  address: '', city: '', phone: '',
  number: '', holder: '', expiry: '', cvc: '',
})
const form = reactive(empty())

function fmtPrice(v) {
  return Number(v).toLocaleString('fr-FR', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

function formatCard() {
  form.number = form.number.replace(/\D/g, '').slice(0, 19).replace(/(.{4})/g, '$1 ').trim()
}

function msg(e) {
  const d = e.response?.data?.detail
  if (!d) return 'Serveur injoignable'
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => x.msg).join(' ; ')
  return JSON.stringify(d)
}

async function pay() {
  error.value = ''
  saving.value = true
  try {
    const { data } = await api.post('/orders', {
      items: cart.items.map((i) => ({ equipment_id: i.id, quantity: i.quantity })),
      address: form.address,
      city: form.city,
      phone: form.phone || null,
      card: { number: form.number, holder: form.holder, expiry: form.expiry, cvc: form.cvc },
    })
    done.value = data
    clearCart()
    Object.assign(form, empty())
  } catch (e) {
    error.value = msg(e)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="mb-4 text-2xl font-bold">Panier</h1>

    <!-- Confirmation -->
    <div v-if="done" class="rounded-lg bg-white p-6 shadow">
      <p class="mb-1 text-lg font-semibold text-green-700">Paiement accepté, commande enregistrée</p>
      <p class="text-sm text-slate-600">
        Commande <strong>{{ done.number }}</strong> · {{ fmtPrice(done.total_tnd) }} TND ·
        carte •••• {{ done.payment.card_last4 }}
      </p>
      <p class="text-sm text-slate-500">Transaction simulée : {{ done.payment.transaction_id }}</p>
      <div class="mt-4 flex gap-3">
        <router-link to="/orders" class="rounded bg-blue-900 px-4 py-2 text-sm text-white">
          Voir mes commandes
        </router-link>
        <router-link to="/shop" class="rounded border bg-white px-4 py-2 text-sm">
          Continuer mes achats
        </router-link>
      </div>
    </div>

    <!-- Panier vide -->
    <div v-else-if="!cart.items.length" class="rounded-lg bg-white p-6 text-center shadow">
      <p class="mb-3 text-slate-500">Votre panier est vide.</p>
      <router-link to="/shop" class="rounded bg-blue-900 px-4 py-2 text-sm text-white">
        Aller à la boutique
      </router-link>
    </div>

    <!-- Panier et paiement -->
    <div v-else class="grid gap-6 lg:grid-cols-2">
      <div class="rounded-lg bg-white p-4 shadow">
        <h2 class="mb-3 font-semibold">Articles</h2>
        <div v-for="i in cart.items" :key="i.id" class="flex items-center gap-3 border-t py-3 text-sm">
          <div class="flex-1">
            <p class="font-medium">{{ i.name }}</p>
            <p class="text-xs text-slate-500">{{ i.reference }} · {{ fmtPrice(i.prix_tnd) }} TND</p>
          </div>
          <input type="number" min="1" :max="i.stock" :value="i.quantity"
                 class="w-20 rounded border p-1 text-right"
                 @change="setQty(i.id, $event.target.value)" />
          <p class="w-28 text-right font-semibold">{{ fmtPrice(i.quantity * i.prix_tnd) }}</p>
          <button class="text-red-600 hover:underline" @click="removeFromCart(i.id)">Retirer</button>
        </div>
        <div class="mt-3 flex items-center justify-between border-t pt-3 text-lg font-bold">
          <span>Total</span>
          <span>{{ fmtPrice(cartTotal) }} TND</span>
        </div>
      </div>

      <form class="rounded-lg bg-white p-4 shadow" @submit.prevent="pay">
        <h2 class="mb-3 font-semibold">Livraison</h2>
        <div class="mb-4 grid gap-3">
          <input v-model="form.address" placeholder="Adresse" required minlength="5"
                 class="rounded border p-2" />
          <div class="grid grid-cols-2 gap-3">
            <input v-model="form.city" placeholder="Ville" required minlength="2"
                   class="rounded border p-2" />
            <input v-model="form.phone" placeholder="Téléphone" class="rounded border p-2" />
          </div>
        </div>

        <h2 class="mb-1 font-semibold">Paiement par carte (simulation)</h2>
        <p class="mb-3 rounded bg-slate-50 p-2 text-xs text-slate-600">
          Aucun paiement réel. Carte acceptée : 4242 4242 4242 4242. Refusée : 4000 0000 0000 0002.
          Date : MM/AA dans le futur, CVC : 3 chiffres.
        </p>
        <div class="grid gap-3">
          <input v-model="form.number" placeholder="Numéro de carte" required inputmode="numeric"
                 autocomplete="off" class="rounded border p-2 font-mono" @input="formatCard" />
          <input v-model="form.holder" placeholder="Titulaire de la carte" required
                 autocomplete="off" class="rounded border p-2" />
          <div class="grid grid-cols-2 gap-3">
            <input v-model="form.expiry" placeholder="MM/AA" required maxlength="5"
                   autocomplete="off" class="rounded border p-2" />
            <input v-model="form.cvc" placeholder="CVC" required maxlength="4" inputmode="numeric"
                   autocomplete="off" class="rounded border p-2" />
          </div>
        </div>

        <p v-if="error" class="mt-3 rounded bg-red-100 p-3 text-sm text-red-700">{{ error }}</p>

        <button :disabled="saving"
                class="mt-4 w-full rounded bg-blue-900 p-3 text-white hover:bg-blue-800 disabled:opacity-50">
          {{ saving ? 'Paiement en cours...' : 'Payer ' + fmtPrice(cartTotal) + ' TND' }}
        </button>
      </form>
    </div>
  </div>
</template>