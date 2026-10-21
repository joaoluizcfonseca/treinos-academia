"""Testes de ponta a ponta do app, num navegador de verdade."""
import json
import re

import pytest

from conftest import SAMPLE, STATE_RE, season_state

TABS = ["hoje", "pesos", "prog", "quadro"]
BROKEN_TEXT = ("undefined", "NaN", "[object Object]")

# Dias que exercitam caminhos diferentes: semana fechada, sábado leve, domingo, feriado.
DAYS = {
    "sexta à noite": "2026-10-02T21:00:00-03:00",
    "sábado": "2026-10-03T10:00:00-03:00",
    "domingo": "2026-10-04T09:00:00-03:00",
    "feriado": "2026-10-12T09:00:00-03:00",
}


def go(page, tab):
    page.click(f'[data-nav="{tab}"]')
    page.wait_for_timeout(150)


def look(skin):
    """Script que deixa um visual escolhido no celular antes de abrir o app ("" é o original)."""
    return f"localStorage.setItem('treinos-visual', '{skin or 'orig'}');"


@pytest.mark.parametrize("scheme", ["dark", "light"])
@pytest.mark.parametrize("day", DAYS.values(), ids=DAYS.keys())
def test_every_tab_renders(app_url, open_app, day, scheme):
    page, errors = open_app(app_url(SAMPLE), day, scheme)
    for tab in TABS:
        go(page, tab)
        text = page.inner_text("#root")
        assert not any(bad in text for bad in BROKEN_TEXT), f"texto quebrado na aba {tab}"
    assert not page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    assert errors == []


def test_empty_app_starts_clean(app_url, open_app):
    page, errors = open_app(app_url({}), "2026-10-05T09:00:00-03:00")
    go(page, "hoje")
    assert "Marca o primeiro treino." in page.inner_text("#root")
    for tab in TABS:
        go(page, tab)
    assert errors == []


def test_every_button_can_be_pressed(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), DAYS["sexta à noite"])
    for tab in TABS:
        go(page, tab)
        count = page.locator("#root button:not([data-nav])").count()
        for i in range(min(count, 40)):
            buttons = page.locator("#root button:not([data-nav])")
            if i >= buttons.count():
                break
            button = buttons.nth(i)
            if button.is_visible() and button.is_enabled():
                button.click(timeout=1000)
                page.wait_for_timeout(80)
            page.keyboard.press("Escape")
            if page.locator(".splash").count():
                page.locator(".splash").first.click()
            go(page, tab)
    assert errors == []


def test_workout_has_no_set_buttons_and_finishes_with_one_tap(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), DAYS["sábado"])
    go(page, "hoje")
    assert "Peito e costas leve" in page.inner_text(".check .plan")
    assert page.locator(".set").count() == 0, "não existe mais marcação de série"
    assert page.locator(".restbar").count() == 0, "não existe mais descanso automático"
    assert "série" not in page.inner_text(".check").lower()

    box = page.locator('.exi input[data-kg="Supino sentado (leve)"]')
    box.fill("22.5")
    box.press("Enter")
    page.click('button[data-act="mark"]')
    page.wait_for_timeout(300)
    assert "Feito: Peito e costas leve" in page.inner_text(".done-msg")
    assert errors == []


def test_weight_from_pesos_tab_fills_next_workout(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), DAYS["sexta à noite"])
    go(page, "pesos")
    box = page.locator('.pw-l input[data-kg="Bíceps na máquina"]')
    box.fill("25")
    box.press("Enter")

    page.clock.set_system_time("2026-10-06T13:30:00-03:00")  # terça: Costas e bíceps
    page.reload()
    page.wait_for_timeout(300)
    go(page, "hoje")
    assert page.input_value('.exi input[data-kg="Bíceps na máquina"]') == "25"
    assert page.input_value('.exi input[data-kg="Rosca com barra W"]') == "10"
    assert errors == []


def test_each_grip_keeps_its_own_weight(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), "2026-10-06T13:30:00-03:00")
    go(page, "hoje")
    page.click('.grip[data-g="Triângulo"]')
    box = page.locator('.exi input[data-kg="Puxada (triângulo)"]')
    box.fill("35")
    box.press("Enter")

    page.click('.grip[data-g="Aberta"]')
    assert page.input_value('.exi input[data-kg="Puxada (aberta)"]') == ""
    page.click('.grip[data-g="Triângulo"]')
    assert page.input_value('.exi input[data-kg="Puxada (triângulo)"]') == "35"
    assert errors == []


# Simula o ambiente do claude.ai, onde o app publica uma versão nova de si mesmo.
PUBLISH_STUB = (
    "window.__pub=[];"
    "window.claude={use:n=>Promise.resolve(n==='artifact'?{publish:async h=>{window.__pub.push(h)}}:null)};"
)


def test_app_saves_itself_and_reopens_with_the_data(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), "2026-10-06T13:30:00-03:00", init=PUBLISH_STUB)
    go(page, "pesos")
    box = page.locator('.pw-l input[data-kg="Bíceps na máquina"]')
    box.fill("27,5")
    box.press("Enter")  # o peso espera uma pausa de ~30 s pra publicar
    page.clock.fast_forward(31000)
    page.wait_for_timeout(200)

    published = page.evaluate("window.__pub.at(-1)")
    assert published, "o app deveria ter publicado uma versão nova"
    state = json.loads(STATE_RE.search(published).group(2))
    assert state["rev"] == 1
    assert state["loads"]["Bíceps na máquina"]["2026-10-06"] == 27.5

    page2, errors2 = open_app(app_url(html=published), "2026-10-06T13:35:00-03:00")
    go(page2, "hoje")
    assert page2.input_value('.exi input[data-kg="Bíceps na máquina"]') == "27,5"
    assert errors == [] and errors2 == []


def test_finishing_saves_the_weights_shown_on_screen(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), "2026-10-06T13:30:00-03:00", init=PUBLISH_STUB)
    go(page, "hoje")
    box = page.locator('.exi input[data-kg="Bíceps na máquina"]')
    box.fill("25")
    box.press("Enter")
    page.click('button[data-act="mark"]')
    page.clock.fast_forward(1000)
    page.wait_for_timeout(300)

    state = json.loads(STATE_RE.search(page.evaluate("window.__pub.at(-1)")).group(2))
    day = "2026-10-06"
    assert state["logs"][day] == "Costas e bíceps"
    assert state["loads"]["Bíceps na máquina"][day] == 25
    assert state["loads"]["Rosca com barra W"][day] == 10, "o peso da última vez entra no registro do dia"
    assert errors == []


def test_progress_counts_planned_sets_of_marked_workouts(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), DAYS["sexta à noite"])
    go(page, "prog")
    row = page.locator(".vo-r", has_text="Peito").inner_text()
    assert re.search(r"12\s*de\s*12", row), row
    assert errors == []


TUESDAY = "2026-10-06T13:30:00-03:00"  # Costas e bíceps


def published_state(page):
    return json.loads(STATE_RE.search(page.evaluate("window.__pub.at(-1)")).group(2))


