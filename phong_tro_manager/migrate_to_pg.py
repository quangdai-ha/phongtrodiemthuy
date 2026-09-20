"""Di chuyển dữ liệu thật từ SQLite (máy nhà) sang PostgreSQL (production).

Cách chạy (ở mấy nhà, LẦN ĐẦU sau khi tạo xong PostgreSQL ở Render/Railway):

    set DATABASE_URL=postgresql://user:pass@host:port/dbname
    .\\.venv\\Scripts\\python migrate_to_pg.py

Lưu ý:
- KHÔNG xoá/đổi dữ liệu SQLite gốc (chỉ đọc).
- Postgres đích nên trống (chưa khởi động app lần nào) để tránh đụng khoá unique.
- Các biến môi trường đọc từ cmd ở trên chỉ có giá trị trong mỗi cửa sổ terminal.
"""
import os
import sys

# In tiếng Việt chuẩn trên Windows (kể cả khi redirect ra file)
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Đưa thư mục gốc dự án vào PYTHONPATH để import app.models
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Admin,
    ContactMessage,
    Contract,
    Room,
    RoomImage,
    SiteSettings,
    StoredFile,
    Tenant,
    UtilityBill,
)


def main() -> None:
    pg_url = os.environ.get("DATABASE_URL", "").strip()
    if not pg_url:
        print("LỖI: Hãy đặt biến môi trường DATABASE_URL trỏ tới PostgreSQL đích.")
        sys.exit(1)

    sqlite_url = (f"sqlite:///{os.path.join(BASE_DIR, 'data', 'phongtro.db')}").replace("\\", "/")
    upload_dir = os.path.join(BASE_DIR, "uploads")

    engine_src = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    engine_dst = create_engine(pg_url.replace("postgres://", "postgresql://", 1))

    Base.metadata.create_all(bind=engine_dst)

    Src = sessionmaker(bind=engine_src)
    Dst = sessionmaker(bind=engine_dst)

    src = Src()
    dst = Dst()
    try:
        # An toàn: không chạy 2 lần trên DB đã có dữ liệu
        if dst.query(Room).count() > 0:
            print("❌ DB đích đã có dữ liệu. Hãy dùng DB trống hoặc xoá (reset) trước.")
            sys.exit(1)

        # --- Admins ---
        for a in src.query(Admin).all():
            dst.add(
                Admin(
                    username=a.username,
                    password_hash=a.password_hash,
                    role=a.role or "admin",
                )
            )
        print(f"✓ Admins: {src.query(Admin).count()}")

        # --- Rooms (giữ mapping id để nối ảnh) ---
        room_id_map = {}
        for r in src.query(Room).order_by(Room.id).all():
            new_room = Room(
                id=None,
                name=r.name,
                price=r.price,
                area=r.area,
                description=r.description,
                equipment=r.equipment,
                status=r.status,
                created_at=r.created_at,
            )
            dst.add(new_room)
            dst.flush()
            room_id_map[r.id] = new_room.id
        print(f"[2] Rooms: {len(room_id_map)}")

        # --- Room images (kèm nội dung ảnh từ đĩa vào DB) ---
        copied = skipped = 0
        for img in src.query(RoomImage).all():
            new_id = room_id_map.get(img.room_id)
            if new_id is None:
                skipped += 1
                continue
            dst.add(RoomImage(room_id=new_id, filename=img.filename, created_at=img.created_at))
            _store_bytes(dst, upload_dir, img.filename)
            copied += 1
        print(f"[3] RoomImages: {copied} bản sao, {skipped} bỏ qua (phòng không tồn tại)")

        # --- SiteSettings ---
        for s in src.query(SiteSettings).all():
            dst.add(
                SiteSettings(
                    address=s.address,
                    phone=s.phone,
                    hours=s.hours,
                    map_location=s.map_location,
                    map_embed_url=s.map_embed_url,
                    background_image=s.background_image,
                    electricity_price=s.electricity_price,
                    water_price=s.water_price,
                    facebook_url=s.facebook_url,
                    house_rules=s.house_rules,
                )
            )
            bg_fn = (s.background_image or "").rsplit("/", 1)[-1]
            if bg_fn:
                _store_bytes(dst, upload_dir, bg_fn)
        print("[4] SiteSettings: ok")

        # --- Tenants (giữ mapping để nối hóa đơn & hợp đồng) ---
        tenant_id_map = {}
        for t in src.query(Tenant).order_by(Tenant.id).all():
            new_tenant = Tenant(
                full_name=t.full_name,
                phone=t.phone,
                id_card=t.id_card,
                permanent_address=t.permanent_address,
                note=t.note,
                room_id=room_id_map.get(t.room_id),
                check_in=t.check_in,
                check_out=t.check_out,
                status=t.status,
                created_at=t.created_at,
            )
            dst.add(new_tenant)
            dst.flush()
            tenant_id_map[t.id] = new_tenant.id
        print(f"[5] Tenants: {len(tenant_id_map)}")

        # --- Utility bills ---
        bill_count = 0
        for b in src.query(UtilityBill).all():
            tenant_id = tenant_id_map.get(b.tenant_id)
            if tenant_id is None:
                continue
            dst.add(
                UtilityBill(
                    tenant_id=tenant_id,
                    month=b.month,
                    elec_old=b.elec_old,
                    elec_new=b.elec_new,
                    water_old=b.water_old,
                    water_new=b.water_new,
                    elec_amount=b.elec_amount,
                    water_amount=b.water_amount,
                    other_fee=b.other_fee,
                    total=b.total,
                    paid=b.paid,
                    note=b.note,
                    created_at=b.created_at,
                )
            )
            bill_count += 1
        print(f"[6] UtilityBills: {bill_count}")

        # --- Contracts ---
        contract_count = 0
        for c in src.query(Contract).all():
            tenant_id = tenant_id_map.get(c.tenant_id)
            if tenant_id is None:
                continue
            dst.add(
                Contract(
                    tenant_id=tenant_id,
                    start_date=c.start_date,
                    end_date=c.end_date,
                    deposit=c.deposit,
                    monthly_rent=c.monthly_rent,
                    note=c.note,
                    created_at=c.created_at,
                )
            )
            contract_count += 1
        print(f"[7] Contracts: {contract_count}")

        # --- Contact / booking messages ---
        message_count = 0
        for m in src.query(ContactMessage).all():
            dst.add(
                ContactMessage(
                    name=m.name,
                    phone=m.phone,
                    email=m.email,
                    room_id=room_id_map.get(m.room_id),
                    message=m.message,
                    is_read=m.is_read,
                    created_at=m.created_at,
                )
            )
            message_count += 1
        print(f"[8] ContactMessages: {message_count}")

        dst.commit()
        print("\n✅ Hoàn tất! Dữ liệu thật đã sang PostgreSQL.")
        print("   Tiếp theo: cấu hình Web Service trên Render trỏ tới repo này và deploy.")
    except Exception as exc:
        dst.rollback()
        print(f"\n❌ Lỗi khi di chuyển: {exc}")
        sys.exit(1)
    finally:
        src.close()
        dst.close()


def _store_bytes(dst, upload_dir: str, filename: str) -> None:
    """Chép nội dung một ảnh đĩa vào bảng stored_files trong DB đích."""
    if not filename or dst.query(StoredFile).filter(StoredFile.filename == filename).first():
        return
    path = os.path.join(upload_dir, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            dst.add(StoredFile(filename=filename, content_type="application/octet-stream", data=f.read()))
    else:
        print(f"   ⚠️  Không tìm thấy file ảnh trên đĩa: {filename}")


if __name__ == "__main__":
    main()