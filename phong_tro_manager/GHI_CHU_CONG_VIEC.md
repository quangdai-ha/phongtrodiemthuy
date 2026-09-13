# 📒 GHI CHÚ CÔNG VIỆC — Xóm trọ Sự Bình

> File này **lưu trạng thái toàn bộ công việc** để phiên sau tiếp tục hoàn thiện.
> Cập nhật ngày: **25/08/2026** — đây là bản ghi hiện tại, phần "Việc cần làm tiếp" ở cuối là các hướng chưa làm.

---

## 1. Dự án là gì & cách chạy

**Trang web quản lý phòng trọ "Xóm trọ Sự Bình"** — backend FastAPI + SQLite, frontend HTML/CSS/JS thuần.

### Chạy ứng dụng

- **Cách dễ nhất:** nhấp đúp file **`chay.bat`** (tự dùng Python trong `.venv`, tự mở trình duyệt).
- **Thủ công:**
  ```
  cd C:\Users\Admin\.cline\data\workspaces\chat\phong_tro_manager
  .\.venv\Scripts\python run.py
  ```
- **Lưu ý quan trọng:** Đừng chạy `python run.py` (bằng Python hệ thống) — Python hệ thống **thiếu thư viện** (fastapi/uvicorn). Phải dùng Python trong `.venv`. Nếu chạy nhầm sẽ in thông báo hướng dẫn.

### Các đường dẫn

| Gì                                       | URL                           |
| ---------------------------------------- | ----------------------------- |
| Trang khách (xem phòng, liên hệ, bản đồ) | `http://127.0.0.1:8000`       |
| Trang quản trị                           | `http://127.0.0.1:8000/admin` |
| Tài liệu API (Swagger)                   | `http://127.0.0.1:8000/docs`  |

### Tài khoản đăng nhập

- **admin** / **admin123** (nên đổi mật khẩu + JWT secret trước khi dùng thật)

---

## 2. Những gì ĐÃ HOÀN THÀNH

### Backend (`app/`)

- **`database.py`** — SQLite engine/session (DB tại `data/phongtro.db`, ảnh tải lên `uploads/`).
- **`models.py`** — bảng `Room`, `RoomImage`, `Admin`, `SiteSettings`.
  - `Room`: tên, giá, diện tích, mô tả, thiết bị(JSON), trạng thái, hình ảnh.
  - `SiteSettings`: địa chỉ, điện thoại, giờ mở cửa, vị trí bản đồ, mã nhúng, **ảnh nền trang chủ**.
- **`auth.py`** — băm mật khẩu PBKDF2 + JWT (secret qua biến môi trường `ROOM_MANAGER_SECRET`).
- **`routers/auth.py`** — `POST /api/auth/login` (trả JWT).
- **`routers/rooms.py`** — CRUD phòng + upload/xóa ảnh.
- **`routers/settings.py`** — `GET/PUT /api/settings`, `POST /api/settings/background` (upload ảnh nền).
- **`main.py`** — seed dữ liệu mẫu lần đầu, migration tự thêm cột mới (không mất dữ liệu cũ).

### Giao diện (`app/static/`)

- **`index.html` + `main.js`** — trang khách: thống kê trống/ở/bảo trì, danh sách phòng + giá, modal chi tiết phòng, mục **Liên hệ & Bản đồ** (địa chỉ, điện thoại, giờ mở, Google Maps), **ảnh nền header**.
- **`admin.html` + `admin.js`** — đăng nhập, thêm/sửa/xóa phòng, đổi trạng thái, upload/xóa ảnh, **⚙️ Cài đặt liên hệ & bản đồ**, đổi ảnh nền trang chủ.
- **`css/style.css`** — toàn bộ phong cách, responsive.

### Đã xử lý / cải thiện quan trọng