@pytest.mark.parametrize("width", [320, 360, 390])
@pytest.mark.parametrize("skin", ["", "mare"])
def test_week_strip_fits_small_phones(app_url, open_app, width, skin):
    page, errors = open_app(app_url(SAMPLE), TUESDAY, width=width, init=look(skin))
    go(page, "hoje")
    assert not page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    square = page.evaluate("document.querySelector('.w7-d i').getBoundingClientRect().width")
    if width >= 390 and not skin:
        assert square == 25, "no original, em tela normal os quadradinhos da semana ficam do tamanho de sempre"
    assert errors == []


def test_undo_takes_back_the_weights_copied_by_finish(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY, init=PUBLISH_STUB)
    go(page, "hoje")
    box = page.locator('.exi input[data-kg="Bíceps na máquina"]')
    box.fill("25")
    box.press("Enter")
    page.click('button[data-act="mark"]')
    page.clock.fast_forward(9000)
    day = "2026-10-06"
    assert published_state(page)["loads"]["Rosca com barra W"][day] == 10

    page.click('button[data-act="undo"]')
    page.click('button[data-act="undook"]')
    page.clock.fast_forward(1000)
    state = published_state(page)
    assert day not in state["logs"]
    assert day not in state["loads"]["Rosca com barra W"], "o peso só copiado sai junto com o treino"
    assert state["loads"]["Bíceps na máquina"][day] == 25, "o peso anotado de verdade continua"
    assert errors == []


def test_removing_a_past_workout_in_the_calendar_drops_its_copied_weights(app_url, open_app):
    state = json.loads(json.dumps(SAMPLE))
    state["loads"] = {"Rosca com barra W": {"2026-09-22": 10, "2026-09-29": 10}, "Bíceps na máquina": {"2026-09-29": 25}}
    page, errors = open_app(app_url(state), TUESDAY, init=PUBLISH_STUB)
    go(page, "quadro")
    page.click('[data-day="2026-09-29"]')
    page.click('[data-act="sh-tr"]')
    page.clock.fast_forward(1000)
    loads = published_state(page)["loads"]
    assert "2026-09-29" not in loads["Rosca com barra W"]
    assert loads["Bíceps na máquina"]["2026-09-29"] == 25
    assert errors == []


def test_holiday_shows_the_planned_workout_as_optional(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), "2026-10-12T10:00:00-03:00")
    go(page, "hoje")
    assert "Feriado, treino opcional" in page.inner_text(".check .plan")
    assert page.inner_text('button[data-act="mark"]') == "Terminei o treino"
    assert errors == []


def test_raise_hint_only_after_three_sessions_at_the_same_weight(app_url, open_app):
    state = json.loads(json.dumps(SAMPLE))
    state["loads"] = {
        "Bíceps na máquina": {"2026-09-22": 25, "2026-09-29": 25, "2026-10-02": 25},
        "Rosca com barra W": {"2026-09-29": 10, "2026-10-02": 10},
    }
    page, errors = open_app(app_url(state), TUESDAY)
    go(page, "hoje")
    hints = page.locator(".exm.up").all_inner_texts()
    assert hints == ["25 kg nas últimas 3 vezes. Tenta subir."]
    assert errors == []


def test_invalid_weight_shows_a_warning(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY)
    go(page, "pesos")
    box = page.locator(".pw-l input").first
    box.fill("abc")
    box.press("Enter")
    assert "Peso inválido" in page.inner_text(".saved.err")
    assert errors == []


def test_finishing_shows_where_the_load_went_up(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY, init=PUBLISH_STUB)
    go(page, "hoje")
    box = page.locator('.exi input[data-kg="Rosca com barra W"]')
    box.fill("12")
    box.press("Enter")
    page.click('button[data-act="mark"]')
    page.wait_for_timeout(200)
    assert page.inner_text(".check .done-up") == "Carga maior hoje: Rosca com barra W +2 kg."
    assert errors == []


def test_reminds_to_mark_the_workout_after_logging_weights(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY)
    go(page, "hoje")
    assert "Anotou pesos hoje" not in page.inner_text(".w7-m")

    box = page.locator('.exi input[data-kg="Remada com apoio no peito"]')
    box.fill("41")
    box.press("Enter")
    go(page, "pesos")
    go(page, "hoje")
    message = page.inner_text(".w7-m")
    assert message.startswith("Anotou pesos hoje. Quando terminar, marca o treino lá embaixo")

    page.click('button[data-act="mark"]')
    page.wait_for_timeout(200)
    assert "Anotou pesos hoje" not in page.inner_text(".w7-m")
    assert errors == []


MONDAY = "2026-10-19T17:00:00-03:00"  # Peito e tríceps, com pendurar na barra


def with_loads(**loads):
    state = json.loads(json.dumps(SAMPLE))
    state["loads"] = {k.replace("_", " "): v for k, v in loads.items()}
    return state


def tap_point(page, index):
    page.evaluate("document.querySelector('.lc svg').scrollIntoView({block: 'center'})")
    box = page.locator(".lc svg").bounding_box()
    x = page.evaluate(f"+document.querySelectorAll('.lc .lc-p')[{index}].getAttribute('cx')")
    width = page.evaluate("document.querySelector('.lc svg').viewBox.baseVal.width")
    page.mouse.click(box["x"] + x / width * box["width"], box["y"] + box["height"] / 2)


def test_pesos_chart_shows_the_history_of_an_exercise(app_url, open_app):
    state = with_loads(**{"Bíceps na máquina": {"2026-09-22": 22.5, "2026-09-29": 25, "2026-10-02": 25}})
    page, errors = open_app(app_url(state), TUESDAY)
    go(page, "pesos")
    page.click('button[data-chart="Bíceps na máquina"]')
    assert page.locator(".lc .lc-p").count() == 3
    assert page.inner_text(".lc-r b") == "25 kg"
    assert page.locator(".lc-tab tr").count() == 3

    tap_point(page, 0)
    assert page.inner_text(".lc-r b") == "22,5 kg"
    assert page.inner_text(".lc-r span") == "22/09"

    page.click('button[data-chart="Bíceps na máquina"]')
    assert page.locator(".lc").count() == 0
    assert errors == []


def test_pesos_chart_with_a_single_record_explains_what_is_missing(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY)
    go(page, "pesos")
    page.click('button[data-chart="Rosca com barra W"]')
    assert page.inner_text(".lc-one").startswith("Só um registro até agora: 10 kg em 29/09.")
    assert errors == []


def test_bar_hang_is_logged_in_seconds_and_not_copied(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), MONDAY, init=PUBLISH_STUB)
    go(page, "hoje")
    row = page.locator(".exi", has_text="Pendurar na barra")
    assert row.locator(".kg span").inner_text() == "s"
    assert "Meta: 30 s." in row.inner_text()
    assert page.locator(".exi", has_text="Escapular na barra").locator("input").count() == 0

    box = row.locator("input")
    box.fill("25")
    box.press("Enter")
    page.click('button[data-act="mark"]')
    page.clock.fast_forward(9000)  # espera o "Salvando…" acabar
    loads = published_state(page)["loads"]
    assert loads["Pendurar na barra"] == {"2026-10-19": 25}

    go(page, "prog")
    assert "25 de 30 s" in page.inner_text(".pb")
    assert "Primeiro registro: 25 s em 19/10." in page.inner_text(".pb")
    assert errors == []


