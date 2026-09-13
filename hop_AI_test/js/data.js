// data.js
// Loads the local normalized HOPPER dataset (data/*.json) once and builds
// simple in-memory indices. Nothing here ever calls out to a remote API —
// the whole site runs against these static files.

let cache = null;

async function fetchJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Coarse, filter-friendly categorizations.
// The canonical schema (Data_Type, Evidence_Type, Geographic_Region) is kept
// free-text and descriptive on purpose — it reads naturally on a record page.
// For the *filter panel* that free text is far too granular (close to one
// distinct value per record), so these small lookup tables bucket records
// into a handful of controlled categories, computed once at load time and
// kept in side-indices rather than mutating the records themselves.
// ---------------------------------------------------------------------------

const DOMAIN_BUCKETS = {
  "Disease image / AI dataset": "Disease image / AI dataset",
  "Pathogen genomics": "Pathogen genomics",
  "Pathogen genomics (viral)": "Pathogen genomics",
  "Host-pathogen interaction": "Host-pathogen interaction",
  "Host-pathogen interaction (transcriptomic)": "Host-pathogen interaction",
  "Plant resistance genes": "Plant resistance genes",
  "Multi-omics (transcriptomic)": "Multi-omics",
  "Multi-omics (proteomic)": "Multi-omics",
  "Crop-specific genomics": "Crop-specific genomics",
  "Stress / phenomics": "Stress / phenomics",
  "Stress / phenomics infrastructure": "Stress / phenomics",
  "Soil microbiome / metagenomics": "Soil microbiome / metagenomics",
  "Ontology / controlled vocabulary": "Ontology / controlled vocabulary",
};

function domainForRecord(record, nameToSourceDomain) {
  if (record.Entity_Type !== "Dataset") return "Core biological entity";
  const raw = nameToSourceDomain.get(record.Source_Database);
  return (raw && DOMAIN_BUCKETS[raw]) || "Other";
}

const EVIDENCE_RULES = [
  [/predict/i, "Computational prediction"],
  [/image dataset|annotat/i, "Image dataset / annotation"],
  [/assembly|sequenc|genotyp/i, "Genomic / metagenomic assembly"],
  [/infrastructure|tooling/i, "Infrastructure / tooling"],
  [/experimental|curat/i, "Experimental / literature-curated"],
];

function evidenceBucketForRecord(record) {
  const text = record.Evidence_Type || "";
  for (const [re, bucket] of EVIDENCE_RULES) {
    if (re.test(text)) return bucket;
  }
  return "Literature-established";
}

const REGION_KEYWORDS = [
  ["Global", /global/i],
  ["Africa", /africa/i],
  ["Asia", /asia/i],
  ["Americas", /america/i],
  ["Europe", /europe/i],
];

function regionBucketsForRecord(record) {
  const text = record.Geographic_Region || "";
  const hits = REGION_KEYWORDS.filter(([, re]) => re.test(text)).map(([name]) => name);
  return hits.length ? hits : ["Other / unspecified"];
}

