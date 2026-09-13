/* ===== Trang công khai: xem danh sách & chi tiết phòng ===== */
"use strict";

const STATUS_LABEL = {
  available: "Phòng trống",
  occupied: "Đã có người ở",
  maintenance: "Đang bảo trì",
};

function formatVND(amount) {
  return new Intl.NumberFormat("vi-VN").format(amount) + " đ";
}

function statusBadge(status, large = false) {
  const label = STATUS_LABEL[status] || status;
  return `<span class="status-badge ${status} ${large ? "badge-lg" : ""}">${label}</span>`;
}

async function apiGet(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error("Lỗi tải dữ liệu");
  return res.json();
}

/* ---------------- Thống kê ---------------- */
async function loadStats() {
  const stats = await apiGet("/api/rooms/stats");
  document.getElementById("stat-total").textContent = stats.total;
  document.getElementById("stat-available").textContent = stats.available;
  document.getElementById("stat-occupied").textContent = stats.occupied;
  document.getElementById("stat-maintenance").textContent = stats.maintenance;
}

/* ---------------- Danh sách phòng ---------------- */
function roomCard(room) {
  const thumb = room.thumbnail_url
    ? `<img src="${room.thumbnail_url}" alt="${room.name}" loading="lazy" />`
    : `<div class="placeholder-text">${room.name}</div>`;

  return `
    <div class="room-card" data-id="${room.id}">
      <div class="room-thumb">
        ${thumb}
        ${statusBadge(room.status)}
      </div>
      <div class="room-body">
        <h3>${room.name}</h3>
        <div class="room-meta">Diện tích: ${room.area} m²</div>
        <div class="room-price">${formatVND(room.price)} <span class="price-suffix">/ tháng</span></div>
      </div>
    </div>`;
}

async function loadRooms() {
  const grid = document.getElementById("rooms");
  const loading = document.getElementById("loading");
  const empty = document.getElementById("empty");
  grid.innerHTML = "";
  loading.style.display = "block";

  try {
    const rooms = await apiGet("/api/rooms");
    loading.style.display = "none";
    document.getElementById("room-count").textContent = `${rooms.length} phòng`;
    if (rooms.length === 0) {
      empty.classList.remove("hidden");
      return;
    }
    grid.innerHTML = rooms.map(roomCard).join("");

    // Khi click vào thẻ phòng -> mở modal chi tiết
    grid.querySelectorAll(".room-card").forEach((card) => {
      card.addEventListener("click", () => openDetail(card.dataset.id));
    });
  } catch (err) {
    loading.style.display = "none";
    empty.textContent = "Không thể tải danh sách phòng. Vui lòng thử lại.";
    empty.classList.remove("hidden");
  }
}

/* ---------------- Chi tiết phòng ---------------- */
const modal = document.getElementById("detail-modal");
const modalBody = document.getElementById("detail-body");
const modalTitle = document.getElementById("detail-title");

function openModal() {
  modal.classList.add("open");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  modal.classList.remove("open");
  document.body.style.overflow = "";
}

function galleryHTML(images) {
  if (!images || images.length === 0) {
    return `<div class="detail-gallery">
      <div class="detail-thumbs"><div class="no-img" style="height:280px; grid-column: 1 / -1;">Chưa có hình ảnh</div></div>
    </div>`;
  }
  let thumbs = "";
  for (let i = 1; i < Math.min(images.length, 5); i++) {
    thumbs += `<img src="${images[i].url}" alt="Ảnh phòng" />`;
  }
  if (images.length > 5) {
    thumbs += `<div class="no-img">+${images.length - 5} ảnh</div>`;
  }
  return `
    <div class="detail-gallery">
      <img class="main-img" src="${images[0].url}" alt="Ảnh phòng" id="gallery-main" />
      <div class="detail-thumbs">
        ${thumbs}
      </div>
    </div>`;
}

function detailHTML(room) {
  const equipment = (room.equipment || []).map((e) => `<li>${e}</li>`).join("");
  const equipmentBlock = equipment
    ? `<ul class="equipment-list">${equipment}</ul>`
    : '<p class="muted">Chưa cập nhật thiết bị.</p>';

  return `
    ${galleryHTML(room.images)}
    <div class="detail-info">
      <div class="info-item"><div class="k">Giá thuê</div><div class="v">${formatVND(room.price)}/tháng</div></div>
      <div class="info-item"><div class="k">Diện tích</div><div class="v">${room.area} m²</div></div>
      <div class="info-item"><div class="k">Trạng thái</div><div class="v">${STATUS_LABEL[room.status] || room.status}</div></div>
      <div class="info-item"><div class="k">Mã phòng</div><div class="v">#${room.id}</div></div>
    </div>
    <h4>Mô tả</h4>
    <p class="detail-desc">${room.description || "Chưa có mô tả."}</p>
    <h4>Trang thiết bị</h4>
    ${equipmentBlock}`;
}

