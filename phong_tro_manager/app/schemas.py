"""Pydantic schemas cho API."""
from datetime import date, datetime
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
    has_ac: bool = False  # Phòng có điều hòa trong thiết bị hay không

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
    electricity_price: float = 3500
    water_price: float = 20000
    facebook_url: str = ""
    house_rules: str = ""


class SettingsUpdate(BaseModel):
    address: Optional[str] = None
    phone: Optional[str] = None
    hours: Optional[str] = None
    map_location: Optional[str] = None
    map_embed_url: Optional[str] = None
    background_image: Optional[str] = None
    electricity_price: Optional[float] = None
    water_price: Optional[float] = None
    facebook_url: Optional[str] = None
    house_rules: Optional[str] = None


# ---------------------------------------------------------------------------
# Liên hệ / đặt phòng
# ---------------------------------------------------------------------------

class ContactMessageCreate(BaseModel):
    name: str
    phone: str
    email: str = ""
    room_id: Optional[int] = None
    message: str = ""


class ContactMessageOut(BaseModel):
    id: int
    name: str
    phone: str
    email: str
    room_id: Optional[int] = None
    room_name: Optional[str] = None
    message: str
    is_read: bool
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Khách trọ
# ---------------------------------------------------------------------------

class TenantOut(BaseModel):
    id: int
    full_name: str
    phone: str
    id_card: str
    permanent_address: str
    note: str
    room_id: Optional[int] = None
    room_name: Optional[str] = None
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    status: str
    created_at: Optional[datetime] = None


class TenantCreate(BaseModel):
    full_name: str
    phone: str = ""
    id_card: str = ""
    permanent_address: str = ""
    note: str = ""
    room_id: Optional[int] = None
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    status: str = "active"


class TenantUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    id_card: Optional[str] = None
    permanent_address: Optional[str] = None
    note: Optional[str] = None
    room_id: Optional[int] = None
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    status: Optional[str] = None


# ---------------------------------------------------------------------------
# Điện nước
# ---------------------------------------------------------------------------

class UtilityBillOut(BaseModel):
    id: int
    tenant_id: int
    tenant_name: Optional[str] = None
    room_name: Optional[str] = None
    month: str
    elec_old: float
    elec_new: float
    water_old: float
    water_new: float
    elec_amount: float
    water_amount: float
    other_fee: float
    total: float
    paid: bool
    note: str
    created_at: Optional[datetime] = None


class UtilityBillCreate(BaseModel):
    tenant_id: int
    month: str
    elec_old: float = 0
    elec_new: float = 0
    water_old: float = 0
    water_new: float = 0
    other_fee: float = 0
    note: str = ""


class UtilityBillUpdate(BaseModel):
    elec_old: Optional[float] = None
    elec_new: Optional[float] = None
    water_old: Optional[float] = None
    water_new: Optional[float] = None
    other_fee: Optional[float] = None
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Hợp đồng
# ---------------------------------------------------------------------------

class ContractOut(BaseModel):
    id: int
    tenant_id: int
    tenant_name: Optional[str] = None
    room_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    deposit: float
    monthly_rent: float
    note: str
    created_at: Optional[datetime] = None


class ContractCreate(BaseModel):
    tenant_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    deposit: float = 0
    monthly_rent: float = 0
    note: str = ""


class ContractUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    deposit: Optional[float] = None
    monthly_rent: Optional[float] = None
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Tài khoản admin & phân quyền
# ---------------------------------------------------------------------------

class AdminOut(BaseModel):
    id: int
    username: str
    role: str


class AdminCreate(BaseModel):
    username: str
    password: str
    role: str = "staff"


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str