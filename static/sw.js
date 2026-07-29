/* MINT service worker.
 *
 * Deliberately modest. This exists so the blog installs as an app and survives
 * a dropped connection, not to build an offline reader.
 *
 * Strategy:
 *   - Pages: network first, falling back to cache, then to a cached homepage.
 *     A blog changes; a stale post served from cache forever would be worse
 *     than a slow one.
 *   - Fonts, styles, scripts, images: cache first. They are fingerprinted or
 *     effectively immutable, and they are what make the site feel instant.
 *   - /admin/ is never cached. It is a login screen talking to GitHub, and a
 *     stale copy of it would be confusing and possibly broken.
 */
const VERSION = "mint-v1";
const SHELL = [
  "/",
  "/css/mint.css",
  "/css/fonts.css",
  "/assets/css/normalize.css",
  "/js/mint.js",
  "/icon-192.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  // Never cache the editor or the feeds.
  if (url.pathname.startsWith("/admin") || url.pathname.startsWith("/feed")) return;

  const isPage = req.mode === "navigate" || (req.headers.get("accept") || "").includes("text/html");

  if (isPage) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(VERSION).then((c) => c.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req).then((hit) => hit || caches.match("/")))
    );
    return;
  }

  event.respondWith(
    caches.match(req).then(
      (hit) =>
        hit ||
        fetch(req).then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(VERSION).then((c) => c.put(req, copy));
          }
          return res;
        })
    )
  );
});
