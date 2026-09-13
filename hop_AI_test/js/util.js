// util.js — small shared helpers. No dependencies, no build step.

export function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function val(v, fallback = "Not available") {
  if (v === null || v === undefined || v === "") return fallback;
  return v;
}

export function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

export function qs(sel, root = document) { return root.querySelector(sel); }
export function qsa(sel, root = document) { return Array.from(root.querySelectorAll(sel)); }

export function setActiveNav(route) {
  qsa("#site-nav a").forEach((a) => {
    const r = a.getAttribute("data-route");
    const active = r === route || (r !== "/" && route.startsWith(r));
    a.classList.toggle("is-active", active);
  });
}

// Renders a compact result card used by Search results and Ask HOPPER answers.
export function resultCardHtml(r) {
  const metaBits = [];
  if (r.Host) metaBits.push(`<span><strong>Host:</strong> ${escapeHtml(r.Host)}</span>`);
  if (r.Pathogen) metaBits.push(`<span><strong>Pathogen:</strong> ${escapeHtml(r.Pathogen)}</span>`);
  if (r.Data_Type) metaBits.push(`<span><strong>Data type:</strong> ${escapeHtml(r.Data_Type)}</span>`);
  if (r.Source_Database && r.Source_Database !== "Not available") {
    metaBits.push(`<span><strong>Source:</strong> ${escapeHtml(r.Source_Database)}</span>`);
  }
  const sourceLink = r.Source_URL
    ? `<a href="${escapeHtml(r.Source_URL)}" target="_blank" rel="noopener">Open source ↗</a>`
    : "";
  return `
    <article class="result-card">
      <div class="result-card__id mono">${escapeHtml(r.HOPPER_ID)} <span class="tag tag--entity">${escapeHtml(r.Entity_Type)}</span></div>
      <h3 class="result-card__name"><a href="#/record/${encodeURIComponent(r.HOPPER_ID)}">${escapeHtml(r.Name)}</a></h3>
      <div class="meta-line">${metaBits.join("")}</div>
      <div class="card-actions">
        <a href="#/record/${encodeURIComponent(r.HOPPER_ID)}">View record</a>
        ${sourceLink}
      </div>
    </article>
  `;
}

export function downloadFile(filename, content, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function recordsToCsv(records) {
  if (!records.length) return "";
  const cols = Object.keys(records[0]);
  const escapeCsv = (v) => {
    if (Array.isArray(v)) v = v.join("; ");
    if (v === null || v === undefined) v = "";
    v = String(v);
    if (/[",\n]/.test(v)) v = '"' + v.replace(/"/g, '""') + '"';
    return v;
  };
  const lines = [cols.join(",")];
  records.forEach((r) => lines.push(cols.map((c) => escapeCsv(r[c])).join(",")));
  return lines.join("\n");
}