def test_hang_every_weekday_and_no_negatives_in_the_plan(app_url, open_app):
    for day in ("2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"):
        page, errors = open_app(app_url(SAMPLE), f"{day}T17:00:00-03:00")
        go(page, "hoje")
        names = page.locator(".exi .exn b").all_inner_texts()
        assert "Pendurar na barra" in names, day
        assert "Negativa na barra" not in names, day
        assert errors == []
    go(page, "prog")
    assert "negativas" not in page.inner_text(".pb"), "sem negativa anotada, o caminho é só o pendurar"
    assert "Depois da meta" in page.inner_text(".pb")


def test_bar_journey_has_goal_lines_and_says_when_ready(app_url, open_app):
    state = with_loads(
        **{
            "Pendurar na barra": {"2026-09-21": 20, "2026-09-28": 30},
            "Negativa na barra": {"2026-09-24": 3, "2026-10-01": 5},
        }
    )
    page, errors = open_app(app_url(state), TUESDAY)
    go(page, "prog")
    text = page.inner_text(".pb")
    assert "Pronto pra tentar" in text
    assert "Já dá pra tentar" in text
    assert page.locator(".pb .lc-goal").count() == 2
    assert "meta 30 s" in text and "meta 5 reps" in text
    ticks = page.locator(".pb .lc").nth(1).locator(".lc-t").all_text_contents()
    assert not any("," in t for t in ticks if t[0].isdigit()), "repetição não aparece quebrada no eixo"
    assert errors == []


def test_undo_keeps_bar_values(app_url, open_app):
    state = with_loads(**{"Pendurar na barra": {"2026-10-12": 25}})
    page, errors = open_app(app_url(state), MONDAY, init=PUBLISH_STUB)
    go(page, "hoje")
    box = page.locator(".exi", has_text="Pendurar na barra").locator("input")
    box.fill("25")
    box.press("Enter")
    page.click('button[data-act="mark"]')
    page.clock.fast_forward(9000)
    page.click('button[data-act="undo"]')
    page.click('button[data-act="undook"]')
    page.clock.fast_forward(1000)
    assert published_state(page)["loads"]["Pendurar na barra"]["2026-10-19"] == 25
    assert errors == []


# ---------- dias que ficaram sem marcar ----------
MON_AFTER = "2026-10-05T12:00:00-03:00"  # segunda; o exemplo vai até quinta, então a sexta 02/10 ficou em aberto


def page_ms(when):
    """O relógio da página em milissegundos, pra montar rascunhos com hora certa."""
    from datetime import datetime

    return int(datetime.fromisoformat(when).timestamp() * 1000)


def test_missed_day_card_marks_with_one_tap(app_url, open_app):
    state = json.loads(json.dumps(SAMPLE))
    state["loads"] = {"Tríceps na polia com corda": {"2026-10-02": 25}}
    page, errors = open_app(app_url(state), MON_AFTER, init=PUBLISH_STUB)
    go(page, "hoje")
    text = page.inner_text(".miss")
    assert "Ficou um dia sem marcar" in text
    assert "Sexta, 02/10" in text
    assert "Tríceps e braço · tem peso anotado" in text
    assert "volta pra 5 dias" in text
    assert "Sequência zerada" not in page.inner_text(".w7-m"), "o aviso já explica a sequência"

    page.click('.miss [data-act="miss-ok"]')
    page.clock.fast_forward(1000)
    assert published_state(page)["logs"]["2026-10-02"] == "Tríceps e braço"
    assert page.locator(".miss").count() == 0
    assert page.inner_text(".w7-a b") == "5"
    assert errors == []


def test_missed_days_open_the_day_and_can_be_dismissed(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY)  # segunda 05/10 e sexta 02/10 em aberto
    go(page, "hoje")
    assert "Ficaram 2 dias sem marcar" in page.inner_text(".miss")
    rows = page.locator(".miss li").all_inner_texts()
    assert rows[0].startswith("Segunda, 05/10") and rows[1].startswith("Sexta, 02/10")

    page.click('.miss [data-act="miss-open"][data-k="2026-10-05"]')
    assert page.inner_text(".sheet .sh-h b") == "Segunda-feira, 5 de outubro"
    page.click('.sheet [data-shtype="Peito e costas"]')
    page.click('.sheet [data-act="sh-tr"]')
    page.click('.sheet [data-act="sh-close"]')
    rows = page.locator(".miss li").all_inner_texts()
    assert len(rows) == 1 and rows[0].startswith("Sexta, 02/10"), "a sexta continua quebrando a sequência"

    page.click('.miss [data-act="miss-no"]')
    assert page.locator(".miss").count() == 0
    assert "Sequência zerada" not in page.inner_text(".w7-m"), "segunda marcada: a sequência é 1"
    page.reload()
    page.wait_for_timeout(300)
    go(page, "hoje")
    assert page.locator(".miss").count() == 0, "quem disse que não treinou não vê o aviso de novo"
    draft = json.loads(page.evaluate("localStorage.getItem('treinos-verao-logs')"))
    assert draft["data"]["logs"]["2026-10-05"] == "Peito e costas"
    assert errors == []


def test_weekend_shows_up_only_with_weights(app_url, open_app):
    state = json.loads(json.dumps(SAMPLE))
    state["logs"]["2026-10-02"] = "Tríceps e braço"
    state["loads"] = {"Supino sentado": {"2026-10-03": 30}, "Remada com apoio no peito": {"2026-10-03": 36}}
    page, errors = open_app(app_url(state), MON_AFTER)
    go(page, "hoje")
    rows = page.locator(".miss li").all_inner_texts()
    assert len(rows) == 1, "domingo sem peso anotado não aparece"
    assert rows[0].startswith("Sábado, 03/10")
    assert "Peito e costas · tem peso anotado" in rows[0], "o treino é o que tem os exercícios anotados"
    assert errors == []


def test_no_missed_card_without_recent_training(app_url, open_app):
    page, errors = open_app(app_url({}), MON_AFTER)
    go(page, "hoje")
    assert page.locator(".miss").count() == 0, "quem ainda não começou não recebe aviso"

    page2, errors2 = open_app(app_url(SAMPLE), "2026-10-14T12:00:00-03:00")
    go(page2, "hoje")
    assert page2.locator(".miss").count() == 0, "duas semanas parado não é esquecimento"
    assert errors == [] and errors2 == []


# ---------- folha do dia ----------
def test_day_sheet_saves_run_distance(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY, init=PUBLISH_STUB)
    go(page, "quadro")
    page.click('[data-day="2026-09-30"]')
    assert "1,70 km em 10:00" in page.inner_text(".sheet")
    page.click('.sheet [data-act="sh-close"]')

    page.click('[data-day="2026-10-01"]')
    page.click('.sheet [data-act="sh-rdist"]')
    page.fill("#skm", "abc")
    page.click('.sheet [data-act="sh-rsave"]')
    assert "Coloca a distância em km" in page.inner_text(".sheet .ferr")
    page.fill("#skm", "2,1")
    page.fill("#stime", "12:30")
    assert page.inner_text("#space") == "Ritmo: 5:57/km"
    page.press("#stime", "Enter")
    page.clock.fast_forward(1000)
    assert published_state(page)["runs"]["2026-10-01"] == {"km": 2.1, "min": 12.5}
    assert "2,10 km em 12:30" in page.inner_text(".sheet")
    assert errors == []


