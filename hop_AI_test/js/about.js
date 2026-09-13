// about.js — About page (single scrollable page, several sections)

export function renderAbout(container) {
  container.innerHTML = `
    <h1>About HOPPER</h1>

    <section class="about-section">
      <h2>Why HOPPER?</h2>
      <p>Plant disease research now depends on a wide range of genomic, phenotypic, imaging and metagenomic databases. Individually, resources like PlantVillage, FungiDB, PHI-base, PRGdb, MaizeGDB, DroughtDB and MGnify are valuable, actively maintained, and well cited. Collectively, though, they were built independently, for different research communities, at different times, with different identifiers, metadata conventions and terminology.</p>
      <p>That fragmentation shows up as a recurring set of problems: data siloed in incompatible formats; inconsistent or missing metadata; very little longitudinal (over-time) disease data; underused or hard-to-find "dark data"; uneven readiness for AI/ML pipelines across crops and regions; inconsistent adoption of shared ontologies; curation effort concentrated on a small number of model species and staple crops; a geographic skew toward well-resourced regions rather than the regions carrying the heaviest disease burden; and — perhaps most fundamentally — very little infrastructure that represents host, pathogen and environment together in one queryable place, even though disease outcomes depend on all three at once.</p>
      <p>HOPPER is a small proof-of-concept for what a common interoperability layer over this landscape could look like.</p>
    </section>

    <section class="about-section">
      <h2>What makes HOPPER different?</h2>
      <p>HOPPER is <em>not</em> a database containing information copied from many other databases side by side. It is a lightweight interoperability and knowledge layer that:</p>
      <ul>
        <li>normalizes heterogeneous field names and metadata into one common schema,</li>
        <li>connects identifiers across databases where a real mapping exists,</li>
        <li>preserves the provenance of every record back to its original source, and</li>
        <li>exposes relationships — host ↔ disease ↔ pathogen ↔ gene ↔ dataset ↔ database — that are usually left implicit and scattered across separate platforms.</li>
      </ul>
      <p>The <a href="#/search">Search</a> and <a href="#/explore">Explore</a> pages, and the small <a href="#/ask">Ask HOPPER</a> query interface, all run against the same normalized local dataset described below.</p>
    </section>

    <section class="about-section">
      <h2>Data &amp; provenance</h2>
      <p>HOPPER is an integration <strong>prototype</strong>. External databases remain the authoritative sources for their own data. HOPPER stores normalized reference metadata and cross-database relationships — it does not claim to replace, mirror, or comprehensively reproduce the source resources.</p>
      <p>Every HOPPER record carries, where available: a source database name, an original identifier, an original URL, and a provenance note. Where an exact source record could not be safely represented in a small demonstration dataset, HOPPER uses resource-level metadata and an external link instead of inventing a specific record — these are labelled as <strong>external resource / integrated reference records</strong> throughout the site. Nothing in the dataset is a fabricated biological observation.</p>
      <p>Each record also carries a <span class="mono">Last_Checked</span> date. This matters in practice, not just in principle — while building this prototype, one linked resource (PVsiRNAdb) was reported unreachable in the registry consulted, and another (the IRRI-hosted Rice SNP-Seek database) reported a temporary service interruption with mirror sites listed. Both are recorded as-is rather than smoothed over, because surfacing exactly this kind of change is what a provenance layer is for.</p>
    </section>

    <section class="about-section">
      <h2>FAIR &amp; interoperability</h2>
      <p>HOPPER is a small demonstration of FAIR-by-design principles applied to a fragmented data landscape:</p>
      <div class="fair-grid">
        <div class="fair-card">
          <h4>Findable</h4>
          <p>Every entity has a stable, structured <span class="mono">HOPPER_ID</span> (for example <span class="mono">HOPPER:DIS:0001</span>) that can be linked to directly.</p>
        </div>
        <div class="fair-card">
          <h4>Accessible</h4>
          <p>The dataset, code and this site are published in a public repository and deployed as a public website with no login or paid access.</p>
        </div>
        <div class="fair-card">
          <h4>Interoperable</h4>
          <p>A common schema, a normalization/mapping layer, and identifier cross-references connect records that originated in different source systems.</p>
        </div>
        <div class="fair-card">
          <h4>Reusable</h4>
          <p>Records are machine-readable JSON/CSV with explicit provenance, and any filtered result set can be exported directly from the Search page.</p>
        </div>
      </div>
    </section>

    <section class="about-section">
      <h2>Limitations</h2>
      <p>This is a first, deliberately small version. It:</p>
      <ul class="limits-list">
        <li>is a demonstration prototype, not production-scale infrastructure;</li>
        <li>contains a small curated subset (on the order of 100 records), not a comprehensive index;</li>
        <li>does not mirror external databases — most dataset-type records are resource-level references with real links, not deep per-record imports;</li>
        <li>may contain incomplete cross-database identifier mappings — only mappings that could be verified are shown;</li>
        <li>does not synchronize with source databases in real time;</li>
        <li>does not guarantee complete ontology alignment — the controlled vocabulary here is intentionally lightweight;</li>
        <li>does not replace any of the authoritative source databases it references; and</li>
        <li>does not (yet) provide large-scale AI infrastructure by default — out of the box, "Ask HOPPER" is a local, rule-based keyword interpreter, not a general-purpose model. Anyone viewing the site can optionally paste their own Anthropic API key on the Ask HOPPER page to get real Claude-generated answers directly in their browser (see the repository README), still constrained to only the records retrieved locally.</li>
      </ul>
    </section>

    <section class="about-section">
      <h2>Scientific foundation</h2>
      <p>HOPPER's structure follows the review <em>"From Fragmented Databases to AI-Ready Data Infrastructure: A Critical Review of Plant Disease Databases"</em> (Yashika, Jhankal, Jha, Aggarwal &amp; Pant), which audits the plant-disease database landscape across seven functional domains — AI-ready image datasets, pathogen genome resources, host-pathogen interaction databases, resistance repositories, crop-specific genomic platforms, stress and phenomics databases, and soil microbiome archives — and identifies ten recurring interoperability bottlenecks across them. HOPPER's schema, source directory and cross-database views are organized around that same set of domains and problems as a way of demonstrating one possible response to them, not as a substitute for reading the review itself.</p>
    </section>

    <section class="about-section">
      <h2>Citation</h2>
      <p>If you reference this prototype, please cite it as: <em>HOPPER — Harmonized Ontology &amp; Plant Pathology Exploration Repository (prototype), ${new Date().getFullYear()}.</em> Please also cite the individual source databases directly when using data derived from them — see the <a href="#/databases">Databases</a> page for links.</p>
    </section>
  `;
}
