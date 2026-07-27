#!/usr/bin/env python3
"""Attach to the running Chrome (steward's session) and work the Bazaar."""
import sys
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://hellominds.ai/"
SHOT = sys.argv[2] if len(sys.argv) > 2 else "bz.png"

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = b.contexts[0]
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    pg.set_viewport_size({"width": 1280, "height": 720})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(7000)
    for sel in ['[data-slot="dialog-close"]', 'button[aria-label*="close" i]']:
        try:
            el = pg.query_selector(sel)
            if el and el.is_visible():
                el.click(timeout=4000); pg.wait_for_timeout(1500); break
        except Exception:
            pass
    pg.keyboard.press("Escape"); pg.wait_for_timeout(1200)
    print("URL:", pg.url)
    body = pg.inner_text("body")
    print("LOGGED IN:", "Log in or sign up" not in body and "Login" not in body.split("\n")[:8])
    for probe in ("Launch a Mind", "My Minds", "Bazaar", "Create", "Publish", "Skill", "Logout", "Login"):
        if probe in body:
            print("  sees:", probe)
    pg.screenshot(path=SHOT)
    print("screenshot:", SHOT)
