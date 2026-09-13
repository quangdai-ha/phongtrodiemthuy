"""Lưu trữ file (ảnh) trong database để dữ liệu bền khi deploy.

Trên hosting free tier (Render/Railway) ổ đĩa là tạm thời, nên ảnh được
lưu dạng bytes ngay trong bảng `stored_files`. Chép ảnh đĩa cũ nếu có để
không vỡ khi chuyển dữ liệu.
"""
import os

from sqlalchemy.orm import Session

from .models import StoredFile

# Suy content-type từ đuôi file nếu chưa lưu sẵn
_MIME = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def _mime(filename: str, fallback: str | None) -> str:
    ct = fallback
    if not ct or ct == "application/octet-stream":
        ct = _MIME.get(os.path.splitext(filename or "")[1].lower())
    return ct or "application/octet-stream"


def _legacy_dir() -> str:
    from .database import UPLOAD_DIR

    return UPLOAD_DIR


def save_file(
    db: Session,
    filename: str,
    data: bytes,
    content_type: str = "application/octet-stream",
) -> StoredFile:
    """Lưu nội dung một ảnh vào DB."""
    sf = db.query(StoredFile).filter(StoredFile.filename == filename).first()
    if sf is None:
        sf = StoredFile(filename=filename)
    sf.data = data
    sf.content_type = content_type or "application/octet-stream"
    db.add(sf)
    return sf


def delete_file(db: Session, filename: str) -> None:
    """Xóa ảnh khỏi DB; đồng thời bỏ file đĩa cũ (nếu có ở máy nhà)."""
    db.query(StoredFile).filter(StoredFile.filename == filename).delete()
    path = os.path.join(_legacy_dir(), filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def get_file(db: Session, filename: str) -> tuple[bytes | None, str | None]:
    """Trả về (data, content_type) của ảnh; fallback qua file đĩa cũ."""
    sf = db.query(StoredFile).filter(StoredFile.filename == filename).first()
    if sf is not None and sf.data:
        return sf.data, _mime(filename, sf.content_type)

    path = os.path.join(_legacy_dir(), filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read(), _mime(filename, None)

    return None, None