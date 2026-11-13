# Reference-data brief — nf-core/mag → Galaxy

Source: nf-core/mag 5.5.0 (db7772f), evidence from `summary-nextflow.json`
(`reference_assets[]`, `reference_rebuilds[]`, `params[]`).
Classified with `nextflow-reference-data-classification`, translated with the v1
posture from `nextflow-to-galaxy-reference-data-mapping` (explicit optional `data`
inputs + in-tool rebuild; no `dbkey`/`.loc` data tables).

## Classification (flags — several apply)

| Classification | Applies | Evidence |
|---|---|---|
| None | no | 15 reference assets |
| Reference-producing | no | DBs are inputs; outputs are results, not bundles |
| Single asset | yes | `phix_reference`, `lambda_reference` (each one optional FASTA, repo-bundled fallback in `assets/data/`) |
| Coordinated bundle | partially | host bundle: `host_fasta` + `host_fasta_bowtie2index` travel together; MultiQC `multiqc_config` + `multiqc_methods_description` pair |
| Key-expanded bundle (iGenomes) | partially | only ONE attribute is key-expanded: `host_fasta` ← `params.genomes[params.host_genome].fasta` (mag.nf ch_host_fasta). No `getGenomeAttribute` fan-out — there is no genome bundle here, just the host. Galaxy surface starts at the resolved `host_fasta` path; the `host_genome`/`igenomes` key is **not carried** (see ledger) |
| Compute-if-missing | **yes, heavily** | 8 `reference_rebuilds[]` entries; every analysis database has a build/download-on-absence fallback |
| Multi-DB pick-list | **yes — primary shape** | 7 independent optional DBs, each enabling its own branch: `busco_db`+`run_busco`, `checkm_db`+`run_checkm`, `checkm2_db`+`run_checkm2`, `gunc_db`+`run_gunc`, `cat_db`, `gtdb_db`+`skip_gtdbtk`, `genomad_db`+`run_virus_identification`, plus `metaeuk_db`/`metaeuk_mmseqs_db` for MetaEuk. Bin-QC DBs converge in one join (`BIN_SUMMARY`), CAT feeds Taxonomy, geNomad feeds virus ID |
| Parallel bundles + cohort | no | no cohort/panel data |

**Reading:** MAG is funcscan-style pick-list *wrapped around* compute-if-missing. The
user picks 0..N analysis DBs; whatever is picked but absent is downloaded/rebuilt by
the pipeline (Zenodo CheckM2, GTDB r232, CAT Nr, geNomad, GUNC, MetaEuk/Kalamari).
Galaxy v1 flips this: **each DB is an explicit optional input; the download-on-absence
fallbacks are not carried** (no admin-managed fetch, and several builds — CAT from Nr —
are impractical inside a run). The pick-list per se IS carried: an optional input
whose presence gates its branch mirrors the `run_*`/`skip_*` + DB-param guards.

## Per-asset disposition

v1 shape per asset. "optional data input" = workflow `data` input, optional. Formats
use vendored `galaxy-datatypes-conf` names; `data` = deliberate fallback, flagged.

