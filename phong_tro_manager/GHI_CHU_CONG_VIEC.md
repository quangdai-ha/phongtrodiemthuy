# 📒 GHI CHÚ CÔNG VIỆC — Xóm trọ Sự Bình

> File này **lưu trạng thái toàn bộ công việc** để phiên sau tiếp tục hoàn thiện.
> Cập nhật ngày: **21/09/2026** — đây là bản ghi hiện tại, phần "Việc cần làm tiếp" ở cuối là các hướng chưa làm.

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
- **Trang quản trị — không bị "văng" khỏi modal khi gõ nhanh**: Enter trong ô nhập (text/number/select) của modal **không tự submit form** (vô tình lưu + đóng modal ngay). Vẫn cho Enter xuống dòng trong textarea, Enter/Space trên nút bấm, và Ctrl/Cmd+Enter để lưu nhanh có chủ đích. Ngoài ra: khi token 401 (phiên hết hạn), trang đóng luôn modal đang mở ngoài đẩy về màn hinh đăng nhập (`closeAllModals()` trong `admin.js`).
- **Trang quản trị — modal KHÔNG tự đóng khi bấm/rê chuột ra ngoài cửa sổ**: bỏ hẳn cơ chế "click nền tối → đóng" ở cả 5 modal chỉnh sửa (phòng, cài đặt, khách trọ, hóa đơn, hợp đồng). Trước đây chỉ cần rê chuột chọn văn bản rồi thả ra ngoài khung (hoặc vô tình chạm ra ngoài trên điện thoại) là click phát trên overlay → modal đóng → **mất toàn bộ nội dung đang sửa** (đúng lỗi "văng khi sửa mô tả phòng"). Giờ đóng bằng nút ✕ / Hủy (ESC với khách trọ/hóa đơn/hợp đồng).

---

## 3. DỮ LIỆU THẬT ĐANG CÓ (rất quan trọng — đừng xóa)

DB đã có **dữ liệu thật của chủ** (không còn là dữ liệu mẫu):

- **7 phòng**: Phòng 1, Phòng 102, Phòng 103, Phòng 201, Phòng 202, Phòng 107, **Kiost_01**.
  - Trạng thái thật: **4 trống** (1, 103, 202, Kiost_01) · **3 đã ở** (102, 201, 107) · **0 bảo trì**.
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
4. ✅ **Đã làm:** lọc/tìm kiếm phòng theo tên, giá, diện tích, trạng thái trên trang khách.
5. ✅ **Đã làm:** liên hệ/đặt phòng qua form, gọi điện, Zalo, Facebook; admin xem/đọc/xóa tin.
6. ✅ **Đã làm:** quản lý khách trọ, điện nước (tự tính tiền), hợp đồng.
7. ✅ **Đã làm:** phân quyền `admin`/`staff`, quản lý tài khoản, đổi mật khẩu, giới hạn ảnh 8MB.
8. Deploy lên máy chủ (cài `uvicorn` worker, tắt `reload`, HTTPS).

---

## 6. Trạng thái kỹ thuật cuối phiên (25/08/2026)

- ✅ Python compile toàn bộ không lỗi.
- ✅ Tất cả API test qua (đăng nhập, CRUD phòng, upload ảnh, settings, upload/xóa ảnh nền, bảo mật URL).
- ✅ Trang chủ & admin hiển thị đúng tên "Xóm trọ Sự Bình".
- ✅ Dữ liệu thật nguyên vẹn.
- ✅ 39/39 smoke test tính năng mới đạt; Edge headless render đủ 6 phòng, bộ lọc và form liên hệ.

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
1. ✅ **`migrate_to_pg.py`** đã sửa UTF-8 và chuyển cả phòng, ảnh, cài đặt, tài khoản, khách trọ, hóa đơn, hợp đồng, tin nhắn.
2. ✅ **`HUONG_DAN_DEPLOY.md`** đã viết đầy (20/09/2026): cài Git → push GitHub → tạo PostgreSQL → chạy `migrate_to_pg.py` → deploy Web Service → kiểm tra → đổi mật khẩu admin → xử lý sự cố.
3. ✅ **`README.md`** đã cập nhật tính năng; hướng dẫn deploy chi tiết giờ ở `HUONG_DAN_DEPLOY.md` (file tách riêng).
4. **Sau khi deploy xong**: đổi mật khẩu admin mặc định `admin123`, đặt `ROOM_MANAGER_SECRET` ngẫu nhiên.
5. Tạm thời **chưa đưa dữ liệu** lên GitHub (`.gitignore` đã loại `data/*.db`, `uploads/*`).

