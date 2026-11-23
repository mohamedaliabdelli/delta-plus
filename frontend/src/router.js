import { createRouter, createWebHistory } from 'vue-router'
import { auth } from './auth'

const buyers = ['client']
const staff = ['admin', 'technicien']

const routes = [
  { path: '/login', component: () => import('./views/LoginView.vue'), meta: { public: true } },
  { path: '/', component: () => import('./views/HomeView.vue') },
  { path: '/equipments', component: () => import('./views/EquipmentsView.vue'), meta: { roles: staff } },
  { path: '/tickets', component: () => import('./views/TicketsView.vue') },
  { path: '/monitoring', component: () => import('./views/MonitoringView.vue'), meta: { roles: staff } },
  { path: '/shop', component: () => import('./views/ShopView.vue'), meta: { roles: buyers } },
  { path: '/cart', component: () => import('./views/CartView.vue'), meta: { roles: buyers } },
  { path: '/orders', component: () => import('./views/OrdersView.vue'), meta: { roles: ['client', 'admin'] } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  if (!to.meta.public && !auth.user) return '/login'
  if (to.path === '/login' && auth.user) return '/'
  if (to.meta.roles && !to.meta.roles.includes(auth.user.role)) return '/'
})

export default router