| Nextflow param | Galaxy input | Format | Required | Notes |
|---|---|---|---|---|
| `phix_reference` | optional input `phiX reference` | `fasta` | no | Absent ⇒ skip phiX removal (= `keep_phix: true`). Default content available from repo `assets/data/GCA_002596845.1_ASM259684v1_genomic.fna.gz`; document in input help (workflows can't bundle, inputs can — file is 5.4 kb) |
| `lambda_reference` | optional input `lambda reference` | `fasta` | no | Same pattern; `assets/data/GCA_000840245.1_ViralProj14204_genomic.fna.gz`; also feeds NANOLYSE/chopper long-read removal |
| `host_fasta` | optional input `host genome` | `fasta` | no | Absent ⇒ no host removal. gz auto-sniffs |
| `host_fasta_bowtie2index` | **not surfaced** | — | no | Rebuild-on-absence stays: wrapper builds the bowtie2 index from `host genome` in-tool. No built-in bowtie2-index directory datatype in the vendored sample — surfacing it would force a `data` directory upload; rebuild is the cleaner default. Wrapper rebuild capability *unverified* (ledger) |
| `gtdb_db` | optional input `GTDB-Tk database` | `data` (tar.gz) or directory | no | Guarded by `skip_gtdbtk`. `GTDBTK_DB_PREPARATION` untar: prefer in-tool unpack from the tarball upload; open question (ledger) |
| `busco_db` (+ `busco_db_lineage`) | optional input `BUSCO database` | `data` (tar.gz) | no | `busco_db_lineage` becomes a text/select companion input (lineage dir name inside the tarball); `run_busco` collapses to input-presence |
| `checkm_db` | optional input `CheckM database` | `data` (tar.gz) | no | `checkm_download_url` Zenodo fallback NOT carried; DB absent ⇒ CheckM branch off. CHECKM_UNTAR unpack in-tool |
| `checkm2_db` | optional input `CheckM2 database` | `data` (tar.gz) | no | `checkm2_db_version` (14897628) documented in help as where to obtain |
| `gunc_db` | optional input `GUNC database` | `data` | no | `gunc_database_type` download fallback not carried |
| `cat_db` | optional input `CAT database pack` | `data` (tar.gz) | no | `cat_db_generate` (CATPACK_DOWNLOAD Nr + CATPACK_PREPARE) **not carried** — hundreds-of-GB build from Nr, logged in-source as very large (ledger: dropped). `cat_classify_unbinned` stays a boolean param |
| `genomad_db` | optional input `geNomad database` | `data` (tar.gz/directory) | no | GENOMAD_DOWNLOAD fallback not carried |
| `metaeuk_db` | optional input `MetaEuk mmseqs database` | `data` (directory) | no | |
| `metaeuk_mmseqs_db` | **merged into `metaeuk_db`** | — | no | URL/mmseqs-name (e.g. `Kalamari`) auto-build via MMSEQS_DATABASES **not carried** (ledger gap: no concrete uploadable artifact from a bare name) |
| `multiqc_config`, `multiqc_methods_description` | not workflow inputs | — | no | Repo-bundled config/template assets; bake into the MultiQC step (tool-config, not reference data). If interface wants customisability, a later revision can add optional text inputs |
| `host_genome` / `genomes` map | not carried | — | no | iGenomes key has no Galaxy analogue in v1 posture |

Pick-list semantics carried into the interface: presence of each optional DB input
gates its branch (`when:` on input-set), mirroring the source guards; the seven
bin-QC/taxonomy DBs join independently into `bin_summary.tsv` (QSV_CAT rowskey), so
any subset is coherent — same as source.

## Rebuild decisions

- **In-tool rebuild kept** where the input is a derived artifact of a *carried* input:
  bowtie2 host index (from host FASTA). Threshold (<3 uses, single consumer chain)
  favors in-tool; matches existing IWC wrapper convention. **Unverified per-wrapper** —
  ledger entry.
- **Download/build fallbacks dropped** (CheckM Zenodo tar, CheckM2 Zenodo record,
  GUNC `download_db`, CAT Nr download+prepare, geNomad download, MMSEQS_DATABASES):
  Galaxy has no admin-curated fetch and v1 posture is user-supplied inputs. Each
  affected branch degrades to "off when the input is absent", exactly like the source
  `run_*: false` case.
- **Unpacks are not rebuilds**: UNTAR/CHECKM_UNTAR/BUSCO_UNTAR/CHECKM2/CATPACK_DB_UNTAR/
  GTDBTK_DB_PREPARATION transform a supplied tarball into the layout the tool wants —
  keep them, in-tool (one wrapper per consumer branch; each unpacks once per run).

## Open questions (carried as ledger entries, not gates)

1. tarball-vs-directory acceptance per DB input (unpack in-tool vs a workflow-tier
   extract step) — proposed: in-tool, `data` tarball inputs.
2. bowtie2-index wrapper rebuild capability — unverified until discover-shed-tool.
3. No worked Galaxy exemplar for a 7-DB pick-list (mapping note gap); interface/data-flow
   Molds design it from optional inputs + `when:`, no exemplar anchor.
4. `busco_db_lineage` as free text vs select — a select can't know the tarball's
   contents; proposed free text with `bacteria_odb10` default hint.
5. MetaEuk `Kalamari`-style remote mmseqs db names have no Galaxy artifact equivalent;
   users must supply an mmseqs DB directory.
