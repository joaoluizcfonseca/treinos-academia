/* Deixa o app abrir e funcionar sem internet.
 * Na primeira visita guarda tudo o que o app precisa. Depois, abre sempre do que está guardado (na hora,
 * com ou sem sinal) e, quando tem internet, baixa a versão nova por trás: ela entra na próxima vez que abrir.
 * Os dados do treino não passam por aqui: ficam no próprio celular (localStorage). */
const CACHE = "treinos-v1";
const CORE = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./fonts/fonts.css",
  "./fonts/archivo-latin.woff2",
  "./fonts/archivo-latin-ext.woff2",
  "./fonts/bricolage-latin.woff2",
  "./fonts/bricolage-latin-ext.woff2",
  "./fonts/kalam-400-latin.woff2",
  "./fonts/kalam-700-latin.woff2",
  "./fonts/kalam-400-latin-ext.woff2",
  "./fonts/kalam-700-latin-ext.woff2",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
  "./icons/apple-touch-icon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(CORE))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // fontes do Google e afins: o navegador resolve sozinho
  event.respondWith(
    caches.open(CACHE).then(async (cache) => {
      const key = req.mode === "navigate" ? "./index.html" : req;
      const saved = await cache.match(key, { ignoreSearch: true });
      const fresh = fetch(req)
        .then((res) => {
          if (res && res.ok) cache.put(key, res.clone());
          return res;
        })
        .catch(() => null);
      if (saved) {
        event.waitUntil(fresh);
        return saved;
      }
      return (await fresh) || Response.error();
    }),
  );
});
