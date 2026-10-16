// Reusable UI components

import { escapeHtml, formatDate, toast } from "./utils.js";
import { addBookmark, removeBookmark, recordInteraction } from "./api.js";

// ── Skeleton loading ─────────────────────────────────────────────────────────
export function renderSkeletons(container, count = 6) {
  container.innerHTML = Array.from({ length: count }, () => `
    <div class="news-card news-card--skeleton" aria-hidden="true">
      <div class="skeleton skeleton-meta"></div>
      <div class="skeleton skeleton-title"></div>
      <div class="skeleton skeleton-title" style="width:70%"></div>
      <div class="skeleton skeleton-body"></div>
      <div class="skeleton skeleton-body" style="width:85%"></div>
    </div>
  `).join("");
}

// ── Article card ─────────────────────────────────────────────────────────────
export function articleCardHTML(article, { bookmarked = false } = {}) {
  const imgHtml = article.image_url
    ? `<div class="card-image"><img src="${escapeHtml(article.image_url)}" alt="" loading="lazy" onerror="this.parentElement.remove()"></div>`
    : "";

  const categories = (article.categories || []).slice(0, 2);
  const pills = categories
    .map((c) => `<span class="domain-pill">${escapeHtml(c)}</span>`)
    .join("");

  return `
    <article class="news-card" data-id="${escapeHtml(article.id)}" data-url="${escapeHtml(article.url)}">
      ${imgHtml}
      <div class="card-inner">
        <div class="card-meta">
          <div class="card-pills">${pills || `<span class="domain-pill">${escapeHtml(article.provider || "news")}</span>`}</div>
          <span class="card-date">${formatDate(article.published_at)}</span>
        </div>
        <h3 class="card-title">${escapeHtml(article.title)}</h3>
        <p class="card-description">${escapeHtml(article.description || "Open the original source for the full story.")}</p>
        <div class="card-bottom">
          <span class="card-source" title="${escapeHtml(article.source || "")}">${escapeHtml(article.source || "Source")}</span>
          <div class="card-actions">
            <button class="card-btn card-btn--bookmark ${bookmarked ? "card-btn--active" : ""}"
              data-action="bookmark" data-id="${escapeHtml(article.id)}"
              title="${bookmarked ? "Remove bookmark" : "Bookmark"}"
              aria-label="${bookmarked ? "Remove bookmark" : "Bookmark article"}">
              <i data-lucide="${bookmarked ? "bookmark-check" : "bookmark"}" style="width:16px;height:16px"></i>
            </button>
            <button class="card-btn card-btn--like" data-action="like" data-id="${escapeHtml(article.id)}"
              title="Like" aria-label="Like article"><i data-lucide="heart" style="width:16px;height:16px"></i></button>
            <button class="card-btn card-btn--menu" data-action="menu" data-id="${escapeHtml(article.id)}"
              title="More options" aria-label="More options"><i data-lucide="more-horizontal" style="width:16px;height:16px"></i></button>
            <a class="card-read" href="${escapeHtml(article.url)}" target="_blank" rel="noopener noreferrer"
              data-action="read">Read ↗</a>
          </div>
        </div>
      </div>
    </article>
  `;
}

// ── Article card context menu ────────────────────────────────────────────────
function showArticleMenu(article, anchor) {
  document.querySelector(".article-menu")?.remove();
  const menu = document.createElement("div");
  menu.className = "article-menu";
  menu.innerHTML = `
    <button data-action="more_like_this">More like this</button>
    <button data-action="less_like_this">Less like this</button>
    <button data-action="hide">Hide this story</button>
    <button data-action="share">Share</button>
  `;
  document.body.appendChild(menu);
  const rect = anchor.getBoundingClientRect();
  menu.style.top = `${rect.bottom + scrollY + 4}px`;
  menu.style.left = `${Math.min(rect.left, innerWidth - 180)}px`;

  menu.addEventListener("click", (e) => {
    const action = e.target.dataset.action;
    if (!action) return;
    menu.remove();
    _handleMenuAction(article, action);
  });

  const dismiss = (e) => {
    if (!menu.contains(e.target)) { menu.remove(); document.removeEventListener("click", dismiss); }
  };
  setTimeout(() => document.addEventListener("click", dismiss), 0);
}

