"""Khởi chạy ứng dụng Quản lý phòng trọ.

Cách chạy đúng:
    venv/Scripts/python run.py        (nên dùng Python trong .venv)
hoặc nhấp đúp file chay.bat

Sau đó mở trình duyệt tại http://127.0.0.1:8000
"""
import os
import sys

# Đảm bảo in tiếng Việt đúng trên Windows (kể cả khi redirect ra file)
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def main():
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


def _importable(name: str) -> bool:
    """Kiểm tra module có import được hay không."""
    try:
        __import__(name)
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    # Kiểm tra nhanh thư viện để báo lỗi dễ hiểu thay vì traceback dài
    missing = [m for m in ("fastapi", "uvicorn", "sqlalchemy", "jwt") if not _importable(m)]
    if missing:
        print("=" * 60)
        print("LỖI: Thiếu thư viện:", ", ".join(missing))
        print("Bạn đang dùng Python:", sys.executable)
        print()
        print("Cách sửa (chọn 1):")
        print('  1) Dùng Python trong .venv:  .\\.venv\\Scripts\\python run.py')
        print("  2) Hoặc nhấp đúp file:        chay.bat")
        print("  3) Hoặc cài thư viện vào Python hiện tại:")
        print("     pip install -r requirements.txt")
        print("=" * 60)
        sys.exit(1)
    main()