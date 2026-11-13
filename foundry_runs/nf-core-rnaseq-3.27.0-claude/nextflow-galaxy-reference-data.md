# Nextflow → Galaxy reference-data brief: nf-core/rnaseq 3.27.0

Produced by `nextflow-summary-to-galaxy-reference-data` from `summary-nextflow.json`
(source revision `95dbcd977a74a4d1b2a3954abb90df3851014afa`, phase 1 artifact).
Consumed by `nextflow-summary-to-galaxy-interface`, `nextflow-summary-to-galaxy-data-flow`,
and `nextflow-summary-to-galaxy-template` before workflow inputs, data-flow edges, and the
gxformat2 skeleton are pinned.

All claims below cite the summary artifact only. Where a signal the classification expects
is missing from the summary, the affected asset is flagged rather than re-derived from the
source tree (per this Mold's runtime contract).

## Classification (nextflow-reference-data-classification)

nf-core/rnaseq 3.27.0 matches more than one of the eight classifications:

| Classification | Verdict | Evidence (summary fields) |
|---|---|---|
| None | No | 22 entries in `reference_assets[]` |
| Reference-producing | No | Outputs are per-sample results; `PREPARE_GENOME_*` builds indexes as intermediates, not as published bundles |
| Single asset | No | Multiple path-shaped reference params |
| **Coordinated bundle** | **Yes (primary)** | 7 assets under `schema_group: "Reference genome options"` (`fasta`, `gtf`, `gff`, `gene_bed`, `transcript_fasta`, `additional_fasta`, `splicesites`) all consumed together by `PREPARE_GENOME_REFERENCES`; switching genome means switching all of them |
| **Key-expanded bundle (iGenomes-style)** | **Yes, weakened form** | `params.genome` exists ("Name of a `params.genomes` catalogue entry (iGenomes or a user-defined catalogue)"), plus hidden `igenomes_base` (default `s3://ngi-igenomes/igenomes/`) and `igenomes_ignore`. **But no `params[]` entry carries `source_kind: "getGenomeAttribute"`** — the detection signal the classifier keys on is absent from this summary (see *iGenomes key disposition* below) |
| **Compute-if-missing (aspect)** | **Yes — rebuild-unverified** | `reference_rebuilds[]` is **empty**. Per the classification note this does NOT mean "no compute-if-missing": nf-core/rnaseq's `PREPARE_GENOME` uses the positive-form idiom (`if (<asset>) { unpack } else if (fasta_provided) { build }`) that the detector does not yet match (galaxyproject/foundry#229 follow-ups). Summary-internal corroborating evidence: `PREPARE_GENOME_INDICES.calls` pairs `UNTAR_STAR_INDEX` … `UNTAR_SORTMERNA_INDEX` with `STAR_GENOMEGENERATE`, `HISAT2_BUILD`, `RSEM_PREPAREREFERENCE_GENOME`, `SALMON_INDEX`, `KALLISTO_INDEX`, `BOWTIE2_BUILD`, `SORTMERNA_INDEX`, and takes a `fasta_provided` boolean ("whether a genome FASTA was provided"). **All rebuild-eligible assets below are flagged `rebuild-unverified`** |
| Multi-DB pick-list | Partial, secondary | QC/filter databases each gate their own optional branch: `kraken_db` (gated by `contaminant_screening` ∈ {kraken2, kraken2_bracken}), `sylph_db` + `sylph_taxonomy` (gated by `contaminant_screening == sylph`), `ribo_database_manifest` / `sortmerna_index` / `bowtie2_rrna_index` (gated by `remove_ribo_rna` + `ribo_removal_tool`), `bbsplit_fasta_list` / `bbsplit_index` (gated by `skip_bbsplit`). User picks 0..N; none is rebuildable |
| Parallel bundles plus cohort data | No | No cohort/panel data (no PoN, germline-resource, intervals) |

Net classification: **coordinated reference bundle over an iGenomes-style genome key, with a
compute-if-missing aspect on every index (rebuild-unverified), plus a secondary multi-DB
pick-list of QC/contamination/rRNA databases**.

## Per-asset translation table

v1 Galaxy posture (nextflow-to-galaxy-reference-data-mapping): **explicit optional `data`
inputs; no `dbkey`-keyed or generic data tables** (admin install breaks portability);
specific datatypes where the vendored datatype table carries them, `data` otherwise.
"Rebuild on absence" states what happens in the source when the input is unset, and the
recommended Galaxy-side behavior.

### Coordinated reference bundle (`PREPARE_GENOME_REFERENCES`)

| Param | Asset kind | Summary required | Used by | Galaxy input (v1) | Rebuild on absence (source) | Recommended Galaxy behavior |
|---|---|---|---|---|---|---|
| `fasta` | fasta (`file-path`) | false | PREPARE_GENOME_REFERENCES, RNASEQ | `data`, `format: fasta`, optional | Never rebuilt — it is the rebuild substrate; GUNZIP_FASTA handles `.gz` | Optional input; effectively required core (see Requiredness) |
| `gtf` | gtf (`file-path`) | false | PREPARE_GENOME_REFERENCES | `data`, `format: gtf`, optional | Not rebuilt (annotation is user data) | Optional; mutually exclusive with `gff` |
| `gff` | gff (`file-path`) | false | PREPARE_GENOME_REFERENCES | `data`, `format: gff3`, optional | Not rebuilt; `GFFREAD*` derives GTF-side artifacts from it | Optional; alternative to `gtf` |
| `gene_bed` | bed (`file-path`) | false | PREPARE_GENOME_REFERENCES | `data`, `format: bed`, optional | Rebuilt from GTF/GFF (`EAUTILS_GTF2BED`, `GFFREAD_GENE_BED` in calls) — **rebuild-unverified** | In-tool / derived: expect consumer wrapper to derive, or derive in the tool that needs it. Supplying it is an optimization, not a requirement |
| `transcript_fasta` | fasta (`file-path`) | false | PREPARE_GENOME_REFERENCES | `data`, `format: fasta`, optional | Rebuilt from GTF (`MAKE_TRANSCRIPTS_FASTA`, `GFFREAD_TRANSCRIPTS`, `RSEM_PREPAREREFERENCE_GENOME`-side extraction) — **rebuild-unverified** | Same as `gene_bed`: derived asset; optional input |
| `additional_fasta` | fasta (`file-path`) | false | PREPARE_GENOME_REFERENCES | `data`, `format: fasta`, optional | Never rebuilt (spike-ins are user data); concatenated via `CUSTOM_CATADDITIONALFASTA` | Optional input, passed through |
| `splicesites` | other (`file-path`) | false | PREPARE_GENOME_INDICES | `data` (HISAT2 extractSpliceSites text file; no specific datatype — document), optional | Rebuilt from GTF via `HISAT2_EXTRACTSPLICESITES` — **rebuild-unverified** | Derived asset; expect the HISAT2 wrapper to derive from GTF when absent (capability unverified) |
| `pipelines_testdata_base_path` | other (`directory-path`) | false | *(none)* | **Exclude** | n/a | **False positive in the curated inventory**: hidden nf-core CLI-plumbing param (test-data base URL), `used_by: []`, evidence confidence medium. Not reference data; the interface Mold should drop it from the reference surface |

### Pre-built indexes (`PREPARE_GENOME_INDICES`) — all rebuild-unverified

All are `format: path` ("directory or tar.gz archive"), summary `required: false`,
consumed via the paired `UNTAR_<X>_INDEX` (pre-built supplied) / `<X>` builder (absent)
branch.

| Param | Used by | Galaxy input (v1) | Builder when absent | Recommended Galaxy behavior |
|---|---|---|---|---|
| `star_index` | PREPARE_GENOME_INDICES | `data` (directory; no STAR-index datatype in the vendored datatype table — use `data` or `directory` and document), optional | `STAR_GENOMEGENERATE` | **Workflow-tier build step** when absent (see *Rebuild placement*): heavy index consumed by the per-sample `ALIGN_STAR` fan-out |
| `hisat2_index` | PREPARE_GENOME_INDICES | `data`/`directory`, optional | `HISAT2_BUILD` | Workflow-tier build step when absent (per-sample `FASTQ_ALIGN_HISAT2` fan-out) |
| `rsem_index` | PREPARE_GENOME_INDICES | `data`/`directory`, optional | `RSEM_PREPAREREFERENCE_GENOME` | Workflow-tier build step when absent |
| `salmon_index` | PREPARE_GENOME_INDICES, RNASEQ | `data`/`directory`, optional | `SALMON_INDEX` | Workflow-tier build step when absent; consumed by `QUANTIFY_PSEUDO_ALIGNMENT` / `QUANTIFY_BAM_SALMON` |
| `kallisto_index` | PREPARE_GENOME_INDICES | `data`/`directory`, optional (note: Galaxy has a single-file `kallisto.idx` datatype; the source expects a directory or tarball) | `KALLISTO_INDEX` | Workflow-tier build step when absent |
| `bowtie2_index` | PREPARE_GENOME_INDICES | `data`, `format: bowtie_base_index` (directory subclass; not displayed in upload UI by default — document), optional | `BOWTIE2_BUILD` | Workflow-tier build step when absent (per-sample `ALIGN_BOWTIE2` fan-out) |
| `bbsplit_index` | PREPARE_GENOME_INDICES | `data`/`directory` (no BBMap datatype in vendored table), optional | `BBMAP_BBSPLIT` (from `bbsplit_fasta_list`) | Workflow-tier build step when absent, gated on BBSplit being enabled |
| `sortmerna_index` | PREPARE_GENOME_INDICES, RNASEQ | `data`/`directory`, optional | `SORTMERNA_INDEX` (from rRNA FASTAs) | Workflow-tier build step when absent, gated on `remove_ribo_rna` |
| `bowtie2_rrna_index` | PREPARE_GENOME_INDICES, RNASEQ | `data`, `format: bowtie_base_index`, optional | `BOWTIE2_BUILD` (from rRNA FASTAs) | Workflow-tier build step when absent, gated on `remove_ribo_rna` + `ribo_removal_tool == 'bowtie2'` |

### Multi-DB pick-list (QC / filtering databases — not rebuildable)

| Param | Asset kind | Used by | Gating condition | Galaxy input (v1) | Rebuild on absence |
|---|---|---|---|---|---|
| `kraken_db` | database (`path`: dir or `.tar.gz`) | PREPARE_GENOME_REFERENCES (calls `UNTAR_KRAKEN_DB`), RNASEQ | `contaminant_screening` ∈ {`kraken2`, `kraken2_bracken`} | `data`/`directory`, optional; **required-when-conditional** | **None** — cannot be rebuilt; explicit user input |
| `sylph_db` | database (`file-path`, comma-separated list) | RNASEQ | `contaminant_screening == sylph` | `data` (or `list` collection), optional; required-when-conditional | None — explicit user input |
| `sylph_taxonomy` | other (`file-path`, comma-separated list) | RNASEQ | `contaminant_screening == sylph` | `data` (or `list` collection), optional; required-when-conditional | None — explicit user input |
| `ribo_database_manifest` | other (`file-path`) | PREPARE_GENOME_REFERENCES | `remove_ribo_rna` (default manifest `${projectDir}/assets/rrna-db-defaults.txt`) | **Translation hazard**: a text file of local filesystem paths to rRNA FASTAs. Paths inside a user-uploaded manifest do not resolve on a stock Galaxy. Recommend replacing with an optional `list` collection of `fasta` datasets fed to the SortMeRNA index build; the source default manifest has no portable Galaxy equivalent | SortMeRNA index is rebuilt from the manifest FASTAs (`SORTMERNA_INDEX`) — **rebuild-unverified** |
| `bbsplit_fasta_list` | other (`file-path`, comma-separated genome list) | PREPARE_GENOME_INDICES | `skip_bbsplit` false | Same hazard/shape as `ribo_database_manifest`: recommend `list` collection of `fasta` datasets instead of a path-list file | `BBMAP_BBSPLIT` builds the BBSplit index from it — **rebuild-unverified** |

### Curated selector cross-check (nextflow-params-to-galaxy-inputs, loaded on demand)

These reference-*adjacent* params are closed enums / mode switches, not data-bearing
paths, and must NOT become data tables or `data` inputs in the interface Mold:

- `aligner` — enum {`star_salmon`, `star_rsem`, `hisat2`, `bowtie2_salmon`}, default
  `star_salmon`. Gates which pre-built index branch is consumed.
- `pseudo_aligner` — enum {`salmon`, `kallisto`}. Gates the pseudo-alignment index branch.
- `ribo_removal_tool` — enum {`sortmerna`, `ribodetector`, `bowtie2`}.
- `contaminant_screening` — enum {`kraken2`, `kraken2_bracken`, `sylph`}.

Each is a workflow-shape control (keep as Galaxy scalar `string` with `restrictions`);
none introduces a data table. `igenomes_base` / `igenomes_ignore` / `arm` are hidden
CLI-plumbing params and are excluded outright.

## Requiredness

- The summary marks **every** reference asset `required: false`, and no
  `workflow.channels[].required_runtime` or `workflow.conditionals[]` entry encodes a
  reference-data gate (the single recorded conditional, `!params.skip_alignment &&
  !params.bam_csi_index`, gates `checkMaxContigSize` only). The source's imperative
  "provide `--genome` or `--fasta` + `--gtf`/`--gff`" launch check is **not represented**
  in the summary.
- **Carried assumption (unverifiable from the summary)**: the effective required core is
  FASTA + (GTF or GFF) for alignment-based runs, and a transcript source
  (transcriptome FASTA or GTF/GFF) for pseudo-alignment-only runs. The interface Mold
  should treat `fasta` + `gtf`/`gff` as the practically-required pair (with the
  GTF/GFF-or-key alternatives handled as documented optionality), not expose 7 equally
  optional inputs with no guidance.
- Branch-conditional requiredness (the multi-DB pick-list): `kraken_db`, `sylph_db`,
  `sylph_taxonomy`, and the rRNA-removal assets are required **only** when their gating
  enum/flag selects that branch. Galaxy's required-when-conditional affordance is weak —
  surface as optional `data` inputs with descriptions stating the gating condition
  (noted as a known representation gap).

## Rebuild-on-absence behavior

Source behavior (summary-corroborated, detector-unverified): for each pre-built index,
the positive-form branch either unpacks the supplied tarball/directory
(`UNTAR_*_INDEX`) or builds from the FASTA-derived references when `fasta_provided`
(`STAR_GENOMEGENERATE`, `HISAT2_BUILD`, `SALMON_INDEX`, `KALLISTO_INDEX`,
`BOWTIE2_BUILD`, `RSEM_PREPAREREFERENCE_GENOME`, `SORTMERNA_INDEX`, `BBMAP_BBSPLIT`).
Derived annotation assets (`gene_bed`, `transcript_fasta`, `splicesites`, `.fai` via
`SAMTOOLS_FAIDX`) are likewise rebuilt from GTF/GFF/FASTA when absent.
**All of these carry the `rebuild-unverified` flag** because `reference_rebuilds[]` is
empty for this pipeline's idiom (known detector gap, galaxyproject/foundry#229).

### Rebuild placement: recommended deviation from the default in-tool posture

The mapping note's default is *in-tool rebuild* (wrapper rebuilds the index when
absent), deviating to a workflow-tier build step only when an index is rebuilt more
than ~3 times. **This pipeline is the deviation case for its heavy indexes:**

