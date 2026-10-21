"""Treinos por ano: um quadradinho por dia, ano por ano, como o gráfico de contribuições do GitHub."""
import json
import re

import pytest

from conftest import ROOT, SAMPLE, SEEN, season_state
from test_app import BROKEN_TEXT, go, look

TUESDAY = "2026-10-06T13:30:00-03:00"
SUMMER_SEEN = "localStorage.setItem('treinos-recap-seen', JSON.stringify(['verao']));"  # a retrospectiva não abre sozinha
# Uma semana com cada tipo de dia: plano antigo, três treinos com peso subindo, corrida sozinha, outro e surf.
WEEK = {
    "logs": {
        "2026-09-21": "Pernas",
        "2026-09-22": "Costas e bíceps",
        "2026-09-23": "Costas e bíceps",
        "2026-09-24": "Costas e bíceps",
        "2026-09-26": "Outro",
        "2026-09-27": "Surf",
    },
    "runs": {"2026-09-23": {"km": 1.2, "min": 8}, "2026-09-25": {"km": 2.5, "min": 15}},
    "loads": {"Rosca com barra W": {"2026-09-22": 10, "2026-09-23": 20, "2026-09-24": 30}},
}


def open_years(open_app, app_url, state, when=TUESDAY, **kw):
    page, errors = open_app(app_url(state), when, **kw)
    go(page, "prog")
    page.locator(".yr").scroll_into_view_if_needed()
    return page, errors


def picked(page, y=2026):
    """O dia marcado no quadro do ano y: o texto embaixo do quadro e o tom do quadradinho dentro do anel."""
    block = page.locator(f'.yr-y[data-y="{y}"]')
    block.scroll_into_view_if_needed()
    tone = page.evaluate(
        """(y) => {
            const r = document.querySelector(`.yr-y[data-y="${y}"] .yh`).getBoundingClientRect();
            const el = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
            return el ? el.getAttribute("class") : null;
        }""",
        y,
    )
    return block.locator(".yr-d").inner_text().replace("\n", " "), tone


def press(page, y, *keys):
    page.focus(f'.yr-y[data-y="{y}"]')
    for k in keys:
        page.keyboard.press(k)


def test_each_day_gets_a_tone_by_the_weight_lifted(app_url, open_app):
    page, errors = open_years(open_app, app_url, WEEK)
    assert page.locator(".yr-y").count() == 1
    assert page.inner_text('.yr-y[data-y="2026"] .yr-h b') == "2026"
    assert page.inner_text('.yr-y[data-y="2026"] .yr-h span') == "6 treinos e 2 corridas"
    # começa no último dia com alguma coisa
    assert picked(page) == ("Domingo, 27/09 Surf.", "yc1")
    press(page, 2026, "ArrowLeft")
    assert picked(page) == ("Domingo, 20/09 Sem treino.", "yc0")
    press(page, 2026, "ArrowDown", "ArrowDown")  # 21 e 22: segunda e terça
    assert picked(page) == ("Terça, 22/09 Costas e bíceps: 300 kg levantados.", "yc2")
    press(page, 2026, "ArrowDown")
    assert picked(page) == ("Quarta, 23/09 Costas e bíceps: 600 kg levantados. Corrida de 1,2 km.", "yc3")
    press(page, 2026, "ArrowDown")
    assert picked(page) == ("Quinta, 24/09 Costas e bíceps: 900 kg levantados.", "yc4"), "o dia mais pesado tem a cor do nível"
    press(page, 2026, "ArrowDown")
    assert picked(page) == ("Sexta, 25/09 Corrida de 2,5 km.", "yc1"), "corrida sozinha fica no tom mais claro"
    press(page, 2026, "ArrowDown")
    assert picked(page) == ("Sábado, 26/09 Outro treino.", "yc1")
    press(page, 2026, "ArrowUp", "ArrowUp", "ArrowUp", "ArrowUp", "ArrowUp")
    assert picked(page) == ("Segunda, 21/09 Pernas.", "yc3"), "treino de plano antigo, sem os pesos, fica no meio"
    # a legenda mostra os cinco tons, do vazio à cor do nível
    assert page.locator(".yr-k i").count() == 5
    assert errors == []


def test_days_before_the_app_and_days_still_to_come_are_faded(app_url, open_app):
    page, errors = open_years(open_app, app_url, WEEK)
    press(page, 2026, "ArrowLeft", "ArrowLeft")  # 27/09 menos duas semanas: 13/09, véspera do primeiro dia do app
    assert picked(page) == ("Domingo, 13/09 Antes do app.", "ycf")
    press(page, 2026, "ArrowDown")  # o dia seguinte, no alto da semana seguinte
    assert picked(page) == ("Segunda, 14/09 Sem treino.", "yc0")
    press(page, 2026, "ArrowRight", "ArrowRight", "ArrowRight")
    assert picked(page) == ("Segunda, 05/10 Sem treino.", "yc0")
    press(page, 2026, "ArrowDown")
    assert picked(page) == ("Hoje, 06/10 Ainda sem treino.", "yc0")
    press(page, 2026, "ArrowDown")
    assert picked(page) == ("Quarta, 07/10 Ainda não chegou.", "ycf")
    # o anel não sai do ano
    press(page, 2026, *(["ArrowRight"] * 20))
    assert picked(page)[0] == "Quinta, 31/12 Ainda não chegou."
    assert errors == []


