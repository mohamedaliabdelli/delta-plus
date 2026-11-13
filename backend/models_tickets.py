from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from beanie import Document
from pydantic import BaseModel, Field


def now():
    return datetime.now(timezone.utc)


class TicketStatus(str, Enum):
    ouvert = "ouvert"
    affecte = "affecte"
    en_cours = "en_cours"
    resolu = "resolu"
    clos = "clos"


class Priority(str, Enum):
    basse = "basse"
    normale = "normale"
    haute = "haute"
    critique = "critique"


class Intervention(BaseModel):
    date: datetime = Field(default_factory=now)
    author_id: int
    author_email: str
    action: str


class Establishment(Document):
    name: str
    type: str = "hopital"  # hopital | clinique
    city: Optional[str] = None
    created_at: datetime = Field(default_factory=now)

    class Settings:
        name = "establishments"


class Ticket(Document):
    title: str
    description: str
    priority: Priority = Priority.normale
    status: TicketStatus = TicketStatus.ouvert
    equipment_id: str
    equipment_name: str
    establishment_id: str
    establishment_name: str
    created_by: int
    created_by_email: str
    assigned_to: Optional[int] = None
    assigned_email: Optional[str] = None
    interventions: list[Intervention] = []
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)
    closed_at: Optional[datetime] = None

    class Settings:
        name = "tickets"