export async function loadData() {
  if (cache) return cache;

  const base = "data/";
  const [records, relationships, sources, mappings, schema] = await Promise.all([
    fetchJson(base + "hopper_records.json"),
    fetchJson(base + "relationships.json"),
    fetchJson(base + "sources.json"),
    fetchJson(base + "identifier_mappings.json"),
    fetchJson(base + "schema_mapping.json"),
  ]);

  const byId = new Map(records.map((r) => [r.HOPPER_ID, r]));
  const sourceById = new Map(sources.map((s) => [s.Source_ID, s]));
  const nameToSourceDomain = new Map(sources.map((s) => [s.Name, s.Domain]));

  const domainById = new Map();
  const evidenceBucketById = new Map();
  const regionBucketsById = new Map();
  records.forEach((r) => {
    domainById.set(r.HOPPER_ID, domainForRecord(r, nameToSourceDomain));
    evidenceBucketById.set(r.HOPPER_ID, evidenceBucketForRecord(r));
    regionBucketsById.set(r.HOPPER_ID, regionBucketsForRecord(r));
  });

  // relationships involving a given HOPPER_ID, in either direction
  const relByEntity = new Map();
  function pushRel(id, rel) {
    if (!id) return;
    if (!relByEntity.has(id)) relByEntity.set(id, []);
    relByEntity.get(id).push(rel);
  }
  relationships.forEach((rel) => {
    pushRel(rel.source, rel);
    if (rel.target) pushRel(rel.target, rel);
  });

  // distinct filter facet values, computed from the actual dataset only
  const facets = {
    hostCrop: new Set(),
    pathogenType: new Set(),
    domain: new Set(),
    sourceDatabase: new Set(),
    region: new Set(),
    evidenceType: new Set(),
    entityType: new Set(),
    year: new Set(),
  };
  records.forEach((r) => {
    // Skip aggregate / multi-crop descriptions (e.g. "Multiple (14 crops)") from
    // the Host/crop facet — they aren't a single comparable host concept, just
    // noise in the checkbox list. The full text still shows on the record page.
    const isCleanCropLabel = (v) => v && !/^multiple\b/i.test(v) && !/\d/.test(v);
    if (isCleanCropLabel(r.Crop)) facets.hostCrop.add(r.Crop);
    if (r.Host) r.Host.split(";").map((s) => s.trim()).forEach((h) => h && facets.hostCrop.add(h));
    if (r.Pathogen_Type) facets.pathogenType.add(r.Pathogen_Type);
    facets.domain.add(domainById.get(r.HOPPER_ID));
    if (r.Source_Database && r.Source_Database !== "Not available") facets.sourceDatabase.add(r.Source_Database);
    regionBucketsById.get(r.HOPPER_ID).forEach((b) => facets.region.add(b));
    facets.evidenceType.add(evidenceBucketById.get(r.HOPPER_ID));
    if (r.Entity_Type) facets.entityType.add(r.Entity_Type);
    if (r.Year) facets.year.add(String(r.Year));
  });

  const toSortedArray = (s) => Array.from(s).sort((a, b) => a.localeCompare(b));

  cache = {
    records,
    relationships,
    sources,
    mappings,
    schema,
    byId,
    sourceById,
    relByEntity,
    domainById,
    evidenceBucketById,
    regionBucketsById,
    facets: {
      hostCrop: toSortedArray(facets.hostCrop),
      pathogenType: toSortedArray(facets.pathogenType),
      domain: toSortedArray(facets.domain),
      sourceDatabase: toSortedArray(facets.sourceDatabase),
      region: toSortedArray(facets.region),
      evidenceType: toSortedArray(facets.evidenceType),
      entityType: toSortedArray(facets.entityType),
      year: toSortedArray(facets.year),
    },
  };
  return cache;
}

// ---------------------------------------------------------------------------
// Search + filter engine, shared by the Search page and Ask HOPPER.
// ---------------------------------------------------------------------------

function recordSearchText(r) {
  return [
    r.Name, r.Normalized_Name, r.Host, r.Pathogen, r.Disease, r.Gene_or_Protein,
    r.Resistance_Factor, r.Strain_or_Isolate, r.Phenotype, r.Crop, r.Data_Type,
    r.Source_Database, r.Source_ID, r.Geographic_Region, r.Pathogen_Type,
    (r.Synonyms || []).join(" "),
  ].filter(Boolean).join(" ").toLowerCase();
}

/**
 * @param {Object} data  the object returned by loadData()
 * @param {Object} opts { query: string, filters: { hostCrop:[], pathogenType:[], domain:[], sourceDatabase:[], region:[], evidenceType:[], entityType:[], year:[] } }
 */
export function searchRecords(data, opts = {}) {
  const query = (opts.query || "").trim().toLowerCase();
  const filters = opts.filters || {};

  return data.records.filter((r) => {
    if (query) {
      if (!recordSearchText(r).includes(query)) return false;
    }
    for (const key of Object.keys(filters)) {
      const selected = filters[key];
      if (!selected || selected.length === 0) continue;
      if (key === "hostCrop") {
        const fieldVal = [r.Crop, r.Host].filter(Boolean).join(" | ");
        if (!selected.some((v) => fieldVal.includes(v))) return false;
      } else if (key === "pathogenType") {
        if (!selected.includes(r.Pathogen_Type)) return false;
      } else if (key === "domain") {
        if (!selected.includes(data.domainById.get(r.HOPPER_ID))) return false;
      } else if (key === "sourceDatabase") {
        if (!selected.includes(r.Source_Database)) return false;
      } else if (key === "region") {
        const buckets = data.regionBucketsById.get(r.HOPPER_ID) || [];
        if (!selected.some((v) => buckets.includes(v))) return false;
      } else if (key === "evidenceType") {
        if (!selected.includes(data.evidenceBucketById.get(r.HOPPER_ID))) return false;
      } else if (key === "entityType") {
        if (!selected.includes(r.Entity_Type)) return false;
      } else if (key === "year") {
        if (!selected.includes(String(r.Year))) return false;
      }
    }
    return true;
  });
}
