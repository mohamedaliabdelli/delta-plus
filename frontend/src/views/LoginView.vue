<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { setToken } from '../auth'

const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const body = new URLSearchParams({ username: email.value, password: password.value })
    const { data } = await api.post('/login', body)
    setToken(data.access_token)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Serveur injoignable'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto mt-24 max-w-sm rounded-lg bg-white p-8 shadow">
    <h1 class="mb-6 text-center text-2xl font-bold text-blue-900">Delta Plus Médical</h1>
    <form class="space-y-4" @submit.prevent="submit">
      <input v-model="email" type="email" placeholder="Email" required
             class="w-full rounded border p-2" />
      <input v-model="password" type="password" placeholder="Mot de passe" required
             class="w-full rounded border p-2" />
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <button :disabled="loading"
              class="w-full rounded bg-blue-900 p-2 text-white hover:bg-blue-800 disabled:opacity-50">
        {{ loading ? 'Connexion...' : 'Se connecter' }}
      </button>
    </form>
  </div>
</template>