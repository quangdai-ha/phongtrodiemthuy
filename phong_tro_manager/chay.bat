@echo off
chcp 65001 >nul
title Quan Ly Phong Tro
cd /d "%~dp0"

rem Chon Python co cai san thu vien (u tien .venv)
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

echo.
echo ============================================
echo    QUAN LY PHONG TRO - Dang khoi dong...
echo ============================================
echo.
echo   Trang khach:   http://127.0.0.1:8000
echo   Trang quan tri: http://127.0.0.1:8000/admin
echo   Tai khoan:     admin / admin123
echo.
echo   Muon dung may chu: dong cua so "PhongTro - Server"
echo.

rem Mo may chu trong cua so rieng
start "PhongTro - Server" "%PY%" run.py

rem Doi may chu khoi dong roi mo trinh duyet
timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:8000"

echo Da mo trinh duyet. Neu trang chua tai du lieu, hay nhan Ctrl+R (lam moi).
echo.
pause