### LƯU Ý QUAN TRỌNG khi tiếp tục
- ✅ **Git đã cài** (2.55.0.3, qua `winget install Git.Git`) và **repo đã khởi tạo** (`git init -b main`), commit đầu `6110d5b`. Giờ chỉ thiếu: tạo repo trống trên GitHub + `git remote add origin ... && git push -u origin main` (ди hướng trong `HUONG_DAN_DEPLOY.md`).
- `chay.bat` / `run.py` vẫn chạy local bằng SQLite bình thường. Muốn test nhanh bằng API ở máy, xoá DB cũ để `create_all` tạo đủ bảng `stored_files` mới, hoặc gọi `seed_data()`.
- Không xoá folder `data/` & `uploads/` (chứa dữ liệu thật đang dùng để migrate).
---

## 8. PHIÊN 20/09/2026 — TÙY BIẾN TRANG KHÁCH & TIẾNG VIỆT (ĐÃ LÀM XONG)

### Các việc đã hoàn thành trong phiên này

| # | Việc | Chi tiết |
|---|------|----------|
| 1 | **Thay Google Maps bằng link nhúng cố định** | Đã lưu iframe embed (`https://www.google.com/maps/embed?pb=...`) vào `map_embed_url` trong `site_settings`. Trang khách nhận biết link embed (hàm `isEmbeddableMapUrl`) và nhúng iframe trực tiếp. Link chia sẻ `maps.app.goo.gl` thường chỉ hiển thị bản đồ theo `map_location`. |
| 2 | **Nút lọc Có điều hòa / Không có điều hòa** | Trang khách có bar lọc chip: `Tất cả phòng` / `Có điều hòa` / `Không có điều hòa` (id `filter-chips`). Backend thêm field `has_ac` vào `RoomListItem` (schemas + `app/routers/rooms.py`). Regex `Đ\w*\s*hòa` (không phân biệt hoa thường) nhận diện "Điều hòa" kể cả viết sai dấu. **Lưu ý:** tên thiết bị phải chứa "điều hòa" / "Điều hòa" mới được coi là có AC. |
| 3 | **Nội quy hiện/ẩn bớt** | Trang khách mặc định chỉ hiện **3 điểm đầu** của Nội quy; nếu nhiều hơn thì có nút `📖 Xem toàn bộ nội quy (n) ▼` / `🙈 Thu gọn nội quy ▲` (id `rules-toggle`, phần ẩn `#rules-rest`). Nếu nội quy ≤ 3 điểm thì không hiện nút. |
| 4 | **Đổi toàn bộ nội dung sang tiếng Việt đúng** | Sửa các câu lẫn tiếng Ba Lan: `Không znaleziono...` → "Không có phòng phù hợp với bộ lọc này.", `Chưa có phòng nào do wyświetlenia` → "Chưa có phòng nào để hiển thị.", nội quy mặc định + nội quy trong DB viết lại tiếng Việt, comment/log trong code chuyển sang tiếng Việt. |
| 5 | **Tiếng Việt có dấu cho chip lọc AC** | `Tất phòng` → `Tất cả phòng`, `Có Điêu hòa` → `Có điều hòa`, `Không có Điêu hòa` → `Không có điều hòa` (index.html + comment CSS/JS + smoke_test). |
| 6 | **Responsive (tự co theo màn hình)** | Thêm `@media` các mức **960px / 768px / 640px / 480px**: filter dồn cột, modal trượt từ dưới lên, header gọn lại, input 16px (tránh zoom iOS), lưới phòng & chips thành full-width, thống kê 2×2, nút gọi riêng full-width. Thêm `touch-action: manipulation`, tắt hiệu ứng hover trên touch, `overflow-x` chặn tràn ngang. |
| 7 | **Đổi ảnh nền header: upload HOẶC ảnh mặc định** | Panel admin → ⚙️ Cài đặt → "Ảnh nền trang chủ" giờ có thêm mục "Hoặc chọn ảnh mặc định": lưới **6 ảnh SVG** (`app/static/images/bg/bg-1..6.svg`), click chọn → bấm Lưu. Endpoint mới `GET /api/settings/backgrounds` (public). Các ảnh mặc định nằm ở `app/static/images/bg/`. Upload cũ (post 8MB) vẫn giữ. |
| 8 | **Chống cache CSS/JS (cache-busting)** | `index.html` + `admin.html` nhúng asset kèm phiên bản. **Trạng thái hiện:** `style.css?v=20260921`, `main.js?v=20260921` (index.html), `admin.js?v=20260921` (admin.html). **Quan trọng:** mỗi lần sửa CSS/JS phải **tăng số `v=`** (VD `v=20260921`) để mọi máy khách nhận bản mới. |
| 9 | **Bấm thẻ thống kê để lọc phòng (trang khách)** | 4 thẻ thống kê (Tổng số phòng / Phòng trống / Phòng đã ở / Đang bảo trì) giờ **bấm được**. Bấm thẻ nào thì danh sách phòng lọc theo đúng trạng thái đó (`/api/rooms?status=...`), thẻ đang chọn được tô sáng + có viền màu riêng, trang tự cuộn xuống mục "Danh sách phòng". Đồng bộ 2 chiều với dropdown lọc trạng thái: chọn dropdown cũng cập nhật highlight thẻ, bấm ✕ Xóa lọc trả về "Tổng số phòng". Thẻ có `data-status` (tổng = `""`), hỗ trợ phím Enter/Space, tăng cache-busting lên `v=20260921`. |
| 10 | **Sửa lỗi "văng khỏi màn hinh cài đặt khi nhập nhanh" (trang quản trị)** | Người nhập nhanh thông tin (đơn giá, điện thoại, địa chỉ...) thoi bấm **Enter vô tình** → trình duyệt tự submit form → handler lưu + đóng modal ngay → "bị văng". Xử: listener `keydown` capture tầ document chặn (`preventDefault`) Enter trong input/select nằm trong `.modal` (trừ textarea & nút); **Ctrl/Cmd+Enter vẫn submit** (lưu nhanh). Ngoài ra: `api()` khi **401** gọi `closeAllModals()` (đóng settings/form/tenant/bill/contract-modal) trước `showLogin()`. File sửa: `app/static/js/admin.js`, cache-busting admin.html → `admin.js?v=20260921`. |
| 11 | **Không đóng modal khi bấm/rê chuột ra ngoài cửa sổ (sửa lỗi "văng khi sửa phần mô tả phòng")** | Thao tác "nhấn giữ + rê chuột chọn văn bản rồi thả RA NGOÀI khung popup" (hoặc vô tình chạm nền tối trên điện thoại) phát một `click` trên `.modal-overlay` → handler cũ `if (e.target === overlay) close...` đóng modal ngay → mất toàn bộ dữ liệu đang sửa (VD đang gõ mô tả phòng thì "bị văng"). Xử: xóa handler đóng-khi-bấm-nền-tối ở cả 5 modal (form/settings/tenant/bill/contract-modal) — chỉ đóng bằng nút ✕ / Hủy (riêng tenant/bill/contract vẫn có ESC). File sửa: `app/static/js/admin.js`, cache-busting admin.html → `admin.js?v=20260922`. |

