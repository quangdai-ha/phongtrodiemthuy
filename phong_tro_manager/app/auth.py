"""Xác thực: băm mật khẩu, tạo/kiểm tra JWT."""
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .database import get_db
from .models import Admin

SECRET_KEY = os.environ.get("ROOM_MANAGER_SECRET", "phong-tro-manager-secret-key-2024")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 12
PBKDF2_ITERATIONS = 100_000


def _digest(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    ).hex()


def hash_password(password: str) -> str:
    """Băm mật khẩu, trả về dạng 'salt$digest'."""
    salt = secrets.token_hex(16)
    return f"{salt}${_digest(password, salt)}"


def verify_password(password: str, stored: str) -> bool:
    """Kiểm tra mật khẩu với chuỗi đã băm."""
    if "$" not in stored:
        return False
    salt, digest = stored.split("$", 1)
    return secrets.compare_digest(_digest(password, salt), digest)


def create_token(username: str) -> str:
    """Tạo JWT cho admin."""
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_admin(
    request: Request, db: Session = Depends(get_db)
) -> Admin:
    """Dependency yêu cầu token admin hợp lệ."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Chưa đăng nhập.")
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập đã hết hạn.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ.")

    username = payload.get("sub")
    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin is None:
        raise HTTPException(status_code=401, detail="Tài khoản không tồn tại.")
    return admin