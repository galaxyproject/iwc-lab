# Galaxy workflow interface brief — nf-core/bamtofastq

*Source: summary-nextflow.json @ aa0150e; reference-data brief (same run). Written 2026-11-09 23:44 local (via date).*

## Workflow inputs

| # | Galaxy input | gxformat2 type | Collection shape / format | Required | Source evidence | Confidence |
|---|---|---|---|---|---|---|
| 1 | `Input samplesheet` | `collection` | `sample_sheet:paired_or_unpaired` (see below) | **true** | `params.input` required in schema_input.json; `samplesheetToList` materialization; columns: `sample_id` (meta, required, pattern \S+), `mapped` (data, required, bam\|cram), `index` (data, optional, bai\|crai), `file_type` (meta, enum bam\|cram, required) | High (nf-schema + samplesheetToList) |
| 2 | `Fasta reference` | `data` | `format: fasta`, `optional: true` | false | reference-data brief: single-asset FASTA; needed only for CRAM rows | High |
| 3 | `Fasta index` | `data` | `format: fai`, `optional: true` | false | reference-data brief: compute-if-missing via samtools faidx, in-tool rebuild posture | Medium (wrapper rebuild unverified) |

### Sample-sheet variant decision

The samplesheet has one **data column per row (`mapped`) plus an optional index data column**. The Nextflow pipeline itself branches single-end vs paired-end *per alignment file*, not per fastq pair: CHECKPAIREDEND inspects the BAM/CRAM's paired flags, and downstream samtools collatefastq produces R1/R2 or other/singletons accordingly. The alignment file is the atomic per-row dataset — there is no R1/R2 pairing in the *input* (unlike rnaseq's fastq_1/fastq_2).

- Inner shape: the alignment + its index travel together per row → this is a **record-like pairing of dataset + sidecar**, not a paired fastq.
- Because `index` is optional (tests/no_bai, no_crai exercise missing indexes) and `mapped` is always present, the closest variant is `sample_sheet` (one dataset per row) with the index either dropped or carried as a second data slot.
- **Decision: `sample_sheet:paired_or_unpaired`.** Justification: the *conversion outputs* split paired vs single-end per row (meta.single_end set by CHECKPAIREDEND), and the pipeline's own test matrix covers both; a homogeneous `sample_sheet` cannot express the optional-index sidecar, and `sample_sheet:record` blocks implicit mapping. `paired_or_unpaired` gives the inner subcollection slot where the alignment (+index) rides per row while keeping per-row metadata (`sample_id`, `file_type`) as column values on the collection. This mirrors what the demo translation validated: Galaxy's `paired_or_unpaired` accepts rows that are paired subcollections OR singleton datasets.
- **Unresolved carried to the data-flow/template tier** (open-requirements: `sample-sheet-index-column-representation`): how to carry the optional `index` file per row. Options: (a) drop the index input and rely on in-tool index building (matching v1 in-tool-rebuild posture — samtools tools build indexes when absent); (b) require it as a paired slot. Option (a) is the v1-consistent default; the reference-data brief already flags wrapper rebuild verification as the gate.
- `column_definitions`: `sample_id` (string, required, regex `^\S+$`), `file_type` (string, required, restrictions [bam, cram]). The mapped/index files become the element datasets.

### Dropped params (exclusion list)

| Param | Class | Effect | Assessment | Reason |
|---|---|---|---|---|
| `outdir` | publish | output location | safe | Galaxy owns histories/outputs |
| `publish_dir_mode` | publish | copy mode | safe | ditto |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | notification | completion email | safe | runtime reporting |
| `monochrome_logs`, `trace_report_suffix`, `validate_params`, `help`, `help_full`, `show_hidden`, `version` | runtime UX / CLI plumbing | none scientific | safe | execution UX |
| `custom_config_*`, `config_profile_*`, `pipelines_testdata_base_path` | site config | profiles | safe | environment config |
| `multiqc_title`, `multiqc_logo`, `multiqc_methods_description` | report customization | MultiQC decoration | safe | cosmetic; MultiQC still runs with default config |
| `multiqc_config` | report config | changes MultiQC sections | **safe-exclude with note**: could be kept as an optional data input if the target wants custom configs; default translation uses the pipeline's own assets/multiqc_config.yml semantics via the MultiQC wrapper's built-in config handling | recorded |
| `genome`, `igenomes_base`, `igenomes_ignore` | reference selector | iGenomes key expansion | safe (dropped per reference-data brief) | no data-table posture; user uploads FASTA directly |
| `multiqc_email_size` (artifact of my summary emit) | — | — | — | not a real pipeline param; ignore |

### Kept scalar inputs (workflow-shape controls)

