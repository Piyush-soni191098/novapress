// API client — all calls to the FastAPI backend

import { getToken } from "./auth.js";
import { getApiBase } from "./utils.js";

async function _request(path, options = {}) {
  const base = getApiBase();
  const token = await getToken();
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${base}${path}`, { ...options, headers });
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try { detail = (await response.json()).detail || detail; } catch {}
    throw new Error(detail);
  }
  return response.json();
}

// ── Categories ────────────────────────────────────────────────────────────────
export async function fetchCategories(q = "") {
  const qs = q ? `?q=${encodeURIComponent(q)}` : "";
  return _request(`/api/categories${qs}`);
}

// ── News ──────────────────────────────────────────────────────────────────────
export async function fetchNews({ categories = "technology", query = "", language = "en", location = "", limit = 30 } = {}) {
  const p = new URLSearchParams({ categories, language, location, limit });
  if (query) p.set("query", query);
  return _request(`/api/news?${p}`);
}

export async function searchNews({ q, language = "en", location = "", limit = 30 }) {
  const p = new URLSearchParams({ q, language, location, limit });
  return _request(`/api/news/search?${p}`);
}

export async function fetchTopicNews({ topic, page = 1, pageSize = 20, language = "en", location = "" }) {
  const p = new URLSearchParams({ page, page_size: pageSize, language, location });
  return _request(`/api/topics/${encodeURIComponent(topic)}/news?${p}`);
}

// ── Personalized Feed ─────────────────────────────────────────────────────────
export async function fetchFeedForYou({ page = 1, pageSize = 20, language = "en", location = "" } = {}) {
  const p = new URLSearchParams({ page, page_size: pageSize, language, location });
  return _request(`/api/feed/for-you?${p}`);
}

export async function fetchFeedLatest({ page = 1, pageSize = 20, categories = "technology,world-news", language = "en", location = "" } = {}) {
  const p = new URLSearchParams({ page, page_size: pageSize, categories, language, location });
  return _request(`/api/feed/latest?${p}`);
}

export async function fetchFeedFollowing({ page = 1, pageSize = 20, language = "en", location = "" } = {}) {
  const p = new URLSearchParams({ page, page_size: pageSize, language, location });
  return _request(`/api/feed/following?${p}`);
}

// ── Bookmarks ─────────────────────────────────────────────────────────────────
export async function fetchBookmarks() {
  return _request("/api/bookmarks");
}

export async function addBookmark(article) {
  return _request("/api/bookmarks", {
    method: "POST",
    body: JSON.stringify({
      article_id: article.id,
      article_url: article.url,
      title: article.title,
      description: article.description || "",
      image_url: article.image_url || null,
      source: article.source || "",
      published_at: article.published_at || "",
      provider: article.provider || "",
      categories: article.categories || [],
    }),
  });
}

export async function removeBookmark(articleId) {
  return _request(`/api/bookmarks/${encodeURIComponent(articleId)}`, { method: "DELETE" });
}

// ── Interactions ──────────────────────────────────────────────────────────────
export async function recordInteraction(event) {
  return _request("/api/interactions", { method: "POST", body: JSON.stringify(event) });
}

export async function recordInteractionsBatch(events) {
  if (!events.length) return;
  return _request("/api/interactions/batch", {
    method: "POST",
    body: JSON.stringify({ events }),
  });
}

// ── Preferences ───────────────────────────────────────────────────────────────
export async function fetchPreferences() {
  return _request("/api/preferences");
}

export async function updatePreferences(prefs) {
  return _request("/api/preferences", { method: "PUT", body: JSON.stringify(prefs) });
}

export async function setInterests(interests) {
  return _request("/api/preferences/interests", {
    method: "POST",
    body: JSON.stringify(interests),
  });
}

export async function saveOnboarding(data) {
  return _request("/api/preferences/onboarding", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ── Insights ──────────────────────────────────────────────────────────────────
export async function fetchInsights() {
  return _request("/api/insights");
}

// ── Health ────────────────────────────────────────────────────────────────────
export async function fetchHealth() {
  return _request("/health");
}