def test_tapping_or_dragging_on_the_grid_picks_the_day(app_url, open_app):
    page, errors = open_years(open_app, app_url, WEEK)
    press(page, 2026, "ArrowLeft", "ArrowDown", "ArrowDown", "ArrowDown", "ArrowDown")  # 24/09
    ring = page.locator('.yr-y[data-y="2026"] .yh').bounding_box()
    press(page, 2026, "ArrowLeft", "ArrowLeft", "ArrowLeft")  # leva o anel pra longe
    assert picked(page)[0] == "Quinta, 03/09 Antes do app."
    cx, cy = ring["x"] + ring["width"] / 2, ring["y"] + ring["height"] / 2
    page.mouse.click(cx, cy)
    assert picked(page) == ("Quinta, 24/09 Costas e bíceps: 900 kg levantados.", "yc4"), "o toque acha o dia"
    # arrastar o dedo pra baixo passa pro dia seguinte
    page.mouse.move(cx, cy)
    page.mouse.down()
    page.mouse.move(cx, cy + ring["height"], steps=3)
    page.mouse.up()
    assert picked(page)[0] == "Sexta, 25/09 Corrida de 2,5 km."
    # o dia escolhido continua escolhido quando a tela redesenha
    page.click('[data-act="theme"]')
    page.wait_for_timeout(150)
    assert picked(page)[0] == "Sexta, 25/09 Corrida de 2,5 km."
    assert errors == []


def test_years_come_newest_first_each_with_its_own_count(app_url, open_app):
    state = json.loads(json.dumps(SAMPLE))
    state["logs"].update({"2027-01-04": "Peito e tríceps", "2027-01-05": "Costas e bíceps"})
    page, errors = open_years(open_app, app_url, state, "2027-01-06T12:00:00-03:00", init=SUMMER_SEEN)
    years = page.locator(".yr-y")
    assert [years.nth(i).get_attribute("data-y") for i in range(years.count())] == ["2027", "2026"]
    assert page.inner_text('.yr-y[data-y="2027"] .yr-h span') == "2 treinos"
    assert page.inner_text('.yr-y[data-y="2026"] .yr-h span') == "4 treinos e 1 corrida"
    # a rosca de 10 kg anotada em setembro vale até anotar outra
    assert picked(page, 2027)[0] == "Terça, 05/01 Costas e bíceps: 300 kg levantados."
    assert picked(page, 2026)[0] == "Quinta, 01/10 Peito e costas.", "cada ano começa no último dia com treino dele"
    # o resto de 2026 já passou: sem treino, e não mais "ainda não chegou"
    press(page, 2026, "ArrowRight")
    assert picked(page, 2026) == ("Quinta, 08/10 Sem treino.", "yc0")
    press(page, 2026, "ArrowDown", "ArrowDown", "ArrowDown", "ArrowDown")
    assert picked(page, 2026)[0] == "Segunda, 12/10 Sem treino. Feriado: Nossa Senhora Aparecida."
    page.click(".yr-tab summary")
    rows = [r.split("\t") for r in page.locator(".yr-tab tbody tr").all_inner_texts()]
    assert rows[0] == ["jan 2027", "2", "0", "300"]
    assert rows[1] == ["dez 2026", "0", "0", "—"]
    assert rows[-1] == ["set 2026", "3", "1", "300"], "a tabela vai do mês de agora até o começo do app"
    assert len(rows) == 5
    assert not any(bad in page.inner_text(".yr") for bad in BROKEN_TEXT)
    assert errors == []


def test_an_empty_app_shows_this_year_without_breaking(app_url, open_app):
    page, errors = open_years(open_app, app_url, {})
    assert page.inner_text('.yr-y[data-y="2026"] .yr-h span') == "0 treinos"
    assert picked(page) == ("Hoje, 06/10 Ainda sem treino.", "yc0")
    assert not any(bad in page.inner_text(".yr") for bad in BROKEN_TEXT)
    assert errors == []


def test_the_weight_of_each_day_adds_up_to_the_summer_recap(app_url, open_app):
    """Os quilos da tabela, mês a mês, somam as toneladas da retrospectiva: as duas contas são a mesma."""
    page, errors = open_years(
        open_app,
        app_url,
        season_state(),
        "2026-12-21T20:00:00-03:00",
        init=SUMMER_SEEN,
        motion="reduce",
    )
    page.click(".yr-tab summary")
    kg = sum(
        int(cells[3].replace(".", ""))
        for cells in (r.split("\t") for r in page.locator(".yr-tab tbody tr").all_inner_texts())
        if cells[3] != "—"
    )
    assert kg > 10000
    page.click(".rcp-v")
    page.wait_for_timeout(200)
    tons = ""
    for _ in range(20):
        tons = next((t for t in page.inner_text(".wr").split("\n") if "toneladas levantadas" in t), "")
        if tons:
            break
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(120)
    shown = float(re.search(r"umas ([\d.,]+) toneladas", tons).group(1).replace(".", "").replace(",", "."))
    assert abs(shown - kg / 1000) <= 0.51, (shown, kg)
    assert errors == []


