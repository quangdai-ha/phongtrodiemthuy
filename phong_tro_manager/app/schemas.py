"""Pydantic schemas cho API."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ImageOut(BaseModel):
    id: int
    filename: str
    url: str

    model_config = {"from_attributes": True}


class RoomListItem(BaseModel):
    id: int
    name: str
    price: float
    area: float
    status: str
    thumbnail_url: Optional[str] = None

    model_config = {"from_attributes": True}


class RoomDetail(RoomListItem):
    description: str
    equipment: List[str] = Field(default_factory=list)
    images: List[ImageOut] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class StatsOut(BaseModel):
    total: int
    available: int
    occupied: int
    maintenance: int


class RoomCreate(BaseModel):
    name: str
    price: float = 0
    area: float = 0
    description: str = ""
    equipment: List[str] = Field(default_factory=list)
    status: str = "available"


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    area: Optional[float] = None
    description: Optional[str] = None
    equipment: Optional[List[str]] = None
    status: Optional[str] = None


class SettingsOut(BaseModel):
    address: str
    phone: str
    hours: str
    map_location: str
    map_embed_url: str
    background_image: str


class SettingsUpdate(BaseModel):
    address: Optional[str] = None
    phone: Optional[str] = None
    hours: Optional[str] = None
    map_location: Optional[str] = None
    map_embed_url: Optional[str] = None
    background_image: Optional[str] = None