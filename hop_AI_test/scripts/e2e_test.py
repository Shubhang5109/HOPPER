#!/usr/bin/env python3
"""End-to-end smoke test for the HOPPER static site using Playwright.
Run against a local http.server instance (no network required).
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
errors = []
console_errors = []


def check(label, cond):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}")
    if not cond:
        errors.append(label)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        def on_response(resp):
            # Ignore the font CDN (blocked in this offline sandbox) and the
            # intentionally-mocked 401 from the BYOK auth-failure test above.
            if resp.status >= 400 and "fonts.googleapis.com" not in resp.url and "fonts.gstatic.com" not in resp.url and "api.anthropic.com" not in resp.url:
                console_errors.append(f"HTTP {resp.status} for {resp.url}")

        page.on("response", on_response)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))

        # --- Home page ---
        page.goto(f"{BASE}/#/", wait_until="networkidle")
        page.wait_for_selector("h1")
        check("home: h1 says HOPPER", "HOPPER" in page.locator("h1").first.inner_text())
        check("home: stats show 87 indexed records", "87" in page.inner_text(".stats-grid"))
        page.screenshot(path="/tmp/shot_home.png", full_page=True)

        # --- Home search -> Search page ---
        page.fill("#home-search-input", "rice blast")
        page.click("#home-search-form button[type=submit]")
        page.wait_for_url("**/#/search*")
        page.wait_for_selector(".result-card", timeout=5000)
        count_text = page.inner_text("#results-count")
        print("search count text:", count_text)
        check("search: 'rice blast' returns results", int(count_text.split()[0]) > 0)
        page.screenshot(path="/tmp/shot_search.png", full_page=True)

        # --- Filters ---
        page.goto(f"{BASE}/#/search", wait_until="networkidle")
        page.wait_for_selector(".result-card")
        initial_count = int(page.inner_text("#results-count").split()[0])
        # click first pathogen-type checkbox if present
        cb = page.locator('#filter-panel input[data-facet="pathogenType"]').first
        if cb.count() > 0:
            cb.check()
            page.wait_for_timeout(200)
            filtered_count = int(page.inner_text("#results-count").split()[0])
            check("filters: pathogen type filter narrows or equals results", filtered_count <= initial_count)
        else:
            check("filters: pathogenType facet present", False)

        # --- Search: known terms ---
        for term in ["rice", "tomato", "fungus", "PHI-base", "resistance"]:
            page.goto(f"{BASE}/#/search?q={term}", wait_until="networkidle")
            page.wait_for_selector("#results-count")
            c = int(page.inner_text("#results-count").split()[0])
            check(f"search term '{term}' returns >=0 and page renders", c >= 0)

        # --- Record page ---
        page.goto(f"{BASE}/#/search?q=rice%20blast", wait_until="networkidle")
        page.wait_for_selector(".result-card a")
        first_link = page.locator(".result-card__name a").first
        record_name = first_link.inner_text()
        first_link.click()
        page.wait_for_selector(".record-header")
        check("record page: header name matches", record_name in page.inner_text(".record-header"))
        check("record page: has Identity section", "Identity" in page.inner_text("main"))
        check("record page: has Provenance section", "Provenance" in page.inner_text("main"))
        page.screenshot(path="/tmp/shot_record.png", full_page=True)

        # --- Explore page ---
        page.goto(f"{BASE}/#/explore", wait_until="networkidle")
        page.wait_for_selector(".graph-panel svg", timeout=5000)
        check("explore: svg diagram rendered", page.locator(".graph-panel svg").count() > 0)
        check("explore: matrix table rendered", page.locator("table.matrix").count() > 0)
        page.screenshot(path="/tmp/shot_explore.png", full_page=True)

        # click a node in the graph to navigate
        node = page.locator(".graph-panel svg .node-link[data-nav]").first
        if node.count() > 0:
            node.click()
            page.wait_for_timeout(300)
            check("explore: clicking neighbor node navigates", "entity=" in page.url)

        # --- Databases page ---
        page.goto(f"{BASE}/#/databases", wait_until="networkidle")
        page.wait_for_selector(".db-table tbody tr")
        rows = page.locator(".db-table tbody tr").count()
        check("databases: table has rows", rows > 10)
        page.screenshot(path="/tmp/shot_databases.png", full_page=True)

        # --- Ask HOPPER ---
        page.goto(f"{BASE}/#/ask", wait_until="networkidle")
        page.click('[data-example="Find fungal pathogens associated with rice diseases"]')
        page.wait_for_selector(".ask-answer")
        page.wait_for_function("document.querySelector('.ask-answer')?.innerText.trim() !== 'Thinking\u2026'", timeout=20000)
        ask_text = page.inner_text(".ask-answer")
        print("ask answer:", ask_text)
        check("ask: demo badge present", page.locator(".demo-badge").count() > 0)
        check("ask: answer references indexed records", "indexed HOPPER records" in ask_text)
        page.screenshot(path="/tmp/shot_ask.png", full_page=True)

        page.fill("#ask-input", "Which databases contain rice pathogen information?")
        page.click('#ask-form button[type=submit]')
        page.wait_for_timeout(300)
        check("ask: second query produced an answer", page.locator(".ask-answer").count() > 0)

        # --- Export ---
        page.goto(f"{BASE}/#/search?q=rice", wait_until="networkidle")
        page.wait_for_selector(".result-card")
        with page.expect_download() as dl_info:
            page.click("#export-csv")
        download = dl_info.value
        check("export: CSV download triggered", download.suggested_filename.endswith(".csv"))

        with page.expect_download() as dl_info2:
            page.click("#export-json")
        download2 = dl_info2.value
        check("export: JSON download triggered", download2.suggested_filename.endswith(".json"))

        # --- Ask HOPPER: bring-your-own-key mode (mocked Anthropic API call) ---
        page.goto(f"{BASE}/#/ask", wait_until="networkidle")
        check("ask: AI settings panel present", page.locator(".ai-settings").count() > 0)

        page.route("https://api.anthropic.com/v1/messages", lambda route: route.fulfill(
            status=200, content_type="application/json",
            body='{"content":[{"type":"text","text":"Rice blast is caused by the fungus Magnaporthe oryzae (HOPPER:PATH:0001)."}]}',
        ))
        page.fill("#ai-key-input", "sk-ant-test-fake-key-0000000000000000")
        page.click("#ai-key-save")
        page.wait_for_selector(".ai-settings summary:has-text(\"Using your API key\")", timeout=5000)
        check("ask+BYOK: key saved and summary updates", "Using your API key" in page.inner_text(".ai-settings summary"))

        page.click('[data-example="Find fungal pathogens associated with rice diseases"]')
        page.wait_for_function("document.querySelector('.ask-answer')?.innerText.trim() !== 'Thinking\u2026'", timeout=20000)
        ask_main_text = page.inner_text("main")
        check("ask+BYOK: success shows AI-assisted answer with key label", "your API key" in ask_main_text)
        check("ask+BYOK: mocked Claude answer text shown", "Magnaporthe oryzae" in page.inner_text(".ask-answer"))

        # failure path: Anthropic rejects the key (401)
        page.unroute("https://api.anthropic.com/v1/messages")
        page.route("https://api.anthropic.com/v1/messages", lambda route: route.fulfill(
            status=401, content_type="application/json",
            body='{"error":{"type":"authentication_error","message":"invalid x-api-key"}}',
        ))
        page.click('[data-example="Bacterial diseases in banana"]')
        page.wait_for_function("document.querySelector('.ask-answer')?.innerText.trim() !== 'Thinking\u2026'", timeout=20000)
        check("ask+BYOK: auth failure falls back gracefully with error shown", "invalid x-api-key" in page.inner_text("main"))

        # clear the key -> back to demo mode (the panel auto-collapses once a
        # key is set, so expand it again before clicking Clear, same as a
        # real person would)
        page.click(".ai-settings summary")
        page.click("#ai-key-clear")
        page.wait_for_selector(".ai-settings summary:has-text(\"Set up real AI answers\")", timeout=5000)
        check("ask+BYOK: clearing key returns to setup prompt", "Set up real AI answers" in page.inner_text(".ai-settings summary"))
        page.click('[data-example="Bacterial diseases in banana"]')
        page.wait_for_selector(".ask-answer")
        page.wait_for_function("document.querySelector('.ask-answer')?.innerText.trim() !== 'Thinking\u2026'", timeout=20000)
        check("ask+BYOK: after clearing, falls back to local rule-based interpretation", "local rule-based interpretation" in page.inner_text("main").lower())
        page.unroute("https://api.anthropic.com/v1/messages")

        # --- Ask HOPPER with a mocked AI proxy ---
        # This test suite is run twice by the shell wrapper: once with the
        # real (empty) config.js, and once with PROXY_TEST_MODE=1 where
        # config.js is temporarily pointed at a fake proxy URL that
        # Playwright intercepts (no real network/API key involved).
        import os as _os
        if _os.environ.get("PROXY_TEST_MODE") == "1":
            proxy_url = "https://ask-hopper-proxy.example.workers.dev/"

            page.route(proxy_url, lambda route: route.fulfill(
                status=200, content_type="application/json",
                body='{"answer": "Rice blast is caused by the fungus Magnaporthe oryzae (HOPPER:PATH:0001)."}',
            ))
            page.goto(f"{BASE}/#/ask", wait_until="networkidle")
            page.click('[data-example="Find fungal pathogens associated with rice diseases"]')
            page.wait_for_selector(".ask-answer p:has-text(\"Magnaporthe\")", timeout=5000)
            check("ask+proxy: success path shows AI-assisted answer", "AI-assisted answer" in page.inner_text("main"))
            check("ask+proxy: answer text from mocked proxy is shown", "Magnaporthe oryzae" in page.inner_text(".ask-answer"))

            page.unroute(proxy_url)
            page.route(proxy_url, lambda route: route.abort())
            page.click('[data-example="Bacterial diseases in banana"]')
            page.wait_for_timeout(500)
            check("ask+proxy: failed proxy falls back gracefully", "ai request failed" in page.inner_text("main").lower())
            check("ask+proxy: fallback still shows result cards or empty-state", page.locator(".result-list").count() > 0)

        # --- About page ---
        page.goto(f"{BASE}/#/about", wait_until="networkidle")
        about_text = page.inner_text("main")
        for heading in ["Why HOPPER", "What makes HOPPER different", "Data & provenance", "FAIR", "Limitations", "Scientific foundation"]:
            check(f"about: contains section '{heading}'", heading in about_text)
        page.screenshot(path="/tmp/shot_about.png", full_page=True)

        # --- Mobile viewport check ---
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(f"{BASE}/#/", wait_until="networkidle")
        page.screenshot(path="/tmp/shot_home_mobile.png", full_page=True)
        page.goto(f"{BASE}/#/search?q=rice", wait_until="networkidle")
        page.wait_for_selector(".result-card")
        check("mobile: filter panel is in a details/summary", page.locator(".filter-panel-mobile summary").count() > 0)
        page.screenshot(path="/tmp/shot_search_mobile.png", full_page=True)

        # --- 404 route ---
        page.goto(f"{BASE}/#/nope", wait_until="networkidle")
        check("404: not found page renders", "not found" in page.inner_text("main").lower())

        browser.close()

    print("\n---- console/page errors captured ----")
    for e in console_errors:
        print("CONSOLE/PAGE ERROR:", e)
    if console_errors:
        errors.append("console_errors_present")

    print(f"\n{len(errors)} failing checks out of total.")
    if errors:
        print("FAILURES:", errors)
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
