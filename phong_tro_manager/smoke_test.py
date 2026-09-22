"""Smoke test nhanh các tính năng mới (dùng DB tạm)."""
import os
import sys

TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smoke_test.db")
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
os.environ["DATABASE_URL"] = "sqlite:///" + TEST_DB.replace("\\", "/")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app, seed_data  # noqa: E402

seed_data()
client = TestClient(app)

passed = 0
failed = 0


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  OK {name}")
    else:
        failed += 1
        print(f"  FAIL {name} {extra}")


# 1. Rooms + lọc
r = client.get("/api/rooms")
check("GET /api/rooms", r.status_code == 200 and len(r.json()) >= 5, r.text[:200])
rooms = r.json()
first = rooms[0]

# Lọc điều hòa
ac_yes = [x for x in rooms if x.get("has_ac")]
ac_no = [x for x in rooms if not x.get("has_ac")]
check("Lọc điều hòa: có/không", bool(ac_yes) and bool(ac_no), f"yes={len(ac_yes)} no={len(ac_no)}")
check(
    "Phòng 101 có điều hòa",
    next((x for x in rooms if x["name"] == "Phòng 101"), {}).get("has_ac") is True,
)
check(
    "Phòng 202 không có điều hòa",
    next((x for x in rooms if x["name"] == "Phòng 202"), {}).get("has_ac") is False,
)

r = client.get("/api/rooms", params={"status": "available"})
check("Loc status=available", r.status_code == 200 and all(x["status"] == "available" for x in r.json()))

r = client.get("/api/rooms", params={"min_price": 2_300_000})
check("Loc min_price", r.status_code == 200 and all(x["price"] >= 2_300_000 for x in r.json()))

r = client.get("/api/rooms", params={"q": "101"})
check("Tim kiem q=101", r.status_code == 200 and all("101" in x["name"] for x in r.json()))

# 2. Đăng nhập
r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
check("Login admin", r.status_code == 200, r.text)
token = r.json()["access_token"]
role = r.json()["role"]
check("Login tra role", role == "admin", role)
H = {"Authorization": f"Bearer {token}"}
r = client.get("/api/auth/me", headers=H)
check("API tai khoan hien tai", r.status_code == 200 and r.json()["role"] == "admin", r.text)

# 3. Đổi mật khẩu (sai mật khẩu cũ)
r = client.post("/api/auth/change-password", headers=H, json={"old_password": "sai", "new_password": "abc12345"})
check("Doi mk sai mk cu bi chan", r.status_code == 400)

# 4. Settings có trường mới
r = client.get("/api/settings")
check("Settings co dien/nuoc/FB", r.status_code == 200 and "electricity_price" in r.json() and "facebook_url" in r.json())
s = r.json()
check("Don gia dien 3500", s["electricity_price"] == 3500, str(s.get("electricity_price")))
check("Settings co noi quy", r.status_code == 200 and bool((s.get("house_rules") or "").strip()), "thiếu house_rules")

r = client.put("/api/settings", headers=H, json={"house_rules": "1. Test quy\n2. Test hai"})
check("Lưu noi quy (admin)", r.status_code == 200 and r.json().get("house_rules") == "1. Test quy\n2. Test hai", r.text)
r = client.get("/api/settings")
check("Kiểm nội quy trong settings", r.status_code == 200 and r.json().get("house_rules", "").startswith("1. Test quy"), r.text)

r = client.get("/")
check("Trang chu co nut noi quy hien/an", r.status_code == 200 and 'id="rules-toggle"' in r.text, "thiếu rules-toggle")

r = client.get("/api/settings/backgrounds")
bgs = r.json().get("defaults", []) if r.status_code == 200 else []
check("DS anh nen mac dinh", r.status_code == 200 and len(bgs) >= 1, r.text)
check("Anh nen mac dinh phuc vu duoc", bgs and client.get(bgs[0]).status_code == 200, str(bgs[:2]))

# 5. Khách trọ: tạo -> sửa
r = client.post("/api/tenants", headers=H, json={"full_name": "Nguyen Van A", "phone": "0900000001", "room_id": first["id"], "status": "active"})
check("Tao khach tro", r.status_code == 201, r.text)
tenant_id = r.json()["id"]
check("Khach tro co ten phong", r.json().get("room_name") == first["name"], r.text)

r = client.get("/api/tenants", headers=H, params={"q": "0900000001"})
check("Tim khach theo SDT", r.status_code == 200 and len(r.json()) == 1)

r = client.put(f"/api/tenants/{tenant_id}", headers=H, json={"note": "Khach ky hop dong 1 nam"})
check("Sua khach tro", r.status_code == 200 and r.json()["note"] == "Khach ky hop dong 1 nam", r.text)
# 6. Điện nước: tạo hóa đơn -> tự tính tiền
r = client.post("/api/tenants/bills", headers=H, json={
    "tenant_id": tenant_id, "month": "2026-09",
    "elec_old": 100, "elec_new": 200, "water_old": 5, "water_new": 15, "other_fee": 10000,
})
check("Tao hoa don dien nuoc", r.status_code == 201, r.text)
b = r.json()
check("Tinh tien dien", b["elec_amount"] == 350000, str(b["elec_amount"]))
check("Tinh tien nuoc", b["water_amount"] == 200000, str(b["water_amount"]))
check("Tinh tong", b["total"] == 560000, str(b["total"]))
bill_id = b["id"]

r = client.put(f"/api/tenants/bills/{bill_id}/paid", headers=H, json={"paid": True})
check("Danh dau da thu", r.status_code == 200 and r.json()["paid"] is True)

