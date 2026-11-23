<script setup>
import { useRouter } from 'vue-router'
import { auth, logout } from '../auth'
import { cartCount, clearCart } from '../cart'

const router = useRouter()

function out() {
  clearCart()
  logout()
  router.push('/login')
}

const isStaff = () => ['admin', 'technicien'].includes(auth.user.role)
const isClient = () => auth.user.role === 'client'
const seesOrders = () => ['client', 'admin'].includes(auth.user.role)
</script>

<template>
  <header class="bg-blue-900 text-white">
    <div class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 p-4">
      <nav class="flex flex-wrap items-center gap-5">
        <span class="text-lg font-semibold">Delta Plus Médical</span>
        <router-link to="/" class="text-sm hover:underline">Accueil</router-link>
        <router-link v-if="isStaff()" to="/equipments" class="text-sm hover:underline">Matériel</router-link>
        <router-link to="/tickets" class="text-sm hover:underline">Tickets SAV</router-link>
        <router-link v-if="isStaff()" to="/monitoring" class="text-sm hover:underline">Monitoring</router-link>
        <router-link v-if="isClient()" to="/shop" class="text-sm hover:underline">Boutique</router-link>
        <router-link v-if="seesOrders()" to="/orders" class="text-sm hover:underline">
          {{ auth.user.role === 'admin' ? 'Commandes' : 'Mes commandes' }}
        </router-link>
        <router-link v-if="isClient()" to="/cart" class="text-sm hover:underline">
          Panier ({{ cartCount }})
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