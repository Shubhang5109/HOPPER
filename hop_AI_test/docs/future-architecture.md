# Future architecture

HOPPER v1 is deliberately a static site over a curated JSON dataset. It was
built this way so it could be understood, run, and deployed by someone who
is not a professional software engineer — see the README. Nothing about
that choice should be read as a ceiling; below is where later versions
could plausibly grow, without any of it being implemented yet.

## Where the seams already are

- **`scripts/build_data.py`** separates *what the dataset contains* from
  *how it's structured*. A later version could replace the hand-written
  Python lists with a real ingestion step (see below) while keeping the
  same output schema, so the frontend would not need to change.
- **`js/data.js`** is the only module that knows about the on-disk JSON
  shape. Everything else (search, filters, record pages, the graph) is
  written against the in-memory indices it returns. Swapping static JSON
  for a real API would mean changing this one file.
- **The common schema itself** (`data-model.md`) is already the shape a
  real integration pipeline would target — v1 just populates it by hand
  for ~90 representative records instead of programmatically for
  thousands.

## Plausible next steps, roughly in order of effort

1. **Scheduled data refresh.** A GitHub Action that periodically re-fetches
   source metadata (not full records) for the resources in `sources.json`
   and flags ones whose `Last_Checked` status has changed — an automated
   version of what building this prototype did by hand for PVsiRNAdb and
   Rice SNP-Seek.
2. **A real ingestion/mapping pipeline.** Turn `schema_mapping.json` from
   documentation into code: small per-source adapters that pull public
   records (where an API exists) and normalize them into the HOPPER schema
   automatically, with the human-reviewed mapping table as configuration.
3. **A queryable API.** Expose the same JSON as a small read-only API
   (even a serverless function) so other tools could query HOPPER
   programmatically instead of only through this site.
4. **Deeper ontology alignment.** Move `Ontology_Term` from "populated
   where safe" to systematic alignment against Plant Ontology, NCBI
   Taxonomy, and Environment Ontology (ENVO), with real term IDs rather
   than descriptive text.
5. **A real knowledge graph / SPARQL endpoint.** Once the relationship
   count grows well beyond what a hand-rolled SVG diagram can show
   legibly, migrate `relationships.json` into an actual graph store and
   offer a query endpoint alongside the visual explorer.
6. **Semantic / vector search.** Replace or augment "Ask HOPPER"'s
   rule-based keyword parser with embedding-based retrieval, still
   constrained to answer only from indexed records.
7. **Optional LLM reasoning layer — already available.** `js/ask.js` can
   call a small serverless proxy (`cloudflare-worker/ask-hopper-proxy.js`)
   that asks Claude to synthesize an answer from the records HOPPER already
   retrieved locally, with automatic fallback to the rule-based mode if the
   proxy is unreachable. It's opt-in (`js/config.js`) precisely because the
   public GitHub Pages deployment can't hold a secret key itself — see
   `docs/ai-proxy-setup.md`. Natural next steps here: streaming responses,
   conversation memory across follow-up questions, and letting the model
   suggest which filters to apply rather than only summarizing results the
   rule-based parser already found.
8. **Longitudinal and environmental integration.** The review this
   prototype is based on specifically flags the near-total absence of
   over-time disease data and of infrastructure that represents host,
   pathogen, and environment together. A v2 schema addition for
   time-stamped observations (not just static reference records) would be
   the most scientifically meaningful next step.
9. **Federated queries / federated learning.** Longer-horizon ideas from
   the same review — federating queries across institutions without
   centralizing raw data — are plausible v3+ directions, not v1.5 ones.

None of the above changes what HOPPER v1 already demonstrates: that a
common schema, a normalization layer, identifier cross-referencing, and a
lightweight ontology can connect fragmented plant-disease data without
requiring a large engineering investment up front.
