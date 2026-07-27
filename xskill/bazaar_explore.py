#!/usr/bin/env python3
"""Reuse the steward's existing Chrome session and find the Bazaar publish flow."""
import os, sys
from playwright.sync_api import sync_playwright

PROFILE = os.path.expanduser("~/Library/Application Support/Google/Chrome")
START = sys.argv[1] if len(sys.argv) > 1 else "https://hellominds.ai/"

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE,
        channel="chrome",
        headless=False,
        viewport={"width": 1280, "height": 720},
        args=["--profile-directory=Default", "--disable-blink-features=AutomationControlled"],
    )
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    pg.goto(START, wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(8000)

    # dismiss promo overlay if present
    for sel in ['[data-slot="dialog-close"]', 'button[aria-label*="close" i]']:
        try:
            el = pg.query_selector(sel)
            if el and el.is_visible():
                el.click(timeout=4000); pg.wait_for_timeout(1500); break
        except Exception:
            pass
    pg.keyboard.press("Escape"); pg.wait_for_timeout(1000)

    print("URL:", pg.url)
    print("TITLE:", pg.title())
    body = pg.inner_text("body")
    logged_in = not ("Log in or sign up" in body)
    # look for account indicators
    for probe in ("Launch a Mind", "My Minds", "Dashboard", "Profile", "Logout", "Sign out", "Login"):
        if probe in body:
            print("  sees:", probe)
    pg.screenshot(path="bz_start.png")
    ctx.close()
