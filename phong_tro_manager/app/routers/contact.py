"""API liên hệ & đặt phòng (khách gửi tin, admin xem/trả lời)."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import require_admin_role
from ..database import get_db
from ..models import STATUS_AVAILABLE, Room, ContactMessage
from ..schemas import ContactMessageCreate, ContactMessageOut

router = APIRouter(prefix="/api/contact", tags=["contact"])


def _to_out(m: ContactMessage) -> ContactMessageOut:
    return ContactMessageOut(
        id=m.id,
        name=m.name,
        phone=m.phone,
        email=m.email or "",
        room_id=m.room_id,
        room_name=m.room.name if m.room else None,
        message=m.message or "",
        is_read=bool(m.is_read),
        created_at=m.created_at,
    )


@router.post("", response_model=ContactMessageOut, status_code=201)
def create_message(body: ContactMessageCreate, db: Session = Depends(get_db)):
    """Khách gửi tin nhắn liên hệ / yêu cầu đặt phòng (công khai)."""
    name = (body.name or "").strip()
    phone = (body.phone or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Vui lòng nhập họ tên.")
    if not phone:
        raise HTTPException(status_code=400, detail="Vui lòng nhập số điện thoại.")

    room_id = body.room_id
    if room_id is not None:
        room = db.query(Room).filter(Room.id == room_id).first()
        if room is None:
            raise HTTPException(status_code=400, detail="Phòng không tồn tại.")
        if room.status != STATUS_AVAILABLE:
            raise HTTPException(
                status_code=400,
                detail="Phòng này hiện không còn trống để đặt.",
            )

    message = ContactMessage(
        name=name,
        phone=phone,
        email=(body.email or "").strip(),
        room_id=room_id,
        message=(body.message or "").strip(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return _to_out(message)


@router.get("", response_model=list[ContactMessageOut])
def list_messages(
    db: Session = Depends(get_db),
    admin=Depends(require_admin_role),
):
    """Danh sách tin nhắn liên hệ (chỉ role admin), mới nhất trước."""
    rows = (
        db.query(ContactMessage)
        .order_by(ContactMessage.created_at.desc(), ContactMessage.id.desc())
        .all()
    )
    return [_to_out(m) for m in rows]


@router.put("/{message_id}/read", response_model=ContactMessageOut)
def mark_read(
    message_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin_role),
):
    """Đánh dấu tin nhắn đã xem."""
    m = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if m is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tin nhắn.")
    m.is_read = True
    db.commit()
    db.refresh(m)
    return _to_out(m)


@router.delete("/{message_id}", status_code=204)
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin_role),
):
    """Xóa tin nhắn (chỉ role admin)."""
    m = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if m is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tin nhắn.")
    db.delete(m)
    db.commit()