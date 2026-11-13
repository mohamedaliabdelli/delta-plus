from datetime import datetime
from enum import Enum

from beanie import Document
from pydantic import Field


class Statut(str, Enum):
    en_stock = "en_stock"
    vendu = "vendu"
    en_maintenance = "en_maintenance"


class Equipment(Document):
    name: str
    reference: str | None = None
    serial_number: str | None = None
    lot: str | None = None
    quantity: int = 1
    min_stock: int = 1
    expiry_date: datetime | None = None
    statut: Statut = Statut.en_stock
    categorie: str | None = None
    conditionnement: str | None = None
    prix_tnd: float | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "equipments"