| Galaxy input | gxformat2 type | default | Source param | Effect |
|---|---|---|---|---|
| `Restrict to chromosome(s)` | `string`, optional | null | `chr` | gates SAMTOOLS_CHR + index branch (conditional) |
| `Skip read QC` | `boolean` | false | `no_read_QC` | gates both FASTQC aliases via ext.when |
| `Skip stats` | `boolean` | false | `no_stats` | gates flagstat/idxstats/stats via ext.when |
| `Collate fast mode` | `boolean` | false | `samtools_collate_fast` | changes collatefastq ext.args (-f -r N) |
| `Reads in memory` | `int` | 100000 | `reads_in_memory` | only meaningful with collate fast mode |

Note: nf-test names it `no_read_qc` but the schema/case-sensitive param is `no_read_QC` (Nextflow params are case-sensitive; conf/modules.config uses `params.no_read_QC`). The no_qc.nf.test sets `no_read_qc = true` — a test-bug in the source (it sets a different, unused param), which means **the no_qc test's snapshot actually still contains QC outputs**. Verification: no_qc.nf.test.snap shows fastqc/* files present in stable_names. This nuance is carried to the test-plan tier.

## Workflow outputs

| Galaxy output | Source | Shape/format | Confidence | Rationale |
|---|---|---|---|---|
| `merged_reads` | CAT_FASTQ.out.reads | list collection of `fastqsanger.gz` (one element per sample; paired samples produce _1/_2 files) | High | The pipeline's scientific product; published to `reads/` (publishDir pattern `*.fastq.gz`) |
| `unmapped_other_reads` | SAMTOOLS_COLLATEFASTQ_SINGLE_END.out.fastq_other | list collection of `fastqsanger.gz` | High | Published to `reads/` (pattern `*{other.fq.gz}`); the single-end extraction path feeds QC from this too |
| `flagstat_reports` | SAMTOOLS_FLAGSTAT.out.flagstat | list collection of `txt` | High | Published to `samtools/` |
| `idxstats_reports` | SAMTOOLS_IDXSTATS.out.idxstats | list collection of `txt` | High | Published to `samtools/` |
| `stats_reports` | SAMTOOLS_STATS.out.stats | list collection of `txt` | High | Published to `samtools/` |
| `fastqutils_reports` | FASTQUTILS_INFO.out.info | list collection of `txt` | Medium | fastqutils has no publishDir entry in modules.config, but the snapshot's stable_paths assert `fastqutils/*.txt:md5` — so these files are expected outputs with checksum evidence |
| `fastqc_reports_html` | FASTQC (both aliases).out.html | list collection of `html` | High | FastQC publishDir defaults to publish; snapshot asserts names |
| `fastqc_reports_zip` | FASTQC.out.zip | list collection of `zip` | Medium | Snapshot asserts zip presence in stable_names; sidecar |
| `multiqc_report` | MULTIQC.out.report | `html` | High | The workflow's declared emit; snapshot asserts `multiqc_report.html` |

### Checkpoint outputs for testability

The nf-test snapshot provides **expected md5 checksums** for: the 4 merged FASTQs (test_1/2, test2_1/2), the 6 samtools outputs (flagstat/idxstats/stats × 2 samples), 2 fastqutils txt, and multiqc_citations.txt. The Galaxy test plan should:
- Promote `merged_reads` elements for per-element checksum assertion (strongest check).
- Promote the three samtools report collections as checkpoint outputs (checksums available).
- Promote `fastqutils_reports` (checksums available).
- Keep `multiqc_report` as a smoke check (html size/assert) — the snapshot only checksums multiqc_citations.txt which is inside multiqc_data/, a directory output.
- `unmapped_other_reads`: for the default test (2 paired samples) the `other` bucket is non-empty per the source comment ("fastq files had empty reads" note suggests other holds the expected reads for single-end; for paired it holds leftover). The snapshot's stable_paths do NOT list reads/*other.fq.gz for the default case (only for no_bai's test3), so the default test should assert element_count of unmapped_other_reads = 2 without checksums (type/count check — logged as such per the test-quality rule).

### Element-identifier design

Samtools/CAT mapped over the samplesheet produce per-sample collections; element identifiers follow the input row identifiers (`test`, `test2`). FastQC over `ch_reads_post_qc` (mixed merged reads + other) renames per its `ext.prefix` idiom; the concrete identifier derivation is a data-flow/template concern — carried as open-requirements `fastqc-element-identifiers`.

## Open questions

1. Index sidecar representation (see above, open-requirements entry).
2. FastQC element identifiers post-mix (see above, open-requirements entry).
3. `multiqc_config` as optional data input — deferred; default translation excludes it.
4. no_qc source-test bug (case-sensitive param mismatch) — carried to test plan as a scope note.

**Ledger updates:** appended `sample-sheet-index-column-representation` and `fastqc-element-identifiers`; no entries closed (first substantive mold).
