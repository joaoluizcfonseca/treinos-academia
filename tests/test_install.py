"""App instalado (GitHub Pages): abre sem internet e faz backup dos dados que ficam no celular."""
import functools
import json
import shutil
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

from conftest import ROOT, SEEN, SAMPLE, STATE_RE, with_state

WHEN = "2026-10-06T13:30:00-03:00"  # terça: Costas e bíceps
FILES = ["index.html", "manifest.webmanifest", "sw.js", "icons", "fonts"]


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture
def site(tmp_path):
    """Publica uma cópia do app como no GitHub Pages (numa pasta com o nome do repositório).

    Devolve a URL e uma função que derruba o servidor, pra simular o celular sem internet."""
    folder = tmp_path / "treinos-ate-o-verao"
    folder.mkdir()
    for name in FILES:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, folder / name)
        else:
            shutil.copy(src, folder / name)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(tmp_path)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    state = {"up": True}

    def offline():
        if state["up"]:
            httpd.shutdown()
            httpd.server_close()
            state["up"] = False

    yield f"http://127.0.0.1:{httpd.server_address[1]}/treinos-ate-o-verao/", offline, folder
    offline()


@pytest.fixture
def phone(browser):
    contexts = []

    def _open(url, init=""):
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, timezone_id="America/Sao_Paulo",
                                  locale="pt-BR", accept_downloads=True)
        ctx.add_init_script(SEEN + init)
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


def ready(page):
    """Espera o service worker terminar de guardar o app e passar a cuidar da página."""
    page.evaluate("navigator.serviceWorker.ready.then(() => true)")
    page.reload()
    page.wait_for_function("navigator.serviceWorker.controller !== null")
    page.wait_for_timeout(200)


def test_installed_app_opens_and_saves_without_internet(site, phone):
    url, offline, _ = site
    page, errors = phone(url)
    assert page.locator('link[rel="manifest"]').count() == 1
    assert page.evaluate("document.querySelector('meta[name=theme-color]').content") != ""
    ready(page)
    offline()
    page.reload()
    page.wait_for_timeout(400)
    page.click('[data-nav="hoje"]')
    assert "Costas e bíceps" in page.inner_text("#root"), "abre do que ficou guardado, sem servidor"
    box = page.locator('.exi input[data-kg="Bíceps na máquina"]')
    box.fill("27,5")
    box.press("Enter")
    page.reload()
    page.wait_for_timeout(400)
    page.click('[data-nav="hoje"]')
    assert page.input_value('.exi input[data-kg="Bíceps na máquina"]') == "27,5", "o peso fica no celular"
    loaded = page.evaluate("[...document.fonts].filter((f) => f.status === 'loaded').map((f) => f.family)")
    assert any("Bricolage" in f for f in loaded), "a fonte do app vem junto, sem internet"
    assert errors == []


def test_backup_goes_out_and_comes_back(site, phone, tmp_path):
    url, _, _ = site
    page, errors = phone(url)
    # dados de exemplo entram como se tivessem sido anotados neste celular
    page.evaluate(
        "(d) => { localStorage.setItem('treinos-verao-logs', JSON.stringify({base: 0, t: Date.now(), data: d})); }",
        SAMPLE,
    )
    page.reload()
    page.wait_for_timeout(300)
    page.click('[data-nav="prog"]')
    assert "Ainda não tem backup." in page.inner_text(".bk")
    with page.expect_download() as dl:
        page.click('[data-act="export"]')
    path = tmp_path / "backup.json"
    dl.value.save_as(path)
    assert dl.value.suggested_filename == "treinos-backup-2026-10-06.json"
    backup = json.loads(path.read_text(encoding="utf-8"))
    assert backup["app"] == "treinos-ate-o-verao"
    assert backup["dados"]["logs"] == SAMPLE["logs"]
    assert "Último backup: 06/10." in page.inner_text(".bk")

    # outro celular, app vazio: importa e fica tudo igual, sem comemoração de nível
    page2, errors2 = phone(url, "localStorage.removeItem('treinos-lvl');")
    page2.click('[data-nav="prog"]')
    page2.set_input_files('input[data-bk="import"]', str(path))
    page2.wait_for_load_state()
    page2.wait_for_timeout(500)
    assert "Backup importado: 4 treinos." in page2.inner_text("body")
    assert page2.locator(".splash").count() == 0
    page2.click('[data-nav="quadro"]')
    assert page2.locator(".d.on").count() >= 4
    assert errors == [] and errors2 == []


def test_importing_into_an_app_with_data_only_adds_what_is_missing(site, phone, tmp_path):
    url, _, _ = site
    mine = json.loads(json.dumps(SAMPLE))
    mine["loads"]["Rosca com barra W"]["2026-10-06"] = 12
    other = json.loads(json.dumps(SAMPLE))
    other["logs"]["2026-10-05"] = "Peito e tríceps"
    other["loads"]["Rosca com barra W"]["2026-10-06"] = 99  # o daqui fica
    path = tmp_path / "outro.json"
    path.write_text(json.dumps({"app": "treinos-ate-o-verao", "versao": 1, "dados": other}), encoding="utf-8")
    page, errors = phone(url)
    page.evaluate(
        "(d) => { localStorage.setItem('treinos-verao-logs', JSON.stringify({base: 0, t: Date.now(), data: d})); }",
        mine,
    )
    page.reload()
    page.wait_for_timeout(300)
    page.click('[data-nav="prog"]')
    page.set_input_files('input[data-bk="import"]', str(path))
    page.wait_for_load_state()
    page.wait_for_timeout(500)
    data = page.evaluate("JSON.parse(localStorage.getItem('treinos-verao-logs')).data")
    assert data["logs"]["2026-10-05"] == "Peito e tríceps"
    assert data["loads"]["Rosca com barra W"]["2026-10-06"] == 12
    assert errors == []


