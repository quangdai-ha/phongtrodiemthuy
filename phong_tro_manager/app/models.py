"""Định nghĩa các bảng dữ liệu."""
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base

# Trạng thái phòng
STATUS_AVAILABLE = "available"      # Phòng trống
STATUS_OCCUPIED = "occupied"        # Đã có người ở
STATUS_MAINTENANCE = "maintenance"  # Đang bảo trì / chưa cho thuê

STATUS_CHOICES = (STATUS_AVAILABLE, STATUS_OCCUPIED, STATUS_MAINTENANCE)

# Phân quyền admin
ROLE_ADMIN = "admin"   # Toàn quyền
ROLE_STAFF = "staff"   # Hạn chế: không xóa dữ liệu, không đổi cài đặt, không quản lý tài khoản
ROLE_CHOICES = (ROLE_ADMIN, ROLE_STAFF)

# Trạng thái khách trọ
TENANT_ACTIVE = "active"        # Đang ở
TENANT_MOVED_OUT = "moved_out"  # Đã chuyển đi
TENANT_STATUS_CHOICES = (TENANT_ACTIVE, TENANT_MOVED_OUT)


class Room(Base):
    """Phòng trọ."""
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    price = Column(Float, nullable=False, default=0)
    area = Column(Float, nullable=False, default=0)
    description = Column(Text, default="")
    equipment = Column(Text, default="[]")  # Danh sách thiết bị dạng JSON
    status = Column(String(20), nullable=False, default=STATUS_AVAILABLE)
    created_at = Column(DateTime, default=datetime.utcnow)

    images = relationship(
        "RoomImage",
        back_populates="room",
        cascade="all, delete-orphan",
        order_by="RoomImage.id",
    )


class RoomImage(Base):
    """Hình ảnh của phòng."""

    __tablename__ = "room_images"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("Room", back_populates="images")


class StoredFile(Base):
    """Nội dung file ảnh lưu trong DB để dữ liệu bền trên hosting.

    Trên môi trường free tier của Render/Railway ổ đĩa là tạm thời nên ta
    lưu dữ liệu ảnh (bytes) ngay trong PostgreSQL/SQLite thay vì file.
    """

    __tablename__ = "stored_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, nullable=False, index=True)
    content_type = Column(String(120), default="application/octet-stream")
    data = Column(LargeBinary)
    created_at = Column(DateTime, default=datetime.utcnow)


class Admin(Base):
    """Tài khoản quản trị viên."""

    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default=ROLE_ADMIN, index=True)


class SiteSettings(Base):
    """Thông tin liên hệ & bản đồ của website."""

    __tablename__ = "site_settings"

    id = Column(Integer, primary_key=True)
    address = Column(String(255), default="")
    phone = Column(String(50), default="")
    hours = Column(String(120), default="")
    map_location = Column(String(255), default="")     # Địa chỉ dùng để tạo bản đồ Google
    map_embed_url = Column(String(500), default="")    # Mã nhúng iframe (tùy chọn, ưu tiên hơn map_location)
    background_image = Column(String(255), default="") # Ảnh nền phần tiêu đề (URL /uploads/...)
    # Đơn giá điện nước (VNĐ) dùng để tính tiền trong mục quản lý điện nước
    electricity_price = Column(Float, default=3500)    # VNĐ / kWh
    water_price = Column(Float, default=20000)         # VNĐ / m³
    # Liên kết mạng xã hội (tùy chọn, hiển thị ở phần Liên hệ)
    facebook_url = Column(String(500), default="")
    # Nội quy & Quy định xóm trọ hiển thị trên trang khách (dạng text, mỗi dòng một điều khoản)
    house_rules = Column(Text, default="")


class Tenant(Base):
    """Khách trọ đang thuê / đã thuê phòng."""

    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(30), default="")
    id_card = Column(String(30), default="")          # Số CCCD/CMND
    permanent_address = Column(String(255), default="")  # Địa chỉ thường trú
    note = Column(Text, default="")
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    check_in = Column(Date, nullable=True)
    check_out = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default=TENANT_ACTIVE, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("Room")


class UtilityBill(Base):
    """Hóa đơn điện nước theo tháng của khách trọ."""

    __tablename__ = "utility_bills"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    month = Column(String(7), nullable=False, index=True)  # Dạng "2026-09"
    elec_old = Column(Float, default=0)     # Chỉ số điện cũ (kWh)
    elec_new = Column(Float, default=0)     # Chỉ số điện mới (kWh)
    water_old = Column(Float, default=0)    # Chỉ số nước cũ (m³)
    water_new = Column(Float, default=0)    # Chỉ số nước mới (m³)
    elec_amount = Column(Float, default=0)  # Thành tiền điện (đã chốt theo đơn giá lúc tạo)
    water_amount = Column(Float, default=0) # Thành tiền nước (đã chốt theo đơn giá lúc tạo)
    other_fee = Column(Float, default=0)    # Phụ phí khác (rác, chung...)
    total = Column(Float, default=0)
    paid = Column(Boolean, default=False)
    note = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant")


class Contract(Base):
    """Hợp đồng thuê phòng."""

    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    deposit = Column(Float, default=0)          # Tiền đặt cọc
    monthly_rent = Column(Float, default=0)     # Tiền thuê hàng tháng
    note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant")


class ContactMessage(Base):
    """Tin nhắn liên hệ / đặt phòng gửi từ trang khách."""

    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=False)
    email = Column(String(120), default="")
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    message = Column(Text, default="")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("Room")