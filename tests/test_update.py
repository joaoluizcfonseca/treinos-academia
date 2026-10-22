"""App instalado: abre na versão mais nova e troca sozinho quando sai uma, sem atrapalhar quem está usando."""
import functools
import shutil
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest

from conftest import ROOT, SEEN

WHEN = "2026-10-06T13:30:00-03:00"  # terça: Costas e bíceps
FILES = ["index.html", "manifest.webmanifest", "sw.js", "icons", "fonts"]
APP = "/treinos-ate-o-verao/index.html"
VERSION = "(document.querySelector('meta[name=versao]') || {}).content"

# O service worker de antes desta versão, como está nos celulares que já instalaram o app: abre sempre a
# cópia guardada e baixa a versão nova por trás, pra próxima vez.
OLD_SW = r"""
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
  if (url.origin !== self.location.origin) return;
  event.respondWith(
    caches.open(CACHE).then(async (cache) => {
      const app = req.mode === "navigate" && /\/(index\.html)?$/.test(url.pathname);
      const key = app ? "./index.html" : req;
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
"""


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture
def site(tmp_path):
    """O app publicado como no GitHub Pages, com como publicar uma versão nova e deixar a internet lenta."""
    folder = tmp_path / "treinos-ate-o-verao"
    folder.mkdir()
    for name in FILES:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, folder / name)
        else:
            shutil.copy(src, folder / name)
    slow = {}  # endereço -> segundos que o servidor demora pra responder

    class Handler(_Quiet):
        def do_GET(self):
            time.sleep(slow.get(self.path.split("?")[0], 0))
            super().do_GET()

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(tmp_path)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    up = {"on": True}

    def offline():
        if up["on"]:
            httpd.shutdown()
            httpd.server_close()
            up["on"] = False

    url = f"http://127.0.0.1:{httpd.server_address[1]}/treinos-ate-o-verao/"
    yield SimpleNamespace(url=url, folder=folder, slow=slow, offline=offline)
    offline()


def publish(site, label):
    """Sai uma versão do app; a marca no index.html diz qual versão está aberta."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    html = html.replace("<head>", f'<head><meta name="versao" content="{label}">', 1)
    (site.folder / "index.html").write_text(html, encoding="utf-8")


@pytest.fixture
def phone(browser):
    contexts = []

    def _open(url):
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, timezone_id="America/Sao_Paulo",
                                  locale="pt-BR")
        ctx.add_init_script(SEEN)
        contexts.append(ctx)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.clock.install(time=WHEN)
        page.goto(url)
        page.wait_for_timeout(300)
        return page, errors

    yield _open
    for ctx in contexts:
        ctx.close()


def installed(page):
    """Espera o service worker guardar o app e passar a cuidar da página, como no app instalado."""
    page.evaluate("navigator.serviceWorker.ready.then(() => true)")
    page.reload()
    page.wait_for_function("navigator.serviceWorker.controller !== null")
    page.wait_for_timeout(200)


def wait_version(page, label, timeout=10000):
    """Espera o app abrir (já desenhado) na versão dada."""
    page.wait_for_function(f"{VERSION} === {label!r} && !!document.querySelector('[data-nav]')", timeout=timeout)
    page.wait_for_timeout(200)


def back_to_the_app(page):
    """O app foi pro fundo (outro app na frente) e voltou pra tela."""
    page.evaluate(
        """() => {
          for (const v of ["hidden", "visible"]) {
            Object.defineProperty(document, "visibilityState", { value: v, configurable: true });
            document.dispatchEvent(new Event("visibilitychange"));
          }
        }"""
    )


def test_a_new_version_opens_on_the_first_try(site, phone):
    publish(site, "a")
    page, errors = phone(site.url)
    installed(page)
    assert page.evaluate(VERSION) == "a"
    publish(site, "b")
    page.goto(site.url)
    assert page.evaluate(VERSION) == "b", "com internet, já abre na versão nova, sem precisar abrir duas vezes"
    page.wait_for_timeout(300)
    site.offline()
    page.reload()
    assert page.evaluate(VERSION) == "b", "sem internet, abre com a versão nova, que ficou guardada"
    assert page.locator('[data-nav="hoje"]').count() == 1
    assert page.locator(".saved").count() == 0, "abrir na versão nova não precisa de aviso"
    assert errors == []


def test_slow_internet_opens_the_saved_copy_and_switches_by_itself(site, phone):
    publish(site, "a")
    page, errors = phone(site.url)
    installed(page)
    publish(site, "b")
    site.slow[APP] = 3  # a internet demora mais do que a abertura espera
    start = time.time()
    page.goto(site.url)
    assert page.evaluate(VERSION) == "a", "abre na hora com a cópia guardada"
    assert time.time() - start < 2.5
    wait_version(page, "b")  # a versão nova chega e o app troca sozinho, sem ninguém tocar em nada
    assert "App atualizado." in page.inner_text(".saved")
    assert errors == []


def test_coming_back_to_the_app_switches_without_getting_in_the_way(site, phone):
    publish(site, "a")
    page, errors = phone(site.url)
    installed(page)
    page.click('[data-nav="pesos"]')
    page.evaluate("window.scrollTo(0, 400)")
    publish(site, "b")
    back_to_the_app(page)
    wait_version(page, "b")
    assert page.locator('[data-nav="pesos"][aria-current="page"]').count() == 1, "volta na mesma aba"
    page.wait_for_function("window.scrollY > 300")
    assert "App atualizado." in page.inner_text(".saved")

    # quem está digitando um peso quando sai outra versão não é interrompido: aparece o aviso
    page.click('[data-nav="hoje"]')
    box = page.locator('.exi input[data-kg="Bíceps na máquina"]')
    box.click()
    box.type("27,5")
    publish(site, "c")
    page.evaluate("navigator.serviceWorker.controller.postMessage('check')")  # a conferida da meia hora
    page.wait_for_selector(".snack")
    assert page.inner_text(".snack span") == "Tem uma versão nova do app."
    assert page.inner_text(".snack button") == "Atualizar"
    assert page.evaluate(VERSION) == "b" and page.input_value('.exi input[data-kg="Bíceps na máquina"]') == "27,5"
    page.click('.snack [data-act="snack-undo"]')
    wait_version(page, "c")
    assert page.input_value('.exi input[data-kg="Bíceps na máquina"]') == "27,5", "o peso digitado não se perde"
    assert errors == []


def test_the_app_installed_before_this_version_updates_itself(site, phone):
    """Quem instalou com o service worker antigo: na primeira vez que abre, o app novo assume e recarrega."""
    (site.folder / "sw.js").write_text(OLD_SW, encoding="utf-8")
    publish(site, "a")
    page, errors = phone(site.url)
    installed(page)
    assert page.evaluate("caches.keys()") == ["treinos-v1"]
    shutil.copy(ROOT / "sw.js", site.folder / "sw.js")
    publish(site, "b")
    page.goto(site.url)  # o service worker antigo ainda abre a cópia guardada...
    wait_version(page, "b", timeout=15000)  # ...e o novo assume e recarrega na versão nova, sozinho
    assert page.evaluate("caches.keys()") == ["treinos-v2"]
    assert errors == []