async function _handleMenuAction(article, action) {
  const topic = (article.categories || [])[0] || null;
  try {
    await recordInteraction({
      article_id: article.id,
      article_url: article.url,
      event_type: action,
      topic_slug: topic,
      provider: article.provider || null,
      metadata: {},
    });
  } catch {}

  if (action === "hide") {
    document.querySelector(`[data-id="${article.id}"]`)?.closest(".news-card")?.remove();
    toast("Story hidden from your feed", "success");
  } else if (action === "more_like_this") {
    toast("We'll show you more stories like this", "success");
  } else if (action === "less_like_this") {
    toast("We'll show you fewer stories like this", "info");
  } else if (action === "share") {
    try {
      await navigator.share({ title: article.title, url: article.url });
    } catch {
      navigator.clipboard?.writeText(article.url);
      toast("Link copied to clipboard", "success");
    }
  }
}

// ── Wire up card interactions ─────────────────────────────────────────────────
export function wireCardInteractions(container, articles, bookmarkSet) {
  container.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const action = btn.dataset.action;
    const id = btn.dataset.id;
    const article = articles.find((a) => a.id === id);
    if (!article) return;

    if (action === "read") {
      try {
        await recordInteraction({
          article_id: article.id,
          article_url: article.url,
          event_type: "click",
          topic_slug: (article.categories || [])[0] || null,
          provider: article.provider || null,
          metadata: {},
        });
      } catch {}
      return; // let the link navigate normally
    }

    if (action === "bookmark") {
      e.preventDefault();
      try {
        if (bookmarkSet.has(article.id)) {
          await removeBookmark(article.id);
          bookmarkSet.delete(article.id);
          btn.innerHTML = `<i data-lucide="bookmark" style="width:16px;height:16px"></i>`;
          window.lucide?.createIcons();
          btn.classList.remove("card-btn--active");
          btn.title = "Bookmark";
          toast("Bookmark removed", "info");
        } else {
          await addBookmark(article);
          bookmarkSet.add(article.id);
          btn.innerHTML = `<i data-lucide="bookmark-check" style="width:16px;height:16px"></i>`;
          window.lucide?.createIcons();
          btn.classList.add("card-btn--active");
          btn.title = "Remove bookmark";
          toast("Article bookmarked", "success");
        }
      } catch (err) {
        toast("Sign in to bookmark articles", "error");
      }
      return;
    }

    if (action === "like") {
      e.preventDefault();
      btn.classList.toggle("card-btn--active");
      try {
        await recordInteraction({
          article_id: article.id,
          article_url: article.url,
          event_type: btn.classList.contains("card-btn--active") ? "like" : "dislike",
          topic_slug: (article.categories || [])[0] || null,
          provider: article.provider || null,
          metadata: {},
        });
      } catch {}
      return;
    }

    if (action === "menu") {
      e.preventDefault();
      showArticleMenu(article, btn);
    }
  });
}

// ── Render a full grid of articles ───────────────────────────────────────────
export function renderArticleGrid(container, articles, bookmarkSet = new Set()) {
  if (!articles.length) {
    container.innerHTML = `<div class="empty-state"><p>No articles found. Try changing your interests or check back later.</p></div>`;
    return;
  }
  container.innerHTML = articles
    .map((a) => articleCardHTML(a, { bookmarked: bookmarkSet.has(a.id) }))
    .join("");
  wireCardInteractions(container, articles, bookmarkSet);
  window.lucide?.createIcons();
}

// ── Intersection Observer for impressions ────────────────────────────────────
export function observeImpressions(container, articles, onImpression) {
  if (!("IntersectionObserver" in window)) return;
  const seen = new Set();
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const id = entry.target.dataset.id;
        if (!id || seen.has(id)) return;
        seen.add(id);
        const article = articles.find((a) => a.id === id);
        if (article) onImpression(article);
        io.unobserve(entry.target);
      });
    },
    { threshold: 0.5 }
  );
  container.querySelectorAll(".news-card[data-id]").forEach((el) => io.observe(el));
}

// ── Password strength meter ──────────────────────────────────────────────────
export function passwordStrength(password) {
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  return score; // 0-5
}

export function renderPasswordStrength(score) {
  const labels = ["", "Weak", "Fair", "Good", "Strong", "Very strong"];
  const classes = ["", "weak", "fair", "good", "strong", "very-strong"];
  return { label: labels[score] || "", cls: classes[score] || "" };
}
