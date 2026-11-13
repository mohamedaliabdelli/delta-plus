from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from beanie import Document
from pydantic import Field


def now():
    return datetime.now(timezone.utc)


class DeviceStatus(str, Enum):
    en_ligne = "en_ligne"
    alerte = "alerte"
    hors_ligne = "hors_ligne"


class NetworkDevice(Document):
    name: str
    ip: str
    type: str = "routeur"  # routeur | switch | borne
    establishment_id: str
    establishment_name: str
    status: DeviceStatus = DeviceStatus.en_ligne
    last_seen: Optional[datetime] = None
    created_at: datetime = Field(default_factory=now)

    class Settings:
        name = "network_devices"


class Metric(Document):
    device_id: str
    date: datetime = Field(default_factory=now)
    status: DeviceStatus
    latency_ms: Optional[float] = None
    packet_loss: Optional[float] = None   # en %
    cpu: Optional[float] = None           # en %
    bandwidth_mbps: Optional[float] = None

    class Settings:
        name = "metrics"