def test_a_file_that_is_not_a_backup_is_refused(site, phone, tmp_path):
    url, _, _ = site
    path = tmp_path / "foto.json"
    path.write_text('{"nome": "qualquer coisa"}', encoding="utf-8")
    page, errors = phone(url)
    page.click('[data-nav="prog"]')
    page.set_input_files('input[data-bk="import"]', str(path))
    page.wait_for_timeout(300)
    assert "Esse arquivo não é um backup do app." in page.inner_text(".bk")
    assert errors == []


def test_inside_claude_there_is_no_install_and_no_backup(app_url, open_app):
    from test_app import PUBLISH_STUB, go

    page, errors = open_app(app_url(SAMPLE), WHEN, init=PUBLISH_STUB)
    assert page.locator('link[rel="manifest"]').count() == 0
    assert page.evaluate("navigator.serviceWorker ? navigator.serviceWorker.controller : null") is None
    go(page, "prog")
    assert page.locator(".bk").count() == 0
    assert errors == []


def test_the_service_worker_keeps_every_file_the_app_needs():
    """Tudo o que o app carrega de si mesmo está na lista que o service worker guarda pra usar offline."""
    sw = (ROOT / "sw.js").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
    css = (ROOT / "fonts" / "fonts.css").read_text(encoding="utf-8")
    import re

    wanted = {"./index.html", "./manifest.webmanifest", "./fonts/fonts.css", "./icons/apple-touch-icon.png"}
    wanted |= {"./" + i["src"] for i in manifest["icons"]}
    wanted |= {"./fonts/" + f for f in re.findall(r'url\("([^"]+)"\)', css)}
    listed = set(re.findall(r'"(\./[^"]*)"', sw))
    assert wanted <= listed, wanted - listed
    for f in listed - {"./"}:
        assert (ROOT / f[2:]).exists(), f
    app = (ROOT / "index.html").read_text(encoding="utf-8")
    assert STATE_RE.search(app).group(2).strip() == "{}", "o repositório vai sem dados de ninguém"


def test_only_the_app_address_opens_the_app(site, phone):
    """O service worker abre o app só pelo endereço dele; o endereço de um arquivo mostra o arquivo."""
    url, _, _ = site
    page, errors = phone(url)
    ready(page)
    page.goto(url + "manifest.webmanifest")
    assert '"short_name": "Treinos"' in page.content()
    page.goto(url + "index.html")
    page.wait_for_timeout(300)
    assert page.locator('[data-nav="hoje"]').count() == 1
    assert errors == []


def seed(page, data):
    """Põe dados como se tivessem sido anotados neste celular e abre de novo."""
    page.evaluate(
        "(d) => { localStorage.setItem('treinos-verao-logs', JSON.stringify({base: 0, t: Date.now(), data: d})); }",
        data,
    )
    page.reload()
    page.wait_for_timeout(300)


def test_backup_reminder_once_a_week_in_the_installed_app(site, phone):
    url, _, _ = site
    page, errors = phone(url)
    assert page.locator(".bkrem").count() == 0, "sem treino anotado, nada pra guardar"
    seed(page, SAMPLE)
    page.click('[data-nav="hoje"]')
    assert "Teus treinos ficam só neste celular." in page.inner_text(".bkrem")
    page.click('.bkrem [data-act="bk-later"]')
    assert page.locator(".bkrem").count() == 0, "Depois adia uma semana"
    page.clock.set_system_time("2026-10-13T13:30:00-03:00")
    page.reload()
    page.wait_for_timeout(300)
    assert page.locator(".bkrem").count() == 1, "uma semana depois volta"
    with page.expect_download():
        page.click('.bkrem [data-act="export"]')
    assert page.locator(".bkrem").count() == 0
    page.clock.set_system_time("2026-10-19T13:30:00-03:00")
    page.reload()
    page.wait_for_timeout(300)
    assert page.locator(".bkrem").count() == 0, "6 dias depois do backup, ainda não"
    page.clock.set_system_time("2026-10-20T13:30:00-03:00")
    page.reload()
    page.wait_for_timeout(300)
    assert "Teu último backup foi há 7 dias." in page.inner_text(".bkrem")
    assert errors == []


def test_imported_backup_counts_as_a_backup(site, phone, tmp_path):
    url, _, _ = site
    path = tmp_path / "backup.json"
    path.write_text(json.dumps({"app": "treinos-ate-o-verao", "versao": 1, "dados": SAMPLE}), encoding="utf-8")
    page, errors = phone(url)
    page.click('[data-nav="prog"]')
    page.set_input_files('input[data-bk="import"]', str(path))
    page.wait_for_load_state()
    page.wait_for_timeout(500)
    page.click('[data-nav="hoje"]')
    assert page.locator(".bkrem").count() == 0, "acabou de vir de um backup, não precisa lembrar"
    assert errors == []


def test_inside_claude_there_is_no_backup_reminder_and_the_name_is_on_the_app(app_url, open_app):
    from test_app import PUBLISH_STUB, go

    page, errors = open_app(app_url(SAMPLE), WHEN, init=PUBLISH_STUB, motion="reduce")
    go(page, "hoje")
    assert page.locator(".bkrem").count() == 0
    assert page.inner_text(".cred") == "Feito por João Candaten"
    go(page, "prog")
    page.click(".rcp-v")
    for _ in range(30):
        if page.locator(".wr-btns").count():
            break
        page.keyboard.press("ArrowRight")
    assert page.inner_text(".wp-f") == "Feito por João Candaten", "o cartão do resumo também"
    assert errors == []
