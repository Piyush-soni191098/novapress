const API_BASE = (window.NEWS_CONFIG?.API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const $ = (id) => document.getElementById(id);
let allArticles = [];
let currentView = "latest";
let lastParams = { domains: "tech,llm", location: "", query: "" };
const BOOKMARK_KEY = "signal-news-bookmarks-v1";

function bookmarks() {
  try { return JSON.parse(localStorage.getItem(BOOKMARK_KEY) || "[]"); }
  catch { return []; }
}
function saveBookmarks(items) { localStorage.setItem(BOOKMARK_KEY, JSON.stringify(items)); updateSavedCount(); }
function updateSavedCount() { $("savedCount").textContent = bookmarks().length; }
function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function formatDate(value) {
  if (!value) return "RECENT";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "RECENT";
  return date.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}
function checkedDomains() {
  return [...document.querySelectorAll('.topic input:checked')].map((el) => el.value);
}
function currentArticles() {
  const savedIds = new Set(bookmarks().map((item) => item.id));
  let list = currentView === "saved" ? bookmarks() : allArticles;
  const term = $("searchInput").value.trim().toLowerCase();
  if (term) list = list.filter((item) => `${item.title} ${item.description} ${item.source} ${item.domain}`.toLowerCase().includes(term));
  return list;
}
function render() {
  const list = currentArticles();
  $("storyCount").textContent = list.length;
  $("newsGrid").innerHTML = "";
  if (!list.length) {
    $("newsGrid").innerHTML = `<div class="empty">${currentView === "saved" ? "No saved stories yet. Tap the bookmark icon on a story to keep it here." : "No stories matched. Try another topic, remove a search term, or refresh in a moment."}</div>`;
    return;
  }
  const savedIds = new Set(bookmarks().map((item) => item.id));
  $("newsGrid").innerHTML = list.map((item) => `
    <article class="news-card">
      <div class="card-meta"><span class="domain-pill">${escapeHtml(item.domain || "news")}</span><span>${escapeHtml(formatDate(item.published_at))}</span></div>
      <h3>${escapeHtml(item.title)}</h3>
      <p>${escapeHtml(item.description || "Open the original source for the full story.")}</p>
      <div class="card-bottom">
        <span class="card-source" title="${escapeHtml(item.source || "")}">${escapeHtml(item.source || "Original source")}</span>
        <span class="card-actions">
          <button class="save-btn" data-save="${encodeURIComponent(item.id)}" title="${savedIds.has(item.id) ? "Remove bookmark" : "Save story"}" aria-label="${savedIds.has(item.id) ? "Remove bookmark" : "Save story"}"><i data-lucide="${savedIds.has(item.id) ? "bookmark-check" : "bookmark"}" style="width:16px;height:16px"></i></button>
          <a class="read-link" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">Read ↗</a>
        </span>
      </div>
    </article>`).join("");
  $("newsGrid").querySelectorAll("[data-save]").forEach((button) => {
    button.addEventListener("click", () => toggleBookmark(decodeURIComponent(button.dataset.save)));
  });
  window.lucide?.createIcons();
}
function toggleBookmark(id) {
  const item = allArticles.find((article) => article.id === id) || bookmarks().find((article) => article.id === id);
  if (!item) return;
  const saved = bookmarks();
  const exists = saved.some((article) => article.id === id);
  saveBookmarks(exists ? saved.filter((article) => article.id !== id) : [item, ...saved]);
  render();
}
async function loadNews() {
  const domains = checkedDomains();
  if (!domains.length) {
    $("status").textContent = "Select at least one news domain.";
    return;
  }
  lastParams = { domains: domains.join(","), location: $("locationInput").value.trim(), query: $("searchInput").value.trim() };
  $("status").textContent = "Fetching stories from selected sources…";
  $("refreshBtn").disabled = true;
  $("applyBtn").disabled = true;
  const params = new URLSearchParams({ ...lastParams, limit: "45" });
  try {
    const response = await fetch(`${API_BASE}/api/news?${params.toString()}`);
    if (!response.ok) throw new Error(`API returned ${response.status}`);
    const data = await response.json();
    allArticles = data.articles || [];
    $("status").textContent = allArticles.length ? `Updated ${new Date(data.generated_at).toLocaleTimeString()} · Source links open the original stories.` : "No stories returned. Try again later or change your filters.";
    render();
  } catch (error) {
    $("status").textContent = `Could not reach the news API. Check that the FastAPI backend is running and API_BASE_URL is correct. (${error.message})`;
    $("newsGrid").innerHTML = `<div class="empty">The feed is unavailable right now. When deploying, set frontend/config.js to your backend URL and allow the frontend origin in FRONTEND_ORIGINS.</div>`;
  } finally {
    $("refreshBtn").disabled = false;
    $("applyBtn").disabled = false;
  }
}
$("applyBtn").addEventListener("click", loadNews);
$("refreshBtn").addEventListener("click", loadNews);
$("searchInput").addEventListener("keydown", (event) => { if (event.key === "Enter") loadNews(); });
$("searchInput").addEventListener("input", () => render());
$("locationInput").addEventListener("keydown", (event) => { if (event.key === "Enter") loadNews(); });
document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => {
  currentView = tab.dataset.view;
  document.querySelectorAll(".tab").forEach((item) => item.classList.toggle("active", item === tab));
  render();
}));
$("notifyBtn").addEventListener("click", async () => {
  if (!("Notification" in window)) {
    $("status").textContent = "Notifications are not supported by this browser.";
    return;
  }
  const permission = await Notification.requestPermission();
  if (permission === "granted") {
    new Notification("NovaPress notifications enabled", { body: "This demo can notify while the app is open. Remote push is a Phase 2 feature." });
    $("status").textContent = "Permission granted. This is a local demo notification, not remote push.";
  } else {
    $("status").textContent = "Notifications were not enabled. You can change this in your browser settings.";
  }
});
updateSavedCount();
if ("serviceWorker" in navigator && location.protocol !== "file:") {
  window.addEventListener("load", () => navigator.serviceWorker.register("./sw.js").catch((error) => console.warn("Service worker registration failed", error)));
}
loadNews();
