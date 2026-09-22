"""Ứng dụng FastAPI - Quản lý phòng trọ."""
import json
import os
import sys
from contextlib import asynccontextmanager

from sqlalchemy import inspect, text

# Đảm bảo in tiếng Việt đúng trên Windows (kể cả khi redirect ra file)
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import storage
from .auth import hash_password
from .database import BASE_DIR, SessionLocal, engine, get_db
from .models import Admin, Base, Room, RoomImage, SiteSettings, StoredFile
from .routers import auth as auth_router
from .routers import contact as contact_router
from .routers import rooms as rooms_router
from .routers import settings as settings_router
from .routers import tenants as tenants_router


# ---------------------------------------------------------------------------
# Seed dữ liệu mẫu
# ---------------------------------------------------------------------------

SAMPLE_ROOMS = [
    {
        "name": "Phòng 101",
        "price": 2_500_000,
        "area": 20,
        "status": "available",
        "description": (
            "Phòng trọ rộng rãi 20m², nằm ở tầng 1, thoáng mát, yên tĩnh."
            " Có ban công riêng, gần khu ăn uống và chợ."
        ),
        "equipment": ["Giường 1m6", "Tủ quần áo", "Điều hòa", "Nóng lạnh", "Wifi", "Bếp từ"],
        "color": "#e8590c",
    },
    {
        "name": "Phòng 102",
        "price": 2_200_000,
        "area": 18,
        "status": "occupied",
        "description": (
            "Phòng 18m² nhỏ gọn, cửa sổ thông thoáng, ánh sáng tự nhiên."
            " Khu vực an ninh, có khóa vân tay."
        ),
        "equipment": ["Giường 1m4", "Tủ quần áo", "Điều hòa", "Nóng lạnh", "Wifi"],
        "color": "#2b8a3e",
    },
    {
        "name": "Phòng 103",
        "price": 2_800_000,
        "area": 24,
        "status": "available",
        "description": (
            "Phòng rộng 24m² thiết kế như chung cư mini, full nội thất."
            " Phù hợp gia đình nhỏ hoặc 2 người ở."
        ),
        "equipment": [
            "Giường 1m6", "Tủ quần áo", "Điều hòa", "Nóng lạnh",
            "Wifi", "Bếp từ", "Máy giặt", "Tủ lạnh",
        ],
        "color": "#1971c2",
    },
    {
        "name": "Phòng 201",
        "price": 2_300_000,
        "area": 20,
        "status": "occupied",
        "description": "Phòng tầng 2, view cây xanh, yên tĩnh. Mới sơn lại và thay mới hệ thống điện nước.",
        "equipment": ["Giường 1m4", "Tủ quần áo", "Điều hòa", "Nóng lạnh", "Wifi"],
        "color": "#9c36b5",
    },
    {
        "name": "Phòng 202",
        "price": 2_100_000,
        "area": 16,
        "status": "maintenance",
        "description": "Phòng đang được bảo trì hệ thống nước, dự kiến mở cho thuê lại trong tháng tới.",
        "equipment": ["Giường 1m4", "Tủ quần áo", "Wifi", "Nóng lạnh"],
        "color": "#f08c00",
    },
]


DEFAULT_HOUSE_RULES = """1. Tiền thuê thanh toán trước, chậm nhất đến ngày 5 hằng tháng.
2. Tiền điện, nước được tính theo công tơ riêng của từng phòng (đơn giá theo mục Điện nước).
3. Giữ yên tĩnh từ 22:00 đến 7:00 — không gây ồn trong phòng và hành lang.
4. Đón tiếp khách từ 8:00 – 22:00. Khách ngủ lại qua đêm chỉ khi được quản lý đồng ý.
5. Giữ gìn vệ sinh trong phòng và khu vực chung (bếp, phòng vệ sinh, hành lang).
6. Cấm hút thuốc trong phòng và trong khuôn viên xóm trọ.
7. Đổ rác đúng nơi quy định (thùng rác ngoài sân) — phải phân loại rác.
8. Cấm mở nhạc / TV ồn ào sau 22:00.
9. Nuôi thú cưng chỉ khi được quản lý đồng ý.
10. Có hư hỏng, sự cố phải báo quản lý ngay.
11. Khi chuyển đi: báo trước quản lý ít nhất 2 tuần và thanh toán đủ các hóa đơn cuối cùng.
12. Nghiêm cấm tàng trữ vũ khí, ma túy và các hành vi vi phạm pháp luật trong khuôn viên xóm trọ."""