def test_no_supplements_to_mark(app_url, open_app):
    state = json.loads(json.dumps(SAMPLE))
    state["supp"] = {"2026-10-05": {"c": 1}}  # dado antigo continua guardado, só não aparece
    page, errors = open_app(app_url(state), TUESDAY)
    go(page, "hoje")
    text = page.inner_text("#root")
    assert "Creatina" not in text and "Whey" not in text
    go(page, "quadro")
    page.click('[data-day="2026-10-05"]')
    assert "Suplementos" not in page.inner_text(".sheet")
    page.click('.sheet [data-act="sh-close"]')
    go(page, "prog")
    assert "Meta de proteína pelo teu peso: 128 a 160 g por dia." in page.inner_text(".weigh")
    assert errors == []


def test_day_sheet_fits_a_short_phone(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY, width=320, height=568)
    go(page, "quadro")
    page.click('[data-day="2026-10-02"]')
    page.click('.sheet [data-act="sh-rdist"]')
    page.wait_for_timeout(400)  # a folha sobe com animação
    box = page.locator(".sheet").bounding_box()
    assert box["y"] >= 0 and box["y"] + box["height"] <= 568.5, "a folha cabe na tela e rola por dentro"
    page.click('.sheet [data-act="sh-close"]')
    assert page.locator(".sheet").count() == 0
    assert not page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    assert errors == []


def test_change_todays_workout_after_marking(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY, init=PUBLISH_STUB)
    go(page, "hoje")
    page.click('button[data-act="mark"]')
    page.clock.fast_forward(9000)
    page.click('button[data-act="retype"]')
    page.click('[data-retype="Peito e costas"]')
    page.clock.fast_forward(1000)
    assert published_state(page)["logs"]["2026-10-06"] == "Peito e costas"
    assert page.inner_text(".done-msg") == "Feito: Peito e costas"
    assert errors == []


# ---------- salvar sem perder nada ----------
def test_notes_made_on_an_older_version_are_kept(app_url, open_app):
    state = json.loads(json.dumps(SAMPLE))
    state["rev"] = 5
    draft = json.loads(json.dumps(SAMPLE))
    draft["logs"]["2026-10-06"] = "Costas e bíceps"
    draft["loads"]["Rosca com barra W"]["2026-10-06"] = 12
    draft["weight"]["2026-09-28"] = 90  # valor diferente do publicado: fica o publicado
    draft["supp"] = {"2026-10-06": {"c": 1}}
    note = {"base": 4, "t": page_ms(TUESDAY) - 3600_000, "data": draft}
    init = PUBLISH_STUB + f"localStorage.setItem('treinos-verao-logs', {json.dumps(json.dumps(note))});"
    page, errors = open_app(app_url(state), TUESDAY, init=init)
    go(page, "hoje")
    assert page.inner_text(".done-msg") == "Feito: Costas e bíceps"
    assert "Juntei o que tinha ficado só neste celular." in page.inner_text("body")

    go(page, "pesos")
    box = page.locator('.pw-l input[data-kg="Bíceps na máquina"]')
    box.fill("26")
    box.press("Enter")
    page.clock.fast_forward(31000)
    saved = published_state(page)
    assert saved["rev"] == 6
    assert saved["logs"]["2026-10-06"] == "Costas e bíceps"
    assert saved["loads"]["Rosca com barra W"] == {"2026-09-29": 10, "2026-10-06": 12}
    assert saved["loads"]["Bíceps na máquina"]["2026-10-06"] == 26
    assert saved["supp"]["2026-10-06"] == {"c": 1}, "dado antigo do rascunho também não se perde"
    assert saved["weight"]["2026-09-28"] == 80
    assert errors == []


def test_old_notes_from_another_version_are_dropped(app_url, open_app):
    state = json.loads(json.dumps(SAMPLE))
    state["rev"] = 5
    draft = json.loads(json.dumps(SAMPLE))
    draft["logs"]["2026-10-01"] = "Peito e costas"
    draft["logs"]["2026-09-20"] = "Outro"
    note = {"base": 4, "t": page_ms(TUESDAY) - 4 * 86400_000, "data": draft}
    init = f"localStorage.setItem('treinos-verao-logs', {json.dumps(json.dumps(note))});"
    page, errors = open_app(app_url(state), TUESDAY, init=init)
    go(page, "quadro")
    assert "20/09 — Outro" not in page.inner_text(".board") + "".join(
        page.locator(".d").evaluate_all("els => els.map(e => e.title)")
    )
    assert "Juntei" not in page.inner_text("body")
    assert errors == []


FLAKY_STUB = (
    "window.__pub=[];window.__tries=0;"
    "window.claude={use:n=>Promise.resolve(n==='artifact'?{publish:async h=>{window.__tries++;"
    "if(window.__tries===1){const e=new Error('falhou');e.code='upstream_error';throw e;}"
    "window.__pub.push(h)}}:null)};"
)
CONFLICT_STUB = (
    "window.__pub=[];"
    "window.claude={use:n=>Promise.resolve(n==='artifact'?{publish:async h=>{"
    "const e=new Error('outra versão');e.code='conflict';throw e;}}:null)};"
)


def test_publish_tries_again_once_after_a_passing_failure(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY, init=FLAKY_STUB)
    go(page, "hoje")
    page.click('button[data-act="mark"]')
    page.clock.fast_forward(4000)
    assert page.evaluate("window.__tries") == 2
    assert published_state(page)["logs"]["2026-10-06"] == "Costas e bíceps"
    assert page.locator(".saved.err").count() == 0
    assert errors == []


def test_conflict_keeps_the_note_for_the_reload(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY, init=CONFLICT_STUB)
    go(page, "hoje")
    page.click('button[data-act="mark"]')
    page.clock.fast_forward(1000)
    assert page.locator(".saved.err").count() == 0, "conflito não é erro: a tela recarrega com a versão nova"
    draft = json.loads(page.evaluate("localStorage.getItem('treinos-verao-logs')"))
    assert draft["data"]["logs"]["2026-10-06"] == "Costas e bíceps", "o treino fica guardado pra depois"
    page.clock.fast_forward(9000)
    assert page.is_enabled('button[data-act="undo"]'), "se não recarregar, os botões destravam"
    assert errors == []


def contrast(a, b):
    def lum(h):
        h = h.lstrip("#")
        cs = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
        cs = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in cs]
        return 0.2126 * cs[0] + 0.7152 * cs[1] + 0.0722 * cs[2]

    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_text_on_level_color_uses_the_more_readable_ink(app_url, open_app, scheme):
    page, errors = open_app(app_url(SAMPLE), TUESDAY, scheme)
    go(page, "hoje")
    done = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--done').trim()")
    ink = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--on-done').trim()")
    best = max(["#150800", "#ffffff"], key=lambda c: contrast(done, c))
    assert ink == best
    assert page.evaluate("getComputedStyle(document.querySelector('.go')).color") in (
        "rgb(21, 8, 0)",
        "rgb(255, 255, 255)",
    )
    assert errors == []


