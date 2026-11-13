<script setup>
import NavBar from './components/NavBar.vue'
import { auth } from './auth'
</script>

<template>
  <div class="min-h-screen bg-slate-100 text-slate-800">
    <NavBar v-if="auth.user" />
    <main class="mx-auto max-w-6xl p-6">
      <router-view />
    </main>
  </div>
</template>