### Trạng thái kỹ thuật cuối phiên
- ✅ **Smoke test: 48/48 đạt / 0 lỗi** (`python -W ignore smoke_test.py`).
- ✅ Trang khách & admin render đúng; các mẫu ảnh nền serve được (`200 image/svg+xml`).
- ✅ Dữ li thật (7 phòng, ảnh, settings, Nội quy tiếng Việt) nguyên vẹn.
- ✅ Thẻ thống kê trang khách kiểm chứng: API lọc trạng thái đúng (7 tổng / 4 trống / 3 đã ở / 0 bảo trì), JS/CSS `v=20260921` phục vụ đúng.
- ✅ Sửa "văng khỏi modal khi nhập nhanh" (admin): balance JS 0/0/0, `admin.js?v=20260921` phục vụ HTTP 200, thẻ script admin.html đã tăng `v=`.
- ✅ Sửa "văng khi sửa mô tả phòng / bấm nền tối": xóa 5 handler đóng-khi-bấm-overlay (form/settings/tenant/bill/contract), `admin.js?v=20260922` phục vụ HTTP 200.

### QUAN TRỌNG — vấn đề server & cách khởi động
- ⚠️ **Auto-reload (`run.py`) đã bị lỗi ở máy này**: uvicorn reloader tạo **"zombie" process** giữ port 8000 và **không nạp code mới** (dính bản cũ). Đã phát hiện 3 process python cùng lúc.
- **Cách khởi động ổn định (đang dùng):** chạy thẳng uvicorn KHÔNG reload:
  ```
  cd C:\Users\Admin\.cline\data\workspaces\chat\phong_tro_manager
  $env:PYTHONIOENCODING='utf-8'
  Start-Process .\.venv\Scripts\python.exe -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000') -WindowStyle Hidden -RedirectStandardOutput s_out.log -RedirectStandardError s_err.log
  ```