async function openDetail(id) {
  modalTitle.textContent = "Đang tải chi tiết...";
  modalBody.innerHTML = '<div class="spinner"></div>';
  openModal();
  try {
    const room = await apiGet(`/api/rooms/${id}`);
    modalTitle.textContent = room.name;
    modalBody.innerHTML = detailHTML(room);
    bindGalleryThumbs();
  } catch (err) {
    modalBody.innerHTML = '<p class="center muted">Không thể tải chi tiết phòng.</p>';
  }
}

function bindGalleryThumbs() {
  const thumbs = modalBody.querySelectorAll(".detail-thumbs img");
  const main = modalBody.querySelector("#gallery-main");
  thumbs.forEach((img) => {
    img.addEventListener("click", () => {
      if (!main) return;
      main.src = img.src;
      thumbs.forEach((t) => t.classList.remove("active"));
      img.classList.add("active");
    });
  });
}

/* ---------------- Liên hệ & Bản đồ ---------------- */
function escHTML(s) {
  const div = document.createElement("div");
  div.textContent = s == null ? "" : String(s);
  return div.innerHTML;
}

function isEmbeddableMapUrl(url) {
  return /\/maps\/embed|output=embed/i.test(url);
}

function mapEmbedSrc(settings) {
  const embed = (settings.map_embed_url || "").trim();
  if (embed && isEmbeddableMapUrl(embed)) {
    return embed;
  }
  // Nếu admin dán link chia sẻ Google Maps (không nhúng được),
  // tự động dùng map_location để hiển thị bản đồ.
  const loc = (settings.map_location || "").trim();
  if (loc) {
    return `https://www.google.com/maps?q=${encodeURIComponent(loc)}&output=embed&z=15`;
  }
  return "";
}

async function loadSettings() {
  const mapBox = document.getElementById("map-box");
  try {
    const s = await apiGet("/api/settings");
    const addr = s.address || "Chưa cập nhật địa chỉ";

    document.getElementById("contact-address").textContent = addr;

    const phoneEl = document.getElementById("contact-phone");
    phoneEl.textContent = s.phone || "Chưa cập nhật";
    phoneEl.href = s.phone ? `tel:${s.phone.replace(/[^+\d]/g, "")}` : "#";

    document.getElementById("contact-hours").textContent =
      s.hours || "Chưa cập nhật giờ mở cửa";

    // Ảnh nền phần tiêu đề
    const header = document.querySelector(".site-header");
    if (header) {
      if (s.background_image) {
        header.style.backgroundImage = `linear-gradient(135deg, rgba(12,166,120,.85), rgba(11,114,133,.85)), url('${s.background_image}')`;
        header.style.backgroundSize = "cover";
        header.style.backgroundPosition = "center";
      } else {
        header.style.backgroundImage = "";
        header.style.backgroundSize = "";
        header.style.backgroundPosition = "";
      }
    }

    const src = mapEmbedSrc(s);
    const query = encodeURIComponent(s.map_location || s.address || "");
    const btnMap = document.getElementById("btn-open-map");

    if (src) {
      mapBox.innerHTML = `<iframe src="${escHTML(src)}" title="Bản đồ Google Maps" loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"></iframe>`;
    } else {
      mapBox.innerHTML = '<div class="map-placeholder">Chưa cập nhật bản đồ.</div>';
    }

    // Nút "Mở Google Maps": ưu tiên dùng đúng link chia sẻ (nếu có),
    // ngược lại mở theo địa chỉ/map_location.
    if (s.map_embed_url && !isEmbeddableMapUrl(s.map_embed_url)) {
      btnMap.classList.remove("hidden");
      btnMap.href = s.map_embed_url;
    } else if (query) {
      btnMap.classList.remove("hidden");
      btnMap.href = `https://www.google.com/maps?q=${query}`;
    } else {
      btnMap.classList.add("hidden");
    }
  } catch (err) {
    if (mapBox) {
      mapBox.innerHTML = '<div class="map-placeholder">Không thể tải thông tin liên hệ.</div>';
    }
  }
}

/* ---------------- Khởi động ---------------- */
document.getElementById("modal-close").addEventListener("click", closeModal);
modal.addEventListener("click", (e) => {
  if (e.target === modal) closeModal();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});

loadStats();
loadRooms();
loadSettings();