"""Hoje: timer dos exercícios de tempo de peso do corpo (a prancha, 3x30s)."""
import json

import pytest

from conftest import SAMPLE
from test_app import go, look

WED = "2026-10-21T13:30:00-03:00"  # quarta: Ombro e abdômen, com Prancha 3x30s
PILL = '[data-timer="Prancha"]'
PANEL = '.tmr[data-tmr="Prancha"]'
# vibração e tela acesa ficam registradas pra conferir
STUBS = (
    "window.__vib=[];navigator.vibrate=(p)=>{window.__vib.push(p);return true};"
    "window.__wake=[];Object.defineProperty(navigator,'wakeLock',{configurable:true,value:{request:async(t)=>{"
    "window.__wake.push('on:'+t);const s=new EventTarget();s.release=async()=>{window.__wake.push('off')};return s}}});"
)


def open_wed(open_app, app_url, **kw):
    page, errors = open_app(app_url(SAMPLE), WED, init=STUBS + kw.pop("init", ""), **kw)
    go(page, "hoje")
    return page, errors


def later(page, ms, **want):
    """O tempo passa no relógio do app. Com want (msg, sec, dots, gone), espera o timer mostrar isso: o relógio
    de teste anda aos saltos, e o toque do timer que cai na virada pode vir um instante depois."""
    page.clock.run_for(ms)
    conds = []
    if "msg" in want:
        conds.append(f"(document.querySelector('{PANEL} .tmr-m') || {{}}).textContent === {json.dumps(want['msg'])}")
    if "sec" in want:
        conds.append(f"(document.querySelector('{PANEL} .tmr-s') || {{}}).textContent === '{want['sec']}'")
    if "dots" in want:
        conds.append(f"document.querySelectorAll('{PANEL} .tmr-d i.on').length === {want['dots']}")
    if want.get("gone"):
        conds.append(f"!document.querySelector('{PANEL}')")
    if conds:
        page.wait_for_function(" && ".join(conds), timeout=3000)
    else:
        page.wait_for_timeout(60)


def panel(page):
    return {
        "msg": page.inner_text(f"{PANEL} .tmr-m"),
        "sec": page.inner_text(f"{PANEL} .tmr-s"),
        "dots": page.locator(f"{PANEL} .tmr-d i.on").count(),
        "cls": page.get_attribute(PANEL, "class"),
    }


def test_plank_timer_counts_each_hold_and_checks_the_plank_off(app_url, open_app):
    page, errors = open_wed(open_app, app_url)
    assert page.inner_text(PILL) == "30 s"
    assert page.get_attribute(PILL, "aria-expanded") == "false"
    assert page.locator(".tmr").count() == 0

    page.click(PILL)
    p = panel(page)
    assert p["msg"] == "Em posição" and p["sec"] == "5" and "prep" in p["cls"], "5 s pra ficar em posição"
    assert page.get_attribute(PILL, "aria-expanded") == "true"
    later(page, 5000, msg="Segura firme")
    p = panel(page)
    assert p["sec"] in ("30", "29") and "hold" in p["cls"]
    assert page.evaluate("window.__vib") == [120], "vibra quando começa a valer"
    later(page, 27000, sec="3")
    assert "last" in panel(page)["cls"], "os três últimos segundos marcam o ritmo"
    later(page, 3000, msg="Boa! Descansa.", dots=1)
    assert page.inner_text(f"{PANEL} .tmr-d em") == "1 de 3"
    assert page.evaluate("window.__vib")[-1] == [220, 120, 220], "e vibra duas vezes no fim"
    assert page.get_attribute('[data-exok="Prancha"]', "aria-pressed") == "false"

    page.click(f'{PANEL} [data-act="tm-next"]')
    assert panel(page)["msg"] == "Em posição"
    later(page, 35000, dots=2)
    page.click(PILL)  # o próprio botão também começa a próxima
    later(page, 35000, msg="Tudo feito!", dots=3)
    assert page.get_attribute('[data-exok="Prancha"]', "aria-pressed") == "true", "a prancha fica feita"
    assert page.inner_text(".check .plan .ex") == "1 de 5 feitos"
    later(page, 3600, gone=True)  # e o timer fecha sozinho
    assert page.get_attribute(PILL, "aria-expanded") == "false"
    assert errors == []