- Nếu port 8000 bị chiếm: tìm `Get-NetTCPConnection -LocalPort 8000 -State Listen` rồi `taskkill /PID <pid> /F`.
- **Sau khi sửa code phải khởi động lại server** (không có auto-reload).
- ✅ Node.js KHÔNG cài trên máy → không chạy được `node --check` để kiểm tra JS.

### MẸO XỬ LÝ SỰ CỐ (đã gặp trong phiên này)
- **Triệu chứng:** mở web bằng máy tính nhưng vẫn thấy **giao diện kiểu điện thoại / giao diện cũ**.
  - **Nguyên nhân thật:** trình duyệt giữ **cache CSS/JS cũ** (không phải lỗi code — đã kiểm tra: CSS trên đĩa trùng khớp CSS máy chủ phục vụ, 24.031 bytes; box model cho thấy cửa sổ rộng 1687.5px > 960px nên lẽ ra phải là giao diện desktop).
  - **Cách xử lý:** nhấn **Ctrl + F5** (hard refresh) → hết ngay. Nay đã thêm `?v=` chống cache nên sẽ không tái diễn.
  - **Kiểm tra nhanh khi nghi ngờ:** F12 → Console gõ `innerWidth` — nếu < 768 thì đúng là cửa sổ hẹp (zoom to / chưa phóng to); nếu ≥ 960 mà vẫn kiểu mobile thì 99% là cache → Ctrl+F5.
  - **Cũng cần loại trừ:** DevTools đang bật **chế độ thiết bị** (📱 / Ctrl+Shift+M) hoặc bị **zoom trang** (Ctrl+0 để về 100%).

### Việc muốn làm tiếp (chưa làm)
1. Deploy (xem mục 7): tạo repo GitHub + `git remote add origin ... && git push -u origin main` → tạo PostgreSQL → `migrate_to_pg.py` → Render.
2. Sau deploy: đổi mật khẩu admin khỏi `admin123`, đặt `ROOM_MANAGER_SECRET` ngẫu nhiên.
3. (Tùy chọn) Thêm ảnh nền mặc định kiểu ảnh thật (JPG) nếu chủ nhà gửi ảnh riêng.
4. (Tùy chọn) Thêm phòng mẫu với trạng thái `maintenance` để kiểm chứng giao diện thẻ "Đang bảo trì" (hiện 0 phòng bảo trì).
5. (Tùy chọn) Áp tính thẻ thống kê lọc phòng (tương thích trang khách) đến trang quản trị (`app/static/admin.html` + `admin.js`).
