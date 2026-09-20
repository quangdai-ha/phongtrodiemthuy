"""API quản lý phòng trọ (công khai xem, admin chỉnh sửa)."""
import json
import os
import re
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..auth import get_current_admin, require_admin_role
from ..database import get_db
from ..models import STATUS_CHOICES, Room, RoomImage
from ..schemas import (
    ImageOut,
    RoomCreate,
    RoomDetail,
    RoomListItem,
    RoomUpdate,
    StatsOut,
)
from ..storage import delete_file, save_file

router = APIRouter(prefix="/api/rooms", tags=["rooms"])

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # Giới hạn mỗi ảnh tối đa 8MB


def _equipment_list(room: Room):
    """Đọc cột equipment (JSON) thành list."""
    try:
        data = json.loads(room.equipment or "[]")
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


# Nhận diện "điều hòa" trong thiết bị phòng —
# chấp nhận các biến thể viết sai dấu (Điêu, Điéu, Đieu...):
# Đ + các ký tự + dấu cách tùy chọn + "hòa".
_AC_RE = re.compile(r"Đ\w*\s*hòa", re.IGNORECASE)


def _has_ac(equipment: list) -> bool:
    """Kiểm tra phòng có điều hòa trong thiết bị hay không."""
    return any(bool(_AC_RE.search(item)) for item in equipment)


def _thumbnail(room: Room):
    return f"/uploads/{room.images[0].filename}" if room.images else None


def _to_list_item(room: Room) -> RoomListItem:
    return RoomListItem(
        id=room.id,
        name=room.name,
        price=room.price,
        area=room.area,
        status=room.status,
        thumbnail_url=_thumbnail(room),
        has_ac=_has_ac(_equipment_list(room)),
    )


def _to_detail(room: Room) -> RoomDetail:
    images = [
        ImageOut(id=img.id, filename=img.filename, url=f"/uploads/{img.filename}")
        for img in room.images
    ]
    return RoomDetail(
        id=room.id,
        name=room.name,
        price=room.price,
        area=room.area,
        status=room.status,
        description=room.description or "",
        equipment=_equipment_list(room),
        images=images,
        thumbnail_url=_thumbnail(room),
        has_ac=_has_ac(_equipment_list(room)),
        created_at=room.created_at,
    )


def _get_room_or_404(db: Session, room_id: int) -> Room:
    room = db.query(Room).filter(Room.id == room_id).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng.")
    return room


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=list[RoomListItem])
def list_rooms(
    db: Session = Depends(get_db),
    q: str = Query("", description="Tìm theo tên phòng"),
    status: str = Query("", description="Lọc theo trạng thái"),
    min_price: float = Query(None, description="Giá thấp nhất"),
    max_price: float = Query(None, description="Giá cao nhất"),
    min_area: float = Query(None, description="Diện tích tối thiểu"),
    max_area: float = Query(None, description="Diện tích tối đa"),
):
    """Danh sách phòng cho khách xem (hỗ trợ lọc/tìm kiếm)."""
    query = db.query(Room)
    if q and q.strip():
        query = query.filter(Room.name.ilike(f"%{q.strip()}%"))
    if status and status in STATUS_CHOICES:
        query = query.filter(Room.status == status)
    if min_price is not None:
        query = query.filter(Room.price >= min_price)
    if max_price is not None:
        query = query.filter(Room.price <= max_price)
    if min_area is not None:
        query = query.filter(Room.area >= min_area)
    if max_area is not None:
        query = query.filter(Room.area <= max_area)
    rooms = query.order_by(Room.id).all()
    return [_to_list_item(r) for r in rooms]


@router.get("/stats", response_model=StatsOut)
def room_stats(db: Session = Depends(get_db)):
    """Thống kê số phòng trống / đã ở / bảo trì."""
    rooms = db.query(Room).all()
    total = len(rooms)
    available = sum(1 for r in rooms if r.status == "available")
    occupied = sum(1 for r in rooms if r.status == "occupied")
    maintenance = sum(1 for r in rooms if r.status == "maintenance")
    return StatsOut(
        total=total,
        available=available,
        occupied=occupied,
        maintenance=maintenance,
    )


@router.get("/{room_id}", response_model=RoomDetail)
def room_detail(room_id: int, db: Session = Depends(get_db)):
    """Chi tiết phòng: mô tả, diện tích, thiết bị, hình ảnh."""
    return _to_detail(_get_room_or_404(db, room_id))


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=RoomDetail, status_code=201)
def create_room(
    body: RoomCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Tạo phòng mới."""
    if body.status not in STATUS_CHOICES:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ.")
    if db.query(Room).filter(Room.name == body.name).first():
        raise HTTPException(status_code=400, detail="Tên phòng đã tồn tại.")
    room = Room(
        name=body.name.strip(),
        price=body.price,
        area=body.area,
        description=body.description,
        equipment=json.dumps(body.equipment, ensure_ascii=False),
        status=body.status,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return _to_detail(room)


@router.put("/{room_id}", response_model=RoomDetail)
def update_room(
    room_id: int,
    body: RoomUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Cập nhật thông tin, trạng thái phòng."""
    room = _get_room_or_404(db, room_id)
    updates = body.model_dump(exclude_unset=True)

    if "status" in updates and updates["status"] not in STATUS_CHOICES:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ.")
    if "name" in updates and updates["name"].strip() != room.name:
        conflict = (
            db.query(Room)
            .filter(Room.name == updates["name"].strip(), Room.id != room_id)
            .first()
        )
        if conflict:
            raise HTTPException(status_code=400, detail="Tên phòng đã tồn tại.")
        updates["name"] = updates["name"].strip()

    if "equipment" in updates:
        updates["equipment"] = json.dumps(updates["equipment"], ensure_ascii=False)

    for field, value in updates.items():
        setattr(room, field, value)

    db.commit()
    db.refresh(room)
    return _to_detail(room)


@router.delete("/{room_id}", status_code=204)
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin_role),
):
    """Xóa phòng và các hình ảnh liên quan (chỉ role admin)."""
    room = _get_room_or_404(db, room_id)
    for img in room.images:
        delete_file(db, img.filename)
    db.delete(room)
    db.commit()


@router.post("/{room_id}/images", response_model=ImageOut, status_code=201)
def upload_image(
    room_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Upload hình ảnh cho phòng."""
    room = _get_room_or_404(db, room_id)
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise HTTPException(
            status_code=400,
            detail="Định dạng ảnh không hợp lệ. Hỗ trợ: jpg, png, gif, webp.",
        )
    data = file.file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Ảnh quá lớn. Giới hạn tối đa 8MB cho mỗi ảnh.",
        )
    filename = f"{uuid.uuid4().hex}{ext}"
    save_file(db, filename, data, file.content_type)

    img = RoomImage(room_id=room.id, filename=filename)
    db.add(img)
    db.commit()
    db.refresh(img)
    return ImageOut(id=img.id, filename=img.filename, url=f"/uploads/{img.filename}")


@router.delete("/{room_id}/images/{image_id}", status_code=204)
def delete_image(
    room_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin_role),
):
    """Xóa một hình ảnh của phòng (chỉ role admin)."""
    room = _get_room_or_404(db, room_id)
    img = db.query(RoomImage).filter(
        RoomImage.id == image_id, RoomImage.room_id == room.id
    ).first()
    if img is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hình ảnh.")
    delete_file(db, img.filename)
    db.delete(img)
    db.commit()