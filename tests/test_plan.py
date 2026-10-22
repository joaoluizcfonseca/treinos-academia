"""Montar o treino: criar exercício, escolher os dias, mudar séries, reordenar e excluir (com desfazer)."""
import json

import pytest

from conftest import SAMPLE, season_state
from test_app import BROKEN_TEXT, PUBLISH_STUB, go, look, published_state

WED = "2026-10-21T11:30:00-03:00"  # quarta: Ombro e abdômen
DRAFT = "JSON.parse(localStorage.getItem('treinos-verao-logs')).data"


def open_pesos(open_app, app_url, state=SAMPLE, when=WED, **kw):
    page, errors = open_app(app_url(state), when, **kw)
    go(page, "pesos")
    return page, errors


def session(page):
    """Exercícios do treino de hoje, na ordem, com séries e repetições."""
    go(page, "hoje")
    return [x.replace("\n", " | ") for x in page.locator(".check .exn").all_inner_texts()]


def edit_rows(page):
    return [x.replace("\n", " | ") for x in page.locator(".pw.editing .pe-x").all_inner_texts()]


def snack(page):
    return page.inner_text(".snack span")


def test_new_exercise_goes_into_the_chosen_days(app_url, open_app):
    page, errors = open_pesos(open_app, app_url)
    page.click(".pe-new")
    assert page.locator(".sheet.xs").count() == 1
    assert page.evaluate("document.activeElement.id") == "xs-name", "o teclado já abre no nome"
    today = page.locator('[data-xsday="Ombro e abdômen"]')
    assert today.get_attribute("aria-pressed") == "true", "o treino de hoje já vem marcado"
    page.fill("#xs-name", "leg press")
    page.click('[data-xsday="Tríceps e braço"]')
    page.click('[data-xs="sets"][data-d="1"]')
    page.click('[data-xs="reps"][data-d="-1"]')
    page.click('[data-xs="reps"][data-d="-1"]')
    page.click('[data-xsg="Pernas"]')
    page.click('.xs [data-act="xs-save"]')
    assert page.locator(".sheet.xs").count() == 0
    assert snack(page) == "Leg press entrou nos treinos de quarta e sexta."
    assert edit_rows(page)[-1] == "Leg press | 4x10, pernas", "o treino abre montando, com o exercício no fim"
    plan = page.evaluate(DRAFT)["plan"]["2026-10-21"]
    assert plan["Ombro e abdômen"][-1] == ["Leg press", "4x10", "Pernas", "kg"]
    assert plan["Tríceps e braço"][-1] == ["Leg press", "4x10", "Pernas", "kg"]
    assert session(page)[-1] == "Leg press | 4x10, pernas"
    assert page.locator('.check input[data-kg="Leg press"]').count() == 1, "com peso: tem onde anotar"
    page.clock.set_system_time("2026-10-23T11:30:00-03:00")  # sexta
    page.reload()
    page.wait_for_timeout(300)
    assert "Leg press | 4x10, pernas" in session(page)
    assert errors == []


def test_an_exercise_that_already_exists_keeps_its_weights(app_url, open_app):
    page, errors = open_pesos(open_app, app_url)
    page.click(".pe-new")
    page.fill("#xs-name", "rosca")
    sug = page.locator(".xs-s")
    assert sug.first.inner_text().startswith("Rosca com barra W")
    sug.first.click()
    assert page.input_value("#xs-name") == "Rosca com barra W"
    assert page.inner_text("#xs-hint") == (
        "Esse já existe: está no treino de terça e sexta. Os pesos que tu anotou nele continuam valendo."
    )
    biceps = page.locator('[data-xsg="Bíceps"]')
    assert biceps.get_attribute("aria-pressed") == "true" and biceps.is_disabled(), "músculo e tipo vêm dele"
    assert page.inner_text("#xs-sets") == "3" and page.inner_text("#xs-reps") == "10"
    page.click('.xs [data-act="xs-save"]')
    assert "Rosca com barra W | 3x10, bíceps" in session(page)
    assert page.input_value('.check input[data-kg="Rosca com barra W"]') == "10", "o último peso anotado vem junto"
    # escrevendo o nome igual (sem acento, sem maiúscula) também reconhece
    go(page, "pesos")
    page.click(".pe-new")
    page.fill("#xs-name", "abdomen na maquina")
    assert page.inner_text("#xs-hint").startswith("Esse já existe")
    page.click('.xs [data-act="xs-save"]')
    assert page.inner_text("#xs-err") == "Abdômen na máquina já está no treino de quarta."
    assert errors == []


