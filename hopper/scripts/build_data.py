#!/usr/bin/env python3
"""
build_data.py
--------------
Generates the HOPPER prototype dataset (data/*.json) from structured
Python definitions below.

This script exists so the dataset can be regenerated/extended without
hand-editing JSON and without hand-computing relationships. It is a
development utility, not part of the deployed site (the deployed site
only reads the generated JSON files under data/).

Usage:
    python3 scripts/build_data.py

Regenerates:
    data/hopper_records.json
    data/relationships.json
    data/sources.json
    data/identifier_mappings.json
    data/schema_mapping.json
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")

NA = "Not available"
UNK = "Unknown"

# ---------------------------------------------------------------------------
# 1. SOURCE DATABASE DIRECTORY
# ---------------------------------------------------------------------------
# Each external resource HOPPER references. URLs were checked against the
# resource's own publication/registry record; a handful of resources are
# noted as currently reporting reduced or intermittent availability, which
# is itself part of the interoperability story this prototype demonstrates.

SOURCES = [
    dict(id="SRC:PLANTVILLAGE", name="PlantVillage", domain="Disease image / AI dataset",
         data_type="Image classification (lab-controlled)",
         organisms="14 crop species, 38 disease classes",
         role="Reference lab-controlled image dataset used across the plant disease computer-vision literature.",
         url="https://plantvillage.psu.edu", access="Open access", geography="Global",
         notes="Widely used benchmark; images are uniform-background and lab-controlled, which limits field generalizability."),
    dict(id="SRC:PLANTDOC", name="PlantDoc", domain="Disease image / AI dataset",
         data_type="Image classification & object detection (field-based)",
         organisms="13 plant species, 17 disease classes",
         role="Field-condition image dataset built to address PlantVillage's lab-only bias.",
         url="https://github.com/pratikkayal/PlantDoc-Dataset", access="Open access (CC BY 4.0)", geography="Multi-regional",
         notes="Internet-sourced and cropped images; comparatively small scale."),
    dict(id="SRC:CCMT", name="CCMT Dataset", domain="Disease image / AI dataset",
         data_type="Image classification (field-based, augmented)",
         organisms="Cashew, cassava, maize, tomato (4 crops)",
         role="Field-condition West African image dataset spanning four crops.",
         url=None, access="Regional access", geography="West Africa (Ghana)",
         notes="Canonical stable dataset URL not independently verified for this prototype; represented via literature reference only."),
    dict(id="SRC:FIELDPLANT", name="FieldPlant", domain="Disease image / AI dataset",
         data_type="Image classification & object detection (field-based)",
         organisms="Cassava, corn, tomato",
         role="Plantation-collected image dataset annotated under plant-pathologist supervision.",
         url="https://doi.org/10.1109/ACCESS.2023.3263042", access="Open access", geography="Central Africa (Cameroon)",
         notes="Linked via its IEEE Access publication DOI rather than a dataset-hosting URL."),
    dict(id="SRC:CASSAVA_LEAF", name="Cassava Leaf Disease Dataset", domain="Disease image / AI dataset",
         data_type="Image classification (regional, ML-pipeline ready)",
         organisms="Cassava (5 disease/health classes)",
         role="Crowdsourced regional dataset structured for direct ML pipeline integration.",
         url="https://www.kaggle.com/c/cassava-leaf-disease-classification", access="Open access", geography="Africa, Asia, Americas",
         notes="Distributed as a Kaggle competition dataset; narrow single-crop focus."),
    dict(id="SRC:PLANTPAD", name="PlantPAD", domain="Disease image / AI dataset",
         data_type="Image classification (large-scale, pre-trained models)",
         organisms="63 crops, 310 disease phenotypes",
         role="Large-scale, literature-aggregated image phenomics platform with pre-trained diagnostic models.",
         url="http://plantpad.samlab.cn", access="Open access", geography="Global",
         notes="Breadth introduces annotation inconsistency inherited from heterogeneous source literature."),
    dict(id="SRC:IP102", name="IP102", domain="Disease image / AI dataset",
         data_type="Image classification & detection (pest recognition)",
         organisms="102 insect pest categories, 8 crops",
         role="Large-scale insect pest recognition benchmark with hierarchical taxonomy.",
         url="https://github.com/xpwu95/IP102", access="Open access (academic use)", geography="Global",
         notes="Natural long-tailed class distribution; common-name labelling introduces taxonomic imprecision."),
    dict(id="SRC:FUNGIDB", name="FungiDB", domain="Pathogen genomics", data_type="Genome sequence & functional annotation",
         organisms="Fungal & oomycete phytopathogens", role="Principal aggregator for fungal/oomycete pathogen genomics; part of the VEuPathDB federation.",
         url="https://fungidb.org", access="Open access", geography="Global",
         notes="Consolidates previously fragmented single-species genome browsers into one comparative platform."),
    dict(id="SRC:DPVWEB", name="DPVweb", domain="Pathogen genomics (viral)", data_type="Viral taxonomy & genome sequence",
         organisms="Plant, fungal and protozoal viruses, viroids, satellites", role="Long-standing reference for plant virus taxonomy and genome organization.",
         url="http://www.dpvweb.net", access="Open access", geography="Global",
         notes="Genome/taxonomy layer only; does not cover host-response or silencing data."),
    dict(id="SRC:PVSIRNADB", name="PVsiRNAdb", domain="Pathogen genomics (viral)", data_type="Virus-derived small interfering RNA catalogue",
         organisms="Plant-infecting viruses", role="Catalogues plant virus-derived siRNAs involved in RNA-silencing defense suppression.",
         url="http://www.nipgr.res.in/PVsiRNAdb", access="Access intermittent (reported unreachable at last check)", geography="Global",
         notes="Database Commons reported this resource as unaccessible at time of last check; retained here as a resource-level reference only."),
    dict(id="SRC:PHIBASE", name="PHI-base", domain="Host-pathogen interaction", data_type="Curated interaction phenotype records",
         organisms="Fungal, oomycete, bacterial and viral pathogens across plant, animal and fungal hosts",
         role="Central, actively maintained host-pathogen interaction aggregator; part of the ELIXIR UK node.",
         url="https://www.phi-base.org", access="Open access", geography="Global",
         notes="Manual literature curation means a lag between new findings and structured records."),
    dict(id="SRC:PLAD", name="PlaD", domain="Host-pathogen interaction (transcriptomic)", data_type="Plant defense-response transcriptomic compilation",
         organisms="Plant hosts under documented pathogen challenge", role="Extends interaction curation into the host expression domain.",
         url=None, access="Open access", geography="Global",
         notes="Cross-referencing to PHI-base interaction records still requires manual reconciliation."),
    dict(id="SRC:PRGDB", name="PRGdb", domain="Plant resistance genes", data_type="Known & predicted resistance genes (NBS-LRR emphasis)",
         organisms="Plant hosts, pathogenic microorganisms", role="Catalogues resistance gene analogs and predicted NBS-LRR immune receptor families.",
         url="https://prgdb.org", access="Open access", geography="Global",
         notes="Domain/model-based prediction over-predicts functional resistance genes relative to experimentally confirmed sets."),
    dict(id="SRC:RGENE_DB", name="R-gene Database", domain="Plant resistance genes", data_type="R-gene sequences, allelic variants, resistance QTLs",
         organisms="Plant hosts across crops", role="Web-queryable catalogue of characterized plant resistance-gene sequences.",
         url=None, access="Web-based query", geography="Global",
         notes="Coverage of wild relatives and functional characterization remains incomplete."),
    dict(id="SRC:EXPR_ATLAS", name="Expression Atlas", domain="Multi-omics (transcriptomic)", data_type="Gene & protein expression data",
         organisms="Multi-species, multiple experimental conditions", role="Aggregates differential expression data across independently deposited studies.",
         url="https://www.ebi.ac.uk/gxa", access="Open access", geography="Global",
         notes="Stress-condition metadata is only as consistent as submitting-lab annotation practice."),
    dict(id="SRC:PROTEOMEXCHANGE", name="ProteomeXchange", domain="Multi-omics (proteomic)", data_type="Mass-spectrometry proteomics submission/retrieval",
         organisms="Multi-organism", role="Consortium standardizing proteomics data submission and retrieval.",
         url="http://www.proteomexchange.org", access="Open access", geography="Global",
         notes="Primary repository partner is PRIDE."),
    dict(id="SRC:PRIDE", name="PRIDE", domain="Multi-omics (proteomic)", data_type="Mass-spectrometry proteomics archive",
         organisms="Multi-organism", role="Main ProteomeXchange repository for effector and host immune proteome data.",
         url="https://www.ebi.ac.uk/pride/archive", access="Open access", geography="Global",
         notes="Metabolomic evidence remains comparatively underrepresented across this layer."),
    dict(id="SRC:MAIZEGDB", name="MaizeGDB", domain="Crop-specific genomics", data_type="Genetic maps, genomic sequence, gene function",
         organisms="Maize (Zea mays)", role="Community-oriented informatics service for maize genetics and genomics.",
         url="https://www.maizegdb.org", access="Open access", geography="Global",
         notes="Uses Plant Ontology and Gene Ontology for functional annotation; single-species scope."),
    dict(id="SRC:SNPSEEK", name="Rice SNP-Seek", domain="Crop-specific genomics", data_type="SNP genotype data",
         organisms="Rice (Oryza sativa) germplasm", role="Large-scale rice SNP repository built on the 3000 Rice Genomes Project.",
         url="http://snp-seek.irri.org", access="Open access (intermittent availability reported)", geography="Global",
         notes="At last check the IRRI-hosted service reported a temporary interruption; mirror sites were listed on its homepage. This is exactly the kind of availability change the Last_Checked field is meant to surface."),
    dict(id="SRC:SOYBASE", name="SoyBase", domain="Crop-specific genomics", data_type="Genetic/genomic data, QTL & GWAS loci",
         organisms="Soybean (Glycine max, G. soja)", role="USDA-ARS repository for soybean genetics and genomics.",
         url="https://soybase.org", access="Open access", geography="Global",
         notes="Links QTL and GWAS loci with standardized trait ontologies (SoyTO)."),
    dict(id="SRC:WHEATIS", name="WheatIS", domain="Crop-specific genomics", data_type="Federated genomic/genetic data access",
         organisms="Wheat (Triticum spp.)", role="Decentralized, internationally federated single-access point for wheat research data.",
         url="http://wheatis.org", access="Open access", geography="Global (federated, 3 continents)",
         notes="Deliberately federated design was intended to reduce single-region dependency."),
    dict(id="SRC:DROUGHTDB", name="DroughtDB", domain="Stress / phenomics", data_type="Curated drought-stress gene compilation",
         organisms="9 plant species", role="Expert-curated drought-responsive gene compilation with cross-species orthologs.",
         url="http://pgsb.helmholtz-muenchen.de/droughtdb/", access="Open access", geography="Global",
         notes="Curation concentrated in a small set of model/crop species."),
    dict(id="SRC:STIFDB2", name="STIFDB2", domain="Stress / phenomics", data_type="Stress-responsive transcription factors & binding sites",
         organisms="Arabidopsis thaliana, Oryza sativa", role="Catalogues stress-responsive transcription factors and predicted binding sites.",
         url="http://caps.ncbs.res.in/stifdb2", access="Open access", geography="Global",
         notes="Taxonomic coverage confined almost entirely to two model/staple species."),
    dict(id="SRC:CYVERSE", name="CyVerse", domain="Stress / phenomics infrastructure", data_type="Cloud compute, storage & workflow orchestration",
         organisms="Domain-general", role="Computational backbone for large-scale, high-throughput phenotyping projects.",
         url="https://cyverse.org", access="Open access", geography="Global",
         notes="Domain-general infrastructure; does not itself enforce stress-phenotype ontologies."),
    dict(id="SRC:MGNIFY", name="MGnify", domain="Soil microbiome / metagenomics", data_type="Metagenome-assembled genomes & protein catalogues",
         organisms="Uncultured soil & other-biome microbes", role="Secondary repository reconstructing metagenome-assembled genomes from public reads.",
         url="https://www.ebi.ac.uk/metagenomics", access="Open access", geography="Global",
         notes="Soil assembly is more computationally intensive and slower to represent than host-associated microbiomes."),
    dict(id="SRC:TMDB", name="TerrestrialMetagenomeDB", domain="Soil microbiome / metagenomics", data_type="Curated terrestrial metagenome metadata",
         organisms="Terrestrial (soil & plant-associated) metagenomes", role="Standardizes and centralizes metadata scattered across SRA and MG-RAST.",
         url="https://webapp.ufz.de/tmdb", access="Open access", geography="Global",
         notes="Uses Environment Ontology (ENVO) text-mining for biome categorization; lacks physicochemical metadata."),
    dict(id="SRC:PLANT_ONTOLOGY", name="Plant Ontology", domain="Ontology / controlled vocabulary", data_type="Standardized anatomy, growth-stage & trait terms",
         organisms="Plants (cross-species)", role="Reference vocabulary HOPPER's ontology layer draws on for host anatomy/stage terms.",
         url="https://planteome.org", access="Open access", geography="Global",
         notes="Adoption across pathogen, interaction, resistance and stress databases remains inconsistent."),
    dict(id="SRC:PLANTEOME", name="Planteome", domain="Ontology / controlled vocabulary", data_type="Federated plant ontology knowledgebase",
         organisms="Plants (cross-species)", role="Broader knowledgebase federating Plant Ontology and related vocabularies.",
         url="https://planteome.org", access="Open access", geography="Global",
         notes="Referenced here as the ontology-alignment inspiration for HOPPER's lightweight controlled vocabulary."),
]

# ---------------------------------------------------------------------------
# 2. CORE BIOLOGICAL ENTITIES
# ---------------------------------------------------------------------------

HOSTS = [
    dict(slug="rice", name="Rice", norm="Oryza sativa", region="South & Southeast Asia, Global",
         synonyms=["paddy", "Oryza sativa"]),
    dict(slug="tomato", name="Tomato", norm="Solanum lycopersicum", region="Global",
         synonyms=["Solanum lycopersicum", "Lycopersicon esculentum"]),
    dict(slug="wheat", name="Wheat", norm="Triticum aestivum", region="Global",
         synonyms=["Triticum aestivum", "bread wheat"]),
    dict(slug="maize", name="Maize", norm="Zea mays", region="Global",
         synonyms=["Zea mays", "corn"]),
    dict(slug="soybean", name="Soybean", norm="Glycine max", region="Global",
         synonyms=["Glycine max", "soya bean"]),
    dict(slug="cassava", name="Cassava", norm="Manihot esculenta", region="Sub-Saharan Africa, South America, Southeast Asia",
         synonyms=["Manihot esculenta", "manioc", "yuca"]),
    dict(slug="potato", name="Potato", norm="Solanum tuberosum", region="Global",
         synonyms=["Solanum tuberosum"]),
    dict(slug="banana", name="Banana", norm="Musa spp.", region="East Africa, Sub-Saharan Africa, Global tropics",
         synonyms=["Musa spp.", "plantain (related)"]),
]

# pathogen_type controlled values: Fungus, Oomycete, Bacterium, Virus
PATHOGENS = [
    dict(slug="m_oryzae", name="Magnaporthe oryzae", ptype="Fungus",
         synonyms=["Pyricularia oryzae", "rice blast fungus"]),
    dict(slug="p_infestans", name="Phytophthora infestans", ptype="Oomycete",
         synonyms=["potato late blight pathogen", "tomato late blight pathogen"]),
    dict(slug="p_striiformis", name="Puccinia striiformis f. sp. tritici", ptype="Fungus",
         synonyms=["wheat stripe rust fungus", "yellow rust fungus"]),
    dict(slug="p_graminis", name="Puccinia graminis f. sp. tritici", ptype="Fungus",
         synonyms=["wheat stem rust fungus", "black rust fungus"]),
    dict(slug="e_turcicum", name="Exserohilum turcicum", ptype="Fungus",
         synonyms=["Setosphaeria turcica", "northern corn leaf blight fungus"]),
    dict(slug="p_pachyrhizi", name="Phakopsora pachyrhizi", ptype="Fungus",
         synonyms=["Asian soybean rust fungus"]),
    dict(slug="foc_tr4", name="Fusarium oxysporum f. sp. cubense (TR4)", ptype="Fungus",
         synonyms=["Foc TR4", "Panama disease fungus", "Tropical Race 4"]),
    dict(slug="xoo", name="Xanthomonas oryzae pv. oryzae", ptype="Bacterium",
         synonyms=["Xoo", "rice bacterial blight pathogen"]),
    dict(slug="x_perforans", name="Xanthomonas perforans", ptype="Bacterium",
         synonyms=["tomato bacterial spot pathogen"]),
    dict(slug="xcm", name="Xanthomonas campestris pv. musacearum", ptype="Bacterium",
         synonyms=["Xcm", "banana Xanthomonas wilt pathogen", "BXW pathogen"]),
    dict(slug="r_solanacearum", name="Ralstonia solanacearum", ptype="Bacterium",
         synonyms=["bacterial wilt pathogen"]),
    dict(slug="acmv", name="African cassava mosaic virus", ptype="Virus",
         synonyms=["ACMV"]),
    dict(slug="tylcv", name="Tomato yellow leaf curl virus", ptype="Virus",
         synonyms=["TYLCV"]),
    dict(slug="wsmv", name="Wheat streak mosaic virus", ptype="Virus",
         synonyms=["WSMV"]),
    dict(slug="pvy", name="Potato virus Y", ptype="Virus",
         synonyms=["PVY"]),
    dict(slug="rtd_complex", name="Rice tungro virus complex", ptype="Virus",
         synonyms=["Rice tungro spherical virus", "Rice tungro bacilliform virus", "RTSV/RTBV complex"]),
]

# disease: host slug, pathogen slug, region
DISEASES = [
    dict(slug="rice_blast", name="Rice blast", host="rice", pathogen="m_oryzae",
         region="Global (esp. South & Southeast Asia)"),
    dict(slug="rice_bact_blight", name="Rice bacterial blight", host="rice", pathogen="xoo",
         region="South & Southeast Asia"),
    dict(slug="rice_tungro", name="Rice tungro disease", host="rice", pathogen="rtd_complex",
         region="South & Southeast Asia"),
    dict(slug="tomato_late_blight", name="Tomato late blight", host="tomato", pathogen="p_infestans",
         region="Global"),
    dict(slug="tomato_bact_spot", name="Tomato bacterial spot", host="tomato", pathogen="x_perforans",
         region="Global (warm, humid regions)"),
    dict(slug="tylcd", name="Tomato yellow leaf curl disease", host="tomato", pathogen="tylcv",
         region="Mediterranean, Middle East, expanding globally"),
    dict(slug="wheat_stripe_rust", name="Wheat stripe rust", host="wheat", pathogen="p_striiformis",
         region="Global (temperate & highland regions)"),
    dict(slug="wheat_stem_rust", name="Wheat stem rust", host="wheat", pathogen="p_graminis",
         region="Global (incl. East Africa Ug99 lineage zone)"),
    dict(slug="wheat_streak_mosaic", name="Wheat streak mosaic", host="wheat", pathogen="wsmv",
         region="North America, Central Asia"),
    dict(slug="maize_nlb", name="Maize northern leaf blight", host="maize", pathogen="e_turcicum",
         region="Global"),
    dict(slug="soybean_rust", name="Soybean (Asian) rust", host="soybean", pathogen="p_pachyrhizi",
         region="South America, Sub-Saharan Africa, Asia"),
    dict(slug="cassava_mosaic", name="Cassava mosaic disease", host="cassava", pathogen="acmv",
         region="Sub-Saharan Africa"),
    dict(slug="potato_late_blight", name="Potato late blight", host="potato", pathogen="p_infestans",
         region="Global"),
    dict(slug="banana_xw", name="Banana Xanthomonas wilt (BXW)", host="banana", pathogen="xcm",
         region="East Africa"),
    dict(slug="banana_fusarium_wilt", name="Banana Fusarium wilt (Panama disease, TR4)", host="banana", pathogen="foc_tr4",
         region="Southeast Asia, expanding globally"),
    dict(slug="bacterial_wilt_potato", name="Bacterial wilt", host="potato", pathogen="r_solanacearum",
         region="Tropical & subtropical regions, global"),
    dict(slug="pvy_disease", name="Potato virus Y disease", host="potato", pathogen="pvy",
         region="Global"),
]

# genes / resistance factors: host slug, target pathogen slug(s), function
GENES = [
    dict(slug="xa21", name="Xa21", host="rice", pathogen="xoo",
         note="Cloned receptor-kinase resistance gene conferring broad-spectrum resistance to rice bacterial blight."),
    dict(slug="pi_ta", name="Pi-ta", host="rice", pathogen="m_oryzae",
         note="Cloned NBS-LRR resistance gene recognizing the AVR-Pita effector of the rice blast fungus."),
    dict(slug="pi9", name="Pi9", host="rice", pathogen="m_oryzae",
         note="Broad-spectrum NBS-LRR blast resistance gene introgressed from wild rice relatives."),
    dict(slug="lr34", name="Lr34", host="wheat", pathogen="p_striiformis",
         note="Durable, adult-plant, multi-pathogen resistance locus associated with reduced rust severity."),
    dict(slug="sr35", name="Sr35", host="wheat", pathogen="p_graminis",
         note="NBS-LRR stem rust resistance gene effective against the Ug99 lineage."),
    dict(slug="rb_gene", name="RB (Rpi-blb1)", host="potato", pathogen="p_infestans",
         note="Broad-spectrum late blight resistance gene introgressed from Solanum bulbocastanum."),
    dict(slug="bs2", name="Bs2", host="tomato", pathogen="x_perforans",
         note="NBS-LRR resistance gene (pepper-derived) recognizing AvrBs2 effectors of Xanthomonas bacterial spot pathogens."),
    dict(slug="cmd2", name="CMD2 locus", host="cassava", pathogen="acmv",
         note="Dominant cassava mosaic disease resistance locus widely used in African cassava breeding programs."),
]

STRAINS = [
    dict(slug="mo_70_15", name="Magnaporthe oryzae strain 70-15", pathogen="m_oryzae",
         note="Widely used laboratory reference strain for rice blast genetics and the first blast reference genome."),
    dict(slug="xoo_pxo99a", name="Xanthomonas oryzae pv. oryzae strain PXO99A", pathogen="xoo",
         note="Commonly used Philippine reference strain in rice bacterial blight molecular research."),
    dict(slug="foc_tr4_vcg", name="Foc TR4 VCG 01213/16 lineage", pathogen="foc_tr4",
         note="Vegetative compatibility group lineage driving the current global spread of banana Fusarium wilt."),
    dict(slug="pinf_blue13", name="Phytophthora infestans clonal lineage 13_A2 (Blue_13)", pathogen="p_infestans",
         note="Dominant, fungicide-resistance-associated European potato late blight clonal lineage."),
]

PHENOTYPES = [
    dict(slug="blast_lesion", name="Blast lesion-type phenotype", disease="rice_blast",
         note="Standard 0-9 lesion-severity scoring scale used in rice blast field and greenhouse phenotyping."),
    dict(slug="fusarium_wilt_phenotype", name="Vascular wilt & discoloration phenotype", disease="banana_fusarium_wilt",
         note="Progressive leaf yellowing, wilting and vascular discoloration characteristic of Fusarium wilt."),
    dict(slug="viral_leaf_curl_phenotype", name="Leaf curling & stunting phenotype", disease="tylcd",
         note="Upward leaf curling, chlorosis and stunting typical of whitefly-transmitted geminivirus infection."),
]

# ---------------------------------------------------------------------------
# 3. DATASET / DATABASE-LINKED RECORDS
# ---------------------------------------------------------------------------
# entity records representing an integrated reference to an external
# resource, tied to one or more biological entities above via "links"
# (list of (kind, slug) tuples referencing HOSTS/PATHOGENS/DISEASES).

DATASETS = [
    dict(slug="ds_plantvillage", name="PlantVillage image collection", source="SRC:PLANTVILLAGE",
         data_type="Disease image dataset (lab-controlled)", evidence="Image dataset / expert-labelled",
         year=2016, crop="Multiple (14 crops)", region="Global",
         links=[("disease", "rice_blast"), ("disease", "tomato_late_blight"), ("disease", "maize_nlb")],
         note="54,306 images across 14 crops and 38 disease classes; uniform lab backgrounds limit field generalizability."),
    dict(slug="ds_plantdoc", name="PlantDoc image collection", source="SRC:PLANTDOC",
         data_type="Disease image dataset (field-based)", evidence="Image dataset / expert-labelled",
         year=2020, crop="Multiple (13 species)", region="Multi-regional",
         links=[("disease", "tomato_late_blight"), ("disease", "rice_blast")],
         note="2,598 field-condition images across 13 species and 17 disease classes."),
    dict(slug="ds_ccmt", name="CCMT image collection", source="SRC:CCMT",
         data_type="Disease image dataset (field-based, augmented)", evidence="Image dataset / expert-labelled",
         year=2024, crop="Cashew, cassava, maize, tomato", region="West Africa (Ghana)",
         links=[("disease", "cassava_mosaic"), ("disease", "maize_nlb")],
         note="24,881 raw / 102,976 augmented images across 4 crops and 22 disease categories."),
    dict(slug="ds_fieldplant", name="FieldPlant image collection", source="SRC:FIELDPLANT",
         data_type="Disease image dataset (field-based)", evidence="Image dataset / expert-labelled",
         year=2023, crop="Cassava, corn, tomato", region="Central Africa (Cameroon)",
         links=[("disease", "cassava_mosaic"), ("disease", "maize_nlb"), ("disease", "tomato_late_blight")],
         note="5,170 plantation-collected images annotated under plant-pathologist supervision."),
    dict(slug="ds_cassava_leaf", name="Cassava Leaf Disease image collection", source="SRC:CASSAVA_LEAF",
         data_type="Disease image dataset (regional)", evidence="Image dataset / crowdsourced + expert-labelled",
         year=2026, crop="Cassava", region="Africa, Asia, Americas",
         links=[("disease", "cassava_mosaic")],
         note="~36,000 images across 5 disease/health classes, structured for direct ML pipeline integration."),
    dict(slug="ds_plantpad", name="PlantPAD image phenomics platform", source="SRC:PLANTPAD",
         data_type="Disease image dataset (large-scale)", evidence="Image dataset / literature-aggregated",
         year=2023, crop="Multiple (63 crops)", region="Global",
         links=[("disease", "rice_blast"), ("disease", "wheat_stripe_rust"), ("disease", "soybean_rust")],
         note="421,314 images across 63 crops and 310 disease phenotypes, with pre-trained diagnostic models."),
    dict(slug="ds_ip102", name="IP102 pest recognition benchmark", source="SRC:IP102",
         data_type="Pest image dataset (large-scale)", evidence="Image dataset / expert-labelled",
         year=2019, crop="Multiple (8 crops)", region="Global",
         links=[("host", "rice"), ("host", "maize")],
         note="75,222 images across 102 insect pest categories with hierarchical taxonomy."),
    dict(slug="ds_fungidb_moryzae", name="FungiDB genome record: Magnaporthe oryzae", source="SRC:FUNGIDB",
         data_type="Pathogen genome & functional annotation", evidence="Genome assembly / sequence data",
         year=2024, crop=None, region="Global",
         links=[("pathogen", "m_oryzae"), ("strain", "mo_70_15")],
         note="Whole-genome sequence, structural annotation and comparative genomics tools for the rice blast fungus."),
    dict(slug="ds_fungidb_foc", name="FungiDB genome record: Fusarium oxysporum f. sp. cubense", source="SRC:FUNGIDB",
         data_type="Pathogen genome & functional annotation", evidence="Genome assembly / sequence data",
         year=2024, crop=None, region="Global",
         links=[("pathogen", "foc_tr4"), ("strain", "foc_tr4_vcg")],
         note="Genome and orthology data for the banana Fusarium wilt pathogen, inherited from EuPathDB annotation pipelines."),
    dict(slug="ds_dpvweb_reference", name="DPVweb taxonomy & genome reference", source="SRC:DPVWEB",
         data_type="Viral taxonomy & genome organization", evidence="Genome assembly / sequence data",
         year=2006, crop=None, region="Global",
         links=[("pathogen", "acmv"), ("pathogen", "tylcv")],
         note="Reference taxonomic and genome-organization entries for plant-infecting geminiviruses."),
    dict(slug="ds_pvsirnadb_reference", name="PVsiRNAdb vsiRNA reference", source="SRC:PVSIRNADB",
         data_type="Virus-derived small RNA catalogue", evidence="Experimental (literature-curated small RNA data)",
         year=2018, crop=None, region="Global",
         links=[("pathogen", "acmv"), ("pathogen", "tylcv")],
         note="Catalogues virus-derived siRNAs relevant to host RNA-silencing antiviral defense for geminiviruses."),
    dict(slug="ds_phibase_moryzae", name="PHI-base interaction record: Magnaporthe oryzae virulence genes", source="SRC:PHIBASE",
         data_type="Host-pathogen interaction", evidence="Experimental (peer-reviewed literature curation)",
         year=2025, crop="Rice", region="Global",
         links=[("pathogen", "m_oryzae"), ("disease", "rice_blast"), ("host", "rice")],
         note="Curated pathogenicity and effector gene interaction phenotypes for the rice blast fungus."),
    dict(slug="ds_phibase_xoo", name="PHI-base interaction record: Xanthomonas oryzae pv. oryzae", source="SRC:PHIBASE",
         data_type="Host-pathogen interaction", evidence="Experimental (peer-reviewed literature curation)",
         year=2025, crop="Rice", region="South & Southeast Asia",
         links=[("pathogen", "xoo"), ("disease", "rice_bact_blight"), ("host", "rice")],
         note="Curated virulence and effector gene interaction phenotypes for rice bacterial blight."),
    dict(slug="ds_phibase_pinfestans", name="PHI-base interaction record: Phytophthora infestans", source="SRC:PHIBASE",
         data_type="Host-pathogen interaction", evidence="Experimental (peer-reviewed literature curation)",
         year=2025, crop="Potato, tomato", region="Global",
         links=[("pathogen", "p_infestans"), ("disease", "potato_late_blight"), ("disease", "tomato_late_blight")],
         note="Curated effector and pathogenicity gene interaction phenotypes for the late blight oomycete."),
    dict(slug="ds_phibase_foc", name="PHI-base interaction record: Fusarium oxysporum f. sp. cubense", source="SRC:PHIBASE",
         data_type="Host-pathogen interaction", evidence="Experimental (peer-reviewed literature curation)",
         year=2025, crop="Banana", region="Southeast Asia, global",
         links=[("pathogen", "foc_tr4"), ("disease", "banana_fusarium_wilt")],
         note="Curated pathogenicity gene interaction phenotypes for banana Fusarium wilt."),
    dict(slug="ds_phibase_rsolanacearum", name="PHI-base interaction record: Ralstonia solanacearum", source="SRC:PHIBASE",
         data_type="Host-pathogen interaction", evidence="Experimental (peer-reviewed literature curation)",
         year=2025, crop="Potato, tomato", region="Tropical & subtropical regions, global",
         links=[("pathogen", "r_solanacearum"), ("disease", "bacterial_wilt_potato")],
         note="Curated virulence gene interaction phenotypes for bacterial wilt."),
    dict(slug="ds_prgdb_rice", name="PRGdb resistance gene catalogue: rice NBS-LRR family", source="SRC:PRGDB",
         data_type="Resistance gene / candidate gene catalogue", evidence="Computational prediction (RGA pipeline) + experimental confirmation for cloned genes",
         year=2022, crop="Rice", region="Global",
         links=[("gene", "pi_ta"), ("gene", "pi9"), ("host", "rice")],
         note="Known and computationally predicted NBS-LRR resistance gene analogs for rice blast resistance."),
    dict(slug="ds_prgdb_wheat", name="PRGdb resistance gene catalogue: wheat NBS-LRR family", source="SRC:PRGDB",
         data_type="Resistance gene / candidate gene catalogue", evidence="Computational prediction (RGA pipeline) + experimental confirmation for cloned genes",
         year=2022, crop="Wheat", region="Global",
         links=[("gene", "lr34"), ("gene", "sr35"), ("host", "wheat")],
         note="Known and computationally predicted resistance gene analogs relevant to wheat rust resistance."),
    dict(slug="ds_rgenedb_potato", name="R-gene Database record: potato late blight resistance family", source="SRC:RGENE_DB",
         data_type="R-gene sequence & allelic variant catalogue", evidence="Experimental (cloned gene sequence)",
         year=2022, crop="Potato", region="Global",
         links=[("gene", "rb_gene"), ("host", "potato")],
         note="Characterized R-gene sequence entry for the Solanum bulbocastanum-derived RB/Rpi-blb1 resistance gene."),
    dict(slug="ds_expratlas_blast", name="Expression Atlas dataset: rice blast infection transcriptome", source="SRC:EXPR_ATLAS",
         data_type="Transcriptomic expression dataset", evidence="Expression profiling (RNA-seq/microarray)",
         year=2016, crop="Rice", region="Global",
         links=[("pathogen", "m_oryzae"), ("disease", "rice_blast")],
         note="Differential expression data queryable alongside PHI-base interaction records for the same pathosystem."),
    dict(slug="ds_expratlas_drought_tomato", name="Expression Atlas dataset: tomato drought-stress transcriptome", source="SRC:EXPR_ATLAS",
         data_type="Transcriptomic expression dataset", evidence="Expression profiling (RNA-seq/microarray)",
         year=2025, crop="Tomato", region="Global",
         links=[("host", "tomato")],
         note="Cross-study synthesis of independently deposited drought-stress expression datasets in tomato."),
    dict(slug="ds_proteomexchange_pinfestans", name="ProteomeXchange/PRIDE dataset: Phytophthora infestans effector proteome", source="SRC:PRIDE",
         data_type="Proteomics dataset", evidence="Mass-spectrometry proteomics",
         year=2025, crop="Potato, tomato", region="Global",
         links=[("pathogen", "p_infestans")],
         note="Mass-spectrometry-based characterization of late blight effector and host immune proteomes."),
    dict(slug="ds_maizegdb_general", name="MaizeGDB genetics & genomics resource", source="SRC:MAIZEGDB",
         data_type="Crop genomics (genetic maps, gene function)", evidence="Genome assembly / curated community annotation",
         year=2016, crop="Maize", region="Global",
         links=[("host", "maize"), ("disease", "maize_nlb")],
         note="Chromosomal maps, QTLs, gene models and community-curated functional annotation for maize."),
    dict(slug="ds_snpseek_rice", name="Rice SNP-Seek 3000 Rice Genomes SNP resource", source="SRC:SNPSEEK",
         data_type="Crop genomics (SNP genotype data)", evidence="Genome resequencing / variant calling",
         year=2017, crop="Rice", region="Global",
         links=[("host", "rice"), ("gene", "xa21"), ("gene", "pi_ta")],
         note="Over 32 million SNPs across reference assemblies, supporting gene-trait association studies including resistance loci."),
    dict(slug="ds_soybase_general", name="SoyBase genetics & genomics resource", source="SRC:SOYBASE",
         data_type="Crop genomics (QTL/GWAS, expression tools)", evidence="Genome assembly / curated community annotation",
         year=2021, crop="Soybean", region="Global",
         links=[("host", "soybean"), ("disease", "soybean_rust")],
         note="Links QTL and GWAS loci relevant to soybean rust resistance with standardized trait ontologies."),
    dict(slug="ds_wheatis_general", name="WheatIS federated genomics access point", source="SRC:WHEATIS",
         data_type="Crop genomics (federated access)", evidence="Federated database access (aggregated, not primary curation)",
         year=2020, crop="Wheat", region="Global (federated)",
         links=[("host", "wheat"), ("disease", "wheat_stem_rust"), ("disease", "wheat_stripe_rust")],
         note="Single-access point spanning 8 geographically distributed nodes for wheat genomic and phenotypic data."),
    dict(slug="ds_droughtdb_general", name="DroughtDB drought-stress gene compilation", source="SRC:DROUGHTDB",
         data_type="Stress genomics (curated gene compilation)", evidence="Literature-curated experimental characterization",
         year=2015, crop="Multiple (9 species incl. rice, maize)", region="Global",
         links=[("host", "rice"), ("host", "maize")],
         note="Expert-curated drought-responsive genes and cross-species orthologs; homology-based inference for non-curated crops."),
    dict(slug="ds_stifdb2_general", name="STIFDB2 stress-responsive transcription factor catalogue", source="SRC:STIFDB2",
         data_type="Stress genomics (regulatory network)", evidence="Computational prediction (HMM-based binding-site scan) + literature curation",
         year=2013, crop="Arabidopsis, rice", region="Global",
         links=[("host", "rice")],
         note="Stress-responsive transcription factor binding site predictions, largely confined to two model/staple species."),
    dict(slug="ds_cyverse_infra", name="CyVerse phenomics computing infrastructure", source="SRC:CYVERSE",
         data_type="Computational infrastructure (domain-general)", evidence="Infrastructure / tooling (not a curated biological dataset)",
         year=2018, crop=None, region="Global",
         links=[],
         note="Cloud storage, workflow orchestration (e.g. SciApps, BioViz Connect) underpinning high-throughput phenotyping projects."),
    dict(slug="ds_mgnify_soil", name="MGnify soil metagenome-assembled genome catalogue", source="SRC:MGNIFY",
         data_type="Soil microbiome (MAGs & protein catalogue)", evidence="Metagenomic assembly & annotation",
         year=2026, crop=None, region="Global (297 sampled biomes)",
         links=[],
         note="Over 518,000 metagenome-assembled genomes and 2.45 billion predicted proteins from soil and other biomes."),
    dict(slug="ds_tmdb_general", name="TerrestrialMetagenomeDB metadata repository", source="SRC:TMDB",
         data_type="Soil microbiome (curated metadata)", evidence="Curated metadata aggregation (text-mining assisted)",
         year=2021, crop=None, region="Global",
         links=[],
         note="Standardized metadata for over 20,000 terrestrial metagenomes drawn from SRA and MG-RAST."),
]

# ---------------------------------------------------------------------------
# 4. BUILD RECORDS
# ---------------------------------------------------------------------------

records = []
id_counters = {}
slug_to_id = {}  # (kind, slug) -> HOPPER_ID


def next_id(kind_code):
    id_counters[kind_code] = id_counters.get(kind_code, 0) + 1
    return f"HOPPER:{kind_code}:{id_counters[kind_code]:04d}"


def base_record(hopper_id, entity_type, name, norm_name):
    return {
        "HOPPER_ID": hopper_id,
        "Entity_Type": entity_type,
        "Name": name,
        "Normalized_Name": norm_name,
        "Host": None,
        "Pathogen": None,
        "Disease": None,
        "Pathogen_Type": None,
        "Strain_or_Isolate": None,
        "Gene_or_Protein": None,
        "Resistance_Factor": None,
        "Phenotype": None,
        "Environmental_Context": None,
        "Geographic_Region": UNK,
        "Crop": None,
        "Data_Type": None,
        "Source_Database": NA,
        "Source_ID": NA,
        "Source_URL": None,
        "Ontology_Term": NA,
        "Synonyms": [],
        "Evidence_Type": "Literature-established / well-characterized",
        "Year": None,
        "License_or_Access_Status": NA,
        "Provenance": NA,
        "Last_Checked": "2026-09-10",
    }


# --- Hosts ---
for h in HOSTS:
    rid = next_id("HOST")
    slug_to_id[("host", h["slug"])] = rid
    rec = base_record(rid, "Host", h["name"], h["norm"])
    rec["Host"] = h["name"]
    rec["Crop"] = h["name"]
    rec["Geographic_Region"] = h["region"]
    rec["Synonyms"] = h["synonyms"]
    rec["Ontology_Term"] = f"Plant Ontology / NCBI Taxonomy concept: {h['norm']}"
    rec["Data_Type"] = "Host organism reference"
    rec["Provenance"] = "Reference-level taxonomic/host entity; not tied to a single external database record."
    records.append(rec)

# --- Pathogens ---
for p in PATHOGENS:
    rid = next_id("PATH")
    slug_to_id[("pathogen", p["slug"])] = rid
    rec = base_record(rid, "Pathogen", p["name"], p["name"])
    rec["Pathogen"] = p["name"]
    rec["Pathogen_Type"] = p["ptype"]
    rec["Synonyms"] = p["synonyms"]
    rec["Ontology_Term"] = f"NCBI Taxonomy concept: {p['name']}"
    rec["Data_Type"] = "Pathogen organism reference"
    rec["Provenance"] = "Reference-level taxonomic/pathogen entity; not tied to a single external database record."
    records.append(rec)

# --- Diseases ---
for d in DISEASES:
    rid = next_id("DIS")
    slug_to_id[("disease", d["slug"])] = rid
    host_name = next(h["name"] for h in HOSTS if h["slug"] == d["host"])
    path = next(p for p in PATHOGENS if p["slug"] == d["pathogen"])
    rec = base_record(rid, "Disease", d["name"], d["name"])
    rec["Host"] = host_name
    rec["Pathogen"] = path["name"]
    rec["Pathogen_Type"] = path["ptype"]  # propagated so "fungal diseases of X" style queries can match
    rec["Disease"] = d["name"]
    rec["Crop"] = host_name
    rec["Geographic_Region"] = d["region"]
    rec["Data_Type"] = "Disease concept reference"
    rec["Ontology_Term"] = NA
    rec["Provenance"] = "Reference-level disease concept linking a host and causal pathogen described in the plant pathology literature."
    records.append(rec)

# --- Genes / Resistance Factors ---
for g in GENES:
    rid = next_id("GENE")
    slug_to_id[("gene", g["slug"])] = rid
    host_name = next(h["name"] for h in HOSTS if h["slug"] == g["host"])
    path_name = next(p["name"] for p in PATHOGENS if p["slug"] == g["pathogen"])
    rec = base_record(rid, "Gene_Resistance_Factor", g["name"], g["name"])
    rec["Host"] = host_name
    rec["Pathogen"] = path_name
    rec["Gene_or_Protein"] = g["name"]
    rec["Resistance_Factor"] = g["name"]
    rec["Crop"] = host_name
    rec["Geographic_Region"] = "Global"
    rec["Data_Type"] = "Resistance gene / locus reference"
    rec["Evidence_Type"] = "Literature-established / experimentally characterized"
    rec["Provenance"] = g["note"]
    records.append(rec)

# --- Strains ---
for s in STRAINS:
    rid = next_id("STRAIN")
    slug_to_id[("strain", s["slug"])] = rid
    path_name = next(p["name"] for p in PATHOGENS if p["slug"] == s["pathogen"])
    rec = base_record(rid, "Strain_Isolate", s["name"], s["name"])
    rec["Pathogen"] = path_name
    rec["Strain_or_Isolate"] = s["name"]
    rec["Geographic_Region"] = "Global"
    rec["Data_Type"] = "Strain / isolate reference"
    rec["Provenance"] = s["note"]
    records.append(rec)

# --- Phenotypes ---
for ph in PHENOTYPES:
    rid = next_id("PHENO")
    slug_to_id[("phenotype", ph["slug"])] = rid
    dis = next(d for d in DISEASES if d["slug"] == ph["disease"])
    rec = base_record(rid, "Phenotype", ph["name"], ph["name"])
    rec["Disease"] = dis["name"]
    rec["Host"] = next(h["name"] for h in HOSTS if h["slug"] == dis["host"])
    rec["Phenotype"] = ph["name"]
    rec["Geographic_Region"] = "Global"
    rec["Data_Type"] = "Phenotype scoring reference"
    rec["Provenance"] = ph["note"]
    records.append(rec)

# --- Datasets / database-linked records ---
for ds in DATASETS:
    rid = next_id("DATA")
    slug_to_id[("dataset", ds["slug"])] = rid
    src = next(s for s in SOURCES if s["id"] == ds["source"])
    rec = base_record(rid, "Dataset", ds["name"], ds["name"])
    rec["Crop"] = ds["crop"]
    rec["Geographic_Region"] = ds["region"]
    rec["Data_Type"] = ds["data_type"]
    rec["Evidence_Type"] = ds["evidence"]
    rec["Year"] = ds["year"]
    rec["Source_Database"] = src["name"]
    rec["Source_ID"] = NA
    rec["Source_URL"] = src["url"]
    rec["License_or_Access_Status"] = src["access"]
    rec["Provenance"] = ("External resource / integrated reference record. " + ds["note"] +
                          " HOPPER stores normalized reference metadata only; " + src["name"] +
                          " remains the authoritative source.")
    # link contextual host/pathogen/disease fields where a single clear one exists
    linked_hosts, linked_paths, linked_dis = [], [], []
    for kind, slug in ds["links"]:
        if kind == "host":
            linked_hosts.append(next(h["name"] for h in HOSTS if h["slug"] == slug))
        elif kind == "pathogen":
            linked_paths.append(next(p["name"] for p in PATHOGENS if p["slug"] == slug))
        elif kind == "disease":
            linked_dis.append(next(d["name"] for d in DISEASES if d["slug"] == slug))
        elif kind == "strain":
            rec["Strain_or_Isolate"] = next(s["name"] for s in STRAINS if s["slug"] == slug)
        elif kind == "gene":
            linked_hosts_gene = next(g for g in GENES if g["slug"] == slug)
    if linked_hosts:
        rec["Host"] = "; ".join(sorted(set(linked_hosts)))
    if linked_paths:
        rec["Pathogen"] = "; ".join(sorted(set(linked_paths)))
        # propagate Pathogen_Type only when every linked pathogen shares one type,
        # so we never assert a type that isn't uniformly true for this record
        linked_ptypes = {next(p["ptype"] for p in PATHOGENS if p["name"] == name) for name in set(linked_paths)}
        if len(linked_ptypes) == 1:
            rec["Pathogen_Type"] = next(iter(linked_ptypes))
    if linked_dis:
        rec["Disease"] = "; ".join(sorted(set(linked_dis)))
    records.append(rec)

# ---------------------------------------------------------------------------
# 5. RELATIONSHIPS
# ---------------------------------------------------------------------------

relationships = []


def add_rel(rel_type, src, tgt, note=None):
    relationships.append({
        "type": rel_type,
        "source": src,
        "target": tgt,
        "note": note,
    })


for d in DISEASES:
    dis_id = slug_to_id[("disease", d["slug"])]
    host_id = slug_to_id[("host", d["host"])]
    path_id = slug_to_id[("pathogen", d["pathogen"])]
    add_rel("HOST_HAS_DISEASE", host_id, dis_id)
    add_rel("DISEASE_CAUSED_BY", dis_id, path_id)

for g in GENES:
    gene_id = slug_to_id[("gene", g["slug"])]
    host_id = slug_to_id[("host", g["host"])]
    path_id = slug_to_id[("pathogen", g["pathogen"])]
    add_rel("HOST_HAS_RESISTANCE_FACTOR", host_id, gene_id)
    add_rel("RESISTANCE_FACTOR_TARGETS_PATHOGEN", gene_id, path_id)

for s in STRAINS:
    strain_id = slug_to_id[("strain", s["slug"])]
    path_id = slug_to_id[("pathogen", s["pathogen"])]
    add_rel("PATHOGEN_HAS_STRAIN", path_id, strain_id)

for ph in PHENOTYPES:
    pheno_id = slug_to_id[("phenotype", ph["slug"])]
    dis = next(d for d in DISEASES if d["slug"] == ph["disease"])
    dis_id = slug_to_id[("disease", dis["slug"])]
    add_rel("DISEASE_HAS_PHENOTYPE", dis_id, pheno_id)

for ds in DATASETS:
    data_id = slug_to_id[("dataset", ds["slug"])]
    for kind, slug in ds["links"]:
        if kind in ("host", "pathogen", "disease", "strain", "gene"):
            key = (kind, slug)
            if key in slug_to_id:
                target_id = slug_to_id[key]
                if kind == "pathogen":
                    add_rel("PATHOGEN_REPRESENTED_IN", target_id, data_id)
                else:
                    add_rel("ENTITY_LINKED_TO_DATASET", target_id, data_id)

# synonym self-relationships (kept lightweight: only for entities with >1 synonym)
for h in HOSTS:
    if len(h["synonyms"]) > 1:
        add_rel("ENTITY_HAS_SYNONYM", slug_to_id[("host", h["slug"])], None, note=", ".join(h["synonyms"]))
for p in PATHOGENS:
    if len(p["synonyms"]) > 1:
        add_rel("ENTITY_HAS_SYNONYM", slug_to_id[("pathogen", p["slug"])], None, note=", ".join(p["synonyms"]))

# geographic association edges (host/disease -> region string, kept as note-only edges)
for d in DISEASES:
    add_rel("ENTITY_ASSOCIATED_WITH_REGION", slug_to_id[("disease", d["slug"])], None, note=d["region"])

# ---------------------------------------------------------------------------
# 6. IDENTIFIER MAPPINGS (cross-reference / multi-database chains)
# ---------------------------------------------------------------------------
# Curated set of "hub" entities that are represented, directly or via a
# linked dataset record, across more than one external source. This is the
# demonstration data behind the Cross-Database Connections view.

def dataset_rec(slug):
    return next(ds for ds in DATASETS if ds["slug"] == slug)


IDENTIFIER_MAPPINGS = [
    {
        "concept": "Rice blast (Magnaporthe oryzae / Oryza sativa)",
        "hopper_id": slug_to_id[("disease", "rice_blast")],
        "chain": [
            {"database": "PHI-base", "hopper_record": slug_to_id[("dataset", "ds_phibase_moryzae")], "source_id": NA, "url": "https://www.phi-base.org"},
            {"database": "FungiDB", "hopper_record": slug_to_id[("dataset", "ds_fungidb_moryzae")], "source_id": NA, "url": "https://fungidb.org"},
            {"database": "PlantVillage", "hopper_record": slug_to_id[("dataset", "ds_plantvillage")], "source_id": NA, "url": "https://plantvillage.psu.edu"},
            {"database": "PlantPAD", "hopper_record": slug_to_id[("dataset", "ds_plantpad")], "source_id": NA, "url": "http://plantpad.samlab.cn"},
            {"database": "Rice SNP-Seek", "hopper_record": slug_to_id[("dataset", "ds_snpseek_rice")], "source_id": NA, "url": "http://snp-seek.irri.org"},
            {"database": "Expression Atlas", "hopper_record": slug_to_id[("dataset", "ds_expratlas_blast")], "source_id": NA, "url": "https://www.ebi.ac.uk/gxa"},
        ],
    },
    {
        "concept": "Rice bacterial blight (Xanthomonas oryzae pv. oryzae / Oryza sativa)",
        "hopper_id": slug_to_id[("disease", "rice_bact_blight")],
        "chain": [
            {"database": "PHI-base", "hopper_record": slug_to_id[("dataset", "ds_phibase_xoo")], "source_id": NA, "url": "https://www.phi-base.org"},
            {"database": "Rice SNP-Seek", "hopper_record": slug_to_id[("dataset", "ds_snpseek_rice")], "source_id": NA, "url": "http://snp-seek.irri.org"},
        ],
    },
    {
        "concept": "Late blight (Phytophthora infestans / potato & tomato)",
        "hopper_id": slug_to_id[("pathogen", "p_infestans")],
        "chain": [
            {"database": "PHI-base", "hopper_record": slug_to_id[("dataset", "ds_phibase_pinfestans")], "source_id": NA, "url": "https://www.phi-base.org"},
            {"database": "R-gene Database", "hopper_record": slug_to_id[("dataset", "ds_rgenedb_potato")], "source_id": NA, "url": None},
            {"database": "PRIDE / ProteomeXchange", "hopper_record": slug_to_id[("dataset", "ds_proteomexchange_pinfestans")], "source_id": NA, "url": "https://www.ebi.ac.uk/pride/archive"},
        ],
    },
    {
        "concept": "Cassava mosaic disease (ACMV / cassava)",
        "hopper_id": slug_to_id[("disease", "cassava_mosaic")],
        "chain": [
            {"database": "DPVweb", "hopper_record": slug_to_id[("dataset", "ds_dpvweb_reference")], "source_id": NA, "url": "http://www.dpvweb.net"},
            {"database": "PVsiRNAdb", "hopper_record": slug_to_id[("dataset", "ds_pvsirnadb_reference")], "source_id": NA, "url": "http://www.nipgr.res.in/PVsiRNAdb"},
            {"database": "CCMT Dataset", "hopper_record": slug_to_id[("dataset", "ds_ccmt")], "source_id": NA, "url": None},
            {"database": "FieldPlant", "hopper_record": slug_to_id[("dataset", "ds_fieldplant")], "source_id": NA, "url": "https://doi.org/10.1109/ACCESS.2023.3263042"},
            {"database": "Cassava Leaf Disease Dataset", "hopper_record": slug_to_id[("dataset", "ds_cassava_leaf")], "source_id": NA, "url": "https://www.kaggle.com/c/cassava-leaf-disease-classification"},
        ],
    },
    {
        "concept": "Banana Fusarium wilt / Panama disease (Foc TR4 / banana)",
        "hopper_id": slug_to_id[("disease", "banana_fusarium_wilt")],
        "chain": [
            {"database": "PHI-base", "hopper_record": slug_to_id[("dataset", "ds_phibase_foc")], "source_id": NA, "url": "https://www.phi-base.org"},
            {"database": "FungiDB", "hopper_record": slug_to_id[("dataset", "ds_fungidb_foc")], "source_id": NA, "url": "https://fungidb.org"},
        ],
    },
    {
        "concept": "Wheat rust resistance (Lr34 / Sr35 / wheat)",
        "hopper_id": slug_to_id[("host", "wheat")],
        "chain": [
            {"database": "PRGdb", "hopper_record": slug_to_id[("dataset", "ds_prgdb_wheat")], "source_id": NA, "url": "https://prgdb.org"},
            {"database": "WheatIS", "hopper_record": slug_to_id[("dataset", "ds_wheatis_general")], "source_id": NA, "url": "http://wheatis.org"},
        ],
    },
    {
        "concept": "Drought stress in staple crops (rice, maize)",
        "hopper_id": slug_to_id[("host", "rice")],
        "chain": [
            {"database": "DroughtDB", "hopper_record": slug_to_id[("dataset", "ds_droughtdb_general")], "source_id": NA, "url": "http://pgsb.helmholtz-muenchen.de/droughtdb/"},
            {"database": "STIFDB2", "hopper_record": slug_to_id[("dataset", "ds_stifdb2_general")], "source_id": NA, "url": "http://caps.ncbs.res.in/stifdb2"},
            {"database": "Expression Atlas", "hopper_record": slug_to_id[("dataset", "ds_expratlas_drought_tomato")], "source_id": NA, "url": "https://www.ebi.ac.uk/gxa"},
            {"database": "CyVerse", "hopper_record": slug_to_id[("dataset", "ds_cyverse_infra")], "source_id": NA, "url": "https://cyverse.org"},
        ],
    },
    {
        "concept": "Soil microbiome & plant disease context",
        "hopper_id": None,
        "chain": [
            {"database": "MGnify", "hopper_record": slug_to_id[("dataset", "ds_mgnify_soil")], "source_id": NA, "url": "https://www.ebi.ac.uk/metagenomics"},
            {"database": "TerrestrialMetagenomeDB", "hopper_record": slug_to_id[("dataset", "ds_tmdb_general")], "source_id": NA, "url": "https://webapp.ufz.de/tmdb"},
        ],
    },
    {
        "concept": "Soybean rust (Phakopsora pachyrhizi / soybean)",
        "hopper_id": slug_to_id[("disease", "soybean_rust")],
        "chain": [
            {"database": "SoyBase", "hopper_record": slug_to_id[("dataset", "ds_soybase_general")], "source_id": NA, "url": "https://soybase.org"},
            {"database": "PlantPAD", "hopper_record": slug_to_id[("dataset", "ds_plantpad")], "source_id": NA, "url": "http://plantpad.samlab.cn"},
        ],
    },
]

# ---------------------------------------------------------------------------
# 7. SCHEMA MAPPING (normalization layer configuration)
# ---------------------------------------------------------------------------

SCHEMA_MAPPING = {
    "HOST": {
        "description": "The plant host organism affected by a disease or pathogen.",
        "source_field_variants": ["host_species", "plant", "host", "crop_species", "host organism", "organism_host", "crop"],
    },
    "PATHOGEN": {
        "description": "The causal biological agent (fungus, oomycete, bacterium or virus).",
        "source_field_variants": ["pathogen_name", "causal_agent", "organism", "etiological_agent", "causal organism", "pathogen"],
    },
    "DISEASE": {
        "description": "The named disease concept linking a host and a pathogen.",
        "source_field_variants": ["disease_name", "disease", "condition", "syndrome"],
    },
    "GENE_OR_PROTEIN": {
        "description": "A gene, protein, or resistance locus referenced by a record.",
        "source_field_variants": ["gene", "gene_id", "locus", "protein", "gene_symbol"],
    },
    "RESISTANCE_FACTOR": {
        "description": "A characterized or predicted resistance gene/locus conferring reduced disease susceptibility.",
        "source_field_variants": ["resistance_gene", "r_gene", "rga", "resistance_locus"],
    },
    "DATA_TYPE": {
        "description": "The category of data a record represents (image dataset, interaction record, genome, expression data, etc).",
        "source_field_variants": ["category", "data_category", "dataset_type", "content_type"],
    },
    "GEOGRAPHIC_REGION": {
        "description": "The geographic scope of the underlying data or sampled material.",
        "source_field_variants": ["region", "country", "location", "geography", "geographic_focus"],
    },
    "SOURCE_DATABASE": {
        "description": "The external database or resource a record was integrated from.",
        "source_field_variants": ["database", "db_name", "resource", "repository", "source"],
    },
    "EVIDENCE_TYPE": {
        "description": "The kind of evidence underlying a record (experimental curation, computational prediction, image annotation, etc).",
        "source_field_variants": ["evidence", "confidence", "validation_type", "method"],
    },
}

# ---------------------------------------------------------------------------
# 8. WRITE OUTPUT
# ---------------------------------------------------------------------------

os.makedirs(DATA_DIR, exist_ok=True)


def write_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"wrote {path} ({len(json.dumps(data))} bytes)")


# finalize sources.json (drop internal-only computation, keep readable shape)
sources_out = [
    {
        "Source_ID": s["id"],
        "Name": s["name"],
        "Domain": s["domain"],
        "Data_Type": s["data_type"],
        "Organisms_Crops": s["organisms"],
        "Role_in_HOPPER": s["role"],
        "External_URL": s["url"],
        "Access": s["access"],
        "Geographic_Scope": s["geography"],
        "Notes": s["notes"],
        "Last_Checked": "2026-09-10",
    }
    for s in SOURCES
]

write_json("hopper_records.json", records)
write_json("relationships.json", relationships)
write_json("sources.json", sources_out)
write_json("identifier_mappings.json", IDENTIFIER_MAPPINGS)
write_json("schema_mapping.json", SCHEMA_MAPPING)

print(f"\nTotals: {len(records)} records, {len(relationships)} relationships, "
      f"{len(sources_out)} sources, {len(IDENTIFIER_MAPPINGS)} identifier mapping chains.")

by_type = {}
for r in records:
    by_type[r["Entity_Type"]] = by_type.get(r["Entity_Type"], 0) + 1
print("Records by Entity_Type:", by_type)
