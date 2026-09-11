// ask.js — "Ask HOPPER": a rule-based / keyword-based semantic search.
//
// This intentionally does NOT call any external LLM API, so the public
// GitHub Pages deployment works with no secret key configured. It parses
// a handful of recognizable signals out of the query (pathogen type, host,
// source database, region, data-type keywords, "database/resource" intent)
// and turns them into the same structured filter object the Search page
// uses. It never answers from anything other than the indexed dataset.

import { searchRecords } from "./data.js";
import { escapeHtml, resultCardHtml, qs } from "./util.js";

const EXAMPLES = [
  "Find fungal pathogens associated with rice diseases",
  "What databases contain information related to tomato resistance?",
  "Show resources connected to soil microbiome and plant disease",
  "Which databases contain rice pathogen information?",
  "Bacterial diseases in banana",
];

const PATHOGEN_TYPE_WORDS = [
  [["fungal", "fungus", "fungi"], "Fungus"],
  [["bacterial", "bacteria", "bacterium"], "Bacterium"],
  [["viral", "virus", "viruses"], "Virus"],
  [["oomycete", "oomycetes"], "Oomycete"],
];

const DATA_TYPE_KEYWORDS = [
  "image", "genom", "interaction", "resistance", "microbiome", "soil",
  "stress", "transcriptom", "proteom", "pest", "metagenom", "expression",
];

function interpretQuery(query, data) {
  const q = query.toLowerCase();
  const filters = {};
  const matchedTerms = [];

  for (const [words, type] of PATHOGEN_TYPE_WORDS) {
    if (words.some((w) => q.includes(w)) && data.facets.pathogenType.includes(type)) {
      filters.pathogenType = [type];
      matchedTerms.push(`pathogen type = ${type}`);
      break;
    }
  }

  const dbHit = data.facets.sourceDatabase.find((db) => q.includes(db.toLowerCase()));
  if (dbHit) {
    filters.sourceDatabase = [dbHit];
    matchedTerms.push(`source database = ${dbHit}`);
  }

  const hostHit = data.facets.hostCrop.find((h) => q.includes(h.toLowerCase()));
  if (hostHit) {
    filters.hostCrop = [hostHit];
    matchedTerms.push(`host / crop = ${hostHit}`);
  }

  const REGION_WORDS = [
    [["africa", "african"], "Africa"],
    [["asia", "asian"], "Asia"],
    [["america", "americas"], "Americas"],
    [["europe", "european"], "Europe"],
    [["global", "worldwide"], "Global"],
  ];
  for (const [words, bucket] of REGION_WORDS) {
    if (words.some((w) => q.includes(w)) && data.facets.region.includes(bucket)) {
      filters.region = [bucket];
      matchedTerms.push(`region = ${bucket}`);
      break;
    }
  }

  const dataTypeValues = Array.from(new Set(data.records.map((r) => r.Data_Type).filter(Boolean)));
  const dataTypeHits = dataTypeValues.filter((dt) => {
    const dtLower = dt.toLowerCase();
    return DATA_TYPE_KEYWORDS.some((kw) => q.includes(kw) && dtLower.includes(kw));
  });
  if (dataTypeHits.length) {
    matchedTerms.push(`data type includes ${dataTypeHits.join(" / ")}`);
  }

  if (/\bresistance genes?\b/.test(q)) {
    filters.entityType = ["Gene_Resistance_Factor"];
    matchedTerms.push("record type = resistance gene / factor");
  }

  if (/\bdatabases?\b|\bresources?\b/.test(q) && !filters.entityType) {
    filters.entityType = ["Dataset"];
    matchedTerms.push("record type = dataset / database record");
  }

  return { filters, matchedTerms, dataTypeHits };
}

export function renderAsk(container, data) {
  container.innerHTML = `
    <h1>Ask HOPPER</h1>
    <p class="lede">Ask a question in plain language about the hosts, pathogens, diseases, genes, datasets and databases indexed in this prototype. HOPPER interprets the question as a structured search over the local dataset — it never invents a database, relationship, or fact that isn't already indexed here.</p>

    <form class="ask-box" id="ask-form">
      <div class="search-row">
        <input type="search" id="ask-input" placeholder="e.g. Find fungal pathogens associated with rice diseases" aria-label="Ask HOPPER a question">
        <button class="btn" type="submit">Ask</button>
      </div>
      <div class="ask-examples">
        Try: ${EXAMPLES.map((e) => `<button type="button" data-example="${escapeHtml(e)}">${escapeHtml(e)}</button>`).join(" &nbsp;·&nbsp; ")}
      </div>
    </form>

    <div id="ask-output"></div>
  `;

  const output = qs("#ask-output", container);

  function run(query) {
    qs("#ask-input", container).value = query;
    const { filters, matchedTerms, dataTypeHits } = interpretQuery(query, data);
    let results = searchRecords(data, { query: "", filters });
    if (dataTypeHits.length) {
      const hitSet = new Set(dataTypeHits);
      results = results.filter((r) => hitSet.has(r.Data_Type));
    }
    let usedFallback = false;

    const hadStructuredSignal = Object.keys(filters).length > 0 || dataTypeHits.length > 0;
    if (!hadStructuredSignal || results.length === 0) {
      // fall back to a plain free-text search over the same query
      const fallback = searchRecords(data, { query });
      if (fallback.length) { results = fallback; usedFallback = true; }
    }

    const interpretation = matchedTerms.length
      ? `Interpreted as: ${matchedTerms.join("; ")}.`
      : usedFallback
      ? `No structured filters were recognized, so this ran as a plain keyword search.`
      : `No structured filters or keyword matches were recognized.`;

    output.innerHTML = `
      <div class="demo-badge">Demo semantic search mode — local, rule-based, no external API</div>
      <div class="ask-answer">
        <p>Based on the currently indexed HOPPER records, ${results.length} record${results.length === 1 ? "" : "s"} matched this question. ${escapeHtml(interpretation)}</p>
      </div>
      <div class="result-list">
        ${results.length ? results.map(resultCardHtml).join("") : `<div class="empty-state">No indexed records matched. Try mentioning a specific host, pathogen, disease, gene, region, or database name.</div>`}
      </div>
    `;
  }

  qs("#ask-form", container).addEventListener("submit", (e) => {
    e.preventDefault();
    const q = qs("#ask-input", container).value.trim();
    if (q) run(q);
  });
  container.querySelectorAll("[data-example]").forEach((btn) => {
    btn.addEventListener("click", () => run(btn.dataset.example));
  });
}
