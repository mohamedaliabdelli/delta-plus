import { reactive, computed } from 'vue'

const KEY = 'cart'

function load() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || []
  } catch {
    return []
  }
}

export const cart = reactive({ items: load() })

function save() {
  try {
    localStorage.setItem(KEY, JSON.stringify(cart.items))
  } catch {
    /* stockage indisponible : le panier reste en mémoire */
  }
}

export function addToCart(p, qty = 1) {
  const it = cart.items.find((i) => i.id === p.id)
  if (it) {
    it.stock = p.stock
    it.quantity = Math.min(it.quantity + qty, p.stock)
  } else {
    cart.items.push({
      id: p.id,
      name: p.name,
      reference: p.reference,
      prix_tnd: p.prix_tnd,
      stock: p.stock,
      quantity: Math.min(qty, p.stock),
    })
  }
  save()
}

export function setQty(id, qty) {
  const it = cart.items.find((i) => i.id === id)
  if (!it) return
  const n = Math.floor(Number(qty)) || 1
  it.quantity = Math.max(1, Math.min(n, it.stock))
  save()
}

export function removeFromCart(id) {
  cart.items = cart.items.filter((i) => i.id !== id)
  save()
}

export function clearCart() {
  cart.items = []
  save()
}

export const cartCount = computed(() => cart.items.reduce((s, i) => s + i.quantity, 0))
export const cartTotal = computed(() =>
  cart.items.reduce((s, i) => s + i.quantity * i.prix_tnd, 0),
)