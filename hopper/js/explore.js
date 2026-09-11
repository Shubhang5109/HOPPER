// explore.js — Explore page: a modest relationship diagram + cross-database matrix
// Deliberately hand-rolled SVG (no charting/graph library) — the brief calls for
// a small, legible diagram, not a force-directed network.

import { escapeHtml, qs } from "./util.js";

const REL_LABELS = {
  HOST_HAS_DISEASE: { forward: "host of", reverse: "affects" },
  DISEASE_CAUSED_BY: { forward: "caused by", reverse: "causes" },
  HOST_HAS_RESISTANCE_FACTOR: { forward: "has resistance factor", reverse: "resistance factor in" },
  RESISTANCE_FACTOR_TARGETS_PATHOGEN: { forward: "confers resistance to", reverse: "targeted by" },
  PATHOGEN_HAS_STRAIN: { forward: "has strain", reverse: "strain of" },
  DISEASE_HAS_PHENOTYPE: { forward: "has phenotype", reverse: "phenotype of" },
  PATHOGEN_REPRESENTED_IN: { forward: "represented in", reverse: "represents" },
  ENTITY_LINKED_TO_DATASET: { forward: "linked to", reverse: "linked to" },
};

const MATRIX_DATABASES = [
  "PHI-base", "FungiDB", "PRGdb", "Expression Atlas", "PlantPAD", "MGnify", "Rice SNP-Seek", "CyVerse",
];

const MAX_NEIGHBORS_SHOWN = 8;

function neighborsFor(entityId, data) {
  const rels = data.relByEntity.get(entityId) || [];
  const out = [];
  rels.forEach((rel) => {
    const labelSet = REL_LABELS[rel.type];
    if (!labelSet) return;
    let otherId, label;
    if (rel.source === entityId && rel.target) { otherId = rel.target; label = labelSet.forward; }
    else if (rel.target === entityId && rel.source) { otherId = rel.source; label = labelSet.reverse; }
    else return;
    const other = data.byId.get(otherId);
    if (other) out.push({ label, other });
  });
  return out;
}

function buildDiagramSvg(focal, neighbors) {
  const shown = neighbors.slice(0, MAX_NEIGHBORS_SHOWN);
  const rowHeight = 54;
  const height = Math.max(120, shown.length * rowHeight + 40);
  const width = 720;
  const focalX = 20, focalY = height / 2 - 20, focalW = 190, focalH = 48;
  const nodeX = 420, nodeW = 280, nodeH = 38;

  const focalBox = `
    <g class="node-link">
      <rect class="node-box is-focus" x="${focalX}" y="${focalY}" width="${focalW}" height="${focalH}" rx="4"></rect>
      <text x="${focalX + focalW / 2}" y="${focalY + focalH / 2 + 5}" text-anchor="middle" font-size="12.5" font-weight="600">${escapeHtml(truncate(focal.Name, 24))}</text>
    </g>
  `;

  let rows = "";
  shown.forEach((n, i) => {
    const y = 30 + i * rowHeight;
    const midY = y + nodeH / 2;
    const focalMidY = focalY + focalH / 2;
    rows += `
      <line class="edge-line" x1="${focalX + focalW}" y1="${focalMidY}" x2="${nodeX}" y2="${midY}"></line>
      <text class="edge-label" x="${(focalX + focalW + nodeX) / 2}" y="${(focalMidY + midY) / 2 - 6}" text-anchor="middle">${escapeHtml(n.label)}</text>
      <g class="node-link" data-nav="${escapeHtml(n.other.HOPPER_ID)}">
        <rect class="node-box" x="${nodeX}" y="${y}" width="${nodeW}" height="${nodeH}" rx="4"></rect>
        <text x="${nodeX + 12}" y="${y + nodeH / 2 + 4}" font-size="12">${escapeHtml(truncate(n.other.Name, 34))}</text>
      </g>
    `;
  });

  const overflowNote = neighbors.length > MAX_NEIGHBORS_SHOWN
    ? `<text x="${nodeX}" y="${height - 6}" font-size="11" fill="var(--color-text-faint)">+${neighbors.length - MAX_NEIGHBORS_SHOWN} more — see the record page for the full list</text>`
    : "";

  return `<svg viewBox="0 0 ${width} ${height}" width="100%" height="${height}" role="img" aria-label="Relationship diagram for ${escapeHtml(focal.Name)}">
    ${rows}
    ${focalBox}
    ${overflowNote}
  </svg>`;
}

function truncate(str, n) {
  if (!str) return "";
  return str.length > n ? str.slice(0, n - 1) + "…" : str;
}

