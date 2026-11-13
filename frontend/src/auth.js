import { reactive } from 'vue'

function decode(token) {
  try {
    const p = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(p))
  } catch {
    return null
  }
}

export const auth = reactive({ token: localStorage.getItem('token'), user: null })

function refresh() {
  const d = auth.token ? decode(auth.token) : null
  if (d && d.exp * 1000 > Date.now()) {
    auth.user = { email: d.sub, role: d.role }
  } else {
    auth.user = null
    auth.token = null
    localStorage.removeItem('token')
  }
}

export function setToken(t) {
  auth.token = t
  localStorage.setItem('token', t)
  refresh()
}

export function logout() {
  auth.token = null
  auth.user = null
  localStorage.removeItem('token')
}

refresh()