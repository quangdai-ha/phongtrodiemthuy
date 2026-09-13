"""API quản lý phòng trọ (công khai xem, admin chỉnh sửa)."""
import json
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..auth import get_current_admin
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


def _equipment_list(room: Room):
    """Đọc cột equipment (JSON) thành list."""
    try:
        data = json.loads(room.equipment or "[]")
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


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
def list_rooms(db: Session = Depends(get_db)):
    """Danh sách phòng cho khách xem."""
    rooms = db.query(Room).order_by(Room.id).all()
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
    admin=Depends(get_current_admin),
):
    """Xóa phòng và các hình ảnh liên quan."""
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
    filename = f"{uuid.uuid4().hex}{ext}"
    data = file.file.read()
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
    admin=Depends(get_current_admin),
):
    """Xóa một hình ảnh của phòng."""
    room = _get_room_or_404(db, room_id)
    img = db.query(RoomImage).filter(
        RoomImage.id == image_id, RoomImage.room_id == room.id
    ).first()
    if img is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hình ảnh.")
    delete_file(db, img.filename)
    db.delete(img)
    db.commit()