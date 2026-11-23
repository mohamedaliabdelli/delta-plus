import re
import uuid
from datetime import datetime
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user
from models_mongo import Equipment
from models_orders import Order, OrderLine, OrderEvent, OrderStatus, Payment, now
from tickets import need_roles, role_of, get_oid

router = APIRouter(tags=["Boutique"])

DECLINED = {
    "4000000000000002": "Carte refusée par la banque (simulation)",
    "4000000000009995": "Fonds insuffisants (simulation)",
}


# ---------- schémas ----------
class CartItem(BaseModel):
    equipment_id: str
    quantity: int = Field(gt=0, le=1000)


class CardIn(BaseModel):
    number: str
    holder: str
    expiry: str          # MM/AA
    cvc: str


class CheckoutIn(BaseModel):
    items: list[CartItem] = Field(min_length=1, max_length=50)
    address: str = Field(min_length=5)
    city: str = Field(min_length=2)
    phone: Optional[str] = None
    card: CardIn


class OrderStatusIn(BaseModel):
    status: OrderStatus


# ---------- paiement simulé ----------
def luhn_ok(num: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(num)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def simulate_payment(card: CardIn) -> tuple[str, str]:
    """Valide la carte et simule la réponse de la banque. Rien n'est stocké."""
    number = re.sub(r"[\s-]", "", card.number)
    if not number.isdigit() or not 13 <= len(number) <= 19 or not luhn_ok(number):
        raise HTTPException(402, "Numéro de carte invalide")
    m = re.fullmatch(r"(\d{2})/(\d{2})", card.expiry.strip())
    if not m:
        raise HTTPException(402, "Date d'expiration invalide (format MM/AA)")
    month, year = int(m[1]), 2000 + int(m[2])
    today = datetime.now()
    if not 1 <= month <= 12:
        raise HTTPException(402, "Date d'expiration invalide (format MM/AA)")
    if (year, month) < (today.year, today.month):
        raise HTTPException(402, "Carte expirée")
    if not re.fullmatch(r"\d{3,4}", card.cvc.strip()):
        raise HTTPException(402, "Code CVC invalide")
    if not card.holder.strip():
        raise HTTPException(402, "Nom du titulaire manquant")
    if number in DECLINED:
        raise HTTPException(402, DECLINED[number])
    return number[-4:], "SIM-" + uuid.uuid4().hex[:10].upper()


# ---------- stock ----------
async def restore(items):
    for eq_id, qty in items:
        await Equipment.find_one({"_id": eq_id}).update({"$inc": {"quantity": qty}})


async def reserve(needed):
    """Décrémente le stock de façon atomique, ou annule tout."""
    done = []
    for eq, qty in needed:
        res = await Equipment.find_one(
            {"_id": eq.id, "quantity": {"$gte": qty}}
        ).update({"$inc": {"quantity": -qty}})
        if not res or getattr(res, "modified_count", 0) != 1:
            await restore(done)
            raise HTTPException(409, f"Stock insuffisant pour « {eq.name} »")
        done.append((eq.id, qty))
    return done


# ---------- helpers ----------
def log(o: Order, user, action: str):
    o.events.append(OrderEvent(author_email=user.email, action=action))
    o.updated_at = now()


def can_view(user, o: Order) -> bool:
    r = role_of(user)
    return r == "admin" or (r == "client" and o.customer_id == user.id)


# ---------- catalogue de la boutique (client uniquement) ----------
@router.get("/shop/products")
async def products(user=Depends(get_current_user)):
    need_roles(user, "client")
    items = await Equipment.find({"prix_tnd": {"$gt": 0}}).sort("reference").to_list()
    return [{
        "id": str(e.id), "name": e.name, "reference": e.reference,
        "categorie": e.categorie, "conditionnement": e.conditionnement,
        "prix_tnd": e.prix_tnd, "stock": e.quantity,
    } for e in items]


# ---------- commandes ----------
@router.post("/orders", status_code=201)
async def checkout(data: CheckoutIn, user=Depends(get_current_user)):
    need_roles(user, "client")

    merged: dict[str, int] = {}
    for it in data.items:
        merged[it.equipment_id] = merged.get(it.equipment_id, 0) + it.quantity

    needed, lines = [], []
    for eid, qty in merged.items():
        eq = await get_oid(Equipment, eid, "Article")
        if eq.prix_tnd is None or eq.prix_tnd <= 0:
            raise HTTPException(400, f"« {eq.name} » n'est pas vendu en ligne")
        if eq.quantity < qty:
            raise HTTPException(
                409, f"Stock insuffisant pour « {eq.name} » ({eq.quantity} disponible(s))")
        needed.append((eq, qty))
        lines.append(OrderLine(
            equipment_id=str(eq.id), reference=eq.reference, name=eq.name,
            unit_price=eq.prix_tnd, quantity=qty,
            line_total=round(eq.prix_tnd * qty, 3)))

    last4, tx = simulate_payment(data.card)      # refus possible avant toute écriture
    reserved = await reserve(needed)

    order = Order(
        number=f"CMD-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:5].upper()}",
        customer_id=user.id, customer_email=user.email,
        lines=lines, total_tnd=round(sum(l.line_total for l in lines), 3),
        address=data.address, city=data.city, phone=data.phone,
        payment=Payment(status="paye", card_last4=last4, transaction_id=tx),
    )
    log(order, user, f"Commande passée et payée (carte •••• {last4})")
    try:
        return await order.insert()
    except Exception:
        await restore(reserved)
        raise


@router.get("/orders")
async def list_orders(status: Optional[OrderStatus] = None,
                      user=Depends(get_current_user)):
    need_roles(user, "client", "admin")
    q = {}
    if role_of(user) == "client":
        q["customer_id"] = user.id
    if status:
        q["status"] = status.value
    return await Order.find(q).sort("-created_at").to_list()


@router.get("/orders/{order_id}")
async def get_order(order_id: str, user=Depends(get_current_user)):
    o = await get_oid(Order, order_id, "Commande")
    if not can_view(user, o):
        raise HTTPException(403, "Commande non accessible")
    return o


@router.patch("/orders/{order_id}/status")
async def change_status(order_id: str, data: OrderStatusIn,
                        user=Depends(get_current_user)):
    need_roles(user, "admin")
    o = await get_oid(Order, order_id, "Commande")
    allowed = {OrderStatus.payee: [OrderStatus.expediee],
               OrderStatus.expediee: [OrderStatus.livree]}
    if data.status not in allowed.get(o.status, []):
        raise HTTPException(400, f"Transition {o.status.value} → "
                                 f"{data.status.value} interdite")
    old = o.status.value
    o.status = data.status
    log(o, user, f"Statut {old} → {data.status.value}")
    await o.save()
    return o


@router.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: str, user=Depends(get_current_user)):
    o = await get_oid(Order, order_id, "Commande")
    if not can_view(user, o):
        raise HTTPException(403, "Commande non accessible")
    if o.status != OrderStatus.payee:
        raise HTTPException(400, "Annulation impossible : commande déjà expédiée ou clôturée")
    await restore([(PydanticObjectId(l.equipment_id), l.quantity) for l in o.lines])
    o.status = OrderStatus.annulee
    o.payment.status = "rembourse"
    log(o, user, "Commande annulée, remboursement simulé")
    await o.save()
    return o