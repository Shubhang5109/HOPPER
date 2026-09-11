// databases.js — Source database directory page

import { escapeHtml } from "./util.js";

export function renderDatabases(container, data) {
  const sorted = data.sources.slice().sort((a, b) => a.Domain.localeCompare(b.Domain) || a.Name.localeCompare(b.Name));

  container.innerHTML = `
    <h1>Databases</h1>
    <p class="lede">HOPPER integrates representative reference records and links from the following external resources. HOPPER does not mirror their full contents — each remains the authoritative source for its own data. See <a href="#/about">Data &amp; Provenance</a> for details.</p>

    <table class="db-table">
      <thead>
        <tr>
          <th>Database</th>
          <th>Domain</th>
          <th>Data type</th>
          <th>Organisms / crops</th>
          <th>Geography</th>
          <th>Access</th>
          <th>Link</th>
        </tr>
      </thead>
      <tbody>
        ${sorted.map((s) => `
          <tr>
            <td><strong>${escapeHtml(s.Name)}</strong><div style="color:var(--color-text-muted); font-size:0.82rem; margin-top:0.2rem;">${escapeHtml(s.Role_in_HOPPER)}</div></td>
            <td>${escapeHtml(s.Domain)}</td>
            <td>${escapeHtml(s.Data_Type)}</td>
            <td>${escapeHtml(s.Organisms_Crops)}</td>
            <td>${escapeHtml(s.Geographic_Scope)}</td>
            <td>${escapeHtml(s.Access)}</td>
            <td>${s.External_URL ? `<a href="${escapeHtml(s.External_URL)}" target="_blank" rel="noopener">Visit ↗</a>` : "<span class=\"mono\" style=\"color:var(--color-text-faint);\">no stable URL on file</span>"}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}
