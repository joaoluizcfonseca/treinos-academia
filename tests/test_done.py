"""Hoje: marcar cada exercício do treino como feito, com a contagem e a barra acompanhando."""
import pytest

from conftest import SAMPLE
from test_app import PUBLISH_STUB, TUESDAY, go, look, published_state

COUNT = ".check .plan .ex"
UNDONE = '.check .exc[aria-pressed="false"]'


def pressed(page, name):
    return page.get_attribute(f'[data-exok="{name}"]', "aria-pressed") == "true"


def test_each_exercise_can_be_checked_off(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY)  # terça: Costas e bíceps
    go(page, "hoje")
    total = page.locator(".check .exc").count()
    assert total == 8
    assert page.inner_text(COUNT) == "8 exercícios"
    assert page.locator(".exp i").count() == 8 and page.locator(".exp i.on").count() == 0

    page.click('[data-exok="Puxada"]')
    assert pressed(page, "Puxada")
    assert "ok" in page.get_attribute('.exi:has([data-exok="Puxada"])', "class")
    assert page.inner_text(COUNT) == "1 de 8 feitos"
    assert page.locator(".exp i.on").count() == 1

    # o peso que estava sendo digitado não some quando marca o exercício
    box = page.locator('.exi input[data-kg="Bíceps na máquina"]')
    box.fill("27,5")
    page.click('[data-exok="Bíceps na máquina"]')
    assert box.input_value() == "27,5"
    assert page.inner_text(COUNT) == "2 de 8 feitos"

    # pelo teclado também
    page.focus('[data-exok="Remada com apoio no peito"]')
    page.keyboard.press("Space")
    assert pressed(page, "Remada com apoio no peito")

    page.click('[data-exok="Puxada"]')  # desmarca
    assert not pressed(page, "Puxada")
    assert page.inner_text(COUNT) == "2 de 8 feitos"

    # fecha e abre o app: o que foi marcado continua marcado, e o peso também
    page.reload()
    page.wait_for_timeout(300)
    go(page, "hoje")
    assert pressed(page, "Bíceps na máquina") and pressed(page, "Remada com apoio no peito")
    assert not pressed(page, "Puxada")
    assert page.input_value('.exi input[data-kg="Bíceps na máquina"]') == "27,5"

    # tudo feito: a contagem fecha e um brilho passa pelo botão de terminar
    while page.locator(UNDONE).count():
        page.locator(UNDONE).first.click()
    assert page.inner_text(COUNT) == "Todos os 8 feitos"
    assert "all" in page.get_attribute(COUNT, "class")
    assert "shine" in page.get_attribute('.go[data-act="mark"]', "class")
    page.click('button[data-act="mark"]')
    page.wait_for_timeout(300)
    assert "Feito: Costas e bíceps" in page.inner_text(".done-msg")
    page.click('[data-act="exopen"]')
    assert page.locator('.check .exc[aria-pressed="true"]').count() == 8, "a lista do treino feito mostra o que foi marcado"
    assert errors == []


def test_checked_exercises_go_out_with_the_app(app_url, open_app):
    page, errors = open_app(app_url(SAMPLE), TUESDAY, init=PUBLISH_STUB)
    go(page, "hoje")
    page.click('[data-exok="Puxada"]')
    page.click('[data-exok="Rosca com barra W"]')
    assert page.evaluate("window.__pub.length") == 0, "espera uma pausa antes de publicar"
    page.clock.run_for(31000)
    page.wait_for_timeout(200)
    day = published_state(page)["ex"]["2026-10-06"]
    assert day["_ok"] == {"Puxada": 1, "Rosca com barra W": 1}
    assert day["_w"] == "Costas e bíceps"
    assert errors == []


def test_the_check_moves_only_when_tapped(app_url, open_app):
    anim = "getComputedStyle(document.querySelector('[data-exok=\"Puxada\"]'), '::before').animationName"
    page, errors = open_app(app_url(SAMPLE), TUESDAY)
    go(page, "hoje")
    page.click('[data-exok="Puxada"]')
    assert page.evaluate(anim) == "excPop", "no toque, a caixinha dá um pulo"
    page.reload()
    page.wait_for_timeout(300)
    go(page, "hoje")
    assert page.evaluate(anim) == "none", "abrir o app com exercício já feito não anima nada"

    calm, errors2 = open_app(app_url(SAMPLE), TUESDAY, motion="reduce")
    go(calm, "hoje")
    calm.click('[data-exok="Puxada"]')
    assert calm.evaluate(anim) == "none", "quem pede menos movimento só vê o certinho"
    assert errors == [] and errors2 == []


@pytest.mark.parametrize("skin", ["mare", "anilha", "caderno", ""])
def test_checks_fit_a_small_phone_in_every_look(app_url, open_app, skin):
    page, errors = open_app(app_url(SAMPLE), TUESDAY, init=look(skin), width=320, height=640)
    go(page, "hoje")
    page.click('[data-exok="Remada com apoio no peito"]')
    assert not page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    for row in page.locator(".check .exi").all():
        check = row.locator(".exc").bounding_box()
        name = row.locator(".exn").bounding_box()
        assert check["width"] >= 44 and check["height"] >= 44, "área de toque de 44 px"
        assert check["x"] >= 0 and name["width"] > 100
        kg = row.locator(".kg")
        if kg.count():
            k = kg.bounding_box()
            assert name["x"] + name["width"] <= k["x"] + 1, "o nome não passa por cima do peso"
    assert errors == []
