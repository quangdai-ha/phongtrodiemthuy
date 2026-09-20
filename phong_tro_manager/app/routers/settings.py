"""API thông tin liên hệ & bản đồ website."""
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..auth import require_admin_role
from ..database import get_db
from ..models import SiteSettings
from ..schemas import SettingsOut, SettingsUpdate
from ..storage import save_file

router = APIRouter(prefix="/api/settings", tags=["settings"])

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # Mỗi ảnh tối đa 8MB

# Thư mục chứa các ảnh nền mặc định (được cài sẵn cùng website)
DEFAULT_BG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", "images", "bg",
)
DEFAULT_BG_EXT = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif"}


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
        electricity_price=s.electricity_price if s.electricity_price is not None else 3500,
        water_price=s.water_price if s.water_price is not None else 20000,
        facebook_url=s.facebook_url or "",
        house_rules=s.house_rules or "",
    )


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    """Lấy thông tin liên hệ (công khai)."""
    return _to_out(_get_settings(db))


@router.put("", response_model=SettingsOut)
def update_settings(
    body: SettingsUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin_role),
):
    """Cập nhật thông tin liên hệ, đơn giá điện nước, mạng xã hội (chỉ role admin)."""
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

    # Kiểm tra link Facebook nếu có
    if "facebook_url" in updates:
        url = (updates.get("facebook_url") or "").strip()
        if url and not url.lower().startswith(("http://", "https://")):
            raise HTTPException(
                status_code=400,
                detail="Link Facebook phải bắt đầu bằng http:// hoặc https://.",
            )
        updates["facebook_url"] = url

    # Đơn giá điện nước phải dương
    for key in ("electricity_price", "water_price"):
        if updates.get(key) is not None and updates[key] < 0:
            raise HTTPException(status_code=400, detail="Đơn giá không được âm.")

    for field, value in updates.items():
        setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    return _to_out(settings)


@router.post("/background", response_model=SettingsOut)
def upload_background(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin=Depends(require_admin_role),
):
    """Upload ảnh nền phần tiêu đề (chỉ role admin)."""
    settings = _get_settings(db)
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
    filename = f"bg_{uuid.uuid4().hex}{ext}"
    save_file(db, filename, data, file.content_type)

    settings.background_image = f"/uploads/{filename}"
    db.commit()
    db.refresh(settings)
    return _to_out(settings)


@router.get("/backgrounds")
def list_default_backgrounds():
    """Danh sách ảnh nền mặc định có sẵn trong website (công khai)."""
    try:
        names = sorted(
            n for n in os.listdir(DEFAULT_BG_DIR)
            if os.path.splitext(n)[1].lower() in DEFAULT_BG_EXT
        )
    except FileNotFoundError:
        names = []
    return {"defaults": [f"/static/images/bg/{n}" for n in names]}