- In the source, each index is built **once** in `PREPARE_GENOME_INDICES` and fanned out
  to per-sample alignment/quantification (`ALIGN_STAR`, `FASTQ_ALIGN_HISAT2`,
  `ALIGN_BOWTIE2`, `QUANTIFY_*` over the samplesheet channel).
- A Galaxy translation that relies on in-tool rebuild with a per-sample map-over would
  rebuild the index **once per sample** (each collection element is a separate job), far
  above the ~3 threshold. For STAR genome generation this is hours per sample.
- Recommendation: keep the v1 default (in-tool rebuild) for the cheap derived assets
  (`.fai`, `gene_bed`, `splicesites`, `transcript_fasta`) where a consumer wrapper can
  regenerate them per job at modest cost, but give the heavy aligner/pseudo-aligner
  indexes (`star`, `hisat2`, `salmon`, `kallisto`, `bowtie2`, `rsem`, `bbsplit`,
  `sortmerna`, `bowtie2_rrna`) an **optional explicit `data` input plus a single
  workflow-tier build-on-absence step**, mirroring the source's own
  `PREPARE_GENOME_INDICES` structure. This also preserves the source's index-sharing
  property across samples.
- Caveat carried forward: wrapper "no index supplied → build one" capability is
  **unverified** for every specific tool the data-flow Mold will select (known gap in
  the mapping note until wrapper rebuild capability discovery exists). The template Mold
  must not silently assume it.

