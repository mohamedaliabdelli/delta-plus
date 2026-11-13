import { createRouter, createWebHistory } from 'vue-router'
import { auth } from './auth'

const routes = [
  { path: '/login', component: () => import('./views/LoginView.vue'), meta: { public: true } },
  { path: '/', component: () => import('./views/HomeView.vue') },
  {
    path: '/equipments',
    component: () => import('./views/EquipmentsView.vue'),
    meta: { roles: ['admin', 'technicien'] },
  },
  { path: '/tickets', component: () => import('./views/TicketsView.vue') },
  {
    path: '/monitoring',
    component: () => import('./views/MonitoringView.vue'),
    meta: { roles: ['admin', 'technicien'] },
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  if (!to.meta.public && !auth.user) return '/login'
  if (to.path === '/login' && auth.user) return '/'
  if (to.meta.roles && !to.meta.roles.includes(auth.user.role)) return '/'
})

export default router 