// home.js — landing page

import { escapeHtml } from "./util.js";

const EXAMPLES = ["rice blast", "Magnaporthe", "tomato", "FungiDB", "PHI-base", "resistance gene", "drought"];

export function renderHome(container, data) {
  const domains = 7; // image/AI, pathogen genomics, interaction & resistance, crop genomics, stress/phenomics, soil microbiome, multi-omics
  container.innerHTML = `
    <section class="hero">
      <div class="eyebrow">Plant disease data interoperability — prototype</div>
      <h1>HOPPER</h1>
      <p class="lede">Harmonized Ontology &amp; Plant Pathology Exploration Repository. HOPPER connects fragmented plant disease data through a common, searchable knowledge layer — it normalizes records from multiple public resources into one schema while keeping each original database as the authoritative source.</p>

      <form class="hero-search" id="home-search-form" role="search">
        <div class="search-row">
          <input type="search" id="home-search-input" placeholder="Search plant, pathogen, disease, gene, database or identifier…" aria-label="Search HOPPER">
          <button class="btn" type="submit">Search</button>
        </div>
        <div class="chip-row">
          ${EXAMPLES.map((e) => `<button type="button" class="chip" data-example="${escapeHtml(e)}">${escapeHtml(e)}</button>`).join("")}
        </div>
      </form>
    </section>

    <section class="feature-grid">
      <div>
        <h3>Search</h3>
        <p>Search across normalized plant disease records — hosts, pathogens, diseases, genes, datasets and the databases they came from.</p>
      </div>
      <div>
        <h3>Connect</h3>
        <p>Explore relationships between hosts, pathogens, diseases, resistance genes, datasets and the external databases that describe them.</p>
      </div>
      <div>
        <h3>Interpret</h3>
        <p>Use a lightweight, rule-based &ldquo;Ask HOPPER&rdquo; query interface to explore the integrated dataset in plain language — grounded only in indexed records.</p>
      </div>
    </section>

    <section class="stats-grid" aria-label="Dataset statistics">
      <div class="stat"><span class="num">${data.records.length}</span><span class="label">Indexed records</span></div>
      <div class="stat"><span class="num">${data.sources.length}</span><span class="label">External resources</span></div>
      <div class="stat"><span class="num">${domains}</span><span class="label">Data domains</span></div>
      <div class="stat"><span class="num">${data.mappings.length}</span><span class="label">Cross-database mapping chains</span></div>
    </section>

    <section class="callout">
      <p><strong>What makes HOPPER different?</strong> HOPPER is not a database containing information from many databases side by side. It is a lightweight interoperability and knowledge layer that normalizes metadata, connects identifiers, preserves provenance, and exposes relationships across heterogeneous plant disease resources.</p>
      <p>Read more about the reasoning behind HOPPER, its FAIR-by-design principles, and its honest limitations on the <a href="#/about">About</a> page.</p>
    </section>
  `;

  const form = container.querySelector("#home-search-form");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = container.querySelector("#home-search-input").value.trim();
    window.location.hash = q ? `#/search?q=${encodeURIComponent(q)}` : "#/search";
  });
  container.querySelectorAll(".chip[data-example]").forEach((chip) => {
    chip.addEventListener("click", () => {
      window.location.hash = `#/search?q=${encodeURIComponent(chip.dataset.example)}`;
    });
  });
}