def test_stopping_keeps_the_holds_already_done(app_url, open_app):
    page, errors = open_wed(open_app, app_url)
    page.click(PILL)
    later(page, 15000, msg="Segura firme")
    page.click(f'{PANEL} [data-act="tm-stop"]')
    assert page.locator(".tmr").count() == 0, "parar antes da primeira fecha o timer"
    page.click(PILL)
    later(page, 35000, dots=1)
    page.click(f'{PANEL} [data-act="tm-next"]')
    later(page, 9000, msg="Segura firme")
    page.click(f'{PANEL} [data-act="tm-stop"]')
    p = panel(page)
    assert p["msg"] == "Boa! Descansa." and p["dots"] == 1, "a que já foi continua contada"
    page.click(f'{PANEL} [data-act="tm-close"]')
    assert page.locator(".tmr").count() == 0
    assert page.evaluate("document.activeElement.dataset.timer") == "Prancha", "o foco volta pro botão do timer"
    assert errors == []


def test_the_screen_stays_on_and_the_timer_survives_a_redraw(app_url, open_app):
    page, errors = open_wed(open_app, app_url)
    page.click(PILL)
    later(page, 5000 + 10000, msg="Segura firme", sec="20")
    assert page.evaluate("window.__wake") == ["on:screen"], "a tela não apaga enquanto conta"
    go(page, "pesos")
    go(page, "hoje")
    p = panel(page)
    assert p["msg"] == "Segura firme" and p["sec"] in ("20", "19"), "trocar de aba não perde o tempo"
    assert "new" not in p["cls"], "e não anima de novo"
    later(page, 20000, msg="Boa! Descansa.")
    assert page.evaluate("window.__wake") == ["on:screen", "off"], "terminou a vez, a tela pode apagar"
    assert errors == []


def test_only_timed_bodyweight_exercises_get_a_timer(app_url, open_app):
    page, errors = open_wed(open_app, app_url)
    rows = {r.locator(".exn b").inner_text(): r for r in page.locator(".check .exi").all()}
    assert rows["Prancha"].locator(".tmb").count() == 1
    assert rows["Pendurar na barra"].locator(".tmb").count() == 0, "a barra tem o campo do tempo"
    assert rows["Ombro na máquina"].locator(".tmb").count() == 0
    assert errors == []


def test_with_reduced_motion_the_timer_does_not_bounce(app_url, open_app):
    page, errors = open_wed(open_app, app_url, motion="reduce")
    page.click(PILL)
    later(page, 5000 + 28000, sec="2")
    assert "last" in panel(page)["cls"]
    assert page.evaluate(f"getComputedStyle(document.querySelector('{PANEL} .tmr-s')).animationName") == "none"
    assert errors == []


@pytest.mark.parametrize("skin", ["mare", "anilha", "caderno", ""])
def test_timer_fits_a_small_phone_in_every_look(app_url, open_app, skin):
    page, errors = open_wed(open_app, app_url, init=look(skin), width=320, height=640)
    page.click(PILL)
    later(page, 35000, msg="Boa! Descansa.")  # entre uma vez e outra: o estado com mais coisa na tela
    assert not page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    box = page.locator(PANEL).bounding_box()
    for b in page.locator(f"{PANEL} button").all():
        bb = b.bounding_box()
        assert bb["height"] >= 40, "botão fácil de tocar"
        assert bb["x"] + bb["width"] <= box["x"] + box["width"] + 0.5, "nada sai do timer"
    assert errors == []
