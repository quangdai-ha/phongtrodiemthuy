/* ===== Trang quản trị: đăng nhập, quản lý phòng, ảnh ===== */
"use strict";

const TOKEN_KEY = "phongtro_admin_token";
const STATUS_LABEL = {
  available: "Phòng trống",
  occupied: "Đã có người ở",
  maintenance: "Đang bảo trì",
};

function getToken() { return localStorage.getItem(TOKEN_KEY) || ""; }
function setToken(t) { localStorage.setItem(TOKEN_KEY, t); }
function clearToken() { localStorage.removeItem(TOKEN_KEY); }
function authHeaders() {
  return { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` };
}
function formatVND(amount) {
  return new Intl.NumberFormat("vi-VN").format(amount) + " đ";
}

/* ---------- Toast ---------- */
const toastEl = document.getElementById("toast");
let toastTimer = null;
function showToast(msg, type = "") {
  toastEl.textContent = msg;
  toastEl.className = `toast show ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toastEl.className = "toast"; }, 3000);
}
const toast = showToast;

/* ---------- Chuyển màn hình ---------- */
function showLogin() {
  document.getElementById("login-screen").classList.remove("hidden");
  document.getElementById("dashboard").classList.add("hidden");
  document.getElementById("btn-logout").classList.add("hidden");
}
function showDashboard() {
  document.getElementById("login-screen").classList.add("hidden");
  document.getElementById("dashboard").classList.remove("hidden");
  document.getElementById("btn-logout").classList.remove("hidden");
}

/* ---------- Đăng nhập / đăng xuất ---------- */
document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Đăng nhập thất bại.");
    setToken(data.access_token);
    showDashboard();
    toast(`Xin chào ${data.username} 👋`, "success");
    loadRooms();
  } catch (err) {
    toast(err.message, "error");
  }
});

document.getElementById("btn-logout").addEventListener("click", () => {
  clearToken();
  showLogin();
  toast("Đã đăng xuất.");
});

/* ---------- Gọi API ---------- */
async function api(url, options = {}) {
  const res = await fetch(url, options);
  if (res.status === 401) {
    clearToken();
    showLogin();
    toast("Phiên đã hết hạn, vui lòng đăng nhập lại.", "error");
    throw new Error("401");
  }
  if (res.status === 204) return null;
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const msg = data && data.detail ? data.detail : "Có lỗi xảy ra.";
    throw new Error(msg);
  }
  return data;
}

/* ---------- Danh sách phòng (thẻ quản trị) ---------- */
function adminCard(room) {
  const thumb = room.thumbnail_url
    ? `<img src="${room.thumbnail_url}" alt="${room.name}" />`
    : `<div class="thumb-text">${room.name}</div>`;
  return `
    <div class="admin-card" data-id="${room.id}">
      <div class="card-head">
        ${thumb}
        <span class="status-badge ${room.status}">${STATUS_LABEL[room.status]}</span>
      </div>
      <div class="card-body">
        <h3>${room.name}</h3>
        <div class="row"><span>Giá thuê</span><b>${formatVND(room.price)}/tháng</b></div>
        <div class="row"><span>Diện tích</span><b>${room.area} m²</b></div>
        <div class="row"><span>Trạng thái</span><b>${STATUS_LABEL[room.status]}</b></div>
        <div class="actions">
          <button class="btn btn-primary btn-sm btn-edit">✏️ Sửa</button>
          <button class="btn btn-danger btn-sm btn-delete">🗑️ Xóa</button>
        </div>
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
    const rooms = await api("/api/rooms", { headers: authHeaders() });
    loading.style.display = "none";
    if (!rooms.length) {
      empty.classList.remove("hidden");
      return;
    }
    empty.classList.add("hidden");
    grid.innerHTML = rooms.map(adminCard).join("");
    grid.querySelectorAll(".admin-card").forEach((card) => {
      const id = card.dataset.id;
      card.querySelector(".btn-edit").addEventListener("click", () => openForm(id));
      card.querySelector(".btn-delete").addEventListener("click", () => deleteRoom(id));
    });
  } catch (err) {
    loading.style.display = "none";
  }
}

async function deleteRoom(id) {
  if (!confirm(`Bạn chắc chắn muốn xóa phòng #${id}?`)) return;
  try {
    await api(`/api/rooms/${id}`, { method: "DELETE", headers: authHeaders() });
    toast("Đã xóa phòng.", "success");
    loadRooms();
  } catch (err) {
    if (err.message !== "401") toast(err.message, "error");
  }
}

