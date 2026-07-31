/* MINT service worker.
 *
 * Exists so the blog installs as an app and survives a dropped connection, not
 * to build an offline reader.
 *
 * THE VERSION IS STAMPED AT BUILD TIME, and that is the whole point of this
 * file being a template rather than a static asset. It used to be the literal
 * string "mint-v1", which never changed, so the caches it created were never
 * evicted.
 *
 * That mattered because the comment underneath it was wrong: it claimed the
 * cached assets were "fingerprinted or effectively immutable". They are not.
 * /css/mint.css keeps its name forever, and so does a photograph that gets
 * reprocessed in place. Cache-first on a file whose name never changes is
 * cache-forever. On 2026-07-30 that served a stale stylesheet and a sideways
 * photograph for hours after both had been fixed and deployed, through repeated
 * hard refreshes, because the worker answered before the network was asked.
 *
 * Strategy now:
 *   - Pages: network first, cache as fallback.
 *   - CSS, JS, images: stale-while-revalidate. The cached copy is served
 *     immediately, and the network copy replaces it for next time. Still
 *     instant, but at most one load behind instead of permanently stuck.
 *   - Fonts: cache first. Those genuinely are immutable.
 *   - /admin/ and the feeds: never cached.
 */
const VERSION = "mint-{{ now.Unix }}";
const SHELL = ["/", "/css/mint.css", "/css/fonts.css", "/js/mint.js", "/icon-192.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(VERSION)
      .then((c) => c.addAll(SHELL).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
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

  // Fonts never change under the same name; everything else might.
  const immutable = /\.(woff2?|ttf|otf)$/i.test(url.pathname);

  event.respondWith(
    caches.match(req).then((hit) => {
      const network = fetch(req)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(VERSION).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => hit);
      if (immutable && hit) return hit;
      return hit || network;      // serve cache now, refresh it behind the scenes
    })
  );
});
