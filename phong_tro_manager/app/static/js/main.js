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

/* ---------- Toast ---------- */
const toastEl = document.getElementById("toast");
let toastTimer = null;
function showToast(msg, type = "") {
  toastEl.textContent = msg;
  toastEl.className = `toast show ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toastEl.className = "toast"; }, 3200);
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
function filterQuery() {
  const q = document.getElementById("f-q").value.trim();
  const status = document.getElementById("f-status").value;
  const price = document.getElementById("f-price").value;
  const area = document.getElementById("f-area").value;
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (status) params.set("status", status);
  if (price) {
    const [min, max] = price.split(",");
    params.set("min_price", min);
    params.set("max_price", max);
  }
  if (area) {
    const [min, max] = area.split(",");
    params.set("min_area", min);
    params.set("max_area", max);
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

function roomCard(room) {
  const thumb = room.thumbnail_url
    ? `<img src="${room.thumbnail_url}" alt="${room.name}" loading="lazy" />`
    : `<div class="placeholder-text">${room.name}</div>`;

  return `
    <div class="room-card" data-id="${room.id}" data-ac="${room.has_ac ? "1" : "0"}">
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
    const rooms = await apiGet("/api/rooms" + filterQuery());
    loading.style.display = "none";
    const count = document.getElementById("room-count");
    count.textContent = rooms.length ? `${rooms.length} phòng` : "0 phòng";
    empty.classList.add("hidden");
    if (rooms.length === 0) {
      empty.classList.remove("hidden");
      return;
    }
    grid.innerHTML = rooms.map(roomCard).join("");

    // Khi click vào thẻ phòng -> mở modal chi tiết
    grid.querySelectorAll(".room-card").forEach((card) => {
      card.addEventListener("click", () => openDetail(card.dataset.id));
    });
    applyAcFilter();
  } catch (err) {
    loading.style.display = "none";
    empty.textContent = "Không thể tải danh sách phòng. Vui lòng thử lại.";
    empty.classList.remove("hidden");
  }
}

/* ---------------- Lọc điều hòa ---------------- */
function currentAcFilter() {
  const bar = document.getElementById("filter-chips");
  if (!bar) return "all";
  for (const chip of bar.querySelectorAll(".filter-chip")) {
    if (chip.classList.contains("active")) return chip.dataset.ac;
  }
  return "all";
}

function applyAcFilter() {
  const grid = document.getElementById("rooms");
  const cards = grid ? grid.querySelectorAll(".room-card") : [];
  const val = currentAcFilter();
  if (!cards.length) return;
  let shown = 0;
  cards.forEach((card) => {
    const ok = val === "all" || card.dataset.ac === val;
    card.style.display = ok ? "" : "none";
    if (ok) shown += 1;
  });
  const empty = document.getElementById("empty");
  if (empty) {
    if (shown === 0) {
      empty.textContent = "Không có phòng phù hợp với bộ lọc này.";
      empty.classList.remove("hidden");
    } else {
      empty.textContent = "Chưa có phòng nào để hiển thị.";
      empty.classList.add("hidden");
    }
  }
  const count = document.getElementById("room-count");
  if (count) count.textContent = shown ? `${shown} phòng` : "0 phòng";
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
  const bookingAction = room.status === "available"
    ? `<button class="btn btn-primary btn-book-room" data-id="${room.id}">🏠 Đặt phòng này</button>`
    : '<span class="muted">Phòng hiện không nhận đặt phòng.</span>';

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
    ${equipmentBlock}
    <div class="modal-actions">
      ${bookingAction}
      <button class="btn btn-ghost" id="btn-close-detail">Đóng</button>
    </div>`;
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
    const bookBtn = modalBody.querySelector(".btn-book-room");
    if (bookBtn) bookBtn.addEventListener("click", () => startBooking(bookBtn.dataset.id));
    const closeBtn = modalBody.querySelector("#btn-close-detail");
    if (closeBtn) closeBtn.addEventListener("click", closeModal);
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

    // Các nút Gọi điện / Zalo / Facebook
    const digits = (s.phone || "").replace(/[^+\d]/g, "");
    const socCall = document.getElementById("soc-call");
    const socZalo = document.getElementById("soc-zalo");
    const socFb = document.getElementById("soc-fb");
    if (socCall) socCall.href = s.phone ? `tel:${digits}` : "#";
    if (socZalo) socZalo.href = digits ? `https://zalo.me/${digits}` : "#";
    if (socFb) {
      if (s.facebook_url) {
        socFb.href = s.facebook_url;
        socFb.classList.remove("hidden");
      } else {
        socFb.classList.add("hidden");
      }
    }

    // Nội quy & Quy định — mặc định chỉ hiện 3 điểm đầu,
    // phần còn lại ẩn đi và bật nút "Xem toàn bộ / Thu gọn".
    const rulesSection = document.getElementById("rules-section");
    const rulesBody = document.getElementById("rules-body");
    const rulesToggle = document.getElementById("rules-toggle");
    const rules = (s.house_rules || "").trim();
    if (rulesSection && rulesBody) {
      if (rules) {
        const lines = rules.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
        const PREVIEW = 3;
        const rest = lines.slice(PREVIEW);
        rulesBody.innerHTML = lines
          .slice(0, PREVIEW)
          .map((l) => `<p>${escHTML(l)}</p>`)
          .join("");
        if (rest.length) {
          const restWrap = document.createElement("div");
          restWrap.id = "rules-rest";
          restWrap.className = "rules-rest hidden";
          restWrap.innerHTML = rest.map((l) => `<p>${escHTML(l)}</p>`).join("");
          rulesBody.appendChild(restWrap);
          if (rulesToggle) {
            rulesToggle.hidden = false;
            rulesToggle.textContent = `📖 Xem toàn bộ nội quy (${rest.length}) ▼`;
          }
        } else if (rulesToggle) {
          rulesToggle.hidden = true;
        }
        rulesSection.classList.remove("hidden");
      } else {
        rulesSection.classList.add("hidden");
      }
    }

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
/* ---------------- Lọc / tìm kiếm phòng ---------------- */
const filterBar = document.getElementById("filter-bar");
if (filterBar) {
  filterBar.addEventListener("input", () => loadRooms());
  filterBar.addEventListener("change", () => loadRooms());
}
document.getElementById("f-clear").addEventListener("click", () => {
  document.getElementById("f-q").value = "";
  document.getElementById("f-status").value = "";
  document.getElementById("f-price").value = "";
  document.getElementById("f-area").value = "";
  const bar = document.getElementById("filter-chips");
  if (bar) {
    bar.querySelectorAll(".filter-chip").forEach((c) => {
      c.classList.toggle("active", c.dataset.ac === "all");
    });
  }
  loadRooms();
});

/* ---------------- Lọc điều hòa ---------------- */
const chipsBar = document.getElementById("filter-chips");
if (chipsBar) {
  chipsBar.querySelectorAll(".filter-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      chipsBar.querySelectorAll(".filter-chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      applyAcFilter();
    });
  });
}

