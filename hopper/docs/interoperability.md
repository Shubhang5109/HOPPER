# Interoperability approach

HOPPER's job is narrow: demonstrate one way to connect plant-disease data
that was never designed to be connected, without pretending to replace any
of it. This document walks through the four layers that make that
demonstration work, and is meant to be read alongside `docs/data-model.md`.

## 1. Common schema

Every entity HOPPER indexes — a host, a pathogen, a disease, a gene, a
strain, a phenotype, or a reference to an external dataset — is expressed
in the same set of fields (see `data-model.md`). A record from a curated
interaction database (PHI-base) and a record from a large image dataset
(PlantPAD) look structurally identical in HOPPER, even though their source
systems have almost nothing in common.

## 2. Normalization / mapping layer

`data/schema_mapping.json` documents, for each canonical field, the
different source-side field names it's meant to absorb — for example
`host_species`, `plant`, `crop_species`, and `host organism` all normalize
to `HOST`. In a production system this mapping would drive an ETL pipeline
against live external schemas; here it is data that documents the concept
and is reflected in how the demonstration records were normalized by hand.

## 3. Identifier cross-referencing

Where a real mapping could be verified, `data/identifier_mappings.json`
records the chain of external identifiers/records that represent one
underlying concept (e.g. rice blast is represented, in different ways, in
PHI-base, FungiDB, PlantVillage, PlantPAD, Rice SNP-Seek, and Expression
Atlas). Every HOPPER record also carries its own `Source_Database` /
`Source_ID` / `Source_URL` triple directly, so cross-referencing does not
depend only on the curated chains — the Explore page's cross-database
matrix is computed live from each entity's own relationships, and falls
back gracefully (showing `—`) wherever no mapping exists in this prototype.

## 4. Lightweight ontology / controlled vocabulary

HOPPER does not implement a full ontology service. Instead it uses a small
set of controlled categories — `Entity_Type`, `Pathogen_Type`, a coarse
`Data_Type` domain bucketing (Disease image / AI dataset, Pathogen
genomics, Host-pathogen interaction, Plant resistance genes, Multi-omics,
Crop-specific genomics, Stress / phenomics, Soil microbiome /
metagenomics) — and, where available, an `Ontology_Term` field that anchors
a record to an external vocabulary such as Plant Ontology or NCBI Taxonomy
rather than reinventing one.

## What this deliberately does not do

- It does not parse or ingest live external schemas — the normalization is
  demonstrated on a static, curated dataset.
- It does not attempt full ontology alignment — `Ontology_Term` is populated
  only where a clear, safe mapping exists.
- It does not resolve every possible identifier — `data/identifier_mappings.json`
  covers a representative set of "hub" concepts, not an exhaustive graph.

See [Future architecture](future-architecture.md) for how these limits map
onto a realistic next-version roadmap, and the **About → Limitations**
section on the live site for the same list in plainer language.
