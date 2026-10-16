// Shared utilities

export function escapeHtml(value = "") {
  return String(value).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

export function formatDate(value) {
  if (!value) return "RECENT";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "RECENT";
  const now = new Date();
  const diffH = (now - date) / 3600000;
  if (diffH < 1) return `${Math.round(diffH * 60)}m ago`;
  if (diffH < 24) return `${Math.round(diffH)}h ago`;
  return date.toLocaleString(undefined, { month: "short", day: "numeric" });
}

export function toast(message, type = "info", duration = 3500) {
  const existing = document.querySelector(".toast-container");
  const container = existing || (() => {
    const c = document.createElement("div");
    c.className = "toast-container";
    document.body.appendChild(c);
    return c;
  })();

  const el = document.createElement("div");
  el.className = `toast toast--${type}`;
  el.textContent = message;
  container.appendChild(el);
  requestAnimationFrame(() => el.classList.add("toast--visible"));

  setTimeout(() => {
    el.classList.remove("toast--visible");
    setTimeout(() => el.remove(), 300);
  }, duration);
}

export function setLoading(btn, loading, originalText) {
  if (!btn) return;
  btn.disabled = loading;
  btn.textContent = loading ? "Loading…" : originalText;
}

export function debounce(fn, ms = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

export function getApiBase() {
  return (window.NEWS_CONFIG?.API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
}

export function getSupabaseConfig() {
  return {
    url: window.NEWS_CONFIG?.SUPABASE_URL || "",
    anonKey: window.NEWS_CONFIG?.SUPABASE_ANON_KEY || "",
  };
}