/* ---------------- Nội quy: hiện / ẩn bớt ---------------- */
const rulesToggleBtn = document.getElementById("rules-toggle");
if (rulesToggleBtn) {
  rulesToggleBtn.addEventListener("click", () => {
    const restWrap = document.getElementById("rules-rest");
    if (!restWrap) return;
    const collapsed = restWrap.classList.toggle("hidden");
    const count = restWrap.querySelectorAll("p").length;
    rulesToggleBtn.textContent = collapsed
      ? `📖 Xem toàn bộ nội quy (${count}) ▼`
      : "🙈 Thu gọn nội quy ▲";
  });
}

/* ---------------- Form liên hệ / đặt phòng ---------------- */
async function loadRoomOptions() {
  const sel = document.getElementById("c-room");
  try {
    const rooms = await apiGet("/api/rooms");
    const opts = rooms
      .filter((r) => r.status === "available")
      .map((r) => `<option value="${r.id}">${escHTML(r.name)} — ${formatVND(r.price)}/tháng</option>`)
      .join("");
    sel.innerHTML = '<option value="">Chưa chọn phòng</option>' + opts;
  } catch (err) {
    /* bỏ qua nếu chưa tải được phòng */
  }
}

function startBooking(roomId) {
  closeModal();
  const sel = document.getElementById("c-room");
  if (sel && roomId) sel.value = String(roomId);
  const name = document.getElementById("c-name");
  const msg = document.getElementById("c-message");
  if (name && !name.value) name.focus();
  if (msg && !msg.value) {
    const roomName = sel && sel.selectedOptions[0] ? sel.selectedOptions[0].textContent : "";
    msg.value = `Xin chào, em muốn đặt phòng ${roomName}. Vui lòng liên hệ lại em ạ.`;
  }
  const section = document.getElementById("contact-form-section");
  if (section) section.scrollIntoView({ behavior: "smooth" });
}

document.getElementById("contact-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = e.target.querySelector('button[type="submit"]');
  const payload = {
    name: document.getElementById("c-name").value.trim(),
    phone: document.getElementById("c-phone").value.trim(),
    email: document.getElementById("c-email").value.trim(),
    room_id: document.getElementById("c-room").value
      ? Number(document.getElementById("c-room").value)
      : null,
    message: document.getElementById("c-message").value.trim(),
  };
  if (!payload.name || !payload.phone || !payload.message) {
    return showToast("Vui lòng điền đầy đủ họ tên, số điện thoại và nội dung.", "error");
  }
  btn.disabled = true;
  try {
    const res = await fetch("/api/contact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Gửi thất bại.");
    showToast("✅ Đã gửi yêu cầu. Quản lý sẽ sớm liên hệ lại bạn!", "success");
    e.target.reset();
    await loadRoomOptions();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
  }
});

loadRoomOptions();
loadSettings();