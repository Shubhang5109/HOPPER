// record.js — single HOPPER record detail page

import { escapeHtml, val } from "./util.js";

const REL_LABELS = {
  HOST_HAS_DISEASE: { forward: "host of", reverse: "affects" },
  DISEASE_CAUSED_BY: { forward: "caused by", reverse: "causes" },
  HOST_HAS_RESISTANCE_FACTOR: { forward: "carries resistance factor", reverse: "resistance factor in" },
  RESISTANCE_FACTOR_TARGETS_PATHOGEN: { forward: "confers resistance to", reverse: "targeted by resistance factor" },
  PATHOGEN_HAS_STRAIN: { forward: "has strain / isolate", reverse: "strain / isolate of" },
  DISEASE_HAS_PHENOTYPE: { forward: "has phenotype", reverse: "phenotype of" },
  PATHOGEN_REPRESENTED_IN: { forward: "represented in dataset", reverse: "represents pathogen" },
  ENTITY_LINKED_TO_DATASET: { forward: "linked to dataset", reverse: "linked to entity" },
};

function fieldRow(label, value) {
  if (value === null || value === undefined || value === "") return "";
  return `<div class="field-row"><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`;
}

function citationRowHtml(record, data) {
  if (!record.Source_Database || record.Source_Database === "Not available") return "";
  const source = data.sources.find((s) => s.Name === record.Source_Database);
  if (!source || !source.Reference_Publication) return "";
  const p = source.Reference_Publication;
  const citationText = `${p.Authors} (${p.Year}). "${p.Title}." ${p.Venue}.`;
  const citationHtml = p.URL
    ? `${escapeHtml(citationText)} <a href="${escapeHtml(p.URL)}" target="_blank" rel="noopener">↗</a>`
    : escapeHtml(citationText);
  return `<div class="field-row"><dt>Reference publication</dt><dd>${citationHtml}</dd></div>`;
}

function relatedRecordsHtml(record, data) {
  const rels = data.relByEntity.get(record.HOPPER_ID) || [];
  const items = [];
  rels.forEach((rel) => {
    const labelSet = REL_LABELS[rel.type];
    if (!labelSet) return; // skip synonym/region note-only edges here
    let otherId, label;
    if (rel.source === record.HOPPER_ID && rel.target) {
      otherId = rel.target; label = labelSet.forward;
    } else if (rel.target === record.HOPPER_ID && rel.source) {
      otherId = rel.source; label = labelSet.reverse;
    } else {
      return;
    }
    const other = data.byId.get(otherId);
    if (!other) return;
    items.push({ label, other });
  });

  if (!items.length) {
    return `<p style="color:var(--color-text-muted);">No related records are linked to this entity in the current prototype dataset.</p>`;
  }

  return `<ul class="related-list">${items.map((it) => `
    <li>
      <span class="rel-type">${escapeHtml(it.label)}</span>
      <a href="#/record/${encodeURIComponent(it.other.HOPPER_ID)}">${escapeHtml(it.other.Name)}</a>
      <span style="color:var(--color-text-faint);"> — ${escapeHtml(it.other.Entity_Type)}</span>
    </li>
  `).join("")}</ul>`;
}

export function renderRecord(container, data, hopperId) {
  const record = data.byId.get(hopperId);

  if (!record) {
    container.innerHTML = `
      <h1>Record not found</h1>
      <p>No HOPPER record matches <span class="mono">${escapeHtml(hopperId || "")}</span> in the current prototype dataset.</p>
      <p><a href="#/search">Return to search</a></p>
    `;
    return;
  }

  const sourceLink = record.Source_URL
    ? `<a href="${escapeHtml(record.Source_URL)}" target="_blank" rel="noopener">${escapeHtml(record.Source_URL)} ↗</a>`
    : val(record.Source_URL);

  container.innerHTML = `
    <div class="record-header">
      <div class="mono">${escapeHtml(record.HOPPER_ID)} <span class="tag tag--entity">${escapeHtml(record.Entity_Type)}</span></div>
      <h1>${escapeHtml(record.Name)}</h1>
      ${record.Normalized_Name && record.Normalized_Name !== record.Name ? `<p class="lede">${escapeHtml(record.Normalized_Name)}</p>` : ""}
    </div>

    <div class="record-grid">
      <div>
        <div class="record-section">
          <h3>Identity</h3>
          <dl>
            ${fieldRow("HOPPER ID", record.HOPPER_ID)}
            ${fieldRow("Name", record.Name)}
            ${fieldRow("Entity type", record.Entity_Type)}
            ${fieldRow("Synonyms", (record.Synonyms || []).join(", ") || null)}
            ${fieldRow("Ontology term", record.Ontology_Term)}
          </dl>
        </div>

        <div class="record-section">
          <h3>Biological context</h3>
          <dl>
            ${fieldRow("Host", record.Host)}
            ${fieldRow("Disease", record.Disease)}
            ${fieldRow("Pathogen", record.Pathogen)}
            ${fieldRow("Pathogen type", record.Pathogen_Type)}
            ${fieldRow("Strain / isolate", record.Strain_or_Isolate)}
            ${fieldRow("Gene / protein", record.Gene_or_Protein)}
            ${fieldRow("Resistance factor", record.Resistance_Factor)}
          </dl>
        </div>

        <div class="record-section">
          <h3>Phenotype &amp; environment</h3>
          <dl>
            ${fieldRow("Phenotype", record.Phenotype)}
            ${fieldRow("Environmental context", record.Environmental_Context)}
            ${fieldRow("Geographic region", record.Geographic_Region)}
            ${fieldRow("Crop", record.Crop)}
          </dl>
        </div>
      </div>

      <div>
        <div class="record-section">
          <h3>Data</h3>
          <dl>
            ${fieldRow("Data type", record.Data_Type)}
            ${fieldRow("Evidence type", record.Evidence_Type)}
            ${fieldRow("Year", record.Year)}
            ${fieldRow("License / access status", record.License_or_Access_Status)}
          </dl>
        </div>

        <div class="record-section">
          <h3>Provenance</h3>
          <dl>
            <div class="field-row"><dt>Source database</dt><dd>${escapeHtml(val(record.Source_Database))}</dd></div>
            <div class="field-row"><dt>Original identifier</dt><dd>${escapeHtml(val(record.Source_ID))}</dd></div>
            <div class="field-row"><dt>Original URL</dt><dd>${sourceLink}</dd></div>
            ${citationRowHtml(record, data)}
            <div class="field-row"><dt>Mapping notes</dt><dd>${escapeHtml(val(record.Provenance))}</dd></div>
            <div class="field-row"><dt>Last checked</dt><dd>${escapeHtml(val(record.Last_Checked))}</dd></div>
          </dl>
        </div>

        <div class="record-section">
          <h3>Related records</h3>
          ${relatedRecordsHtml(record, data)}
          <p style="margin-top:0.75rem;"><a href="#/explore?entity=${encodeURIComponent(record.HOPPER_ID)}">View this entity in Explore →</a></p>
        </div>
      </div>
    </div>
  `;
}
