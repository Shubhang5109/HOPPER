// ask.js — "Ask HOPPER": local rule-based retrieval, with two optional
// real-model synthesis layers on top of it. Priority, per question:
//
//   1. Bring-your-own-key mode: if the person viewing the page has entered
//      their own Anthropic API key (this session or remembered in this
//      browser's localStorage), HOPPER calls Claude directly from the
//      browser using Anthropic's documented "direct browser access" CORS
//      header. No deployment step, no server, works the moment these files
//      are uploaded — the key lives only in this browser and is sent only
//      to api.anthropic.com.
//   2. Shared proxy mode: if js/config.js ASK_HOPPER_PROXY_URL is set (see
//      cloudflare-worker/ask-hopper-proxy.js + docs/ai-proxy-setup.md),
//      HOPPER calls that instead — useful if you want every visitor to get
//      AI answers without each of them needing their own key.
//   3. Local rule-based mode: the default. Parses a handful of recognizable
//      signals out of the query (pathogen type, host, source database,
//      region, data-type keywords) into the same structured filter object
//      the Search page uses. Never calls any external service.
//
// In every mode, the *retrieval* step is identical and always local: Ask
// HOPPER never answers from anything other than the records HOPPER itself
// indexes, and modes 1 and 2 only ever send Claude the records retrieval
// already found, with an instruction not to go beyond them.

import { searchRecords } from "./data.js";
import { escapeHtml, resultCardHtml, qs } from "./util.js";
import { ASK_HOPPER_PROXY_URL, ASK_HOPPER_PROXY_TIMEOUT_MS } from "./config.js";

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

const MAX_CONTEXT_RECORDS = 25;
const CLAUDE_MODEL = "claude-haiku-4-5-20251001";
const CLAUDE_MAX_TOKENS = 400;
const STORAGE_KEY = "hopper_ask_anthropic_key";

// In-memory only unless the person opts in to "remember on this device".
let sessionApiKey = "";
try {
  sessionApiKey = localStorage.getItem(STORAGE_KEY) || "";
} catch {
  // localStorage can throw in locked-down/private-browsing contexts — fine,
  // BYOK mode just won't persist across reloads in that case.
}

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

function compactForContext(r) {
  return {
    HOPPER_ID: r.HOPPER_ID,
    Name: r.Name,
    Entity_Type: r.Entity_Type,
    Host: r.Host,
    Pathogen: r.Pathogen,
    Disease: r.Disease,
    Data_Type: r.Data_Type,
    Source_Database: r.Source_Database,
    Geographic_Region: r.Geographic_Region,
    Provenance: r.Provenance,
  };
}

function buildSystemPrompt(records) {
  return [
    'You are "Ask HOPPER", answering questions about a small plant-disease',
    "prototype database called HOPPER (Harmonized Ontology & Plant Pathology",
    "Exploration Repository).",
    "",
    "Answer ONLY using the JSON records listed below, which HOPPER's own",
    "local search already retrieved for this question. Do not use outside",
    "knowledge, and do not invent databases, genes, relationships, or facts",
    "that are not present in these records.",
    "",
    "If the records don't contain enough to answer the question, say that",
    "plainly instead of guessing.",
    "",
    "When you reference a record, name it and give its HOPPER_ID so the",
    "person can find it on the site. Keep the answer under 120 words, plain",
    "prose, no markdown headers or bullet lists.",
    "",
    "INDEXED RECORDS (JSON):",
    JSON.stringify(records.slice(0, MAX_CONTEXT_RECORDS).map(compactForContext)),
  ].join("\n");
}

// --- Mode 1: direct-from-browser call using the person's own API key -----

async function askClaudeDirect(question, records, apiKey) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), ASK_HOPPER_PROXY_TIMEOUT_MS);
  try {
    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
        "anthropic-dangerous-direct-browser-access": "true",
      },
      body: JSON.stringify({
        model: CLAUDE_MODEL,
        max_tokens: CLAUDE_MAX_TOKENS,
        system: buildSystemPrompt(records),
        messages: [{ role: "user", content: question }],
      }),
      signal: controller.signal,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data?.error?.message || `Anthropic API returned status ${res.status}`;
      return { ok: false, error: msg };
    }
    const answer = (data.content || []).filter((b) => b.type === "text").map((b) => b.text).join("\n").trim();
    return { ok: true, answer: answer || "The model returned no text." };
  } catch (err) {
    return { ok: false, error: err.name === "AbortError" ? "Request timed out" : err.message };
  } finally {
    clearTimeout(timeout);
  }
}

// --- Mode 2: shared server-side proxy (Cloudflare Worker etc.) -----------

async function askProxy(question, records) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), ASK_HOPPER_PROXY_TIMEOUT_MS);
  try {
    const res = await fetch(ASK_HOPPER_PROXY_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, records: records.slice(0, MAX_CONTEXT_RECORDS).map(compactForContext) }),
      signal: controller.signal,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.answer) {
      return { ok: false, error: data.error || `Proxy responded with status ${res.status}` };
    }
    return { ok: true, answer: data.answer };
  } catch (err) {
    return { ok: false, error: err.name === "AbortError" ? "Proxy request timed out" : err.message };
  } finally {
    clearTimeout(timeout);
  }
}