- Sửa lỗi **encoding tiếng Việt** trên Windows (cp1252) khi in log — `main.py`, `run.py`.
- `run.py` có thông báo lỗi thân thiện nếu thiếu thư viện; file **`chay.bat`** nhấp đúp là chạy.
- **Bản đồ Google Maps**: nếu admin dán link chia sẻ `maps.app.goo.gl/...` (không nhúng được iframe), trang tự dùng `map_location` để hiển thị bản đồ; nút "Mở Google Maps" vẫn dẫn đúng.
- **Bảo mật**: backend chặn `map_embed_url` không phải `http(s)://`.

---

## 3. DỮ LIỆU THẬT ĐANG CÓ (rất quan trọng — đừng xóa)

DB đã có **dữ liệu thật của chủ** (không còn là dữ liệu mẫu):

- **6 phòng**: Phòng 1, Phòng 102, Phòng 103, Phòng 201, Phòng 202, **Kiost_01**.
- **6 hình ảnh** phòng (JPG/PNG/WEBP) trong `uploads/`.
- **Thông tin liên hệ thật** (trong `site_settings`):
  - Địa chỉ: TDP Yên Mễ, phường Hồng Tiến, TP Phổ Yên, tỉnh Thái Nguyên
  - Điện thoại: `0896 93 2222`
  - Giờ mở: `Mở cửa: 6:00 – 23:00 hằng ngày`
  - Bản đồ: link chia sẻ `https://maps.app.goo.gl/pR7zoGti7K2D2yzY8` (hiện bản đồ theo địa chỉ Yên Mễ...)
  - Ảnh nền trang chủ: chưa đặt (trống)

> ⚠️ Migration `_migrate()` trong `main.py` chỉ **thêm cột mới**, không xóa/sửa dữ liệu cũ — an toàn.

---

## 4. CÁCH VẬN HÀNH / MẸO

- Server đang chạy `reload=True` (xem `run.py`), đổi code tải lại tự động — **không cần khởi động lại** khi sửa file.
- Muốn dừng server: đóng cửa sổ "PhongTro - Server" (nếu dùng `chay.bat`) hoặc Ctrl+C.
- Upload ảnh phòng / ảnh nền: phải đăng nhập admin.

---

## 5. VIỆC CÓ THỂ LÀM TIẾP (chưa làm — hướng phát triển)

Ưu tiên gợi ý (tùy nhu cầu):

1. **Đặt ảnh nền trang chủ** cho "Xóm trọ Sự Bình" (admin → ⚙️ Cài đặt → mục Ảnh nền).
2. **Đặt mật khẩu mới** cho admin (hiện đang là mặc định `admin123`), thêm tài khoản admin khác, hoặc trang đổi mật khẩu.
3. **Đổi secret** JWT bằng biến môi trường `ROOM_MANAGER_SECRET`.
4. Thêm **lọc/tìm kiếm** phòng theo giá, diện tích, trạng thái trên trang khách.
5. Thêm **liên hệ/đặt phòng** qua form (gửi tin nhắn, Zalo, Facebook).
6. Chức năng **quản lý khách trọ/điện nước/hợp đồng**.
7. Thêm xác thực **phân quyền chi tiết**, giới hạn upload kích thước ảnh.
8. Deploy lên máy chủ (cài `uvicorn` worker, tắt `reload`, HTTPS).

---

## 6. Trạng thái kỹ thuật cuối phiên (25/08/2026)

- ✅ Python compile toàn bộ không lỗi.
- ✅ Tất cả API test qua (đăng nhập, CRUD phòng, upload ảnh, settings, upload/xóa ảnh nền, bảo mật URL).
- ✅ Trang chủ & admin hiển thị đúng tên "Xóm trọ Sự Bình".
- ✅ Dữ liệu thật nguyên vẹn.

---

## 7. TIẾN ĐỘ DEPLOY LÊN INTERNET (đang làm dở — 27/08/2026)

> Bạn muốn **deploy website thật lên internet** (hướng đã chọn: **chuyển sang
> PostgreSQL** để dữ liệu bền, dự kiến dùng Render/Railway).

