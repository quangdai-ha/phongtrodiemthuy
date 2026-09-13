"""Định nghĩa các bảng dữ liệu."""
from datetime import datetime

from sqlalchemy import (
    Column,
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