def test_saved_page_has_the_same_shape_as_the_published_one(app_url, open_app):
    """O app salvo tem um documento só, no formato do claude.ai (esqueleto + página dentro do body)."""
    from conftest import APP_HTML

    page, errors = open_app(app_url(SAMPLE), TUESDAY, init=PUBLISH_STUB)
    go(page, "hoje")
    page.click('button[data-act="mark"]')
    page.clock.fast_forward(1000)
    published = page.evaluate("window.__pub.at(-1)")
    outside = re.sub(r'<script id="app-script">.*?</script>', "", published, flags=re.S)
    assert outside.lower().count("<!doctype") == 1, "nada de documento dentro de documento"
    assert published.endswith("\n</body></html>")
    before, _, after = APP_HTML.partition('<script type="application/json" id="state">')
    pub_before, _, pub_after = published.partition('<script type="application/json" id="state">')
    assert pub_before == before, "tudo antes dos dados é igual ao arquivo do app"
    assert pub_after.split("</script>", 1)[1] == after.split("</script>", 1)[1]
    assert page.evaluate("document.documentElement.lang") == "pt-BR"
    assert page.title() == "Treinos até o verão"
    assert errors == []


# ---------- retrospectivas ----------
SUMMER_DAY = "2026-12-21T10:00:00-03:00"


def story_texts(page):
    """Passa por todas as histórias abertas, com a seta do teclado, e devolve o texto de cada uma."""
    texts = []
    for _ in range(40):
        texts.append(page.inner_text(".wr-in"))
        if page.locator(".wr-btns").count():
            break
        page.keyboard.press("ArrowRight")
    return texts


def test_summer_recap_opens_by_itself_with_the_season_numbers(app_url, open_app):
    page, errors = open_app(app_url(season_state()), SUMMER_DAY, motion="reduce")
    assert page.locator(".wr").count() == 1, "no dia 21/12 a retrospectiva abre sozinha"
    assert page.inner_text(".wr-tag") == "Retrospectiva do verão"
    texts = story_texts(page)
    full = "\n".join(texts)
    assert not any(bad in full for bad in BROKEN_TEXT)
    assert "Chegou o verão." in texts[0]
    total = next(t for t in texts if t.startswith("Você treinou"))
    assert "66" in total and "Foi em 94% dos dias úteis, e mais 2 vezes no fim de semana ou feriado." in total
    fav = next(t for t in texts if t.startswith("Seu treino mais feito"))
    assert "Costas e bíceps" in fav and "13 vezes. Depois vem Peito e costas, com 11." in fav
    run = next(t for t in texts if t.startswith("Você correu"))
    assert "61" in run and "Em 24 corridas" in run
    for kicker in ("Somando tudo, foram", "O músculo que mais trabalhou", "Onde você mais ficou forte",
                   "Rumo à primeira barra", "Sua maior sequência", "1% melhor a cada treino", "Peso do corpo",
                   "Seu nível", "Seu perfil de treino"):
        assert any(t.startswith(kicker) for t in texts), kicker
    assert not any(t.startswith("No ritmo de agora") for t in texts), "projeção é só na prévia"
    assert "Meu verão 2026" in texts[-1] and "14/09 a 21/12" in texts[-1]
    assert "Tira um print" in texts[-1]

    page.keyboard.press("Escape")
    page.wait_for_timeout(450)
    assert page.locator(".wr").count() == 0
    page.reload()
    page.wait_for_timeout(400)
    assert page.locator(".wr").count() == 0, "abre sozinha só uma vez"
    go(page, "hoje")
    assert "Ver de novo" in page.inner_text(".rcc"), "na semana do verão, o Hoje tem atalho pra rever"
    page.click(".rcc [data-recap]")
    assert page.locator(".wr").count() == 1
    assert errors == []


def test_preview_before_summer_from_progress(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY, motion="reduce")
    go(page, "prog")
    card = page.inner_text(".rcp-v")
    assert "prévia" in card.lower() and "4 treinos até aqui" in card
    assert page.locator(".rcp-m .chip").all_inner_texts() == ["Setembro", "Outubro, até agora"]

    page.click(".rcp-v")
    assert page.inner_text(".wr-tag") == "Prévia do verão"
    texts = story_texts(page)
    assert "Até aqui." in texts[0]
    assert any(t.startswith("No ritmo de agora") and "treinos até 21/12" in t for t in texts)
    assert any(t.startswith("Você correu") and "1,7" in t for t in texts)
    assert not any(t.startswith("Peso do corpo") for t in texts), "uma pesagem só não vira slide"
    assert not any(t.startswith("Onde você mais ficou forte") for t in texts), "carga sem subir não vira slide"
    assert "Meu verão até agora" in texts[-1] and "A completa sai em 21/12." in texts[-1]

    page.click('.wr [data-wr="again"]')
    assert page.inner_text(".wr-pos").startswith("1 de")
    page.click(".wr-x")
    page.wait_for_timeout(450)
    assert page.locator(".wr").count() == 0
    seen = page.evaluate("localStorage.getItem('treinos-recap-seen')")
    assert "verao" not in (seen or ""), "a prévia não conta como vista: a completa ainda vai abrir sozinha"
    assert page.evaluate("document.activeElement.dataset.recap") == "verao", "o foco volta pro cartão"
    assert errors == []


def test_month_recap_shows_up_on_the_first_days(app_url, open_app):
    url = app_url(season_state())
    page, errors = open_app(url, "2026-11-03T08:00:00-03:00", motion="reduce")
    go(page, "hoje")
    assert "Seu outubro em histórias" in page.inner_text(".rcc")
    page.click(".rcc [data-recap]")
    assert page.inner_text(".wr-tag") == "Retrospectiva de outubro"
    texts = story_texts(page)
    assert "Outubro" in texts[0] and "De 01/10 a 31/10." in texts[0]
    total = next(t for t in texts if t.startswith("Em outubro você treinou"))
    assert "21" in total and "São 8 a mais que em setembro." in total
    assert "Meu outubro" in texts[-1]
    page.keyboard.press("Escape")
    page.wait_for_timeout(450)
    assert page.locator(".rcc").count() == 0, "depois de ver, o aviso some"
    page.reload()
    page.wait_for_timeout(400)
    go(page, "hoje")
    assert page.locator(".rcc").count() == 0

    page2, errors2 = open_app(url, "2026-12-01T08:00:00-03:00")
    go(page2, "hoje")
    assert "Seu novembro em histórias" in page2.inner_text(".rcc")
    page2.click('.rcc [data-act="recap-skip"]')
    assert page2.locator(".rcc").count() == 0, "dá pra dispensar sem abrir"

    page3, errors3 = open_app(url, "2026-11-04T08:00:00-03:00")
    go(page3, "hoje")
    assert page3.locator(".rcc").count() == 0, "só nos 3 primeiros dias do mês"
    assert errors == [] and errors2 == [] and errors3 == []