### ĐÃ LÀM
- **`app/database.py`** — tự đọc `DATABASE_URL` (Postgres khi deploy) hoặc quay lại SQLite file ở máy nhà. Tự chuẩn hoá `postgres://` → `postgresql://`.
- **`app/models.py`** — thêm bảng `StoredFile` (lưu nội dung ảnh dạng bytes trong DB) để ảnh bền trên hosting (ổ đĩa free tier là tạm thời).
- **`app/storage.py`** (mới) — helper `save_file` / `get_file` / `delete_file` đọc-ghi ảnh trong DB, kèm **fallback đọc file đĩa cũ** cho các ảnh chưa migrate; tự suy `content_type` từ đuôi file.
- **`app/main.py`** — import `storage`; seed SVG lưu vào `StoredFile`; thay mount `/uploads` tĩnh bằng route đọc ảnh từ DB (`GET /uploads/{filename}`).
- **`app/routers/rooms.py` & `settings.py`** — upload/xóa ảnh phòng & ảnh nền giờ lưu vào DB; bỏ đi code ghi file đĩa cũ.
- **`requirements.txt`** — thêm `psycopg2-binary`.
- **`Procfile`** (mới) + **`render.yaml`** (mới) — cấu hình Blueprint deploy lên Render (free PostgreSQL + Web Service).
- **`migrate_to_pg.py`** (mới) — di chuyển toàn bộ dữ liệu thật hiện có (admin, rooms, room_images, site_settings + ảnh từ đĩa) sang PostgreSQL đích.

### ĐÃ KIỂM TRA (smoke test bằng TestClient)
- ✅ Compile toàn bộ không lỗi.
- ✅ `GET /api/rooms` (200, 6 phòng), `/stats`, `/api/settings`.
- ✅ `GET /uploads/...` đọc ảnh cũ từ đĩa (fallback) OK.
- ✅ `POST /api/auth/login` (200), upload ảnh mới (201, lưu vào DB), `GET /uploads/<mới>` đọc từ DB (len đúng), `DELETE` ảnh (204).

### CÒN DỞ / VIỆC TIẾP TỤC (hôm sau)
1. **`migrate_to_pg.py`** — còn thiếu đoạn `sys.stdout.reconfigure(encoding="utf-8")` ở đầu file để in tiếng Việt chuẩn trên Windows (đã bị lỗi cp1252 khi test; hiện file **chưa thêm đoạn này** — cần bổ sung rồi test lại).
2. Viết **`HUONG_DAN_DEPLOY.md`** hướng dẫn từng bước: tạo tài khoản GitHub/Render, push code, tạo DB PostgreSQL, chạy `migrate_to_pg.py`, cấu hình env (`DATABASE_URL`, `ROOM_MANAGER_SECRET`), deploy, đổi mật khẩu admin.
3. Cập nhật **`README.md`** (mô tả tính năng PostgreSQL/DB-lưu-ảnh, hướng deploy).
4. **Sau khi deploy xong**: đổi mật khẩu admin mặc định `admin123`, đặt `ROOM_MANAGER_SECRET` ngẫu nhiên.
5. Tạm thời **chưa đưa dữ liệu** lên GitHub (`.gitignore` đã loại `data/*.db`, `uploads/*`).

### LƯU Ý QUAN TRỌNG khi tiếp tục
- Thư mục đang **chưa có git** → chưa thể push. Cần cài đặt Git (vd dùng `winget install Git.Git`) hoặc Azure khi tiếp nối phiên sau.
- `chay.bat` / `run.py` vẫn chạy local bằng SQLite bình thường. Muốn test nhanh bằng API ở máy, xoá DB cũ để `create_all` tạo đủ bảng `stored_files` mới, hoặc gọi `seed_data()`.
- Không xoá folder `data/` & `uploads/` (chứa dữ liệu thật đang dùng để migrate).
