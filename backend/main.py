import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from beanie import init_beanie
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import AsyncMongoClient
from sqlalchemy import text

from auth import get_current_user, require_role
from auth import router as auth_router
from config import settings
from database import Base, engine
import models_sql  # noqa: F401
from models_mongo import Equipment
from models_tickets import Ticket, Establishment
from models_monitoring import NetworkDevice, Metric
from tickets import router as tickets_router
from monitoring import router as monitoring_router, simulator_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncMongoClient(settings.mongo_url)
    await init_beanie(
        database=client["delta_sav"],
        document_models=[Equipment, Ticket, Establishment,
                         NetworkDevice, Metric],
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    task = asyncio.create_task(simulator_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    await client.close()
    await engine.dispose()


app = FastAPI(title="Delta Plus Médical API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(tickets_router)
app.include_router(monitoring_router)


@app.get("/health")
async def health():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"postgres": "ok", "mongo": "ok"}


@app.post("/equipments")
async def create_equipment(
    item: Equipment,
    user=Depends(require_role("admin", "technicien")),
):
    await item.insert()
    return item


@app.get("/equipments")
async def list_equipments(user=Depends(get_current_user)):
    return await Equipment.find_all().to_list()


@app.get("/equipments/alerts")
async def alerts(days: int = 30, user=Depends(get_current_user)):
    limite = datetime.utcnow() + timedelta(days=days)
    stock_bas = await Equipment.find(
        {"$expr": {"$lte": ["$quantity", "$min_stock"]}}
    ).to_list()
    peremption = await Equipment.find(
        {"expiry_date": {"$ne": None, "$lte": limite}}
    ).to_list()
    return {"stock_bas": stock_bas, "peremption_proche": peremption}