def test_empty_recap_says_there_is_nothing_yet(app_url, open_app):
    page, errors = open_app(app_url({}), TUESDAY, motion="reduce")
    go(page, "prog")
    assert "0 treinos até aqui" in page.inner_text(".rcp-v")
    page.click(".rcp-v")
    texts = story_texts(page)
    assert len(texts) == 2 and "Nada marcado." in texts[1]
    page.click('.wr [data-wr="close"]')
    page.wait_for_timeout(450)
    assert page.locator(".wr").count() == 0
    assert errors == []


def test_story_taps_hold_and_keys(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY)
    page.clock.pause_at("2026-10-06T13:30:05-03:00")  # daqui pra frente o tempo só anda quando o teste manda
    go(page, "prog")
    page.click(".rcp-v")
    pos = lambda: page.inner_text(".wr-pos").split(" de ")[0]  # noqa: E731
    assert pos() == "1"
    page.clock.run_for(6600)
    assert pos() == "2", "passa sozinho depois de uns 6 segundos"
    page.mouse.click(330, 420)
    assert pos() == "3", "toque na direita avança"
    page.mouse.click(40, 420)
    assert pos() == "2", "toque na esquerda volta"
    page.mouse.move(330, 420)
    page.mouse.down()
    page.clock.run_for(9000)
    assert pos() == "2", "segurando, fica parado"
    page.mouse.up()
    assert pos() == "2", "soltar não conta como toque"
    page.clock.run_for(7000)
    assert pos() == "3", "solto, volta a andar"
    page.keyboard.press("ArrowRight")
    assert pos() == "4"
    page.keyboard.press("ArrowLeft")
    assert pos() == "3"
    page.keyboard.press("Escape")
    page.clock.run_for(500)
    assert page.locator(".wr").count() == 0
    assert errors == []


@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_recap_fits_a_small_phone(app_url, open_app, scheme):
    page, errors = open_app(app_url(season_state()), SUMMER_DAY, scheme, width=320, height=568, motion="reduce")
    for _ in range(30):
        fits = page.evaluate(
            """() => {
              const body = document.querySelector('.wr-body');
              const bigs = [...document.querySelectorAll('.wr-big, .wp-h b')];
              return body.scrollWidth <= body.clientWidth && bigs.every((b) => b.scrollWidth <= b.clientWidth + 1);
            }"""
        )
        assert fits, f"slide {page.inner_text('.wr-pos')} passa da largura"
        if page.locator(".wr-btns").count():
            break
        page.keyboard.press("ArrowRight")
    page.locator('.wr [data-wr="close"]').scroll_into_view_if_needed()
    page.click('.wr [data-wr="close"]')
    assert errors == []


def test_after_summer_the_app_keeps_going(app_url, open_app):
    page, errors = open_app(app_url(season_state()), "2026-12-28T09:00:00-03:00", motion="reduce")
    page.keyboard.press("Escape")  # a retrospectiva abriu sozinha
    page.wait_for_timeout(450)
    go(page, "hoje")
    assert page.inner_text(".count").replace("\n", " ") == "8º dia do verão"
    go(page, "quadro")
    assert page.inner_text("h2.first") == "Calendário"
    assert page.inner_text(".qsub") == "66 treinos até o verão. Agora é manter."
    assert page.locator('[data-day="2027-01-03"]').count() == 1, "o calendário vai até o domingo desta semana"
    assert page.locator('[data-day="2027-01-04"]').count() == 0
    page.click('[data-day="2026-12-26"]')
    page.click('.sheet [data-shtype="Surf"]')
    page.click('.sheet [data-act="sh-tr"]')
    draft = json.loads(page.evaluate("localStorage.getItem('treinos-verao-logs')"))
    assert draft["data"]["logs"]["2026-12-26"] == "Surf"
    page.click('.sheet [data-act="sh-close"]')
    assert "e 1 depois dele" in page.inner_text(".qsub")
    go(page, "prog")
    assert "Projeção pro verão" not in page.inner_text(".weigh")
    assert errors == []


def test_christmas_and_new_year_are_holidays(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), "2026-12-24T09:00:00-03:00", motion="reduce")
    page.keyboard.press("Escape")  # depois de 21/12 a retrospectiva abre sozinha na primeira vez
    page.wait_for_timeout(450)
    go(page, "hoje")
    assert "Amanhã (25/12) é feriado: Natal" in page.inner_text(".holi")
    page2, errors2 = open_app(app_url(SAMPLE), "2026-12-31T09:00:00-03:00", motion="reduce")
    page2.keyboard.press("Escape")
    page2.wait_for_timeout(450)
    go(page2, "hoje")
    assert "Amanhã (01/01) é feriado: Ano-Novo" in page2.inner_text(".holi")
    assert errors == [] and errors2 == []


def test_a_save_waits_for_the_story_to_close(app_url, open_app):
    """Publicar recarrega a página: com a retrospectiva aberta, a publicação espera ela fechar."""
    page, errors = open_app(app_url(SAMPLE), TUESDAY, init=PUBLISH_STUB, motion="reduce")
    go(page, "pesos")
    box = page.locator('.pw-l input[data-kg="Bíceps na máquina"]')
    box.fill("27,5")
    box.press("Enter")  # o peso publica numa pausa de uns 30 s
    go(page, "prog")
    page.click(".rcp-v")
    page.clock.fast_forward(40000)
    assert page.evaluate("window.__pub.length") == 0, "nada de recarregar no meio da história"
    assert page.locator(".wr").count() == 1
    page.keyboard.press("Escape")
    page.clock.fast_forward(2000)
    assert published_state(page)["loads"]["Bíceps na máquina"]["2026-10-06"] == 27.5
    assert errors == []


def test_progress_lists_how_each_load_went_up(app_url, open_app):
    state = json.loads(json.dumps(SAMPLE))
    state["loads"] = {
        "Supino sentado": {"2026-10-03": 32, "2026-10-05": 32, "2026-10-08": 41},
        "Rosca com barra W": {"2026-09-29": 10},
        "Puxada (aberta)": {"2026-10-03": 32, "2026-10-06": 35},
    }
    page, errors = open_app(app_url(state), TUESDAY)
    go(page, "prog")
    rows = page.locator(".lp-l li").all_inner_texts()
    assert rows[0].startswith("Supino sentado") and "32 → 41 kg" in rows[0] and "+9 kg" in rows[0]
    assert "Puxada (aberta)" in rows[1] and "+3 kg" in rows[1]
    assert "um registro" in rows[2]
    assert "A carga subiu em 2 de 3 exercícios" in page.inner_text(".lp")
    page.click('[data-lp="Puxada (aberta)"]')
    assert page.locator('[data-nav="pesos"][aria-current="page"]').count() == 1
    assert page.locator(".lc").count() == 1, "abre o gráfico do exercício"
    assert errors == []