def test_deleting_an_exercise_can_be_undone(app_url, open_app):
    page, errors = open_pesos(open_app, app_url)
    page.click(".pw.open .pe-go")
    before = edit_rows(page)
    assert before[3] == "Prancha | 3x30s, abdômen, peso do corpo"
    page.click('[aria-label="Excluir Prancha do treino"]')
    assert "Prancha | 3x30s, abdômen, peso do corpo" not in edit_rows(page)
    focused = "document.activeElement.getAttribute('aria-label')"
    assert page.evaluate(focused) == "Excluir Pendurar na barra do treino", "o foco vai pra linha de baixo"
    assert snack(page) == "Prancha saiu do treino de quarta."
    page.click('.snack [data-act="snack-undo"]')
    assert edit_rows(page) == before, "volta no mesmo lugar"
    assert page.locator(".snack").count() == 0
    page.click('[aria-label="Excluir Prancha do treino"]')
    assert not any(x.startswith("Prancha") for x in session(page))
    assert errors == []


def test_order_and_sets_change_the_workout(app_url, open_app):
    page, errors = open_pesos(open_app, app_url)
    page.click(".pw.open .pe-go")
    page.click('[aria-label="Subir Elevação lateral"]')
    assert edit_rows(page)[:2] == ["Elevação lateral | 3x12, ombro", "Ombro na máquina | 3x10, ombro"]
    assert page.evaluate("document.activeElement.getAttribute('aria-label')") == "Descer Elevação lateral", (
        "o foco segue o exercício que subiu (o de subir ficou desligado no topo)"
    )
    page.click('[aria-label="Mudar séries e repetições de Ombro na máquina"]')
    assert page.inner_text(".xs #xs-t") == "Ombro na máquina"
    page.click('[data-xs="sets"][data-d="1"]')
    page.click('[data-xs="reps"][data-d="-1"]')
    page.click('[data-xs="reps"][data-d="-1"]')
    page.click('.xs [data-act="xs-save"]')
    assert snack(page) == "Ombro na máquina: agora 4x8."
    assert session(page)[:2] == ["Elevação lateral | 3x12, ombro", "Ombro na máquina | 4x8"]
    assert errors == []


def test_past_workouts_keep_the_plan_they_had(app_url, open_app):
    """Tirar um exercício hoje não muda o que já foi feito: as contas do passado ficam iguais."""
    seen = "localStorage.setItem('treinos-recap-seen', JSON.stringify(['verao']));"
    page, errors = open_app(app_url(season_state()), "2026-11-10T14:00:00-03:00", init=seen)

    def months():
        go(page, "prog")
        page.click(".yr-tab summary")
        return {r.split("\t")[0]: r for r in page.locator(".yr-tab tbody tr").all_inner_texts()}

    before = months()
    go(page, "pesos")
    page.click('[data-pw="Peito e tríceps"]')
    page.click('.pw.open .pe-go')
    page.click('[aria-label="Excluir Supino sentado do treino"]')
    after = months()
    assert after["set 2026"] == before["set 2026"] and after["out 2026"] == before["out 2026"]
    page.clock.set_system_time("2026-11-16T14:00:00-03:00")  # a segunda seguinte
    page.reload()
    page.wait_for_timeout(300)
    assert not any(x.startswith("Supino sentado") for x in session(page)), "daqui pra frente, sem o supino"
    assert months()["out 2026"] == before["out 2026"]
    assert errors == []


def test_saturday_light_workout_can_get_bodyweight_exercises(app_url, open_app):
    page, errors = open_pesos(open_app, app_url)
    assert page.locator('[data-pw="Peito e costas leve"]').inner_text().endswith("Sábado (opcional), 0 de 3 com peso")
    page.click(".pe-new")
    page.fill("#xs-name", "Abdominal infra")
    page.click('[data-xsday="Ombro e abdômen"]')  # tira o de hoje
    page.click('[data-xsday="Peito e costas leve"]')
    page.click('[data-xskind="corpo"]')
    page.click('[data-xsg="Abdômen"]')
    page.click('[data-xsunit="s"]')
    assert page.inner_text("#xs-rl") == "Segundos" and page.inner_text("#xs-reps") == "30"
    page.click('[data-xs="reps"][data-d="1"]')
    page.click('.xs [data-act="xs-save"]')
    assert snack(page) == "Abdominal infra entrou no treino de sábado."
    page.clock.set_system_time("2026-10-24T10:00:00-03:00")  # sábado
    page.reload()
    page.wait_for_timeout(300)
    assert "Abdominal infra | 3x35s, abdômen" in session(page)
    assert page.locator('.check input[data-kg^="Abdominal infra"]').count() == 0, "peso do corpo: nada pra anotar"
    assert errors == []


