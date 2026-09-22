/* ===== Trang quản trị: đăng nhập, quản lý phòng, ảnh ===== */
"use strict";

const TOKEN_KEY = "phongtro_admin_token";
const ROLE_KEY = "phongtro_admin_role";
const USERNAME_KEY = "phongtro_admin_username";
const ROLE_LABEL = { admin: "Quản trị viên", staff: "Nhân viên" };
const STATUS_LABEL = {
  available: "Phòng trống",
  occupied: "Đã có người ở",
  maintenance: "Đang bảo trì",
};
const TENANT_LABEL = { active: "Đang ở", moved_out: "Đã chuyển đi" };

function getToken() { return localStorage.getItem(TOKEN_KEY) || ""; }
function setToken(t) { localStorage.setItem(TOKEN_KEY, t); }
function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  localStorage.removeItem(USERNAME_KEY);
}
function getRole() { return localStorage.getItem(ROLE_KEY) || "staff"; }
function authHeaders() {
  return { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` };
}
function isAdmin() { return getRole() === "admin"; }
function escHTML(value) {
  const div = document.createElement("div");
  div.textContent = value == null ? "" : String(value);
  return div.innerHTML;
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
    localStorage.setItem(ROLE_KEY, data.role || "staff");
    localStorage.setItem(USERNAME_KEY, data.username || "");
    showDashboard();
    applyRoleUI();
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

/* ---------- Đóng mọi modal đang mở ---------- */
function closeAllModals() {
  ["settings-modal", "form-modal", "tenant-modal", "bill-modal", "contract-modal"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.classList.remove("open");
  });
  document.body.style.overflow = "";
}

/* ---------- Chặn Enter vô tình submit form trong modal ----------
   Khi gõ nhanh và vô tình bấm Enter trong một ô nhập (text/number/select
   nằm trong modal), trình duyệt sẽ tự submit form → lưu + đóng modal ngay.
   Chặn hành vi đó để không bị "văng" khỏi màn hình cài đặt khi chưa nhập xong.
   - Enter trong textarea vẫn xuống dòng bình thường.
   - Enter/Space trên nút bấm vẫn hoạt động.
   - Ctrl/Cmd+Enter vẫn cho phép submit (lưu nhanh có chủ đích).
   - Các form ngoài modal (đăng nhập, tạo tài khoản, đổi mật khẩu) không bị ảnh hưởng.
*/
document.addEventListener("keydown", (e) => {
  if (e.key !== "Enter" || e.ctrlKey || e.metaKey || e.altKey || e.shiftKey) return;
  const t = e.target;
  if (!t || !t.closest) return;
  const form = t.closest("form");
  if (!form || !form.closest(".modal")) return;
  if (t.tagName === "TEXTAREA" || t.tagName === "BUTTON") return;
  e.preventDefault();
}, true);

/* ---------- Gọi API ---------- */
async function api(url, options = {}) {
  const res = await fetch(url, options);
  if (res.status === 401) {
    clearToken();
    closeAllModals();
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
      const delBtn = card.querySelector(".btn-delete");
      if (delBtn) {
        if (isAdmin()) delBtn.addEventListener("click", () => deleteRoom(id));
        else delBtn.remove();
      }
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
// Không đóng modal khi bấm/rê chuột ra ngoài cửa sổ (nền tối).
// Trước đây thả chuột ngoài khung (hoặc vô tình chạm ra ngoài) sẽ phát
// click trên overlay -> đóng modal -> mất dữ liệu đang sửa. Đóng bằng ✕ / Hủy.

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
async function setCover(imgId) {
  if (!currentRoomId) return;
  try {
    await api(`/api/rooms/${currentRoomId}/cover`, {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify({ image_id: imgId }),
    });
    toast("Đã đặt ảnh bìa.", "success");
    const room = await api(`/api/rooms/${currentRoomId}`);
    renderImageEditor(room.images || []);
  } catch (err) {
    if (err.message !== "401") toast(err.message, "error");
  }
}

function renderImageEditor(images) {
  imgEditor.innerHTML = "";
  images.forEach((img) => {
    const box = document.createElement("div");
    box.className = "img-box" + (img.is_cover ? " is-cover" : "");
    box.innerHTML = `
      <div class="img-thumb">
        <img src="${img.url}" alt="Ảnh phòng" />
        <button class="del" data-id="${img.id}" title="Xóa ảnh">&times;</button>
      </div>
      <button type="button" class="cover-btn ${img.is_cover ? "active" : ""}" data-id="${img.id}"
        title="${img.is_cover ? "Đây là ảnh bìa hiện tại" : "Chọn ảnh này làm ảnh bìa"}">
        ${img.is_cover ? "⭐ Ảnh bìa" : "☆ Đặt ảnh bìa"}
      </button>`;
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
  imgEditor.querySelectorAll(".cover-btn").forEach((btn) => {
    btn.addEventListener("click", () => setCover(Number(btn.dataset.id)));
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
const bgDefaultsBox = document.getElementById("s-bg-defaults");
let currentBg = "";

function renderBgDefaults(url) {
  if (!bgDefaultsBox) return;
  bgDefaultsBox.querySelectorAll(".bg-default-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.url === url);
  });
}

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
  renderBgDefaults(currentBg);
}

function loadBgDefaults() {
  if (!bgDefaultsBox) return;
  fetch("/api/settings/backgrounds")
    .then((res) => (res.ok ? res.json() : Promise.reject(new Error("HTTP " + res.status))))
    .then((data) => {
      const list = data.defaults || [];
      bgDefaultsBox.innerHTML = "";
      if (!list.length) {
        bgDefaultsBox.textContent = "Không có ảnh nền mặc định.";
        return;
      }
      list.forEach((url) => {
        const item = document.createElement("div");
        item.className = "bg-default-item";
        item.dataset.url = url;
        item.style.backgroundImage = `url('${url}')`;
        item.title = "Đặt ảnh này làm nền";
        item.addEventListener("click", () => {
          renderBgPreview(url);
          bgUpload.value = "";
          toast("Đã chọn ảnh mặc định. Nhấn «Lưu cài đặt» để áp dụng.", "success");
        });
        bgDefaultsBox.appendChild(item);
      });
      renderBgDefaults(currentBg);
    })
    .catch(() => {
      bgDefaultsBox.innerHTML = '<span class="muted" style="font-size:0.85rem;">Không tải được danh sách ảnh mặc định.</span>';
    });
}

function openSettings() {
  api("/api/settings")
    .then((s) => {
      document.getElementById("s-address").value = s.address || "";
      document.getElementById("s-phone").value = s.phone || "";
      document.getElementById("s-hours").value = s.hours || "";
      document.getElementById("s-map-location").value = s.map_location || "";
      document.getElementById("s-map-embed").value = s.map_embed_url || "";
      document.getElementById("s-elec-price").value = s.electricity_price ?? "";
      document.getElementById("s-water-price").value = s.water_price ?? "";
      document.getElementById("s-facebook").value = s.facebook_url || "";
      document.getElementById("s-rules").value = s.house_rules || "";
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
  // (Bỏ đóng modal khi bấm nền tối - tránh mất dữ liệu đang sửa, xem ghi chú formModal)
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
    electricity_price: Number(document.getElementById("s-elec-price").value) || 0,
    water_price: Number(document.getElementById("s-water-price").value) || 0,
    facebook_url: document.getElementById("s-facebook").value.trim(),
    house_rules: document.getElementById("s-rules").value.trim(),
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
function applyRoleUI() {
  const navUser = document.getElementById("nav-user");
  if (navUser) {
    const uname = localStorage.getItem(USERNAME_KEY) || getRole();
    navUser.textContent = `👤 ${uname} (${ROLE_LABEL[getRole()] || getRole()})`;
  }
  // Ẩn tab Tài khoản / các nút xóa nếu không phải admin
  const tabAccounts = document.getElementById("tab-accounts");
  if (tabAccounts) {
    if (isAdmin()) tabAccounts.classList.remove("hidden");
    else tabAccounts.classList.add("hidden");
  }
  const tabMessages = document.querySelector('.tab-btn[data-tab="messages"]');
  if (tabMessages) tabMessages.classList.toggle("hidden", !isAdmin());
  const btnSettings = document.getElementById("btn-settings");
  if (btnSettings) {
    if (isAdmin()) btnSettings.classList.remove("hidden");
    else btnSettings.classList.add("hidden");
  }
}

async function refreshIdentity() {
  try {
    const me = await api("/api/auth/me", { headers: authHeaders() });
    localStorage.setItem(ROLE_KEY, me.role || "staff");
    localStorage.setItem(USERNAME_KEY, me.username || "");
    applyRoleUI();
    loadRooms();
  } catch (err) {
    /* api() tự chuyển về màn hình đăng nhập nếu token hết hạn */
  }
}

(function init() {
  loadBgDefaults();
  if (getToken()) {
    showDashboard();
    applyRoleUI();
    loadRooms();
    refreshIdentity();
  } else {
    showLogin();
  }
})();
/* ================================================================
 * PHẦN TÍNH NĂNG MỚI
 * ================================================================ */
function fmtNum(n) {
  return new Intl.NumberFormat("vi-VN").format(n || 0);
}
function fmtDate(d) {
  if (!d) return "—";
  return String(d).slice(0, 10);
}

/* ---------- Chuyển tab ---------- */
document.querySelectorAll(".admin-tabs .tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const tab = btn.dataset.tab;
    document.querySelectorAll(".admin-tabs .tab-btn").forEach((b) => b.classList.toggle("active", b === btn));
    document.querySelectorAll(".admin-section").forEach((sec) => {
      sec.classList.toggle("active", sec.id === `sec-${tab}`);
    });
    if (tab === "tenants") loadTenants();
    if (tab === "bills") { loadBillFilters(); loadBills(); }
    if (tab === "contracts") loadContracts();
    if (tab === "messages") loadMessages();
    if (tab === "accounts") loadAdmins();
  });
});

/* ================================================================
 * KHÁCH TRỌ
 * ================================================================ */
let tenantOptionsCache = [];
let roomOptionsCache = [];

async function loadTenantOptions() {
  try {
    const list = await api("/api/tenants", { headers: authHeaders() });
    tenantOptionsCache = list;
    for (const id of ["b-tenant", "ct-tenant"]) {
      const sel = document.getElementById(id);
      if (!sel) continue;
      sel.innerHTML = "";
      list.forEach((t) => {
        sel.insertAdjacentHTML("beforeend", `<option value="${t.id}">${t.full_name}${t.room_name ? " — " + t.room_name : ""}</option>`);
      });
    }
  } catch (err) { /* bỏ qua */ }
}

async function loadRoomSelectOptions() {
  try {
    const rooms = await api("/api/rooms", { headers: authHeaders() });
    roomOptionsCache = rooms;
    const sel = document.getElementById("t-room");
    if (!sel) return;
    sel.innerHTML = '<option value="">(Chưa xếp phòng)</option>';
    rooms.forEach((r) => sel.insertAdjacentHTML("beforeend", `<option value="${r.id}">${r.name}</option>`));
  } catch (err) { /* bỏ qua */ }
}

function tenantRow(t) {
  const badge = t.status === "active"
    ? '<span class="badge-pill badge-green">Đang ở</span>'
    : '<span class="badge-pill badge-gray">Đã chuyển đi</span>';
  const delBtn = isAdmin()
    ? `<button class="btn btn-danger btn-sm btn-t-del" data-id="${t.id}">🗑️</button>`
    : "";
  return `<tr>
    <td><b>${t.full_name}</b><br><span class="muted" style="font-size:.8rem">${t.id_card || ""}</span></td>
    <td>${t.phone || "—"}</td><td>${t.room_name || "—"}</td>
    <td>${fmtDate(t.check_in)}</td><td>${badge}</td>
    <td><div class="row-actions"><button class="btn btn-primary btn-sm btn-t-edit" data-id="${t.id}">✏️ Sửa</button>${delBtn}</div></td>
  </tr>`;
}

async function loadTenants() {
  const tbody = document.getElementById("tenant-tbody");
  const empty = document.getElementById("tenant-empty");
  const params = new URLSearchParams();
  const q = document.getElementById("tenant-q").value.trim();
  const status = document.getElementById("tenant-status").value;
  if (q) params.set("q", q);
  if (status) params.set("status", status);
  try {
    const list = await api(`/api/tenants?${params}`, { headers: authHeaders() });
    empty.classList.toggle("hidden", list.length > 0);
    tbody.innerHTML = list.map(tenantRow).join("");
    tbody.querySelectorAll(".btn-t-edit").forEach((b) => b.addEventListener("click", () => openTenantForm(b.dataset.id)));
    tbody.querySelectorAll(".btn-t-del").forEach((b) => b.addEventListener("click", () => deleteTenant(b.dataset.id)));
  } catch (err) {
    if (err.message !== "401") toast(err.message, "error");
  }
}

function closeTenantModal() {
  document.getElementById("tenant-modal").classList.remove("open");
  document.body.style.overflow = "";
}

async function openTenantForm(id = "") {
  document.getElementById("tenant-form").reset();
  document.getElementById("t-id").value = "";
  document.getElementById("t-status").value = "active";
  await loadRoomSelectOptions();
  document.getElementById("tenant-form-title").textContent = id ? "Sửa khách trọ" : "Thêm khách trọ";
  if (id) {
    try {
      const t = await api(`/api/tenants/${id}`, { headers: authHeaders() });
      document.getElementById("t-id").value = t.id;
      document.getElementById("t-name").value = t.full_name;
      document.getElementById("t-phone").value = t.phone || "";
      document.getElementById("t-room").value = t.room_id || "";
      document.getElementById("t-status").value = t.status;
      document.getElementById("t-checkin").value = t.check_in || "";
      document.getElementById("t-checkout").value = t.check_out || "";
      document.getElementById("t-idcard").value = t.id_card || "";
      document.getElementById("t-address").value = t.permanent_address || "";
      document.getElementById("t-note").value = t.note || "";
    } catch (err) {
      return toast(err.message, "error");
    }
  }
  document.getElementById("tenant-modal").classList.add("open");
  document.body.style.overflow = "hidden";
}

document.getElementById("tenant-q").addEventListener("input", loadTenants);
document.getElementById("tenant-status").addEventListener("change", loadTenants);
document.getElementById("btn-add-tenant").addEventListener("click", () => openTenantForm());
document.getElementById("tenant-close").addEventListener("click", closeTenantModal);
document.getElementById("tenant-cancel").addEventListener("click", closeTenantModal);
// (Bỏ đóng modal khi bấm nền tối - tránh mất dữ liệu đang sửa, xem ghi chú formModal)

document.getElementById("tenant-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("t-id").value;
  const roomValue = document.getElementById("t-room").value;
  const payload = {
    full_name: document.getElementById("t-name").value.trim(),
    phone: document.getElementById("t-phone").value.trim(),
    room_id: roomValue ? Number(roomValue) : null,
    status: document.getElementById("t-status").value,
    check_in: document.getElementById("t-checkin").value || null,
    check_out: document.getElementById("t-checkout").value || null,
    id_card: document.getElementById("t-idcard").value.trim(),
    permanent_address: document.getElementById("t-address").value.trim(),
    note: document.getElementById("t-note").value.trim(),
  };
  try {
    await api(id ? `/api/tenants/${id}` : "/api/tenants", {
      method: id ? "PUT" : "POST", headers: authHeaders(), body: JSON.stringify(payload),
    });
    toast(id ? "Đã cập nhật khách trọ." : "Đã thêm khách trọ.", "success");
    closeTenantModal(); loadTenants();
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
});

async function deleteTenant(id) {
  if (!confirm("Xóa khách trọ này? Hóa đơn và hợp đồng liên quan cũng sẽ bị xóa.")) return;
  try {
    await api(`/api/tenants/${id}`, { method: "DELETE", headers: authHeaders() });
    toast("Đã xóa khách trọ.", "success"); loadTenants();
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
}

/* ================================================================
 * ĐIỆN NƯỚC
 * ================================================================ */
let billsCache = [];

async function loadBillFilters() {
  try {
    const [tenants, months, settings] = await Promise.all([
      api("/api/tenants", { headers: authHeaders() }),
      api("/api/tenants/bills/months", { headers: authHeaders() }),
      api("/api/settings"),
    ]);
    tenantOptionsCache = tenants;
    const tenantFilter = document.getElementById("bill-tenant");
    const oldTenant = tenantFilter.value;
    tenantFilter.innerHTML = '<option value="">Tất cả khách</option>';
    tenants.forEach((t) => tenantFilter.insertAdjacentHTML("beforeend", `<option value="${t.id}">${t.full_name}${t.room_name ? " — " + t.room_name : ""}</option>`));
    tenantFilter.value = oldTenant;

    const monthFilter = document.getElementById("bill-month");
    const oldMonth = monthFilter.value;
    monthFilter.innerHTML = '<option value="">Tất cả tháng</option>';
    (months.months || []).forEach((m) => monthFilter.insertAdjacentHTML("beforeend", `<option value="${m}">${m}</option>`));
    monthFilter.value = oldMonth;
    document.getElementById("bill-elec-price").textContent = `${fmtNum(settings.electricity_price)}đ`;
    document.getElementById("bill-water-price").textContent = `${fmtNum(settings.water_price)}đ`;
  } catch (err) {
    if (err.message !== "401") toast(err.message, "error");
  }
}

function billRow(b) {
  const usedElec = (b.elec_new || 0) - (b.elec_old || 0);
  const usedWater = (b.water_new || 0) - (b.water_old || 0);
  const paid = b.paid
    ? '<span class="chip chip-paid">Đã thu</span>'
    : '<span class="chip chip-unpaid">Chưa thu</span>';
  const delBtn = isAdmin() ? `<button class="btn btn-danger btn-sm btn-b-del" data-id="${b.id}">🗑️</button>` : "";
  return `<tr>
    <td><b>${b.month}</b></td><td>${b.tenant_name || "—"}</td><td>${b.room_name || "—"}</td>
    <td>${usedElec} <span class="muted">(${fmtNum(b.elec_amount)}đ)</span></td>
    <td>${usedWater} <span class="muted">(${fmtNum(b.water_amount)}đ)</span></td>
    <td><b>${fmtNum(b.total)}đ</b></td><td>${paid}</td>
    <td><div class="row-actions">
      <button class="btn btn-primary btn-sm btn-b-edit" data-id="${b.id}">✏️</button>
      <button class="btn btn-ghost btn-sm btn-b-paid" data-id="${b.id}" data-paid="${!b.paid}">${b.paid ? "↩ Chưa thu" : "✓ Đã thu"}</button>
      ${delBtn}
    </div></td>
  </tr>`;
}

async function loadBills() {
  const params = new URLSearchParams();
  const month = document.getElementById("bill-month").value;
  const tenant = document.getElementById("bill-tenant").value;
  if (month) params.set("month", month);
  if (tenant) params.set("tenant_id", tenant);
  try {
    billsCache = await api(`/api/tenants/bills?${params}`, { headers: authHeaders() });
    document.getElementById("bill-empty").classList.toggle("hidden", billsCache.length > 0);
    const tbody = document.getElementById("bill-tbody");
    tbody.innerHTML = billsCache.map(billRow).join("");
    tbody.querySelectorAll(".btn-b-edit").forEach((b) => b.addEventListener("click", () => openBillForm(b.dataset.id)));
    tbody.querySelectorAll(".btn-b-paid").forEach((b) => b.addEventListener("click", () => setBillPaid(b.dataset.id, b.dataset.paid === "true")));
    tbody.querySelectorAll(".btn-b-del").forEach((b) => b.addEventListener("click", () => deleteBill(b.dataset.id)));
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
}

function closeBillModal() {
  document.getElementById("bill-modal").classList.remove("open");
  document.body.style.overflow = "";
}

async function openBillForm(id = "") {
  document.getElementById("bill-form").reset();
  document.getElementById("b-id").value = "";
  ["b-elec-old", "b-elec-new", "b-water-old", "b-water-new", "b-other"].forEach((x) => { document.getElementById(x).value = 0; });
  await loadTenantOptions();
  document.getElementById("bill-form-title").textContent = id ? "Sửa hóa đơn điện nước" : "Thêm hóa đơn điện nước";
  const b = billsCache.find((x) => String(x.id) === String(id));
  if (b) {
    document.getElementById("b-id").value = b.id;
    document.getElementById("b-tenant").value = b.tenant_id;
    document.getElementById("b-month").value = b.month;
    document.getElementById("b-month").disabled = true;
    document.getElementById("b-tenant").disabled = true;
    document.getElementById("b-elec-old").value = b.elec_old;
    document.getElementById("b-elec-new").value = b.elec_new;
    document.getElementById("b-water-old").value = b.water_old;
    document.getElementById("b-water-new").value = b.water_new;
    document.getElementById("b-other").value = b.other_fee;
    document.getElementById("b-note").value = b.note || "";
  } else {
    document.getElementById("b-month").disabled = false;
    document.getElementById("b-tenant").disabled = false;
    document.getElementById("b-month").value = new Date().toISOString().slice(0, 7);
  }
  document.getElementById("bill-modal").classList.add("open");
  document.body.style.overflow = "hidden";
}

document.getElementById("bill-month").addEventListener("change", loadBills);
document.getElementById("bill-tenant").addEventListener("change", loadBills);
document.getElementById("btn-add-bill").addEventListener("click", () => openBillForm());
document.getElementById("bill-close").addEventListener("click", closeBillModal);
document.getElementById("bill-cancel").addEventListener("click", closeBillModal);
// (Bỏ đóng modal khi bấm nền tối - tránh mất dữ liệu đang sửa, xem ghi chú formModal)

document.getElementById("bill-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("b-id").value;
  const payload = {
    tenant_id: Number(document.getElementById("b-tenant").value),
    month: document.getElementById("b-month").value.trim(),
    elec_old: Number(document.getElementById("b-elec-old").value) || 0,
    elec_new: Number(document.getElementById("b-elec-new").value) || 0,
    water_old: Number(document.getElementById("b-water-old").value) || 0,
    water_new: Number(document.getElementById("b-water-new").value) || 0,
    other_fee: Number(document.getElementById("b-other").value) || 0,
    note: document.getElementById("b-note").value.trim(),
  };
  if (!payload.tenant_id || !/^\d{4}-\d{2}$/.test(payload.month)) {
    return toast("Vui lòng chọn khách và nhập tháng dạng YYYY-MM.", "error");
  }
  if (id) delete payload.tenant_id, delete payload.month;
  try {
    await api(id ? `/api/tenants/bills/${id}` : "/api/tenants/bills", {
      method: id ? "PUT" : "POST", headers: authHeaders(), body: JSON.stringify(payload),
    });
    toast(id ? "Đã cập nhật hóa đơn." : "Đã tạo hóa đơn.", "success");
    closeBillModal(); await loadBillFilters(); loadBills();
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
});

async function setBillPaid(id, paid) {
  try {
    await api(`/api/tenants/bills/${id}/paid`, {
      method: "PUT", headers: authHeaders(), body: JSON.stringify({ paid }),
    });
    toast(paid ? "Đã ghi nhận thu tiền." : "Đã chuyển về chưa thu.", "success"); loadBills();
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
}

async function deleteBill(id) {
  if (!confirm("Xóa hóa đơn này?")) return;
  try {
    await api(`/api/tenants/bills/${id}`, { method: "DELETE", headers: authHeaders() });
    toast("Đã xóa hóa đơn.", "success"); await loadBillFilters(); loadBills();
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
}

/* ================================================================
 * HỢP ĐỒNG
 * ================================================================ */
let contractsCache = [];

function contractRow(c) {
  const delBtn = isAdmin() ? `<button class="btn btn-danger btn-sm btn-c-del" data-id="${c.id}">🗑️</button>` : "";
  return `<tr>
    <td><b>${c.tenant_name || "—"}</b></td><td>${c.room_name || "—"}</td>
    <td>${fmtDate(c.start_date)}</td><td>${fmtDate(c.end_date)}</td>
    <td>${fmtNum(c.deposit)}đ</td><td>${fmtNum(c.monthly_rent)}đ</td>
    <td><div class="row-actions"><button class="btn btn-primary btn-sm btn-c-edit" data-id="${c.id}">✏️ Sửa</button>${delBtn}</div></td>
  </tr>`;
}

async function loadContracts() {
  try {
    contractsCache = await api("/api/tenants/contracts", { headers: authHeaders() });
    document.getElementById("contract-empty").classList.toggle("hidden", contractsCache.length > 0);
    const tbody = document.getElementById("contract-tbody");
    tbody.innerHTML = contractsCache.map(contractRow).join("");
    tbody.querySelectorAll(".btn-c-edit").forEach((b) => b.addEventListener("click", () => openContractForm(b.dataset.id)));
    tbody.querySelectorAll(".btn-c-del").forEach((b) => b.addEventListener("click", () => deleteContract(b.dataset.id)));
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
}

function closeContractModal() {
  document.getElementById("contract-modal").classList.remove("open");
  document.body.style.overflow = "";
}

async function openContractForm(id = "") {
  document.getElementById("contract-form").reset();
  document.getElementById("ct-id").value = "";
  document.getElementById("ct-deposit").value = 0;
  document.getElementById("ct-rent").value = 0;
  await loadTenantOptions();
  document.getElementById("contract-form-title").textContent = id ? "Sửa hợp đồng" : "Thêm hợp đồng";
  const c = contractsCache.find((x) => String(x.id) === String(id));
  if (c) {
    document.getElementById("ct-id").value = c.id;
    document.getElementById("ct-tenant").value = c.tenant_id;
    document.getElementById("ct-tenant").disabled = true;
    document.getElementById("ct-start").value = c.start_date || "";
    document.getElementById("ct-end").value = c.end_date || "";
    document.getElementById("ct-deposit").value = c.deposit;
    document.getElementById("ct-rent").value = c.monthly_rent;
    document.getElementById("ct-note").value = c.note || "";
  } else {
    document.getElementById("ct-tenant").disabled = false;
    document.getElementById("ct-start").value = new Date().toISOString().slice(0, 10);
  }
  document.getElementById("contract-modal").classList.add("open");
  document.body.style.overflow = "hidden";
}

document.getElementById("btn-add-contract").addEventListener("click", () => openContractForm());
document.getElementById("contract-close").addEventListener("click", closeContractModal);
document.getElementById("contract-cancel").addEventListener("click", closeContractModal);
// (Bỏ đóng modal khi bấm nền tối - tránh mất dữ liệu đang sửa, xem ghi chú formModal)

document.getElementById("contract-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("ct-id").value;
  const payload = {
    tenant_id: Number(document.getElementById("ct-tenant").value),
    start_date: document.getElementById("ct-start").value || null,
    end_date: document.getElementById("ct-end").value || null,
    deposit: Number(document.getElementById("ct-deposit").value) || 0,
    monthly_rent: Number(document.getElementById("ct-rent").value) || 0,
    note: document.getElementById("ct-note").value.trim(),
  };
  if (!payload.tenant_id) return toast("Vui lòng chọn khách trọ.", "error");
  if (id) delete payload.tenant_id;
  try {
    await api(id ? `/api/tenants/contracts/${id}` : "/api/tenants/contracts", {
      method: id ? "PUT" : "POST", headers: authHeaders(), body: JSON.stringify(payload),
    });
    toast(id ? "Đã cập nhật hợp đồng." : "Đã tạo hợp đồng.", "success");
    closeContractModal(); loadContracts();
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
});

async function deleteContract(id) {
  if (!confirm("Xóa hợp đồng này?")) return;
  try {
    await api(`/api/tenants/contracts/${id}`, { method: "DELETE", headers: authHeaders() });
    toast("Đã xóa hợp đồng.", "success"); loadContracts();
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
}

/* ================================================================
 * TIN NHẮN LIÊN HỆ
 * ================================================================ */
function messageCard(m) {
  const digits = (m.phone || "").replace(/[^+\d]/g, "");
  const dateText = m.created_at ? new Date(m.created_at).toLocaleString("vi-VN") : "";
  const delBtn = isAdmin() ? `<button class="btn btn-danger btn-sm btn-m-del" data-id="${m.id}">🗑️ Xóa</button>` : "";
  return `<div class="message-card ${m.is_read ? "" : "unread"}">
    <div class="message-head"><div><b>${escHTML(m.name)}</b> ${m.is_read ? "" : '<span class="badge-pill badge-blue">Mới</span>'}</div><span class="muted">${escHTML(dateText)}</span></div>
    <div class="message-meta">📞 <a href="tel:${digits}">${escHTML(m.phone)}</a>${m.email ? ` · ✉️ ${escHTML(m.email)}` : ""}${m.room_name ? ` · 🏠 ${escHTML(m.room_name)}` : ""}</div>
    <p class="message-body">${escHTML(m.message || "(Không có nội dung)")}</p>
    <div class="row-actions">
      <a class="btn btn-primary btn-sm" href="tel:${digits}">📞 Gọi</a>
      <a class="btn btn-ghost btn-sm" href="https://zalo.me/${digits}" target="_blank" rel="noopener">💬 Zalo</a>
      ${m.is_read ? "" : `<button class="btn btn-ghost btn-sm btn-m-read" data-id="${m.id}">✓ Đã đọc</button>`}
      ${delBtn}
    </div>
  </div>`;
}

async function loadMessages() {
  try {
    const list = await api("/api/contact", { headers: authHeaders() });
    document.getElementById("message-empty").classList.toggle("hidden", list.length > 0);
    const box = document.getElementById("message-list");
    box.innerHTML = list.map(messageCard).join("");
    box.querySelectorAll(".btn-m-read").forEach((b) => b.addEventListener("click", () => markMessageRead(b.dataset.id)));
    box.querySelectorAll(".btn-m-del").forEach((b) => b.addEventListener("click", () => deleteMessage(b.dataset.id)));
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
}

async function markMessageRead(id) {
  try {
    await api(`/api/contact/${id}/read`, { method: "PUT", headers: authHeaders() }); loadMessages();
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
}

async function deleteMessage(id) {
  if (!confirm("Xóa tin nhắn này?")) return;
  try {
    await api(`/api/contact/${id}`, { method: "DELETE", headers: authHeaders() });
    toast("Đã xóa tin nhắn.", "success"); loadMessages();
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
}
document.getElementById("btn-reload-messages").addEventListener("click", loadMessages);

/* ================================================================
 * TÀI KHOẢN & PHÂN QUYỀN
 * ================================================================ */
function adminRow(a) {
  const self = a.username === localStorage.getItem(USERNAME_KEY);
  return `<tr><td>${a.id}</td><td><b>${a.username}</b>${self ? ' <span class="muted">(bạn)</span>' : ""}</td>
    <td>${self ? `<span class="badge-pill badge-blue">${ROLE_LABEL[a.role]}</span>` : `<select class="form-control admin-role" data-id="${a.id}"><option value="staff" ${a.role === "staff" ? "selected" : ""}>Nhân viên</option><option value="admin" ${a.role === "admin" ? "selected" : ""}>Quản trị viên</option></select>`}</td>
    <td>${self ? "—" : `<button class="btn btn-danger btn-sm btn-a-del" data-id="${a.id}">🗑️ Xóa</button>`}</td></tr>`;
}

async function loadAdmins() {
  if (!isAdmin()) return;
  try {
    const list = await api("/api/auth/admins", { headers: authHeaders() });
    const tbody = document.getElementById("admin-tbody");
    tbody.innerHTML = list.map(adminRow).join("");
    tbody.querySelectorAll(".admin-role").forEach((s) => s.addEventListener("change", () => changeAdminRole(s.dataset.id, s.value)));
    tbody.querySelectorAll(".btn-a-del").forEach((b) => b.addEventListener("click", () => deleteAdmin(b.dataset.id)));
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
}

document.getElementById("admin-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    username: document.getElementById("a-username").value.trim(),
    password: document.getElementById("a-password").value,
    role: document.getElementById("a-role").value,
  };
  try {
    await api("/api/auth/admins", { method: "POST", headers: authHeaders(), body: JSON.stringify(payload) });
    toast("Đã tạo tài khoản.", "success"); e.target.reset(); loadAdmins();
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
});

async function changeAdminRole(id, role) {
  try {
    await api(`/api/auth/admins/${id}/role`, {
      method: "PUT", headers: authHeaders(), body: JSON.stringify({ role }),
    });
    toast("Đã đổi vai trò.", "success"); loadAdmins();
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); loadAdmins(); }
}

async function deleteAdmin(id) {
  if (!confirm("Xóa tài khoản này?")) return;
  try {
    await api(`/api/auth/admins/${id}`, { method: "DELETE", headers: authHeaders() });
    toast("Đã xóa tài khoản.", "success"); loadAdmins();
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
}

document.getElementById("password-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/auth/change-password", {
      method: "POST", headers: authHeaders(), body: JSON.stringify({
        old_password: document.getElementById("p-old").value,
        new_password: document.getElementById("p-new").value,
      }),
    });
    toast("Đã đổi mật khẩu. Hãy dùng mật khẩu mới ở lần đăng nhập sau.", "success"); e.target.reset();
  } catch (err) { if (err.message !== "401") toast(err.message, "error"); }
});

document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  closeTenantModal(); closeBillModal(); closeContractModal();
});