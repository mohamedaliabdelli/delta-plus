from typing import Optional
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_session as get_db
from models_sql import User
from models_mongo import Equipment          # adapte le nom du module
from models_tickets import (Establishment, Ticket, TicketStatus, Priority,
                            Intervention, now)

router = APIRouter(tags=["SAV"])


# ---------- helpers ----------
def role_of(u) -> str:
    return str(getattr(u.role, "value", u.role))


def need_roles(user, *roles):
    if role_of(user) not in roles:
        raise HTTPException(403, "Accès refusé pour ce rôle")


async def get_oid(model, id_: str, label: str):
    try:
        oid = PydanticObjectId(id_)
    except Exception:
        raise HTTPException(400, f"{label} : id invalide")
    doc = await model.get(oid)
    if not doc:
        raise HTTPException(404, f"{label} introuvable")
    return doc


def can_work_on(user, t: Ticket) -> bool:
    return role_of(user) == "admin" or (
        role_of(user) == "technicien" and t.assigned_to == user.id)


def log(t: Ticket, user, action: str):
    t.interventions.append(Intervention(
        author_id=user.id, author_email=user.email, action=action))
    t.updated_at = now()


# ---------- schemas ----------
class EstablishmentIn(BaseModel):
    name: str
    type: str = "hopital"
    city: Optional[str] = None


class TicketIn(BaseModel):
    title: str
    description: str
    priority: Priority = Priority.normale
    equipment_id: str
    establishment_id: str


class AssignIn(BaseModel):
    technician_id: int


class StatusIn(BaseModel):
    status: TicketStatus   # en_cours ou resolu
    comment: Optional[str] = None


class InterventionIn(BaseModel):
    action: str


# ---------- établissements ----------
@router.post("/establishments", status_code=201)
async def create_establishment(data: EstablishmentIn, user=Depends(get_current_user)):
    need_roles(user, "admin")
    return await Establishment(**data.model_dump()).insert()


@router.get("/establishments")
async def list_establishments(user=Depends(get_current_user)):
    return await Establishment.find_all().to_list()


# ---------- tickets ----------
@router.post("/tickets", status_code=201)
async def create_ticket(data: TicketIn, user=Depends(get_current_user)):
    need_roles(user, "client", "admin")
    eq = await get_oid(Equipment, data.equipment_id, "Équipement")
    est = await get_oid(Establishment, data.establishment_id, "Établissement")
    t = Ticket(**data.model_dump(), equipment_name=eq.name,
               establishment_name=est.name,
               created_by=user.id, created_by_email=user.email)
    log(t, user, "Ticket créé")
    return await t.insert()


@router.get("/tickets")
async def list_tickets(status: Optional[TicketStatus] = None,
                       user=Depends(get_current_user)):
    q = {}
    r = role_of(user)
    if r == "client":
        q["created_by"] = user.id
    elif r == "technicien":
        q["assigned_to"] = user.id
    if status:
        q["status"] = status.value
    return await Ticket.find(q).sort("-created_at").to_list()


@router.get("/tickets/technicians")
async def list_technicians(user=Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    need_roles(user, "admin")
    users = (await db.execute(select(User))).scalars().all()
    return [{"id": u.id, "email": u.email} for u in users
            if role_of(u) == "technicien"]


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, user=Depends(get_current_user)):
    t = await get_oid(Ticket, ticket_id, "Ticket")
    r = role_of(user)
    if (r == "client" and t.created_by != user.id) or \
       (r == "technicien" and t.assigned_to != user.id):
        raise HTTPException(403, "Ticket non accessible")
    return t


@router.patch("/tickets/{ticket_id}/assign")
async def assign_ticket(ticket_id: str, data: AssignIn,
                        user=Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    need_roles(user, "admin")
    t = await get_oid(Ticket, ticket_id, "Ticket")
    if t.status == TicketStatus.clos:
        raise HTTPException(400, "Ticket déjà clos")
    tech = (await db.execute(select(User).where(User.id == data.technician_id))
            ).scalar_one_or_none()
    if not tech or role_of(tech) != "technicien":
        raise HTTPException(400, "Utilisateur non technicien")
    t.assigned_to, t.assigned_email = tech.id, tech.email
    if t.status == TicketStatus.ouvert:
        t.status = TicketStatus.affecte
    log(t, user, f"Affecté à {tech.email}")
    await t.save()
    return t


@router.patch("/tickets/{ticket_id}/status")
async def change_status(ticket_id: str, data: StatusIn,
                        user=Depends(get_current_user)):
    t = await get_oid(Ticket, ticket_id, "Ticket")
    if not can_work_on(user, t):
        raise HTTPException(403, "Seul le technicien affecté (ou admin)")
    allowed = {
        TicketStatus.affecte: [TicketStatus.en_cours],
        TicketStatus.en_cours: [TicketStatus.resolu],
        TicketStatus.resolu: [TicketStatus.en_cours],
    }
    if data.status not in allowed.get(t.status, []):
        raise HTTPException(400, f"Transition {t.status.value} → "
                                 f"{data.status.value} interdite")
    old = t.status.value
    t.status = data.status
    log(t, user, f"Statut {old} → {data.status.value}"
                 + (f" : {data.comment}" if data.comment else ""))
    await t.save()
    return t


@router.post("/tickets/{ticket_id}/interventions", status_code=201)
async def add_intervention(ticket_id: str, data: InterventionIn,
                           user=Depends(get_current_user)):
    t = await get_oid(Ticket, ticket_id, "Ticket")
    if not can_work_on(user, t):
        raise HTTPException(403, "Seul le technicien affecté (ou admin)")
    if t.status == TicketStatus.clos:
        raise HTTPException(400, "Ticket clos")
    log(t, user, data.action)
    await t.save()
    return t


@router.post("/tickets/{ticket_id}/close")
async def close_ticket(ticket_id: str, user=Depends(get_current_user)):
    t = await get_oid(Ticket, ticket_id, "Ticket")
    if not can_work_on(user, t):
        raise HTTPException(403, "Seul le technicien affecté (ou admin)")
    if t.status != TicketStatus.resolu:
        raise HTTPException(400, "Le ticket doit être 'resolu' avant clôture")
    t.status, t.closed_at = TicketStatus.clos, now()
    log(t, user, "Ticket clos")
    await t.save()
    return t


# ---------- historique par établissement ----------
@router.get("/establishments/{est_id}/history")
async def establishment_history(est_id: str, user=Depends(get_current_user)):
    need_roles(user, "admin", "technicien")
    est = await get_oid(Establishment, est_id, "Établissement")
    tickets = await Ticket.find(Ticket.establishment_id == est_id).to_list()
    events = [{
        "date": i.date, "ticket_id": str(t.id), "ticket": t.title,
        "equipment": t.equipment_name, "by": i.author_email, "action": i.action,
    } for t in tickets for i in t.interventions]
    events.sort(key=lambda e: e["date"], reverse=True)
    return {
        "establishment": est.name,
        "tickets_total": len(tickets),
        "tickets_clos": sum(t.status == TicketStatus.clos for t in tickets),
        "events": events,
    }