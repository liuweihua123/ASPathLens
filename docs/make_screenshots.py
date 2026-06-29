"""Take screenshots of all ASPathLens pages for README using Playwright."""

import asyncio
import os
from pathlib import Path

# Ensure app is running: backend on 8000, frontend on 3000
BASE = "http://127.0.0.1:3000"
OUT = Path(__file__).resolve().parent / "screenshots"
os.makedirs(OUT, exist_ok=True)

CHROME = r"C:\Users\liuweihua888\AppData\Local\ms-playwright\chromium-1208\chrome-win64\chrome.exe"

PAGES = [
    ("home",            "/",                              1280, 720),
    ("analyzer",        "/analyzer",                      1280, 900),
    ("diff",            "/diff",                          1280, 900),
    ("asn-explorer",    "/asn",                           1280, 800),
    ("batch",           "/batch",                         1280, 900),
    ("pattern-search",  "/pattern",                       1280, 720),
    ("dataset-status",  "/dataset",                       1280, 720),
    ("dataset-diff",    "/dataset-diff",                   1280, 720),
    ("knowledge-graph", "/kg",                            1280, 720),
    ("api-playground",  "/api",                           1280, 720),
    ("examples",        "/examples",                      1280, 720),
]


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=CHROME)
        page = await browser.new_page()

        for name, path, w, h in PAGES:
            url = BASE + path
            print(f"Screenshot: {name} -> {url}")
            await page.set_viewport_size({"width": w, "height": h})

            try:
                await page.goto(url, wait_until="networkidle", timeout=15000)
            except Exception:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(1500)

            # Auto-trigger analysis on Path Analyzer / Diff pages
            if path == "/analyzer":
                try:
                    await page.click('button:has-text("Analyze")', timeout=4000)
                    await page.wait_for_timeout(2000)
                except Exception:
                    pass
            elif path == "/diff":
                try:
                    await page.click('button:has-text("Compare")', timeout=4000)
                    await page.wait_for_timeout(2000)
                except Exception:
                    pass
            elif path == "/asn":
                try:
                    await page.click('button:has-text("Search")', timeout=4000)
                    await page.wait_for_timeout(2000)
                except Exception:
                    pass
            elif path == "/dataset":
                await page.wait_for_timeout(2000)
            elif path == "/kg":
                try:
                    await page.click('button:has-text("Build Graph")', timeout=4000)
                    await page.wait_for_timeout(2500)
                except Exception:
                    pass

            out_path = OUT / f"{name}.png"
            await page.screenshot(path=str(out_path), full_page=True)
            print(f"  Saved: {out_path}")

        await browser.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