@pytest.fixture
def phone_with_fonts(browser):
    """Celular que carrega as fontes do repositório, como o app instalado, pra medir o texto do tamanho real."""
    contexts = []

    def _open(url, when, width, init=""):
        ctx = browser.new_context(viewport={"width": width, "height": 844}, timezone_id="America/Sao_Paulo",
                                  locale="pt-BR")
        contexts.append(ctx)
        ctx.add_init_script(SEEN + init)
        ctx.route("https://fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
        ctx.route("**/fonts/**", lambda r: r.fulfill(path=str(ROOT / "fonts" / r.request.url.split("/fonts/")[-1])))
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.clock.install(time=when)
        page.goto(url)
        page.wait_for_timeout(300)
        page.evaluate("document.fonts.ready.then(() => true)")
        go(page, "prog")
        page.locator(".yr").scroll_into_view_if_needed()
        return page, errors

    yield _open
    for ctx in contexts:
        ctx.close()


@pytest.mark.parametrize("width", [320, 360, 390])
@pytest.mark.parametrize("skin", ["mare", "anilha", "caderno", ""])
def test_year_grid_fits_small_phones_in_every_look(app_url, phone_with_fonts, skin, width):
    page, errors = phone_with_fonts(app_url(season_state()), "2026-12-10T14:00:00-03:00", width, look(skin))
    fonts = page.evaluate("[...document.fonts].filter((f) => f.status === 'loaded').map((f) => f.family).join()")
    assert ("Bricolage" if skin == "mare" else "Archivo") in fonts, "mede com a letra de verdade do app"
    assert not page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    fit = page.evaluate(
        """() => {
            const svg = document.querySelector('.yr svg'), box = svg.getBoundingClientRect(),
              host = svg.parentNode.getBoundingClientRect(), sc = box.width / svg.viewBox.baseVal.width;
            const ms = [...svg.querySelectorAll('.ym')].map((t) => t.getBoundingClientRect());
            const ws = [...svg.querySelectorAll('.yw')].map((t) => ({
              y: t.y.baseVal[0].value * sc, size: parseFloat(getComputedStyle(t).fontSize) * sc }));
            return {
              inside: box.left >= host.left - 0.5 && box.right <= host.right + 0.5,
              months: ms.length,
              monthGap: Math.min(...ms.slice(1).map((b, i) => b.left - ms[i].right)),
              monthsIn: ms.every((b) => b.left >= box.left - 1 && b.right <= box.right + 1),
              weekRoom: Math.min(...ws.slice(1).map((w, i) => (w.y - ws[i].y) / w.size)),
              smallest: Math.min(...ws.map((w) => w.size), ...[...svg.querySelectorAll('.ym')].map(
                (t) => parseFloat(getComputedStyle(t).fontSize) * sc)),
            };
        }"""
    )
    assert fit["inside"]
    assert fit["months"] in (6, 12)
    if width == 320:
        assert fit["months"] == 6, "no celular estreito, um mês sim e outro não"
    if width == 390:
        assert fit["months"] == 12, "no celular comum, os doze meses"
    assert fit["monthGap"] >= 3, "os nomes dos meses não encostam um no outro"
    assert fit["monthsIn"]
    assert fit["weekRoom"] >= 1.08, "os dias da semana têm espaço pra letra"
    assert fit["smallest"] >= 9, "a letra do quadro não fica menor que 9 px na tela"
    assert errors == []


@pytest.mark.parametrize("width", [320, 390])
def test_number_tables_keep_each_number_in_its_column(app_url, open_app, width):
    """Na tabela do painel e na do mês a mês, cada número fica embaixo do título dele, sem colar no vizinho."""
    page, errors = open_years(open_app, app_url, season_state(), "2026-12-10T14:00:00-03:00", width=width)
    for table in (".dash .lc-tab", ".yr-tab"):
        page.click(f"{table} summary")
        gaps = page.evaluate(
            """(sel) => {
                const text = (el) => { const r = document.createRange(); r.selectNodeContents(el); return r.getBoundingClientRect(); };
                const head = [...document.querySelectorAll(`${sel} th`)].map(text);
                let worst = 99, off = 0;
                for (const tr of document.querySelectorAll(`${sel} tbody tr`)) {
                    const cells = [...tr.children].map(text);
                    cells.slice(1).forEach((c, i) => { worst = Math.min(worst, c.left - cells[i].right); });
                    // número e título da coluna terminam juntos (alinhados à direita)
                    cells.slice(1).forEach((c, i) => { off = Math.max(off, Math.abs(c.right - head[i + 1].right)); });
                }
                return { worst, off };
            }""",
            table,
        )
        assert gaps["worst"] >= 8, (table, gaps)
        assert gaps["off"] <= 1, (table, gaps)
    assert errors == []