r = client.post("/api/tenants/bills", headers=H, json={"tenant_id": tenant_id, "month": "2026-09", "elec_old": 300, "elec_new": 100})
check("Chan chi so moi < cu", r.status_code == 400, r.text)

# 7. Hợp đồng
r = client.post("/api/tenants/contracts", headers=H, json={
    "tenant_id": tenant_id, "start_date": "2026-09-01", "end_date": "2027-08-31", "deposit": 3000000, "monthly_rent": 2500000,
})
check("Tao hop dong", r.status_code == 201, r.text)
contract_id = r.json()["id"]
check("Hop dong co ten khach", r.json().get("tenant_name") == "Nguyen Van A", r.text)

r = client.get("/api/tenants/contracts", headers=H)
check("Danh sach hop dong", r.status_code == 200 and len(r.json()) == 1)

# 8. Liên hệ / đặt phòng
r = client.post("/api/contact", json={"name": "Khach X", "phone": "0988888888", "room_id": first["id"], "message": "Muon xem phong"})
check("Khach gui tin lien he", r.status_code == 201, r.text)
msg_id = r.json()["id"]
check("Tin co ten phong", r.json().get("room_name") == first["name"], r.text)

r = client.post("/api/contact", json={"name": "", "phone": ""})
check("Chan tin trong", r.status_code == 400)

r = client.get("/api/contact", headers=H)
check("Admin xem tin nhan", r.status_code == 200 and len(r.json()) == 1)

r = client.put(f"/api/contact/{msg_id}/read", headers=H)
check("Danh dau da doc", r.status_code == 200 and r.json()["is_read"] is True)
# 9. Phân quyền staff
r = client.post("/api/auth/admins", headers=H, json={"username": "nhanvien", "password": "123456", "role": "staff"})
check("Tao tai khoan staff", r.status_code == 201, r.text)

r = client.post("/api/auth/login", json={"username": "nhanvien", "password": "123456"})
staff_token = r.json()["access_token"]
SH = {"Authorization": f"Bearer {staff_token}"}

r = client.get("/api/auth/admins", headers=SH)
check("Staff khong xem duoc ds admin", r.status_code == 403)

r = client.put("/api/settings", headers=SH, json={"phone": "000"})
check("Staff khong doi duoc settings", r.status_code == 403)

r = client.delete(f"/api/rooms/{first['id']}", headers=SH)
check("Staff khong xoa duoc phong", r.status_code == 403)

r = client.delete(f"/api/tenants/{tenant_id}", headers=SH)
check("Staff khong xoa duoc khach tro", r.status_code == 403)

r = client.post("/api/tenants", headers=SH, json={"full_name": "NV them"})
check("Staff them duoc khach tro", r.status_code == 201, r.text)

# 10. Giới hạn upload ảnh
big_blob = b"\xff" * (9 * 1024 * 1024)
r = client.post(f"/api/rooms/{first['id']}/images", headers=H, files={"file": ("big.png", big_blob, "image/png")})
check("Chan anh > 8MB", r.status_code == 413, r.text)

r = client.post(f"/api/rooms/{first['id']}/images", headers=H, files={"file": ("a.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 100, "image/png")})
check("Upload anh nho OK", r.status_code == 201, r.text)

# 10b. Ảnh bìa (ảnh đại diện): đổi / kiểm tra / xóa
r = client.get(f"/api/rooms/{first['id']}")
detail = r.json()
seed_img = detail["images"][0]
check("Anh bia mac dinh la anh dau tien", seed_img.get("is_cover") is True, r.text)
check("Thumbnail theo anh bia", detail.get("thumbnail_url") == seed_img["url"], r.text)

r = client.post(f"/api/rooms/{first['id']}/images", headers=H, files={"file": ("b.png", b"\\x89PNG\\r\\n\\x1a\\n" + b"\\x00" * 100, "image/png")})
check("Upload anh thu 2", r.status_code == 201 and r.json().get("is_cover") is False, r.text)
img_b = r.json()

r = client.put(f"/api/rooms/{first['id']}/cover", headers=H, json={"image_id": img_b["id"]})
check("Dat anh bia la anh thu 2", r.status_code == 200 and r.json()["thumbnail_url"] == img_b["url"], r.text)
new_first = r.json()["images"][0]
check("Anh bia dung dau danh sach", new_first["id"] == img_b["id"] and new_first.get("is_cover") is True, r.text)

r = client.put(f"/api/rooms/{first['id']}/cover", headers=H, json={"image_id": 999999})
check("Cover anh khong ton tai bi chan", r.status_code == 404, r.text)

r = client.delete(f"/api/rooms/{first['id']}/images/{img_b['id']}", headers=H)
check("Xoa anh bia", r.status_code == 204, r.text)
r = client.get(f"/api/rooms/{first['id']}")
check("Anh bia chuyen sang anh con lai", r.json()["thumbnail_url"] == seed_img["url"] and r.json()["images"][0].get("is_cover") is True, r.text)
# 11. Xóa hết test data
r = client.delete(f"/api/tenants/{tenant_id}", headers=H)
check("Xoa khach tro (kem hoa don/hop dong)", r.status_code == 204, r.text)
r = client.get("/api/tenants/bills", headers=H)
check("Hoa don da xoa theo", r.status_code == 200 and len(r.json()) == 0)
r = client.delete(f"/api/contact/{msg_id}", headers=H)
check("Xoa tin nhan", r.status_code == 204)

print(f"\nKết quả: {passed} đạt / {failed} lỗi")
sys.exit(1 if failed else 0)