/* ===== Form tạo / sửa phòng ===== */
const formModal = document.getElementById("form-modal");
const formTitle = document.getElementById("form-title");
const tagsEditor = document.getElementById("tags-editor");
const tagInput = document.getElementById("tag-input");
const imgEditor = document.getElementById("img-editor");
const imgUpload = document.getElementById("img-upload");

let currentRoomId = null;

function resetForm() {
  document.getElementById("room-id").value = "";
  document.getElementById("f-name").value = "";
  document.getElementById("f-status").value = "available";
  document.getElementById("f-price").value = "";
  document.getElementById("f-area").value = "";
  document.getElementById("f-desc").value = "";
  tagsEditor.querySelectorAll(".tag").forEach((t) => t.remove());
  imgEditor.innerHTML = "";
  imgUpload.value = "";
}

function openForm(id = null) {
  currentRoomId = id;
  resetForm();

  if (id) {
    formTitle.textContent = "Chỉnh sửa phòng";
    formModal.classList.add("open");
    document.body.style.overflow = "hidden";
    api(`/api/rooms/${id}`)
      .then((room) => fillForm(room))
      .catch(() => toast("Không tải được phòng.", "error"));
  } else {
    formTitle.textContent = "Thêm phòng";
    formModal.classList.add("open");
    document.body.style.overflow = "hidden";
  }
}

function fillForm(room) {
  document.getElementById("room-id").value = room.id;
  document.getElementById("f-name").value = room.name;
  document.getElementById("f-status").value = room.status;
  document.getElementById("f-price").value = room.price;
  document.getElementById("f-area").value = room.area;
  document.getElementById("f-desc").value = room.description || "";
  (room.equipment || []).forEach((e) => addTag(e));
  renderImageEditor(room.images || []);
}

function closeForm() {
  formModal.classList.remove("open");
  document.body.style.overflow = "";
  currentRoomId = null;
}

document.getElementById("form-close").addEventListener("click", closeForm);
document.getElementById("form-cancel").addEventListener("click", closeForm);
formModal.addEventListener("click", (e) => {
  if (e.target === formModal) closeForm();
});

/* ---------- Editor thiết bị (tags) ---------- */
function addTag(text) {
  text = text.trim();
  if (!text) return;
  const tag = document.createElement("span");
  tag.className = "tag";
  tag.appendChild(document.createTextNode(text));
  const btn = document.createElement("button");
  btn.type = "button";
  btn.textContent = "×";
  btn.addEventListener("click", () => tag.remove());
  tag.appendChild(btn);
  tagsEditor.insertBefore(tag, tagInput);
}

tagInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === ",") {
    e.preventDefault();
    addTag(tagInput.value);
    tagInput.value = "";
  }
});
tagsEditor.addEventListener("click", () => tagInput.focus());

function getTags() {
  return Array.from(tagsEditor.querySelectorAll(".tag")).map(
    (t) => t.firstChild.textContent
  );
}

/* ---------- Editor hình ảnh ---------- */
function renderImageEditor(images) {
  imgEditor.innerHTML = "";
  images.forEach((img, i) => {
    const box = document.createElement("div");
    box.className = "img-box";
    box.innerHTML = `
      <img src="${img.url}" alt="Ảnh phòng" />
      <button class="del" data-id="${img.id}" title="Xóa ảnh">&times;</button>
      ${i === 0 ? '<span class="main-tag">Ảnh bìa</span>' : ""}`;
    imgEditor.appendChild(box);
  });
  imgEditor.querySelectorAll(".del").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!currentRoomId) return;
      try {
        await api(`/api/rooms/${currentRoomId}/images/${btn.dataset.id}`, {
          method: "DELETE",
          headers: authHeaders(),
        });
        toast("Đã xóa ảnh.", "success");
        const room = await api(`/api/rooms/${currentRoomId}`);
        renderImageEditor(room.images || []);
      } catch (err) {
        if (err.message !== "401") toast(err.message, "error");
      }
    });
  });
}

imgUpload.addEventListener("change", async () => {
  if (!currentRoomId || !imgUpload.files.length) return;
  const files = Array.from(imgUpload.files);
  imgUpload.disabled = true;
  try {
    for (const file of files) {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`/api/rooms/${currentRoomId}/images`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
        body: fd,
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Tải ảnh thất bại.");
      }
    }
    const room = await api(`/api/rooms/${currentRoomId}`);
    renderImageEditor(room.images || []);
    toast("Đã tải ảnh lên.", "success");
  } catch (err) {
    if (err.message !== "401") toast(err.message, "error");
  } finally {
    imgUpload.disabled = false;
    imgUpload.value = "";
  }
});