function keySettingsHtml() {
  const masked = sessionApiKey
    ? `${sessionApiKey.slice(0, 7)}${"•".repeat(Math.max(0, sessionApiKey.length - 11))}${sessionApiKey.slice(-4)}`
    : "";
  return `
    <details class="ai-settings" ${sessionApiKey ? "" : "open"}>
      <summary>${sessionApiKey ? `Using your API key (${escapeHtml(masked)}) — click to change` : "Set up real AI answers (optional)"}</summary>
      <div class="ai-settings__body">
        <p>Paste your own <a href="https://console.anthropic.com" target="_blank" rel="noopener">Anthropic API key</a> to have Claude answer questions directly in this browser — no deployment needed. The key is sent only to <span class="mono">api.anthropic.com</span>, never anywhere else, and is not required to use the rest of HOPPER.</p>
        <div class="search-row">
          <input type="password" id="ai-key-input" placeholder="sk-ant-..." aria-label="Anthropic API key" autocomplete="off">
          <button class="btn btn--quiet" id="ai-key-save" type="button">Save</button>
          ${sessionApiKey ? `<button class="btn btn--quiet" id="ai-key-clear" type="button">Clear</button>` : ""}
        </div>
        <label class="filter-option" style="margin-top:0.5rem;">
          <input type="checkbox" id="ai-key-remember">
          <span>Remember on this device (stored only in this browser's localStorage)</span>
        </label>
        <p style="font-size:0.82rem; color:var(--color-text-muted); margin-top:0.5rem;">Tip: set a spend limit on this key in the Anthropic Console before using it here. Uses <span class="mono">${CLAUDE_MODEL}</span>.</p>
      </div>
    </details>
  `;
}

export function renderAsk(container, data) {
  const proxyConfigured = Boolean(ASK_HOPPER_PROXY_URL);

  container.innerHTML = `
    <h1>Ask HOPPER</h1>
    <p class="lede">Ask a question in plain language about the hosts, pathogens, diseases, genes, datasets and databases indexed in this prototype. HOPPER retrieves matching records locally first — it never answers from a database, relationship, or fact that isn't already indexed here.</p>

    ${keySettingsHtml()}

    <form class="ask-box" id="ask-form" style="margin-top:1.25rem;">
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

  function wireKeySettings() {
    const saveBtn = qs("#ai-key-save", container);
    const clearBtn = qs("#ai-key-clear", container);
    saveBtn?.addEventListener("click", () => {
      const val = qs("#ai-key-input", container).value.trim();
      const remember = qs("#ai-key-remember", container).checked;
      if (!val) return;
      sessionApiKey = val;
      try {
        if (remember) localStorage.setItem(STORAGE_KEY, val);
        else localStorage.removeItem(STORAGE_KEY);
      } catch {
        /* ignore storage errors */
      }
      renderAsk(container, data); // re-render to reflect the new state
    });
    clearBtn?.addEventListener("click", () => {
      sessionApiKey = "";
      try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
      renderAsk(container, data);
    });
  }
  wireKeySettings();

  function localInterpretation(query) {
    const { filters, matchedTerms, dataTypeHits } = interpretQuery(query, data);
    let results = searchRecords(data, { query: "", filters });
    if (dataTypeHits.length) {
      const hitSet = new Set(dataTypeHits);
      results = results.filter((r) => hitSet.has(r.Data_Type));
    }
    let usedFallback = false;

    const hadStructuredSignal = Object.keys(filters).length > 0 || dataTypeHits.length > 0;
    if (!hadStructuredSignal || results.length === 0) {
      const fallback = searchRecords(data, { query });
      if (fallback.length) { results = fallback; usedFallback = true; }
    }

    const interpretation = matchedTerms.length
      ? `Interpreted as: ${matchedTerms.join("; ")}.`
      : usedFallback
      ? `No structured filters were recognized, so this ran as a plain keyword search.`
      : `No structured filters or keyword matches were recognized.`;

    return { results, interpretation };
  }

  function renderResults({ badgeHtml, answerHtml, results }) {
    output.innerHTML = `
      ${badgeHtml}
      <div class="ask-answer">${answerHtml}</div>
      <div class="result-list">
        ${results.length ? results.map(resultCardHtml).join("") : `<div class="empty-state">No indexed records matched. Try mentioning a specific host, pathogen, disease, gene, region, or database name.</div>`}
      </div>
    `;
  }

  function ruleBasedFallback(results, interpretation, note) {
    renderResults({
      badgeHtml: `<div class="demo-badge">${note ? escapeHtml(note) + " — showing" : "Showing"} local rule-based interpretation${note ? "" : " (Demo semantic search mode — no external API)"}</div>`,
      answerHtml: `<p>Based on the currently indexed HOPPER records, ${results.length} record${results.length === 1 ? "" : "s"} matched this question. ${escapeHtml(interpretation)}</p>`,
      results,
    });
  }

  async function run(query) {
    qs("#ask-input", container).value = query;
    const { results, interpretation } = localInterpretation(query);

    if (!sessionApiKey && !proxyConfigured) {
      ruleBasedFallback(results, interpretation, null);
      return;
    }

    const modeLabel = sessionApiKey
      ? "Asking Claude directly from your browser with your API key…"
      : "Asking Claude via the configured proxy…";
    output.innerHTML = `
      <div class="demo-badge">${escapeHtml(modeLabel)}</div>
      <div class="ask-answer"><p>Thinking…</p></div>
      <div class="result-list">${results.map(resultCardHtml).join("")}</div>
    `;

    const aiResult = sessionApiKey
      ? await askClaudeDirect(query, results, sessionApiKey)
      : await askProxy(query, results);

    if (aiResult.ok) {
      renderResults({
        badgeHtml: `<div class="demo-badge">AI-assisted answer — Claude${sessionApiKey ? " (your API key, called directly from your browser)" : " (via configured proxy)"}, answering only from the records shown below</div>`,
        answerHtml: `<p>${escapeHtml(aiResult.answer)}</p>`,
        results,
      });
    } else {
      ruleBasedFallback(results, interpretation, `AI request failed (${aiResult.error})`);
    }
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
