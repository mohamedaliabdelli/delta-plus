import axios from 'axios'
import { auth, logout } from './auth'
import router from './router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
})

api.interceptors.request.use((config) => {
  if (auth.token) config.headers.Authorization = `Bearer ${auth.token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (e) => {
    if (e.response?.status === 401) {
      logout()
      router.push('/login')
    }
    return Promise.reject(e)
  },
)

export default api