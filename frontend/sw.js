// Service worker — v5.0 (NovaPress local Lucide + SVG logo)
// Caches static assets only. Never caches authenticated API responses.
const CACHE_NAME = "novapress-static-v3";

const STATIC_ASSETS = [
  "./",
  "./index.html",
  "./login.html",
  "./register.html",
  "./styles.css",
  "./config.js",
  "./manifest.webmanifest",
  "./icons/icon.svg",
  "./logo.svg",
  "./js/lucide.min.js",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Never cache API or Supabase requests — these contain user-specific or auth data
  if (
    url.pathname.startsWith("/api/") ||
    url.hostname.includes("supabase.co") ||
    url.hostname.includes("supabase.io") ||
    event.request.headers.has("authorization")
  ) {
    event.respondWith(fetch(event.request));
    return;
  }

  // For navigation requests, try network then cache
  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request).catch(() =>
        caches.match(event.request).then((r) => r || caches.match("./index.html"))
      )
    );
    return;
  }

  // Static assets: cache-first
  event.respondWith(
    caches.match(event.request).then((cached) =>
      cached || fetch(event.request).then((response) => {
        if (response.ok && event.request.method === "GET") {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
    )
  );
});