function matrixHtml(entityId, data) {
  const rels = data.relByEntity.get(entityId) || [];
  const linkedSourceDbs = new Set();
  const linkedRecordByDb = new Map();
  rels.forEach((rel) => {
    if (rel.type !== "PATHOGEN_REPRESENTED_IN" && rel.type !== "ENTITY_LINKED_TO_DATASET") return;
    const datasetId = rel.source === entityId ? rel.target : rel.source;
    const ds = data.byId.get(datasetId);
    if (ds && ds.Source_Database && ds.Source_Database !== "Not available") {
      linkedSourceDbs.add(ds.Source_Database);
      if (!linkedRecordByDb.has(ds.Source_Database)) linkedRecordByDb.set(ds.Source_Database, ds);
    }
  });

  const cells = MATRIX_DATABASES.map((db) => {
    const hit = linkedSourceDbs.has(db);
    if (!hit) return `<td class="miss">—</td>`;
    const rec = linkedRecordByDb.get(db);
    return `<td class="hit"><a href="#/record/${encodeURIComponent(rec.HOPPER_ID)}">✓ view</a></td>`;
  }).join("");

  return `
    <table class="matrix">
      <caption>Cells are populated only where this prototype dataset contains an actual linked record — this is a demonstration subset, not a complete cross-reference.</caption>
      <thead><tr><th>Concept</th><th>HOPPER</th>${MATRIX_DATABASES.map((d) => `<th>${escapeHtml(d)}</th>`).join("")}</tr></thead>
      <tbody><tr><td>${escapeHtml(data.byId.get(entityId).Name)}</td><td class="hit">✓ indexed</td>${cells}</tr></tbody>
    </table>
  `;
}

function curatedMappingHtml(entityId, data) {
  const chains = data.mappings.filter((m) => m.hopper_id === entityId);
  if (!chains.length) return "";
  return chains.map((chain) => `
    <div style="margin-top:1.25rem;">
      <h4>Curated concept mapping: ${escapeHtml(chain.concept)}</h4>
      <ul class="related-list">
        ${chain.chain.map((c) => `
          <li>
            <span class="rel-type mono">${escapeHtml(c.database)}</span>
            <a href="#/record/${encodeURIComponent(c.hopper_record)}">${escapeHtml(data.byId.get(c.hopper_record)?.Name || c.hopper_record)}</a>
            ${c.url ? ` — <a href="${escapeHtml(c.url)}" target="_blank" rel="noopener">source ↗</a>` : ""}
          </li>
        `).join("")}
      </ul>
    </div>
  `).join("");
}

export function renderExplore(container, data, hash) {
  const params = new URLSearchParams((hash || "").split("?")[1] || "");
  let entityId = params.get("entity") || data.records.find((r) => r.HOPPER_ID === "HOPPER:DIS:0001")?.HOPPER_ID;

  const options = data.records
    .slice()
    .sort((a, b) => a.Name.localeCompare(b.Name))
    .map((r) => `<option value="${escapeHtml(r.Name)} (${escapeHtml(r.HOPPER_ID)})"></option>`)
    .join("");
  const nameToId = new Map(data.records.map((r) => [`${r.Name} (${r.HOPPER_ID})`, r.HOPPER_ID]));

  container.innerHTML = `
    <h1>Explore</h1>
    <p class="lede">Pick any HOPPER entity to see its direct relationships and which external databases represent it in this prototype dataset.</p>

    <div class="entity-picker">
      <label for="entity-input" style="display:block;font-size:0.85rem;color:var(--color-text-muted);margin-bottom:0.3rem;">Entity</label>
      <input type="text" id="entity-input" list="entity-options" placeholder="Start typing a host, pathogen, disease, gene or dataset…" style="width:100%;">
      <datalist id="entity-options">${options}</datalist>
    </div>

    <div id="explore-body"></div>
  `;

  const input = qs("#entity-input", container);
  const body = qs("#explore-body", container);

  function draw(id) {
    const focal = data.byId.get(id);
    if (!focal) {
      body.innerHTML = `<div class="empty-state">Type an entity name above (or pick from the list) to explore its relationships.</div>`;
      return;
    }
    input.value = `${focal.Name} (${focal.HOPPER_ID})`;
    const neighbors = neighborsFor(id, data);
    body.innerHTML = `
      <h2>Relationships for ${escapeHtml(focal.Name)}</h2>
      <p class="mono" style="color:var(--color-text-faint);">${escapeHtml(focal.HOPPER_ID)} · <a href="#/record/${encodeURIComponent(focal.HOPPER_ID)}">Open full record →</a></p>
      <div class="graph-panel">${buildDiagramSvg(focal, neighbors)}</div>

      <h2>Cross-database connections</h2>
      <p>For this entity, which of a representative set of external databases contain a linked record in the current prototype dataset:</p>
      ${matrixHtml(id, data)}
      ${curatedMappingHtml(id, data)}
    `;
    body.querySelectorAll("[data-nav]").forEach((node) => {
      node.addEventListener("click", () => {
        window.location.hash = `#/explore?entity=${encodeURIComponent(node.dataset.nav)}`;
      });
    });
  }

  input.addEventListener("change", () => {
    const id = nameToId.get(input.value);
    if (id) window.location.hash = `#/explore?entity=${encodeURIComponent(id)}`;
  });

  draw(entityId);
}
