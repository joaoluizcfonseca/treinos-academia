/* Deixa o app abrir sem internet e sempre na versão mais nova.
 * Abrir o app: com internet, ele busca a versão do site (sem passar pelo cache do navegador) e abre com ela.
 * Sem sinal, ou se a internet não responder em 1,5 segundo, abre na hora com a cópia guardada; se depois
 * chegar uma versão nova, ela fica guardada e o app é avisado, pra trocar sozinho sem atrapalhar.
 * Fontes, ícones e manifesto abrem do que está guardado e se atualizam por trás.
 * Os dados do treino não passam por aqui: ficam no próprio celular (localStorage). */
const CACHE = "treinos-v2";
const APP = new URL("./index.html", self.location).href;
const WAIT = 1500; // quanto a abertura espera pela internet antes de usar a cópia guardada
const CORE = [
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
      .then((cache) => cache.addAll(CORE.map((u) => new Request(u, { cache: "reload" }))))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const old = (await caches.keys()).filter((k) => k !== CACHE);
      await Promise.all(old.map((k) => caches.delete(k)));
      await self.clients.claim();
      // Veio de uma versão anterior deste arquivo: quem está com o app aberto recarrega já na versão nova.
      // Sem esperar a navegação terminar: ela passa por este service worker, que só atende depois de ativo.
      if (old.length) {
        for (const w of await self.clients.matchAll({ type: "window" })) {
          if (w.navigate) w.navigate(w.url).catch(() => {});
        }
      }
    })(),
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // fontes do Google e afins: o navegador resolve sozinho
  // abrir o app (a pasta ou o index.html); o endereço de qualquer outro arquivo mostra o arquivo
  if (req.mode === "navigate" && /\/(index\.html)?$/.test(url.pathname)) event.respondWith(openApp(event));
  else event.respondWith(fromCache(event));
});

// a versão do site, conferida com o servidor mesmo que o navegador tenha uma cópia recente
const latest = () =>
  fetch(APP, { cache: "no-cache" })
    .then((res) => (res.ok ? res : null))
    .catch(() => null);

async function openApp(event) {
  const cache = await caches.open(CACHE);
  const saved = await cache.match(APP);
  const net = latest();
  if (!saved) return (await net) || Response.error();
  const first = await Promise.race([net, new Promise((r) => setTimeout(r, WAIT, null))]);
  if (first) {
    event.waitUntil(cache.put(APP, first.clone()));
    return first;
  }
  // sem internet, ou lenta: abre com a cópia guardada, e a versão do site entra quando chegar
  const kept = saved.clone();
  event.waitUntil(net.then((res) => res && keep(cache, kept, res)));
  return saved;
}

// guarda a versão do site; se for diferente da que estava guardada, avisa o app aberto
async function keep(cache, saved, res) {
  if (saved && (await saved.text()) === (await res.clone().text())) return;
  await cache.put(APP, res);
  if (!saved) return;
  for (const w of await self.clients.matchAll({ type: "window" })) w.postMessage({ type: "app-update" });
}

// o app voltou pra tela: confere se o site tem versão nova
self.addEventListener("message", (event) => {
  if (event.data !== "check") return;
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE);
      const [saved, res] = await Promise.all([cache.match(APP), latest()]);
      if (res) await keep(cache, saved, res);
    })(),
  );
});

// fontes, ícones e manifesto: da cópia guardada, na hora, e atualizados por trás
async function fromCache(event) {
  const req = event.request;
  const cache = await caches.open(CACHE);
  const saved = await cache.match(req, { ignoreSearch: true });
  const fresh = fetch(req)
    .then((res) => {
      if (res && res.ok) cache.put(req, res.clone());
      return res;
    })
    .catch(() => null);
  if (saved) {
    event.waitUntil(fresh);
    return saved;
  }
  return (await fresh) || Response.error();
}
