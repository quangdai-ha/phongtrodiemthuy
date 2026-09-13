"""API thông tin liên hệ & bản đồ website."""
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..auth import get_current_admin
from ..database import get_db
from ..models import SiteSettings
from ..schemas import SettingsOut, SettingsUpdate
from ..storage import save_file

router = APIRouter(prefix="/api/settings", tags=["settings"])

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _get_settings(db: Session) -> SiteSettings:
    """Lấy dòng cài đặt (tạo mới nếu chưa có)."""
    settings = db.query(SiteSettings).order_by(SiteSettings.id).first()
    if settings is None:
        settings = SiteSettings(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def _to_out(s: SiteSettings) -> SettingsOut:
    return SettingsOut(
        address=s.address or "",
        phone=s.phone or "",
        hours=s.hours or "",
        map_location=s.map_location or "",
        map_embed_url=s.map_embed_url or "",
        background_image=s.background_image or "",
    )


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    """Lấy thông tin liên hệ (công khai)."""
    return _to_out(_get_settings(db))


@router.put("", response_model=SettingsOut)
def update_settings(
    body: SettingsUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Cập nhật thông tin liên hệ (chỉ admin)."""
    settings = _get_settings(db)
    updates = body.model_dump(exclude_unset=True)

    # Chỉ cho phép URL http/https cho mã nhúng bản đồ
    if "map_embed_url" in updates:
        url = (updates.get("map_embed_url") or "").strip()
        if url and not url.lower().startswith(("http://", "https://")):
            raise HTTPException(
                status_code=400,
                detail="Mã nhúng bản đồ phải bắt đầu bằng http:// hoặc https://.",
            )
        updates["map_embed_url"] = url

    for field, value in updates.items():
        setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    return _to_out(settings)


@router.post("/background", response_model=SettingsOut)
def upload_background(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Upload ảnh nền phần tiêu đề (chỉ admin)."""
    settings = _get_settings(db)
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise HTTPException(
            status_code=400,
            detail="Định dạng ảnh không hợp lệ. Hỗ trợ: jpg, png, gif, webp.",
        )
    filename = f"bg_{uuid.uuid4().hex}{ext}"
    data = file.file.read()
    save_file(db, filename, data, file.content_type)

    settings.background_image = f"/uploads/{filename}"
    db.commit()
    db.refresh(settings)
    return _to_out(settings)