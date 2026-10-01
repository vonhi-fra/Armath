// Service worker: keeps Armath working offline (and so installable as an app).
// scripts/build_site.py fills in BUILD: this build's id, its files and the Pyodide files.
const BUILD = __BUILD__;
const CACHE = `armath-${BUILD.id}`;
const SCOPE = self.registration.scope;

// Pyodide and the wheel have a version or content hash in their URL, so a cached copy from an
// older build is still right: no need to download those again after an update.
function immutable(url) {
  return url.startsWith(BUILD.pyodideUrl) || url.startsWith(`${SCOPE}wheels/`);
}

async function fetchOk(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
  return response;
}

async function precache() {
  const cache = await caches.open(CACHE);
  const urls = [
    ...BUILD.files.map((path) => new URL(path, SCOPE).href),
    ...BUILD.pyodideFiles.map((name) => BUILD.pyodideUrl + name),
  ];
  await Promise.all(
    urls.map(async (url) => {
      const cached = immutable(url) ? await caches.match(url, { ignoreVary: true }) : undefined;
      await cache.put(url, cached ?? (await fetchOk(url, { cache: "no-cache" })));
    }),
  );
}

async function cacheFirst(request) {
  const cached = await caches.match(request, { ignoreVary: true });
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok) await (await caches.open(CACHE)).put(request, response.clone());
  return response;
}

// The page, scripts and styles come fresh from the network whenever it answers, so they always
// match each other (no timeout: a slow network must not mix cached and fresh files). "no-cache"
// skips the browser's HTTP cache too: GitHub Pages allows reusing files for 10 minutes, long
// enough to pair a new page with an old wheel.json. Offline, fetch fails at once and the cached
// copy is used. (A navigation request can't be copied with new options, hence the URL.)
async function networkFirst(request) {
  const cache = await caches.open(CACHE);
  try {
    const response = await fetch(request.url, { cache: "no-cache" });
    if (response.ok) await cache.put(request, response.clone());
    return response;
  } catch (error) {
    const cached =
      (await cache.match(request, { ignoreSearch: true })) ??
      (request.mode === "navigate" ? await cache.match(SCOPE) : undefined);
    if (cached) return cached;
    throw error;
  }
}

self.addEventListener("install", (event) => {
  event.waitUntil(precache().then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const names = await caches.keys();
      await Promise.all(
        names.filter((name) => name.startsWith("armath-") && name !== CACHE).map((name) => caches.delete(name)),
      );
      await self.clients.claim();
    })(),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  if (immutable(request.url)) {
    event.respondWith(cacheFirst(request));
  } else if (request.url.startsWith(SCOPE)) {
    event.respondWith(networkFirst(request));
  }
});