/* ---------- Lưu phòng (tạo mới / cập nhật) ---------- */
document.getElementById("room-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    name: document.getElementById("f-name").value.trim(),
    status: document.getElementById("f-status").value,
    price: Number(document.getElementById("f-price").value) || 0,
    area: Number(document.getElementById("f-area").value) || 0,
    description: document.getElementById("f-desc").value,
    equipment: getTags(),
  };
  if (!payload.name) return toast("Vui lòng nhập tên phòng.", "error");

  const url = currentRoomId ? `/api/rooms/${currentRoomId}` : "/api/rooms";
  const method = currentRoomId ? "PUT" : "POST";
  try {
    await api(url, {
      method,
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    toast(currentRoomId ? "Đã cập nhật phòng." : "Đã thêm phòng mới.", "success");
    closeForm();
    loadRooms();
  } catch (err) {
    if (err.message !== "401") toast(err.message, "error");
  }
});

document.getElementById("btn-add-room").addEventListener("click", () => openForm());

/* ===== Cài đặt liên hệ & bản đồ ===== */
const settingsModal = document.getElementById("settings-modal");
const bgPreview = document.getElementById("s-bg-preview");
const bgUpload = document.getElementById("s-bg-upload");
const bgRemove = document.getElementById("s-bg-remove");
let currentBg = "";

function renderBgPreview(url) {
  currentBg = url || "";
  if (currentBg) {
    bgPreview.style.backgroundImage = `url('${currentBg}')`;
    bgPreview.textContent = "";
    bgRemove.classList.remove("hidden");
  } else {
    bgPreview.style.backgroundImage = "";
    bgPreview.textContent = "Chưa có ảnh nền";
    bgRemove.classList.add("hidden");
  }
}

function openSettings() {
  api("/api/settings")
    .then((s) => {
      document.getElementById("s-address").value = s.address || "";
      document.getElementById("s-phone").value = s.phone || "";
      document.getElementById("s-hours").value = s.hours || "";
      document.getElementById("s-map-location").value = s.map_location || "";
      document.getElementById("s-map-embed").value = s.map_embed_url || "";
      renderBgPreview(s.background_image);
      settingsModal.classList.add("open");
      document.body.style.overflow = "hidden";
    })
    .catch(() => toast("Không tải được cài đặt.", "error"));
}

function closeSettings() {
  settingsModal.classList.remove("open");
  document.body.style.overflow = "";
}

document.getElementById("btn-settings").addEventListener("click", openSettings);
document.getElementById("settings-close").addEventListener("click", closeSettings);
document.getElementById("settings-cancel").addEventListener("click", closeSettings);
settingsModal.addEventListener("click", (e) => {
  if (e.target === settingsModal) closeSettings();
});

document.getElementById("settings-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    address: document.getElementById("s-address").value.trim(),
    phone: document.getElementById("s-phone").value.trim(),
    hours: document.getElementById("s-hours").value.trim(),
    map_location: document.getElementById("s-map-location").value.trim(),
    map_embed_url: document.getElementById("s-map-embed").value.trim(),
    background_image: currentBg,
  };
  try {
    await api("/api/settings", {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    toast("Đã lưu cài đặt liên hệ.", "success");
    closeSettings();
  } catch (err) {
    if (err.message !== "401") toast(err.message, "error");
  }
});

/* Upload / xóa ảnh nền */
bgUpload.addEventListener("change", async () => {
  const file = bgUpload.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  bgUpload.disabled = true;
  try {
    const res = await fetch("/api/settings/background", {
      method: "POST",
      headers: { Authorization: `Bearer ${getToken()}` },
      body: fd,
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || "Tải ảnh nền thất bại.");
    }
    const updated = await res.json();
    renderBgPreview(updated.background_image);
    toast("Đã đặt ảnh nền.", "success");
  } catch (err) {
    if (err.message !== "401") toast(err.message, "error");
  } finally {
    bgUpload.disabled = false;
    bgUpload.value = "";
  }
});

bgRemove.addEventListener("click", async () => {
  try {
    const updated = await api("/api/settings", {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify({ background_image: "" }),
    });
    renderBgPreview("");
    toast("Đã xóa ảnh nền.", "success");
  } catch (err) {
    if (err.message !== "401") toast(err.message, "error");
  }
});

/* ---------- Khởi động ---------- */
(function init() {
  if (getToken()) {
    showDashboard();
    loadRooms();
  } else {
    showLogin();
  }
})();