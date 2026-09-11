// search.js — Search page: free-text search + faceted filters + results + export

import { searchRecords } from "./data.js";
import { escapeHtml, resultCardHtml, downloadFile, recordsToCsv, qs, qsa } from "./util.js";

const FACET_CONFIG = [
  { key: "hostCrop", label: "Host / crop", facetKey: "hostCrop" },
  { key: "pathogenType", label: "Pathogen type", facetKey: "pathogenType" },
  { key: "entityType", label: "Record type", facetKey: "entityType" },
  { key: "domain", label: "Data domain", facetKey: "domain" },
  { key: "sourceDatabase", label: "Source database", facetKey: "sourceDatabase", scrollable: true },
  { key: "region", label: "Geographic region", facetKey: "region" },
  { key: "evidenceType", label: "Evidence type", facetKey: "evidenceType" },
  { key: "year", label: "Year", facetKey: "year" },
];

function parseQueryParams(hash) {
  const idx = hash.indexOf("?");
  const out = { q: "" };
  if (idx === -1) return out;
  const params = new URLSearchParams(hash.slice(idx + 1));
  out.q = params.get("q") || "";
  return out;
}

function filterPanelHtml(data, activeFilters) {
  return FACET_CONFIG.map((cfg) => {
    const options = data.facets[cfg.facetKey];
    if (!options.length) return "";
    const selected = activeFilters[cfg.key] || [];
    return `
      <div class="filter-group">
        <fieldset>
          <legend>${escapeHtml(cfg.label)}</legend>
          <div class="${cfg.scrollable ? "filter-scroll" : ""}">
          ${options.map((opt) => `
            <label class="filter-option">
              <input type="checkbox" data-facet="${cfg.key}" value="${escapeHtml(opt)}" ${selected.includes(opt) ? "checked" : ""}>
              <span>${escapeHtml(opt)}</span>
            </label>
          `).join("")}
          </div>
        </fieldset>
      </div>
    `;
  }).join("");
}

export function renderSearch(container, data, hash) {
  const { q } = parseQueryParams(hash || "");
  const state = { query: q, filters: {} };

  container.innerHTML = `
    <h1>Search HOPPER</h1>
    <p class="lede">Search runs entirely against the local normalized dataset shipped with this prototype — no external calls are made.</p>
    <form class="hero-search" id="search-form" role="search" style="margin-bottom:1.75rem;">
      <div class="search-row">
        <input type="search" id="search-input" placeholder="Search plant, pathogen, disease, gene, database or identifier…" value="${escapeHtml(state.query)}" aria-label="Search HOPPER">
        <button class="btn" type="submit">Search</button>
      </div>
    </form>

    <details class="filter-panel-mobile"><summary>Filters</summary>
      <div class="filter-panel" id="filter-panel-mobile-inner"></div>
    </details>

    <div class="search-layout">
      <aside class="filter-panel" id="filter-panel" aria-label="Filters"></aside>
      <div>
        <div class="results-meta">
          <span class="count" id="results-count"></span>
          <div class="export-controls">
            <button class="btn btn--quiet" id="export-csv" type="button">Export CSV</button>
            <button class="btn btn--quiet" id="export-json" type="button">Export JSON</button>
          </div>
        </div>
        <div class="result-list" id="result-list"></div>
      </div>
    </div>
  `;

  const filterPanel = qs("#filter-panel", container);
  const filterPanelMobile = qs("#filter-panel-mobile-inner", container);
  const resultList = qs("#result-list", container);
  const resultsCount = qs("#results-count", container);

  let currentResults = [];

  function runSearch() {
    currentResults = searchRecords(data, { query: state.query, filters: state.filters });
    resultsCount.textContent = `${currentResults.length} record${currentResults.length === 1 ? "" : "s"} found`;
    resultList.innerHTML = currentResults.length
      ? currentResults.map(resultCardHtml).join("")
      : `<div class="empty-state">No records matched this search. Try a broader term (for example a host, pathogen, or source database name), or clear filters.</div>`;
  }

  function renderFilters() {
    const html = filterPanelHtml(data, state.filters);
    filterPanel.innerHTML = `<h4>Filters</h4>${html}`;
    filterPanelMobile.innerHTML = html;
    [filterPanel, filterPanelMobile].forEach((panel) => {
      qsa("input[type=checkbox][data-facet]", panel).forEach((cb) => {
        cb.addEventListener("change", () => {
          const key = cb.dataset.facet;
          const set = new Set(state.filters[key] || []);
          if (cb.checked) set.add(cb.value); else set.delete(cb.value);
          state.filters[key] = Array.from(set);
          // keep both panels' checkboxes in sync
          qsa(`input[data-facet="${key}"][value="${CSS.escape(cb.value)}"]`, container).forEach((other) => {
            other.checked = cb.checked;
          });
          runSearch();
        });
      });
    });
  }

  qs("#search-form", container).addEventListener("submit", (e) => {
    e.preventDefault();
    state.query = qs("#search-input", container).value.trim();
    history.replaceState(null, "", `#/search${state.query ? "?q=" + encodeURIComponent(state.query) : ""}`);
    runSearch();
  });

  qs("#export-csv", container).addEventListener("click", () => {
    downloadFile("hopper_results.csv", recordsToCsv(currentResults), "text/csv");
  });
  qs("#export-json", container).addEventListener("click", () => {
    downloadFile("hopper_results.json", JSON.stringify(currentResults, null, 2), "application/json");
  });

  renderFilters();
  runSearch();
}