def test_the_sheet_says_what_is_missing(app_url, open_app):
    page, errors = open_pesos(open_app, app_url)
    page.click(".pe-new")
    page.click('.xs [data-act="xs-save"]')
    assert page.inner_text("#xs-err") == "Escreve o nome do exercício."
    page.fill("#xs-name", "Leg press")
    assert page.inner_text("#xs-err") == "", "o aviso some quando a pessoa corrige"
    page.click('.xs [data-act="xs-save"]')
    assert page.inner_text("#xs-err") == "Escolhe o músculo que ele trabalha."
    page.click('[data-xsg="Pernas"]')
    page.click('[data-xsday="Ombro e abdômen"]')
    page.click('.xs [data-act="xs-save"]')
    assert page.inner_text("#xs-err") == "Escolhe pelo menos um dia."
    page.keyboard.press("Escape")
    assert page.locator(".sheet.xs").count() == 0
    plan = page.evaluate("(JSON.parse(localStorage.getItem('treinos-verao-logs') || 'null') || {data: {}}).data.plan")
    assert not plan, "cancelar não muda nada"
    assert errors == []


def test_the_hoje_shortcut_opens_the_workout_to_edit(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), WED)
    go(page, "hoje")
    page.click('.ck-a [data-act="plan-edit"]')
    assert page.locator('[data-nav="pesos"][aria-current="page"]').count() == 1
    assert page.locator('.pw.editing [data-pw="Ombro e abdômen"]').count() == 1
    page.click('.pw.editing [data-act="plan-done"]')
    assert page.locator(".pw.editing").count() == 0
    assert page.locator('.pw.open .pw-l input[data-kg="Ombro na máquina"]').count() == 1, "volta pros pesos"
    assert errors == []


def test_plan_changes_are_published_with_the_app(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), WED, init=PUBLISH_STUB)
    go(page, "pesos")
    page.click(".pw.open .pe-go")
    page.click('[aria-label="Excluir Pendurar na barra do treino"]')
    assert page.evaluate("window.__pub.length") == 0, "espera uma pausa antes de publicar"
    page.clock.run_for(31000)
    page.wait_for_timeout(200)
    plan = published_state(page)["plan"]["2026-10-21"]["Ombro e abdômen"]
    assert [e[0] for e in plan] == ["Ombro na máquina", "Elevação lateral", "Abdômen na máquina", "Prancha"]
    assert errors == []


@pytest.mark.parametrize("skin", ["mare", "anilha", "caderno", ""])
def test_editor_fits_a_small_phone_in_every_look(app_url, open_app, skin):
    page, errors = open_app(app_url(season_state()), "2026-11-10T14:00:00-03:00", width=320, init=look(skin))
    go(page, "pesos")
    page.click('.pw.open .pe-go')
    fits = "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    assert page.evaluate(fits)
    rows = page.locator(".pe-l li")
    for i in range(rows.count()):
        box, dele = rows.nth(i).bounding_box(), rows.nth(i).locator(".pe-del").bounding_box()
        assert dele["x"] + dele["width"] <= box["x"] + box["width"] + 9, "o botão de excluir cabe na linha"
        assert dele["height"] >= 40, "alvo de toque bom pro dedo"
    page.click(".pw.editing .pe-add")
    sheet = page.locator(".sheet.xs")
    assert page.evaluate("(() => { const s = document.querySelector('.sheet.xs'); return s.scrollWidth <= s.clientWidth; })()")
    sheet.locator('[data-act="xs-save"]').scroll_into_view_if_needed()
    assert sheet.locator('[data-act="xs-save"]').is_visible()
    assert not any(bad in sheet.inner_text() for bad in BROKEN_TEXT)
    assert page.evaluate(fits)
    assert errors == []
