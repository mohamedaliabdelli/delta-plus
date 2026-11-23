from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document
from pydantic import BaseModel, Field


def now():
    return datetime.now(timezone.utc)


class OrderStatus(str, Enum):
    payee = "payee"
    expediee = "expediee"
    livree = "livree"
    annulee = "annulee"


class OrderLine(BaseModel):
    equipment_id: str
    reference: Optional[str] = None
    name: str
    unit_price: float
    quantity: int
    line_total: float


class Payment(BaseModel):
    method: str = "carte_simulee"
    status: str                      # paye | rembourse
    card_last4: str
    transaction_id: str
    paid_at: datetime = Field(default_factory=now)


class OrderEvent(BaseModel):
    date: datetime = Field(default_factory=now)
    author_email: str
    action: str


class Order(Document):
    number: str
    customer_id: int
    customer_email: str
    lines: list[OrderLine]
    total_tnd: float
    address: str
    city: str
    phone: Optional[str] = None
    status: OrderStatus = OrderStatus.payee
    payment: Payment
    events: list[OrderEvent] = []
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)

    class Settings:
        name = "orders"