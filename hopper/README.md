# HOPPER

**Harmonized Ontology & Plant Pathology Exploration Repository**

A small, working prototype of an interoperability layer over fragmented
plant-disease databases — searchable, explorable, and deployable as a
static site with no backend, no build step, and no paid hosting.

**Live demo:** once deployed (see below), your site will be at
`https://<your-github-username>.github.io/<your-repo-name>/`

---

## Overview

Plant-disease research depends on many independently built databases —
image datasets, pathogen genome browsers, host-pathogen interaction
catalogues, resistance-gene repositories, crop genomics platforms, stress
and phenomics databases, soil microbiome archives. Each is valuable. None
of them were designed to be queried together.

HOPPER does not try to replace or mirror any of them. It normalizes a
small, curated set of representative records from across these domains
into one common schema, links them to each other and to their original
sources, and puts a simple search, filter, relationship-explorer, and
plain-language query interface on top.

> **HOPPER is a demonstration prototype, not production infrastructure.**
> It contains roughly 90 curated records, not a comprehensive index. See
> **About → Limitations** on the site (or the bottom of this README) for
> the full, honest list of what it does not do.

## Scientific motivation

HOPPER's structure follows the review *"From Fragmented Databases to
AI-Ready Data Infrastructure: A Critical Review of Plant Disease
Databases"*, which audits the plant-disease database landscape across
seven functional domains (AI-ready image datasets, pathogen genomics,
host-pathogen interaction, resistance genes, crop-specific genomics,
stress/phenomics, and soil microbiome data) and identifies ten recurring
interoperability bottlenecks — inconsistent metadata, weak identifier
mapping, missing longitudinal data, uneven AI-readiness, inconsistent
ontology adoption, species and geographic bias, and weak host-pathogen-
environment integration, among others. HOPPER's schema and cross-database
views are organized around that same set of domains and problems. See
`docs/interoperability.md` and the site's About page for more detail.

## Architecture

```
                     HOPPER WEB INTERFACE (static HTML/CSS/JS)
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                      │
           Search                Filters              Ask HOPPER
              │                     │                      │
              └─────────────────────┼──────────────────────┘
                                    │
                       NORMALIZATION LAYER (schema_mapping.json)
                                    │
                  ┌──────────────────┴──────────────────┐
                  │                                      │
        hopper_records.json                  relationships.json /
        (the common schema)                  identifier_mappings.json
                  │                                      │
                  └──────────────────┬───────────────────┘
                                    │
                         sources.json (Databases directory)
                                    │
                          EXTERNAL AUTHORITATIVE RESOURCES
                     (PHI-base, FungiDB, PlantVillage, MaizeGDB, …)
```

There is deliberately no backend, no database server, no authentication,
and no build step. It is a static site: open `index.html` through any web
server and it works. See `docs/future-architecture.md` for where a later
version could add real infrastructure.

**Why no build step?** A plain HTML/CSS/JS (ES modules) site can be pushed
straight to GitHub Pages with nothing to install and nothing that can fail
to compile. If you'd rather work in React/Vite later, `docs/future-architecture.md`
explains where that would slot in without changing the data layer.

## Data model

See [`docs/data-model.md`](docs/data-model.md) for the full field-by-field
reference. In short: every record — host, pathogen, disease, gene, strain,
phenotype, or a reference to an external dataset — shares one schema
(`HOPPER_ID`, `Entity_Type`, `Name`, `Host`, `Pathogen`, `Disease`,
`Source_Database`, `Source_URL`, `Provenance`, `Last_Checked`, …), and
every record's provenance is explicit: where an exact source record
couldn't be safely represented, HOPPER links to the resource itself
instead of inventing a specific ID.

## Integrated resources

HOPPER references ~28 external resources spanning disease image/AI
datasets, pathogen genomics, host-pathogen interaction, resistance genes,
multi-omics, crop-specific genomics, stress/phenomics, and soil
microbiome data — see the **Databases** page on the site, or
`data/sources.json`.

## Search & filtering

Search runs entirely client-side against `data/hopper_records.json` — no
network calls. Filters (host/crop, pathogen type, record type, data
domain, source database, geographic region, evidence type, year) are
computed from the dataset itself, so a filter option only ever appears if
at least one record actually has that value. Any filtered result set can
be exported as CSV or JSON directly from the Search page.

## Ask HOPPER (AI-assisted query)

`js/ask.js` implements a **local, rule-based keyword parser** — not a
hosted LLM. It recognizes host, pathogen-type, source-database, region,
and data-domain keywords in a plain-language question, turns them into the
same structured filter object the Search page uses, and always answers
only from indexed records (falling back to a plain keyword search if no
structured signal is recognized). This means the public GitHub Pages
deployment works with **no API key and no secret configuration** — see
`docs/future-architecture.md` for how a real LLM could later be added
behind the same interface.

