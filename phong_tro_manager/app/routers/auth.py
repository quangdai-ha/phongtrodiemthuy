"""API đăng nhập & quản lý tài khoản quản trị."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import (
    create_token,
    get_current_admin,
    hash_password,
    require_admin_role,
    verify_password,
)
from ..database import get_db
from ..models import ROLE_CHOICES, Admin
from ..schemas import AdminCreate, AdminOut, ChangePasswordRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str = "staff"


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
        role=admin.role,
    )


@router.post("/init", include_in_schema=False)
def init_admin(db: Session = Depends(get_db)):
    """(Chỉ dùng khi seed) Tạo tài khoản admin đầu tiên nếu chưa có."""
    if db.query(Admin).count() == 0:
        db.add(Admin(username="admin", password_hash=hash_password("admin123"), role="admin"))
        db.commit()
    return {"ok": True}


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Đổi mật khẩu của chính tài khoản đang đăng nhập."""
    if not verify_password(body.old_password, admin.password_hash):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng.")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 6 ký tự.")
    admin.password_hash = hash_password(body.new_password)
    db.commit()
    return {"ok": True}


@router.get("/me", response_model=AdminOut)
def current_account(admin=Depends(get_current_admin)):
    """Thông tin tài khoản hiện tại để frontend đồng bộ vai trò."""
    return _to_admin_out(admin)


# ---------------------------------------------------------------------------
# Quản lý tài khoản (chỉ role admin)
# ---------------------------------------------------------------------------

def _to_admin_out(a: Admin) -> AdminOut:
    return AdminOut(id=a.id, username=a.username, role=a.role or "staff")


@router.get("/admins", response_model=list[AdminOut])
def list_admins(
    db: Session = Depends(get_db),
    admin=Depends(require_admin_role),
):
    """Danh sách tài khoản quản trị (chỉ admin)."""
    return [_to_admin_out(a) for a in db.query(Admin).order_by(Admin.id).all()]


@router.post("/admins", response_model=AdminOut, status_code=201)
def create_admin(
    body: AdminCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin_role),
):
    """Tạo tài khoản quản trị mới (chỉ admin)."""
    username = body.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Vui lòng nhập tên đăng nhập.")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 6 ký tự.")
    if body.role not in ROLE_CHOICES:
        raise HTTPException(status_code=400, detail="Vai trò không hợp lệ.")
    if db.query(Admin).filter(Admin.username == username).first():
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại.")
    new_admin = Admin(username=username, password_hash=hash_password(body.password), role=body.role)
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return _to_admin_out(new_admin)


@router.put("/admins/{admin_id}/role", response_model=AdminOut)
def set_admin_role(
    admin_id: int,
    body: dict,
    db: Session = Depends(get_db),
    admin=Depends(require_admin_role),
):
    """Đổi vai trò (admin/staff) của tài khoản khác (chỉ admin)."""
    role = (body.get("role") or "").strip()
    if role not in ROLE_CHOICES:
        raise HTTPException(status_code=400, detail="Vai trò không hợp lệ.")
    target = db.query(Admin).filter(Admin.id == admin_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản.")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="Không thể thay đổi vai trò của chính mình.")
    target.role = role
    db.commit()
    db.refresh(target)
    return _to_admin_out(target)


@router.delete("/admins/{admin_id}", status_code=204)
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin_role),
):
    """Xóa tài khoản quản trị (chỉ admin, không xóa chính mình / tài khoản cuối cùng)."""
    target = db.query(Admin).filter(Admin.id == admin_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản.")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="Không thể xóa tài khoản của chính mình.")
    admins = db.query(Admin).all()
    if len(admins) <= 1:
        raise HTTPException(status_code=400, detail="Cần ít nhất một tài khoản quản trị.")
    if target.role == "admin" and sum(1 for a in admins if a.role == "admin") <= 1:
        raise HTTPException(status_code=400, detail="Cần ít nhất một tài khoản role admin.")
    db.delete(target)
    db.commit()