def test_dashboard_shows_everything_week_by_week(app_url, open_app):
    page, errors = open_app(app_url(season_state()), "2026-12-10T14:00:00-03:00")
    go(page, "prog")
    kpi = page.inner_text(".dk")
    for label in ("TREINOS", "SEQUÊNCIA", "CORRIDA", "PESO", "FORÇA", "NÍVEL"):
        assert label in kpi.upper()
    assert page.locator(".dash .dpn").count() == 4
    assert page.inner_text(".dr").startswith("Esta semana")
    box = page.locator(".dash .dpn svg").first.bounding_box()
    page.mouse.click(box["x"] + 12, box["y"] + box["height"] / 2)
    assert page.inner_text(".dr").startswith("14/09 a 20/09"), "tocar numa semana mostra os valores dela"
    page.focus(".dash")
    page.keyboard.press("ArrowRight")
    assert page.inner_text(".dr").startswith("21/09 a 27/09")
    assert not any(bad in page.inner_text(".dash") for bad in BROKEN_TEXT)
    assert errors == []


def test_dashboard_without_runs_or_weights_explains_what_is_missing(app_url, open_app):
    state = json.loads(json.dumps(SAMPLE))
    state["runs"], state["weight"] = {}, {}
    page, errors = open_app(app_url(state), TUESDAY)
    go(page, "prog")
    text = page.inner_text(".dash")
    assert "Marca as corridas com a distância pra aparecer aqui." in text
    assert "Anota o peso uma vez por semana." in text
    assert page.locator(".dash .dpn svg").count() == 2, "treinos sempre aparece (meta); força com os pesos anotados"
    assert "0 semanas fechadas em 5/5" in text
    assert page.locator("h2", has_text="Retrospectivas").count() == 1
    order = page.locator("#root h2").all_inner_texts()
    assert order.index("Painel geral") < order.index("Retrospectivas") < order.index("Resumo da semana")
    assert errors == []


def test_recap_says_ready_when_the_hang_goal_is_hit(app_url, open_app):
    state = json.loads(json.dumps(SAMPLE))
    state["loads"] = {"Pendurar na barra": {"2026-09-28": 18, "2026-10-05": 31}}
    page, errors = open_app(app_url(state), TUESDAY, motion="reduce")
    go(page, "prog")
    page.click(".rcp-v")
    texts = story_texts(page)
    bar = next(t for t in texts if t.startswith("Rumo à primeira barra"))
    assert "Meta batida." in bar and "Aguentou 31 s pendurado. Agora é tentar a primeira barra." in bar
    assert errors == []


def test_weigh_in_reminder_fits_a_gym_scale(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY)
    go(page, "hoje")
    assert "Sempre na mesma balança e no mesmo horário." in page.inner_text(".wrem")
    assert "jejum" not in page.inner_text("#root")
    assert errors == []


# ---------- visuais ----------
def test_the_app_opens_in_mare_until_another_look_is_picked(app_url, open_app):
    old_try = "localStorage.setItem('treinos-skin', 'caderno');"  # escolha da versão de teste, antes do padrão
    page, errors = open_app(app_url(SAMPLE), TUESDAY, init=old_try)
    assert page.evaluate("document.documentElement.dataset.skin") == "mare"
    go(page, "prog")
    buttons = page.locator(".skins button")
    assert buttons.first.get_attribute("data-skin") == "mare", "a Maré, que é o padrão, vem primeiro"
    assert buttons.first.get_attribute("aria-pressed") == "true"
    assert page.evaluate("localStorage.getItem('treinos-skin')") is None
    page.click('.skins [data-skin=""]')
    assert page.evaluate("document.documentElement.dataset.skin") is None, "o original continua pra escolher"
    page.reload()
    page.wait_for_timeout(300)
    assert page.evaluate("document.documentElement.dataset.skin") is None, "e fica escolhido depois de abrir de novo"
    assert errors == []


@pytest.mark.parametrize("skin", ["anilha", "caderno", ""])
def test_each_look_can_be_picked_and_stays_on_the_phone(app_url, open_app, skin):
    page, errors = open_app(app_url(SAMPLE), TUESDAY)
    go(page, "prog")
    page.click(f'.skins [data-skin="{skin}"]')
    assert page.evaluate("document.documentElement.dataset.skin") == (skin or None)
    assert page.get_attribute(f'.skins [data-skin="{skin}"]', "aria-pressed") == "true"
    page.reload()
    page.wait_for_timeout(300)
    assert page.evaluate("document.documentElement.dataset.skin") == (skin or None), "a escolha fica salva neste celular"
    go(page, "prog")
    page.click('.skins [data-skin="mare"]')
    assert page.evaluate("document.documentElement.dataset.skin") == "mare", "volta pro padrão"
    assert errors == []


@pytest.mark.parametrize("scheme", ["dark", "light"])
@pytest.mark.parametrize("skin", ["mare", "anilha", "caderno", ""])
def test_each_look_renders_every_tab_on_a_small_phone(app_url, open_app, skin, scheme):
    page, errors = open_app(app_url(season_state()), "2026-11-10T17:00:00-03:00", scheme, init=look(skin), width=320, height=640)
    assert page.evaluate("document.documentElement.dataset.skin") == (skin or None)
    for tab in TABS:
        go(page, tab)
        text = page.inner_text("#root")
        assert not any(bad in text for bad in BROKEN_TEXT), f"texto quebrado na aba {tab}"
        assert not page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"), tab
    go(page, "quadro")
    page.click('[data-day="2026-11-09"]')
    assert page.locator(".sheet").count() == 1
    # a cor do nível vem da escada do visual e o texto em cima dela é o que contrasta mais
    done = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--done').trim()")
    ink = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--on-done').trim()")
    assert ink == max(["#150800", "#ffffff"], key=lambda c: contrast(done, c))
    assert errors == []


# ---------- virada do dia com o app aberto ----------
def test_the_day_turns_with_the_app_open(app_url, open_app):
    """Meia-noite com o app aberto: espera a pessoa terminar de digitar, guarda o peso no dia em que ele foi
    feito e depois mostra o dia novo. Quem volta no outro dia com o campo ainda selecionado vê o dia certo."""
    page, errors = open_app(app_url(SAMPLE), "2026-10-06T23:58:40-03:00")  # terça, Costas e bíceps
    go(page, "hoje")
    box = page.locator('.exi input[data-kg="Bíceps na máquina"]')
    box.click()
    page.keyboard.press("Control+A")
    page.keyboard.type("27")
    page.clock.run_for(65000)  # 23:59:45
    page.keyboard.type(",5")
    page.clock.run_for(60000)  # 00:00:45: virou, mas a pessoa ainda está digitando
    assert page.inner_text(".date").startswith("Terça-feira, 6 de outubro")
    assert page.evaluate("document.activeElement.dataset.kg") == "Bíceps na máquina"
    assert box.input_value() == "27,5"
    with page.expect_navigation():
        page.clock.run_for(125000)  # parou de digitar faz mais de 2 min: atualiza
    page.wait_for_timeout(300)
    assert page.inner_text(".date").startswith("Quarta-feira, 7 de outubro")
    data = page.evaluate("JSON.parse(localStorage.getItem('treinos-verao-logs')).data")
    assert data["loads"]["Bíceps na máquina"]["2026-10-06"] == 27.5, "o peso fica no dia em que foi digitado"
    assert "2026-10-07" not in data["loads"]["Bíceps na máquina"]
    assert errors == []


