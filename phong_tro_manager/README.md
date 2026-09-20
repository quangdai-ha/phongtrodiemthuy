# 🏠 Xóm trọ Sự Bình

Trang web quản lý phòng trọ được xây bằng **FastAPI + SQLite + HTML/CSS/JS thuần**.

## Tính năng

### Trang công khai (`/`)
- Hiển thị thống kê: tổng phòng, phòng **trống**, phòng **đã ở**, phòng bảo trì.
- Lưới danh sách phòng với **giá** và **trạng thái**.
- Bấm vào phòng để xem chi tiết: mô tả, diện tích, trang thiết bị, hình ảnh.
- Tìm kiếm/lọc phòng theo tên, trạng thái, mức giá và diện tích.
- Mục **Liên hệ & Bản đồ**: địa chỉ, số điện thoại, giờ mở/đóng cửa và bản đồ Google Maps nhúng.
- Gửi yêu cầu liên hệ/đặt phòng; gọi điện, mở Zalo và Facebook nhanh.

### Trang quản trị (`/admin`)
- Đăng nhập bằng tài khoản quản trị.
- Thêm / sửa / xóa phòng.
- Đổi trạng thái phòng (trống / đã ở / bảo trì).
- Sửa mô tả, giá, diện tích, danh sách thiết bị.
- Upload / xóa hình ảnh của từng phòng.
- **Cài đặt liên hệ & bản đồ**: chỉnh địa chỉ, điện thoại, giờ mở cửa, vị trí Google Maps.
- **Đổi ảnh nền trang chủ**: upload / xóa ảnh nền phần tiêu đề ngay trong mục Cài đặt liên hệ.
- Quản lý khách trọ, CCCD, phòng đang ở và ngày nhận/trả phòng.
- Quản lý hóa đơn điện nước theo tháng, tự tính tiền và trạng thái đã thu.
- Quản lý hợp đồng, tiền cọc và tiền thuê hàng tháng.
- Xem và xử lý tin nhắn liên hệ/đặt phòng.
- Quản lý tài khoản `admin`/`staff`, đổi mật khẩu và phân quyền thao tác.
- Giới hạn mỗi ảnh tải lên tối đa 8MB.

## Cài đặt & chạy

```bash
# 1. Cài dependency (nên dùng virtual environment)
pip install -r requirements.txt

# 2. Chạy server
python run.py
```

Mở trình duyệt:
- Trang khách: http://127.0.0.1:8000
- Trang quản trị: http://127.0.0.1:8000/admin

### Tài khoản quản trị mặc định
| Tên đăng nhập | Mật khẩu |
| --------------| ---------|
| `admin`       | `admin123` |

> ⚠️ Hãy đổi mật khẩu mặc định trước khi triển khai thật.
> Bạn có thể đổi secret cho JWT bằng biến môi trường `ROOM_MANAGER_SECRET`.

## Cấu trúc dự án

```
phong_tro_manager/
├── run.py                 # Điểm vào
├── requirements.txt
├── app/
│   ├── main.py            # FastAPI app + seed dữ liệu mẫu
│   ├── database.py        # SQLite local / PostgreSQL production
│   ├── models.py          # Phòng, khách, hóa đơn, hợp đồng, tin nhắn, tài khoản
│   ├── schemas.py         # Pydantic schemas
│   ├── auth.py            # Băm mật khẩu + JWT
│   ├── routers/
│   │   ├── auth.py        # POST /api/auth/login
│   │   └── rooms.py       # CRUD phòng + upload ảnh
│   └── static/
│       ├── index.html     # Trang khách
│       ├── admin.html     # Trang quản trị
│       ├── css/style.css
│       └── js/main.js, admin.js
├── data/phongtro.db       # SQLite (tạo tự động)
└── uploads/               # Hình ảnh phòng (tạo tự động)
```

## API chính

| Phương thức | Đường dẫn                            | Mô tả                          |
|-------------|--------------------------------------|--------------------------------|
| GET         | `/api/rooms`                         | Danh sách phòng                |
| GET         | `/api/rooms/stats`                   | Thống kê trống/ở/bảo trì       |
| GET         | `/api/rooms/{id}`                    | Chi tiết phòng                 |
| POST        | `/api/auth/login`                    | Đăng nhập admin (JWT)          |
| POST        | `/api/rooms`                         | Tạo phòng *(admin)*            |
| PUT         | `/api/rooms/{id}`                    | Cập nhật phòng *(admin)*       |
| DELETE      | `/api/rooms/{id}`                    | Xóa phòng *(admin)*            |
| POST        | `/api/rooms/{id}/images`             | Upload ảnh *(admin)*           |
| DELETE      | `/api/rooms/{id}/images/{img_id}`    | Xóa ảnh *(admin)*              |
| GET         | `/api/settings`                      | Lấy thông tin liên hệ          |
| PUT         | `/api/settings`                      | Cập nhật liên hệ & bản đồ *(admin)* |
| POST        | `/api/settings/background`           | Upload ảnh nền trang chủ *(admin)* |
| POST        | `/api/contact`                       | Gửi liên hệ/đặt phòng              |
| GET/POST    | `/api/tenants`                       | Danh sách/thêm khách trọ *(quản trị)* |
| GET/POST    | `/api/tenants/bills`                 | Danh sách/thêm hóa đơn *(quản trị)* |
| GET/POST    | `/api/tenants/contracts`             | Danh sách/thêm hợp đồng *(quản trị)* |
| GET         | `/api/auth/me`                       | Tài khoản hiện tại                 |
| GET/POST    | `/api/auth/admins`                   | Quản lý tài khoản *(admin)*        |

Tài liệu API tương tác: http://127.0.0.1:8000/docs