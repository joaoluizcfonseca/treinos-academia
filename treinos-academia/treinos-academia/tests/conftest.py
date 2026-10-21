"""Fixtures dos testes de ponta a ponta.

O app é servido por um servidor HTTP local (e não por file://), porque o
localStorage de páginas file:// não é confiável no Chromium headless.
"""
import functools
import json
import re
import threading
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
APP_HTML = (ROOT / "index.html").read_text(encoding="utf-8")
STATE_RE = re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)', re.S)

# Conquistas e nível já "vistos": evita as telas de comemoração no meio dos testes.
SEEN = (
    "localStorage.setItem('treinos-lvl','99');"
    "localStorage.setItem('treinos-secret',JSON.stringify(['chuva','cedo','noite','feriado','fds','dobra','3km','ferro','metade']));"
)


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def server(tmp_path_factory):
    root = tmp_path_factory.mktemp("site")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_QuietHandler, directory=str(root)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield root, f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def with_state(html: str, state: dict) -> str:
    """Troca os dados salvos dentro do HTML."""
    data = json.dumps(state, ensure_ascii=False).replace("<", "\\u003c")
    return STATE_RE.sub(lambda m: m.group(1) + data + m.group(3), html, count=1)


@pytest.fixture
def app_url(server):
    """Publica uma cópia do app com os dados dados e devolve a URL."""
    root, base = server

    def make(state=None, html=None):
        name = f"app-{uuid.uuid4().hex[:8]}.html"
        page = html if html is not None else (APP_HTML if state is None else with_state(APP_HTML, state))
        (root / name).write_text(page, encoding="utf-8")
        return f"{base}/{name}"

    return make


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def open_app(browser):
    """Abre o app num celular simulado (390x844 por padrão, fuso de Floripa) numa data fixa.

    motion="reduce" simula quem pede menos movimento: a retrospectiva não passa sozinha e os números
    aparecem direto, sem contagem.
    """
    contexts = []

    def _open(url, when, scheme="dark", init=None, width=390, height=844, motion=None):
        ctx = browser.new_context(
            viewport={"width": width, "height": height},
            color_scheme=scheme,
            timezone_id="America/Sao_Paulo",
            locale="pt-BR",
            reduced_motion=motion or "no-preference",
        )
        ctx.add_init_script(SEEN)
        if init:
            ctx.add_init_script(init)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.clock.install(time=when)
        page.goto(url)
        page.wait_for_timeout(300)
        contexts.append(ctx)
        return page, errors

    yield _open
    for ctx in contexts:
        ctx.close()


# Dados de exemplo (inventados) usados pelos testes.
SAMPLE = {
    "logs": {
        "2026-09-28": "Peito e tríceps",
        "2026-09-29": "Costas e bíceps",
        "2026-09-30": "Ombro e abdômen",
        "2026-10-01": "Peito e costas",
    },
    "runs": {"2026-09-30": {"km": 1.7, "min": 10}},
    "loads": {"Rosca com barra W": {"2026-09-29": 10}},
    "weight": {"2026-09-28": 80},
}


def season_state():
    """Um verão inteiro inventado (14/09 a 21/12), sempre igual: treinos, corridas, cargas, peso e barra."""
    import random
    from datetime import date, timedelta

    rnd = random.Random(7)
    split = {0: "Peito e tríceps", 1: "Costas e bíceps", 2: "Ombro e abdômen", 3: "Peito e costas", 4: "Tríceps e braço"}
    old = {0: "Peito, ombro e tríceps", 1: "Costas e bíceps", 2: "Pernas", 3: "Superiores leves", 4: "Pernas e abdômen"}
    holidays = {"2026-10-12", "2026-11-02", "2026-11-20"}
    start = {
        "Supino sentado": 30, "Voador (peito)": 30, "Tríceps na máquina": 45, "Tríceps na polia com corda": 22.5,
        "Tríceps na polia com barra": 25, "Puxada (aberta)": 32, "Remada com apoio no peito": 36,
        "Voador invertido (costas)": 20, "Bíceps na máquina": 14, "Bíceps na polia com corda": 15,
        "Rosca com barra W": 10, "Antebraço com halter": 5, "Ombro na máquina": 14, "Elevação lateral": 6,
        "Abdômen na máquina": 18,
    }
    plan = {
        "Peito e tríceps": ["Supino sentado", "Voador (peito)", "Tríceps na máquina", "Tríceps na polia com corda", "Tríceps na polia com barra"],
        "Costas e bíceps": ["Puxada (aberta)", "Remada com apoio no peito", "Voador invertido (costas)", "Bíceps na máquina", "Bíceps na polia com corda", "Rosca com barra W", "Antebraço com halter"],
        "Ombro e abdômen": ["Ombro na máquina", "Elevação lateral", "Abdômen na máquina"],
        "Peito e costas": ["Supino sentado", "Puxada (aberta)", "Voador (peito)", "Remada com apoio no peito", "Abdômen na máquina"],
        "Tríceps e braço": ["Bíceps na máquina", "Bíceps na polia com corda", "Rosca com barra W", "Tríceps na máquina", "Tríceps na polia com corda", "Antebraço com halter"],
    }
    st = {"logs": {}, "runs": {}, "loads": {}, "weight": {}, "hr": {}, "ex": {}}
    cur = dict(start)
    hang, neg = 12, 2
    d = date(2026, 9, 14)
    while d <= date(2026, 12, 21):
        k = d.isoformat()
        wd = d.weekday()
        weeks = (d - date(2026, 9, 14)).days // 7
        if wd < 5 and k not in holidays and rnd.random() < 0.9:
            w = old[wd] if d < date(2026, 9, 28) else split[wd]
            st["logs"][k] = w
            st["hr"][k] = rnd.choice([18, 19, 19, 20, 20, 21, 7, 13])
            for n in plan.get(w, []):
                if rnd.random() < 0.25 and weeks > 1:
                    cur[n] = cur[n] + (2.5 if cur[n] >= 20 else 1)
                st["loads"].setdefault(n, {})[k] = cur[n]
            if w == "Peito e tríceps":
                hang = min(34, hang + rnd.choice([0, 1, 2, 3]))
                st["loads"].setdefault("Pendurar na barra", {})[k] = hang
            if w == "Peito e costas":
                neg = min(5, neg + rnd.choice([0, 0, 1]))
                st["loads"].setdefault("Negativa na barra", {})[k] = neg
        elif wd == 5 and rnd.random() < 0.3:
            st["logs"][k] = "Peito e costas leve"
        elif wd == 6 and rnd.random() < 0.12:
            st["logs"][k] = "Surf"
        if wd in (0, 2, 4) and rnd.random() < 0.55:
            km = round(min(4.6, 1.2 + weeks * 0.22 + rnd.uniform(-0.3, 0.3)), 2)
            st["runs"][k] = {"km": km, "min": round(km * (6.6 - weeks * 0.06), 2)}
        if wd == 0:
            st["weight"][k] = round(81 - weeks * 0.12 + rnd.uniform(-0.3, 0.3), 1)
        d += timedelta(days=1)
    st["runs"]["2026-10-21"] = True  # corrida marcada sem distância
    return st
