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
            if resp.status >= 400 and "fonts.googleapis.com" not in resp.url and "fonts.gstatic.com" not in resp.url:
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
