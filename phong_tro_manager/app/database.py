"""Cấu hình cơ sở dữ liệu: PostgreSQL (production) hoặc SQLite (máy nhà)."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Thư mục gốc của dự án (phong_tro_manager/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "phongtro.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Trong môi trường production (Render/Railway) ta dùng biến môi trường DATABASE_URL
# trỏ tới PostgreSQL. Khi chạy ở máy nhà, chưa đặt biến này -> dùng SQLite.
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL:
    # Production: PostgreSQL (đã có sẵn trình điều khiển psycopg2)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    # Máy nhà / không có biến môi trường -> SQLite file
    engine = create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency cung cấp session DB cho các route."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()