## iGenomes key disposition

- The source exposes a genome key: `params.genome` ("Name of a `params.genomes`
  catalogue entry (iGenomes or a user-defined catalogue)"), with hidden
  `igenomes_base` (default `s3://ngi-igenomes/igenomes/`) and `igenomes_ignore`.
- **The summary carries no `getGenomeAttribute`-derived params** (no `params[]` entry
  with `source_kind: "getGenomeAttribute"`, no `source_path` under `conf/`). The
  key-expansion machinery exists in the source per the key params' descriptions, but
  the resolved per-asset paths never surface in `params[]` for this pipeline — the
  classifier's detection signal for a full key-expanded bundle is absent. This brief
  therefore treats the bundle as *key-addressed but not key-expanded in the summary*,
  and flags the discrepancy rather than re-parsing `conf/igenomes.config`.
- **Galaxy disposition (v1)**: the key is **not carried** into the Galaxy interface.
  There is no Galaxy data table to key into (v1 posture forbids new `.loc` tables and
  `dbkey`-keyed caches), and the iGenomes S3 base is not a user-uploadable dataset on a
  stock Galaxy. The Galaxy workflow surface starts at the **resolved per-asset paths**
  (the explicit optional `data` inputs above), exactly as the mapping note prescribes
  for key-expanded bundles. Consequence recorded as an open obligation: the one-flag
  `--genome GATK.GRCh38` convenience is lost; a user must supply FASTA + annotation
  (+ indexes, or accept rebuild) explicitly.

## Open questions

1. **iGenomes key** (open obligation, ledger `igenomes-key-no-galaxy-data-table`): no
   Galaxy data table exists for the genome key under the v1 no-tables posture; the key
   is dropped from the interface and per-asset paths become the surface. Downstream
   Molds must not reintroduce a data table or an S3-path string input.
2. **Rebuild verification** (ledger `rebuild-unverified-positive-form`): the summary's
   `reference_rebuilds[]` is empty due to the known positive-form detector gap; every
   rebuild claim above rests on call-graph corroboration only. Any Galaxy step that
   assumes a rebuild branch must verify the wrapper actually supports it.
3. **Bundle UX**: the coordinated bundle surfaces ≥7 coupled optional inputs; the
   mapping note admits no worked Galaxy exemplar for bundles this size
   (`sample_sheet:record` is suggested but unexemplified for reference data). v1 keeps
   N separate optional `data` inputs; the translation strain is accepted and flagged.
4. **Path-list files** (ledger `path-list-inputs-not-portable`): `ribo_database_manifest`
   and `bbsplit_fasta_list` are files whose *contents* are local filesystem paths.
   They cannot be uploaded to a stock Galaxy and resolve. Recommended translation is a
   `list` collection of FASTA datasets; the data-flow Mold must decide the concrete
   wiring, and the source default manifest (`assets/rrna-db-defaults.txt`) has no
   portable equivalent (its loss changes default behavior when `remove_ribo_rna` is
   enabled without user rRNA data).
5. **Conditional requiredness**: `kraken_db` / `sylph_db` / `sylph_taxonomy` /
   rRNA-removal assets are required only under their gating enum/flag; Galaxy's
   required-when-conditional affordance is weak, so they surface as optional inputs
   with documented gating. Validation loss, recorded.
6. **Curated-inventory false positive**: `pipelines_testdata_base_path` appears in
   `reference_assets[]` (confidence medium, `used_by: []`) but is a hidden CLI-plumbing
   param. Excluded here; noting for the summary producer.
7. **Effective requiredness of the FASTA+GTF core** is an assumption (see
   *Requiredness*) — the launch-time gate is not encoded in the summary.