## Installation & local development

You do not need Node, npm, or any package manager to run HOPPER — it's
plain files. You do need a simple local web server, because browsers block
`fetch()` of local JSON files when a page is opened directly from disk
(a `file://` URL).

**If you have Python installed** (macOS and Linux usually already do):

```bash
cd hopper
python3 -m http.server 8000
```

Then open `http://localhost:8000` in your browser.

**If you have Node instead:**

```bash
cd hopper
npx serve .
```

and open the URL it prints.

Either way, you should see the HOPPER homepage with a working search box.

## GitHub Pages deployment

See the step-by-step walkthrough at the end of this README if you're not
already comfortable with Git/GitHub — the short version:

1. Push this folder to a new GitHub repository.
2. In the repository, go to **Settings → Pages**.
3. Under **Build and deployment → Source**, choose **GitHub Actions**.
4. The included workflow (`.github/workflows/deploy.yml`) will run
   automatically on your next push to `main` and publish the site — no
   build step, it just uploads the files as-is.

## Data provenance

External databases remain the authoritative sources for their own data.
HOPPER stores normalized reference metadata and cross-database
relationships — it does not claim to replace, mirror, or comprehensively
reproduce any source resource. Every record carries a `Source_Database`,
`Source_ID` (or `Not available` for resource-level references),
`Source_URL`, a `Provenance` note, and a `Last_Checked` date. See the
site's **About → Data & provenance** section.

## Limitations

HOPPER v1:

- is a demonstration prototype, not production-scale infrastructure;
- contains a small curated subset (~90 records), not a comprehensive index;
- does not mirror external databases — most dataset-type records are
  resource-level references with real links, not deep per-record imports;
- may contain incomplete cross-database identifier mappings;
- does not synchronize with source databases in real time;
- does not guarantee complete ontology alignment;
- does not replace any of the authoritative source databases it references;
- does not (yet) provide large-scale AI infrastructure.

## Future development

See [`docs/future-architecture.md`](docs/future-architecture.md) for a
realistic v1 → v1.5 → v2 roadmap (scheduled data refresh, a real
ingestion pipeline, a queryable API, deeper ontology alignment, a real
knowledge graph, semantic search, and eventually an optional LLM
reasoning layer) — none of it implemented yet, on purpose.

## Citation

If you reference this prototype: *HOPPER — Harmonized Ontology & Plant
Pathology Exploration Repository (prototype), 2026.* Please also cite the
individual source databases directly when using data derived from them —
see the Databases page or `data/sources.json` for links.

---

## Project structure

```
hopper/
├── index.html                  single-page app shell
├── css/styles.css              all styling (design tokens + components)
├── js/
│   ├── app.js                  entry point + hash router
│   ├── data.js                 loads data/*.json, builds indices, search/filter engine
│   ├── util.js                 small DOM/formatting helpers
│   ├── home.js / search.js / record.js / explore.js / databases.js / ask.js / about.js
│                                one module per page
├── data/
│   ├── hopper_records.json     the ~90 normalized entity records (the common schema)
│   ├── relationships.json      typed edges between records
│   ├── sources.json            the external database directory
│   ├── identifier_mappings.json  curated cross-database "hub concept" chains
│   └── schema_mapping.json     the normalization/mapping layer config
├── scripts/
│   ├── build_data.py           regenerates everything in data/ from structured Python
│   └── e2e_test.py             Playwright smoke test (optional, for contributors)
├── docs/
│   ├── data-model.md
│   ├── interoperability.md
│   └── future-architecture.md
└── .github/workflows/deploy.yml  GitHub Pages deploy workflow (no build step)
```

## Adding a new record or source

1. Open `scripts/build_data.py`.
2. To add a **source database**: add an entry to the `SOURCES` list (name,
   domain, URL, access status, etc).
3. To add a **host, pathogen, disease, gene, strain, phenotype, or
   dataset**: add an entry to the matching list (`HOSTS`, `PATHOGENS`,
   `DISEASES`, `GENES`, `STRAINS`, `PHENOTYPES`, `DATASETS`). Datasets
   reference other entities via a `links` list of `(kind, slug)` pairs —
   the script derives `relationships.json` from these automatically, so
   you don't need to hand-write relationship edges.
4. Regenerate the data:
   ```bash
   python3 scripts/build_data.py
   ```
5. Refresh your local server and confirm the new record shows up in
   Search. Commit and push — the GitHub Actions workflow redeploys
   automatically.

If you added new checks that should stay green, `scripts/e2e_test.py` is a
Playwright smoke test you can run locally (`pip install playwright &&
playwright install chromium`, then start a local server and run the
script) — it is not required for deployment.
