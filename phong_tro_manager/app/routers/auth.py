"""API đăng nhập quản trị viên."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import create_token, verify_password
from ..database import get_db
from ..models import Admin
from ..auth import create_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Đăng nhập, trả về JWT nếu đúng tài khoản."""
    admin = db.query(Admin).filter(Admin.username == body.username).first()
    if admin is None or not verify_password(body.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng.",
        )
    return TokenResponse(
        access_token=create_token(admin.username),
        username=admin.username,
    )


@router.post("/init", include_in_schema=False)
def init_admin(db: Session = Depends(get_db)):
    """(Chỉ dùng khi seed) Tạo tài khoản admin đầu tiên nếu chưa có."""
    if db.query(Admin).count() == 0:
        db.add(Admin(username="admin", password_hash=hash_password("admin123")))
        db.commit()
    return {"ok": True}