STORY_STYLE = """(() => [...document.querySelectorAll('.wr *')].filter((e) => !(e instanceof SVGElement)).map((e) => {
  const s = getComputedStyle(e);
  return [e.className, s.fontFamily, s.fontSize, s.fontVariationSettings, s.textTransform, s.backgroundImage];
}))()"""


@pytest.mark.parametrize("skin", ["mare", "anilha", "caderno"])
def test_recap_keeps_its_own_look_in_every_skin(app_url, open_app, skin):
    """A retrospectiva é igual em todos os visuais: os títulos do visual não entram nela."""
    def styles(page):
        go(page, "prog")
        page.click(".rcp-v")
        out = []
        for _ in range(20):  # passa por todas as telas da história
            out.append(page.evaluate(STORY_STYLE))
            if page.locator(".wr-btns").count():
                break
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(50)
        return out

    url = app_url(season_state())
    base, errors0 = open_app(url, "2026-11-10T17:00:00-03:00", init=look(""), motion="reduce")
    want = styles(base)
    assert len(want) > 5 and any("wr-big" in x[0] for slide in want for x in slide)
    page, errors = open_app(url, "2026-11-10T17:00:00-03:00", init=look(skin), motion="reduce")
    assert styles(page) == want
    assert errors0 == [] and errors == []


@pytest.mark.parametrize("scheme,word", [("light", "da caneta "), ("dark", "do giz ")])
def test_level_up_shows_and_names_the_new_color(app_url, open_app, scheme, word):
    """Subiu de nível: a barra enche com a cor nova e o nome bate com ela (no Caderno, caneta de dia, giz de noite)."""
    init = look("caderno") + "localStorage.setItem('treinos-lvl', '1');"
    page, errors = open_app(app_url(season_state()), "2026-11-10T17:00:00-03:00", scheme, init=init, motion="reduce")
    assert page.locator(".splash.lvup").count() == 1
    assert word in page.inner_text(".splash .sp-s")
    done = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--done').trim()")
    bar = page.evaluate("getComputedStyle(document.querySelector('.splash .sp-bar i')).backgroundColor")
    r, g, b = (int(done[i:i + 2], 16) for i in (1, 3, 5))
    assert bar == f"rgb({r}, {g}, {b})"
    assert errors == []


# ---------- tela que não consegue salvar ----------
DENIED_STUB = (
    "window.__pub=[];window.__tries=0;"
    "window.claude={use:n=>Promise.resolve(n==='artifact'?{publish:async h=>{window.__tries++;"
    "const e=new Error('sem permissão');e.code='not_granted';throw e;}}:null)};"
)
NO_ARTIFACT_STUB = "window.claude={use:n=>Promise.resolve(null)};"


def test_a_screen_that_cannot_save_never_locks_the_fields(app_url, open_app):
    """Se esta tela não pode publicar, nada trava: dá pra seguir anotando, fica no celular e o topo avisa."""
    page, errors = open_app(app_url(SAMPLE), TUESDAY, init=DENIED_STUB)
    go(page, "hoje")
    box = page.locator('.exi input[data-kg="Bíceps na máquina"]')
    box.fill("25")
    box.press("Enter")
    page.clock.fast_forward(31000)
    assert page.evaluate("window.__tries") == 1
    assert "Anotando só neste celular" in page.inner_text(".nosave")
    other = page.locator('.exi input[data-kg="Voador invertido (costas)"]')
    assert other.is_enabled(), "o campo seguinte continua aceitando o peso"
    other.fill("39")
    other.press("Enter")
    assert page.is_enabled('button[data-act="mark"]')
    page.click('button[data-act="mark"]')
    page.clock.fast_forward(31000)
    assert page.evaluate("window.__tries") == 1, "não fica tentando publicar de novo a cada toque"
    draft = json.loads(page.evaluate("localStorage.getItem('treinos-verao-logs')"))["data"]
    assert draft["loads"]["Voador invertido (costas)"]["2026-10-06"] == 39
    assert draft["loads"]["Bíceps na máquina"]["2026-10-06"] == 25
    assert draft["logs"]["2026-10-06"] == "Costas e bíceps"
    go(page, "quadro")
    assert page.locator(".nosave").count() == 1, "o aviso aparece em todas as abas"
    assert errors == []


def test_claude_view_without_saving_says_so_and_keeps_notes(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY, init=NO_ARTIFACT_STUB)
    page.wait_for_timeout(100)
    go(page, "pesos")
    assert page.locator(".nosave").count() == 1
    box = page.locator('.pw-l input[data-kg="Bíceps na máquina"]')
    box.fill("26")
    box.press("Enter")
    draft = json.loads(page.evaluate("localStorage.getItem('treinos-verao-logs')"))["data"]
    assert draft["loads"]["Bíceps na máquina"]["2026-10-06"] == 26
    assert errors == []


def test_outside_claude_saving_on_the_phone_needs_no_warning(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY)  # GitHub Pages ou o arquivo aberto direto
    page.wait_for_timeout(100)
    assert page.locator(".nosave").count() == 0
    assert errors == []


def test_notes_left_on_the_phone_go_up_on_the_first_tap(app_url, open_app):
    """Anotação que ficou só no celular (tela que não salvava) vai pro app no primeiro toque, sem esperar."""
    state = json.loads(json.dumps(SAMPLE))
    state["rev"] = 5
    draft = json.loads(json.dumps(SAMPLE))
    draft["loads"]["Voador invertido (costas)"] = {"2026-10-06": 39}
    note = {"base": 5, "t": page_ms(TUESDAY) - 600_000, "data": draft}
    init = PUBLISH_STUB + f"localStorage.setItem('treinos-verao-logs', {json.dumps(json.dumps(note))});"
    page, errors = open_app(app_url(state), TUESDAY, init=init)
    page.clock.fast_forward(10000)
    assert page.evaluate("window.__pub.length") == 0, "abrir não publica nada sozinho"
    go(page, "hoje")
    assert page.input_value('.exi input[data-kg="Voador invertido (costas)"]') == "39"
    page.clock.fast_forward(4000)
    saved = published_state(page)
    assert saved["loads"]["Voador invertido (costas)"]["2026-10-06"] == 39
    assert saved["rev"] == 6
    assert errors == []


def test_nothing_is_sent_on_the_first_tap_when_there_is_nothing_new(app_url, open_app):
    state = json.loads(json.dumps(SAMPLE))
    state["rev"] = 5
    note = {"base": 5, "t": page_ms(TUESDAY) - 600_000, "data": json.loads(json.dumps(SAMPLE))}
    init = PUBLISH_STUB + f"localStorage.setItem('treinos-verao-logs', {json.dumps(json.dumps(note))});"
    page, errors = open_app(app_url(state), TUESDAY, init=init)
    go(page, "pesos")
    page.clock.fast_forward(10000)
    assert page.evaluate("window.__pub.length") == 0
    assert errors == []
