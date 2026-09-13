// app.js — entry point + hash router. No build step, no framework: this
// script is loaded as a native ES module directly by index.html.

import { loadData } from "./data.js";
import { renderHome } from "./home.js";
import { renderSearch } from "./search.js";
import { renderRecord } from "./record.js";
import { renderExplore } from "./explore.js";
import { renderDatabases } from "./databases.js";
import { renderAsk } from "./ask.js";
import { renderAbout } from "./about.js";
import { setActiveNav } from "./util.js";

const app = document.getElementById("app");

async function main() {
  let data;
  try {
    data = await loadData();
  } catch (err) {
    app.innerHTML = `
      <div class="empty-state">
        <h2>Could not load HOPPER data</h2>
        <p>${err.message}</p>
        <p>If you opened index.html directly from disk (a <span class="mono">file://</span> URL), most browsers block loading local JSON files that way. Serve the folder with a simple local server instead — see the README for a one-line command.</p>
      </div>
    `;
    return;
  }

  function route() {
    const hash = window.location.hash || "#/";
    const path = hash.slice(1).split("?")[0] || "/";
    window.scrollTo(0, 0);
    setActiveNav(path);

    if (path === "/") {
      renderHome(app, data);
    } else if (path === "/search") {
      renderSearch(app, data, hash);
    } else if (path.startsWith("/record/")) {
      const id = decodeURIComponent(path.slice("/record/".length));
      renderRecord(app, data, id);
    } else if (path === "/explore") {
      renderExplore(app, data, hash);
    } else if (path === "/databases") {
      renderDatabases(app, data);
    } else if (path === "/ask") {
      renderAsk(app, data);
    } else if (path === "/about") {
      renderAbout(app);
    } else {
      app.innerHTML = `<h1>Page not found</h1><p><a href="#/">Return home</a></p>`;
    }
  }

  window.addEventListener("hashchange", route);
  route();
}

main();
