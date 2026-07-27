#!/usr/bin/env python3
"""Send a message to NeoBerlin in app.hellominds.ai and capture the reply."""
import sys, time
from playwright.sync_api import sync_playwright

MSG = sys.argv[1]
WAIT = int(sys.argv[2]) if len(sys.argv) > 2 else 75
SHOT = sys.argv[3] if len(sys.argv) > 3 else "chat.png"


def composer(pg):
    for sel in ['div[contenteditable="true"]', "textarea",
                'input[placeholder*="Type" i]', '[role="textbox"]']:
        els = pg.query_selector_all(sel)
        for e in els:
            try:
                if e.is_visible():
                    return e
            except Exception:
                continue
    return None


with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = b.contexts[0]
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    pg.set_viewport_size({"width": 1280, "height": 720})
    if "app.hellominds.ai" not in pg.url:
        pg.goto("https://app.hellominds.ai/", wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_timeout(9000)

    before = pg.inner_text("body")

    el = composer(pg)
    if not el:
        pg.mouse.click(800, 682)
        pg.wait_for_timeout(1500)
        el = composer(pg)
    if not el:
        print("NO COMPOSER FOUND")
        pg.screenshot(path="chat_nocomposer.png")
        sys.exit(2)

    el.click()
    pg.wait_for_timeout(600)
    # type without newlines triggering send prematurely
    pg.keyboard.insert_text(MSG)
    pg.wait_for_timeout(1200)
    pg.keyboard.press("Enter")
    print("sent:", MSG[:70].replace("\n", " "), "...")

    # wait for the reply to grow
    last = ""
    stable = 0
    for i in range(WAIT):
        pg.wait_for_timeout(2000)
        now = pg.inner_text("body")
        if now == last:
            stable += 1
            if stable >= 4 and len(now) > len(before) + 40:
                break
        else:
            stable = 0
            last = now
    pg.screenshot(path=SHOT)
    text = pg.inner_text("body")
    new = text[len(before):] if text.startswith(before[:200]) else text
    print("--- REPLY (tail) ---")
    print(text[-2200:])
