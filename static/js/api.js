// Thin fetch wrapper: attaches the JWT, parses the {success,message,data} envelope,
// and redirects to /login on 401.
const API = {
  base: "/api",

  token() {
    return localStorage.getItem("access_token");
  },

  async request(path, { method = "GET", body = null } = {}) {
    const headers = { "Content-Type": "application/json" };
    const token = this.token();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(this.base + path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : null,
    });

    if (res.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
      return null;
    }

    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(json.message || `Request failed (${res.status})`);
    }
    return json;
  },

  get(path) { return this.request(path); },
  post(path, body) { return this.request(path, { method: "POST", body }); },
  put(path, body) { return this.request(path, { method: "PUT", body }); },
  del(path) { return this.request(path, { method: "DELETE" }); },
};

function showToast(message, type = "success") {
  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

function requireAuth() {
  if (!API.token()) {
    window.location.href = "/login";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try { await API.post("/auth/logout"); } catch (e) { /* ignore */ }
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    });
  }

  const userEl = document.getElementById("current-user");
  if (userEl && API.token()) {
    API.get("/auth/me").then((res) => {
      if (res && res.data) userEl.textContent = `${res.data.name} (${res.data.role})`;
    }).catch(() => {});
  }

  // Highlight the current page in the sidebar.
  const currentPath = window.location.pathname;
  document.querySelectorAll("#sidebar-nav a").forEach((link) => {
    const linkPath = link.getAttribute("data-path");
    if (linkPath && (currentPath === linkPath || currentPath.startsWith(linkPath + "/"))) {
      link.classList.add("active");
    }
  });

  // Mobile sidebar toggle.
  const menuToggle = document.getElementById("menu-toggle");
  if (menuToggle) {
    menuToggle.addEventListener("click", () => {
      document.querySelector(".sidebar").classList.toggle("open");
    });
  }

  // Unread notification count badge.
  const unreadBadge = document.getElementById("unread-badge");
  if (unreadBadge && API.token()) {
    API.get("/notifications").then((res) => {
      const count = res && res.data ? res.data.unread_count : 0;
      if (count > 0) {
        unreadBadge.textContent = count;
        unreadBadge.style.display = "inline-block";
      }
    }).catch(() => {});
  }
});
