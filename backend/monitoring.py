import asyncio
import random
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import get_current_user
from models_monitoring import NetworkDevice, Metric, DeviceStatus, now
from models_tickets import Establishment, Ticket, Priority, Intervention
from tickets import need_roles, get_oid

router = APIRouter(tags=["Monitoring"])

SIM_INTERVAL = 30            # secondes entre deux mesures
P_FAILURE = 0.03             # probabilité de panne par mesure
P_RECOVERY = 0.30            # probabilité de rétablissement par mesure
SYSTEM_EMAIL = "monitoring@delta.tn"


# ---------- ticket automatique ----------
async def open_ticket_for(device: NetworkDevice, reason: str):
    existing = await Ticket.find_one(
        {"equipment_id": str(device.id), "status": {"$ne": "clos"}})
    if existing:
        return existing
    t = Ticket(
        title=f"Panne réseau : {device.name}",
        description=reason,
        priority=Priority.haute,
        equipment_id=str(device.id),
        equipment_name=device.name,
        establishment_id=device.establishment_id,
        establishment_name=device.establishment_name,
        created_by=0,
        created_by_email=SYSTEM_EMAIL,
    )
    t.interventions.append(Intervention(
        author_id=0, author_email=SYSTEM_EMAIL,
        action="Ticket créé automatiquement par le monitoring"))
    return await t.insert()


# ---------- simulateur ----------
def measure() -> dict:
    latency = random.uniform(5, 60)
    loss = random.uniform(0, 1)
    cpu = random.uniform(10, 70)
    if random.random() < 0.10:       # pic occasionnel
        latency = random.uniform(100, 250)
        cpu = random.uniform(90, 99)
        loss = random.uniform(5, 15)
    return {"latency_ms": round(latency, 1), "packet_loss": round(loss, 1),
            "cpu": round(cpu, 1),
            "bandwidth_mbps": round(random.uniform(50, 900), 1)}


def status_from(m: dict) -> DeviceStatus:
    if m["latency_ms"] > 100 or m["packet_loss"] > 5 or m["cpu"] > 90:
        return DeviceStatus.alerte
    return DeviceStatus.en_ligne


async def go_down(d: NetworkDevice, reason: str):
    d.status = DeviceStatus.hors_ligne
    await d.save()
    await Metric(device_id=str(d.id), status=d.status).insert()
    await open_ticket_for(d, reason)


async def simulate_once():
    for d in await NetworkDevice.find_all().to_list():
        if d.status == DeviceStatus.hors_ligne:
            if random.random() >= P_RECOVERY:
                await Metric(device_id=str(d.id), status=d.status).insert()
                continue
        elif random.random() < P_FAILURE:
            await go_down(d, "Équipement injoignable (détecté par le monitoring)")
            continue
        m = measure()
        d.status, d.last_seen = status_from(m), now()
        await d.save()
        await Metric(device_id=str(d.id), status=d.status, **m).insert()


async def simulator_loop():
    while True:
        try:
            await simulate_once()
        except Exception as e:
            print("Erreur simulateur :", e)
        await asyncio.sleep(SIM_INTERVAL)


# ---------- schémas ----------
class DeviceIn(BaseModel):
    name: str
    ip: str
    type: str = "routeur"
    establishment_id: str


# ---------- routes ----------
@router.post("/devices", status_code=201)
async def create_device(data: DeviceIn, user=Depends(get_current_user)):
    need_roles(user, "admin")
    est = await get_oid(Establishment, data.establishment_id, "Établissement")
    d = NetworkDevice(name=data.name, ip=data.ip, type=data.type,
                      establishment_id=data.establishment_id,
                      establishment_name=est.name)
    return await d.insert()


@router.get("/devices")
async def list_devices(user=Depends(get_current_user)):
    need_roles(user, "admin", "technicien")
    return await NetworkDevice.find_all().to_list()


@router.get("/devices/{device_id}/metrics")
async def device_metrics(device_id: str, limit: int = 50,
                         user=Depends(get_current_user)):
    need_roles(user, "admin", "technicien")
    await get_oid(NetworkDevice, device_id, "Équipement réseau")
    return await Metric.find(Metric.device_id == device_id) \
        .sort("-date").limit(limit).to_list()


@router.post("/devices/{device_id}/simulate-failure")
async def simulate_failure(device_id: str, user=Depends(get_current_user)):
    """Force une panne (pour les tests et la démo)."""
    need_roles(user, "admin")
    d = await get_oid(NetworkDevice, device_id, "Équipement réseau")
    await go_down(d, "Panne simulée manuellement")
    return d


@router.get("/monitoring/alerts")
async def alerts(user=Depends(get_current_user)):
    need_roles(user, "admin", "technicien")
    return await NetworkDevice.find(
        {"status": {"$ne": DeviceStatus.en_ligne.value}}).to_list()


@router.get("/monitoring/summary")
async def summary(user=Depends(get_current_user)):
    need_roles(user, "admin", "technicien")
    devices = await NetworkDevice.find_all().to_list()
    counts = {s.value: 0 for s in DeviceStatus}
    for d in devices:
        counts[d.status.value] += 1
    return {"total": len(devices), **counts}