DEFAULT_SETTINGS = {
    "address": "123 Đường Nguyễn Trãi, Phường Bến Thành, Quận 1, TP. Hồ Chí Minh",
    "phone": "0901 234 567",
    "hours": "Mở cửa: 7:00 – 22:00 hằng ngày",
    "map_location": "Nguyễn Trãi, Bến Thành, Quận 1, TP. Hồ Chí Minh",
    "map_embed_url": "",
    "background_image": "",
    "electricity_price": 3500,
    "water_price": 20000,
    "facebook_url": "",
    "house_rules": DEFAULT_HOUSE_RULES,
}


def create_sample_svg(filename: str, label: str, color: str) -> tuple[str, bytes]:
    """Tạo nội dung SVG giữ chỗ cho phòng mẫu."""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500">
<defs>
  <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:{color};stop-opacity:1"/>
    <stop offset="100%" style="stop-color:#212529;stop-opacity:1"/>
  </linearGradient>
</defs>
<rect width="800" height="500" fill="url(#g)"/>
<rect x="40" y="40" width="720" height="420" rx="16" fill="none" stroke="#ffffff" stroke-opacity="0.4" stroke-width="3"/>
<text x="400" y="230" font-family="Arial, sans-serif" font-size="64" font-weight="bold" fill="#ffffff" text-anchor="middle">{label}</text>
<text x="400" y="290" font-family="Arial, sans-serif" font-size="24" fill="#ffffff" fill-opacity="0.85" text-anchor="middle">Xóm trọ Sự Bình</text>
</svg>'''
    return filename, svg.encode("utf-8")


def _migrate(db):
    """Thêm các cột mới cho bảng đã tồn tại (nâng cấp schema nhẹ).

    LƯU Ý: mọi câu lệnh ở đây phải chạy được trên CẢ SQLite (máy nhà) và
    PostgreSQL (Render). PostgreSQL KHÔNG chấp nhận giá trị kiểu số cho cột
    BOOLEAN:
      - `... ADD COLUMN is_cover BOOLEAN NOT NULL DEFAULT 0` →
        DatatypeMismatch: column "is_cover" is of type boolean but default
        expression is of type integer
      - `... WHERE is_cover = 1` →
        operator does not exist: boolean = integer
    Vì vậy giá trị boolean được viết theo đúng hệ quản trị đang dùng.
    """
    is_postgres = engine.dialect.name == "postgresql"
    bool_true = "TRUE" if is_postgres else "1"
    bool_false = "FALSE" if is_postgres else "0"

    insp = inspect(engine)
    if "site_settings" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("site_settings")}
        for col, ddl in (
            ("background_image", "VARCHAR(255) DEFAULT ''"),
            ("electricity_price", "FLOAT DEFAULT 3500"),
            ("water_price", "FLOAT DEFAULT 20000"),
            ("facebook_url", "VARCHAR(500) DEFAULT ''"),
            ("house_rules", "TEXT DEFAULT ''"),
        ):
            if col not in cols:
                db.execute(text(f"ALTER TABLE site_settings ADD COLUMN {col} {ddl}"))
                print(f"[seed] Đã thêm cột {col} cho site_settings.")
        db.commit()
    if "admins" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("admins")}
        if "role" not in cols:
            db.execute(text("ALTER TABLE admins ADD COLUMN role VARCHAR(20) DEFAULT 'admin'"))
            db.commit()
            print("[seed] Đã thêm cột role cho admins.")

    if "room_images" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("room_images")}
        if "is_cover" not in cols:
            # Cột NOT NULL thêm vào bảng đã có dữ liệu nên bắt buộc phải có DEFAULT.
            # Dùng FALSE trên PostgreSQL, 0 trên SQLite (xem giải thích ở đầu hàm).
            db.execute(
                text(
                    "ALTER TABLE room_images "
                    f"ADD COLUMN is_cover BOOLEAN NOT NULL DEFAULT {bool_false}"
                )
            )
            db.commit()
            print("[seed] Đã thêm cột is_cover cho room_images.")
        # Ảnh bìa: đảm bảo mỗi phòng có đúng 1 ảnh bìa.
        # Với dữ liệu cũ (chưa đánh dấu) thì ảnh đầu tiên (id nhỏ nhất) làm ảnh bìa.
        rows = db.execute(
            text("SELECT room_id, MIN(id) AS first_id FROM room_images GROUP BY room_id")
        ).fetchall()
        dirty = False
        for row in rows:
            cnt = db.execute(
                text(
                    "SELECT COUNT(*) FROM room_images "
                    f"WHERE room_id = :rid AND is_cover = {bool_true}"
                ),
                {"rid": row[0]},
            ).fetchone()
            if cnt[0] == 0:
                db.execute(
                    text(f"UPDATE room_images SET is_cover = {bool_true} WHERE id = :iid"),
                    {"iid": row[1]},
                )
                dirty = True
        if dirty:
            db.commit()
            print("[seed] Đã gán ảnh bìa cho các phòng chưa có ảnh bìa.")


def seed_data():
    """Tạo bảng, tài khoản admin và dữ liệu phòng mẫu nếu chưa có."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _migrate(db)
        if db.query(Admin).count() == 0:
            db.add(Admin(username="admin", password_hash=hash_password("admin123")))
            db.commit()
            print("[seed] Đã tạo tài khoản admin: admin / admin123")

        if db.query(Room).count() == 0:
            for sample in SAMPLE_ROOMS:
                room = Room(
                    name=sample["name"],
                    price=sample["price"],
                    area=sample["area"],
                    status=sample["status"],
                    description=sample["description"].strip(),
                    equipment=json.dumps(sample["equipment"], ensure_ascii=False),
                )
                db.add(room)
                db.flush()
                filename, svg_bytes = create_sample_svg(
                    f"room{sample['name'].split()[-1]}.svg",
                    sample["name"].replace("Phòng ", "P."),
                    sample["color"],
                )
                db.add(
                    StoredFile(
                        filename=filename,
                        data=svg_bytes,
                        content_type="image/svg+xml",
                    )
                )
                db.add(RoomImage(room_id=room.id, filename=filename, is_cover=True))
            db.commit()
            print("[seed] Đã tạo dữ liệu phòng mẫu.")

        if db.query(SiteSettings).count() == 0:
            db.add(SiteSettings(**DEFAULT_SETTINGS))
            db.commit()
            print("[seed] Đã tạo thông tin liên hệ mẫu.")
        else:
            # Điền nội quy mặc định nếu vẫn còn trống (bản sao cơ sở dữ liệu cũ)
            st = db.query(SiteSettings).order_by(SiteSettings.id).first()
            if st is not None and not (st.house_rules or "").strip():
                st.house_rules = DEFAULT_HOUSE_RULES
                db.commit()
                print("[seed] Đã điền nội quy mặc định.")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_data()
    yield


app = FastAPI(
    title="Xóm trọ Sự Bình",
    description="Trang quản lý phòng trọ Xóm trọ Sự Bình: xem phòng, đặt trạng thái, chỉnh sửa thông tin, hình ảnh, liên hệ và bản đồ.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(rooms_router.router)
app.include_router(settings_router.router)
app.include_router(contact_router.router)
app.include_router(tenants_router.router)

STATIC_DIR = os.path.join(BASE_DIR, "app", "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/uploads/{filename}", include_in_schema=False)
def upload_file(filename: str, db: Session = Depends(get_db)):
    """Trả ảnh đã lưu trong DB (hoặc fallback file đĩa cũ ở máy nhà)."""
    data, content_type = storage.get_file(db, filename)
    if data is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp.")
    return Response(
        content=data,
        media_type=content_type or "application/octet-stream",
    )


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/admin", include_in_schema=False)
def admin_page():
    return FileResponse(os.path.join(STATIC_DIR, "admin.html"))