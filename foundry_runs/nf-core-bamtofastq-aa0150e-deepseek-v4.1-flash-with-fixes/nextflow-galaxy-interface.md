# Interface brief — nf-core/bamtofastq → Galaxy

Source: `nf-core/bamtofastq` @ `aa0150e`.
Inputs read: `summary-nextflow.json`, `nextflow-galaxy-reference-data.md`,
`open-requirements.ledger.yml`.
Mold: `nextflow-summary-to-galaxy-interface`.

## 1. Source interface (evidence)

| Source surface | Evidence |
|---|---|
| `--input` samplesheet | `sample_sheets[0]`, `nf-schema`, `assets/schema_input.json`; columns `sample_id` (meta `id`), `mapped` (file-path, `.bam|.cram`, required), `index` (file-path, `.bai|.crai`, optional), `file_type` (meta `filetype`, enum bam/cram, required) |
| `--fasta`, `--fasta_fai` | `reference_assets[]`; optional; CRAM only (see reference-data brief) |
| `--chr` | `workflow.conditionals[]` guard `params.chr`, affects `SAMTOOLS_CHR`, `SAMTOOLS_CHR_INDEX` |
| `--no_read_QC` | conditional `!params.no_read_QC`, affects `FASTQC_PRE_CONVERSION`, `FASTQC_POST_CONVERSION` |
| `--no_stats` | conditional `!params.no_stats`, affects `SAMTOOLS_FLAGSTAT`, `SAMTOOLS_IDXSTATS`, `SAMTOOLS_STATS` |
| `--samtools_collate_fast`, `--reads_in_memory` | `resolved_args` on `COLLATE_FASTQ_MAP` / `COLLATE_FASTQ_UNMAP` / `SAMTOOLS_COLLATEFASTQ_SINGLE_END` (`-f -r <n>`) |
| `--multiqc_config`, `--multiqc_title`, `--multiqc_logo`, `--multiqc_methods_description` | `MULTIQC` inputs / `resolved_args` |
| workflow emit | `multiqc_report` only; the converted FASTQs, FastQC reports, samtools stats and `fastqutils` `.txt` files are published by `publishDir` but not emitted |

## 2. Galaxy workflow inputs

| Galaxy input id | Type | `collection_type` / `format` | Required | Source param | Confidence | Basis / notes |
|---|---|---|---|---|---|---|
| `input` | collection | `list` (no `format`; elements are `bam` or `cram`) | required | `params.input` (`mapped` column) | high for required; medium for shape | Every row carries exactly one alignment. Element identifier = `sample_id` |
| `fasta` | data | `fasta` | optional | `params.fasta` | high | only needed for CRAM inputs |
| `fasta_fai` | data | `fai` | optional | `params.fasta_fai` | high | index of `fasta`; rebuilt in-tool when absent |
| `chr` | string | — | optional | `params.chr` | high | space/`-`/`:`-separated region list consumed by `samtools view`; gate on non-empty |
| `no_read_QC` | boolean | — | optional, default `false` | `params.no_read_QC` | high | skips both FastQC steps |
| `no_stats` | boolean | — | optional, default `false` | `params.no_stats` | high | skips flagstat/idxstats/stats |
| `samtools_collate_fast` | boolean | — | optional, default `false` | `params.samtools_collate_fast` | high | passes `-f -r 100000` to `samtools collate` |
| `multiqc_config` | data | `yaml` | optional | `params.multiqc_config` | medium | data input, not a data table |
| `multiqc_title` | string | — | optional | `params.multiqc_title` | high | `MULTIQC` `ext.args` |

### Why a plain `list`, not a `sample_sheet`

The samplesheet's four columns map to Galaxy as follows: `mapped` → the collection
element; `sample_id` → the element identifier; `file_type` → **the element's own
datatype** (`bam` / `cram`), which Galaxy already knows; `index` → not exposed (see
decision `index-rebuilt-in-workflow`). The only metadata a *tool* would need is nothing —
`meta` reaches workflow-level branches only. A `sample_sheet:record` would add typed
columns that no mapped tool reads, and gxformat2 workflow inputs declare
`column_definitions` (scalars) but no named dataset slots for a `record`, so the
`mapped`/`index` slots cannot be declared on the input. A `list` with an
identifier-carrying element name is the faithful, testable shape.

### Excluded params (recorded for review)

| Source param | Class | Effect if omitted | Assessment |
|---|---|---|---|
| `outdir`, `publish_dir_mode` | publish | none — Galaxy owns histories | safe |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | notification | none | safe |
| `trace_report_suffix`, `monochrome_logs`, `validate_params`, `version`, `help`, `help_full`, `show_hidden` | runtime UX / CLI | none | safe |
| `config_profile_name`, `config_profile_description`, `config_profile_contact`, `config_profile_url`, `custom_config_*`, `pipelines_testdata_base_path` | site config | none | safe |
| `igenomes_base`, `igenomes_ignore` | reference plumbing | none — no iGenomes key is exposed | safe |
| `genome` | reference selector | none — user supplies `fasta`/`fasta_fai` directly | safe (decision `no-igenomes-key`) |
| `multiqc_logo` | report styling | no logo in the report | safe |
| `multiqc_methods_description` | report text | default methods text is used | safe |
| `reads_in_memory` | performance | fixed at the source default 100000 | safe (decision `fix-reads-in-memory`) |
| `no_read_QC`, `no_stats` spelling | — | kept, including the capital `QC` | — |

## 3. Galaxy workflow outputs

| Galaxy output id | Type | `collection_type` / `format` | Source of truth | Purpose |
|---|---|---|---|---|
| `reads_paired` | collection | `list:paired`, `fastqsanger.gz` | `CAT_FASTQ.out.reads` (`*_1.merged.fastq.gz`, `*_2.merged.fastq.gz`) | **primary product**; the nf-test snapshot pins md5 for these files |
| `reads_single` | collection | `list`, `fastqsanger.gz` | `SAMTOOLS_COLLATEFASTQ_SINGLE_END.out.fastq_other` (`*_other.fq.gz`) | single-end product (source renames the emitted channel to `fastq_other`) |
| `fastqc_pre_conversion` | collection | `list`, `html` | `FASTQC_PRE_CONVERSION.out.html` | published QC, not consumed; BAM inputs only |
| `fastqc_post_conversion` | collection | `list`, `html` | `FASTQC_POST_CONVERSION.out.html` | post-conversion QC |
| `fastqutils_info` | collection | `list`, `txt` | `FASTQUTILS_INFO.out.info` | conversion sanity check |
| `samtools_flagstat` | collection | `list`, `txt` | `SAMTOOLS_FLAGSTAT.out.flagstat` | pre-conversion QC (fastqsanger-free content) |
| `samtools_idxstats` | collection | `list`, `txt` | `SAMTOOLS_IDXSTATS.out.idxstats` | pre-conversion QC |
| `samtools_stats` | collection | `list`, `txt` | `SAMTOOLS_STATS.out.stats` | pre-conversion QC |
| `multiqc_report` | data | `html` | `MULTIQC.out.report` | the source's only `emit:` |

`fastqc_post_conversion` is `list` even for paired samples: `FASTQC_POST_CONVERSION` maps
over the mixed `ch_reads_post_qc` channel, whose element shapes differ between the single
and paired branches. Exposing it as `list` (one report set per sample) loses element
pairing, which is recorded as an open requirement.

`samtools_*` outputs are `txt` at **low** datatype confidence (the source writes plain text
with a `.flagstat`/`.idxstats`/`.stats` extension; no Galaxy extension is registered for
those).

## 4. Labels and test addresses

- Input ids are the public test `job:` keys: `input`, `fasta`, `fasta_fai`, `chr`,
  `no_read_QC`, `no_stats`, `samtools_collate_fast`, `multiqc_config`, `multiqc_title`.
- Output ids are the public test `outputs:` keys. Element addresses follow the collection
  shape: `reads_paired/test/forward`, `reads_paired/test/reverse`, `reads_paired/test2/...`
  for the selected `-profile test` fixture (sample ids `test`, `test2`).
- `reads_paired` is the checkpoint to assert: the nf-test snapshot carries md5 sums for
  `test_1.merged.fastq.gz` (`9b0c08862a5e47e842a485ddad31b871`),
  `test_2.merged.fastq.gz` (`40e17982d1231e561d6420234ae29357`),
  `test2_1.merged.fastq.gz` (`a4984fb5a60f80ccbfbfcf1cef9daaf3`),
  `test2_2.merged.fastq.gz` (`bde23801e2d60604afb3bd0b0ab014ab`).

## 5. Structural obligations this interface creates

1. **Per-element single/paired routing.** `CHECKPAIREDEND` decides per sample, then the
   sample takes one of two different subgraphs. Galaxy has no plain per-element branch;
   the documented route is a per-element boolean dataset (`paired.txt`) →
   `param_value_from_file` → `when`-gated branches → `pick_value` rejoin. Logged on the
   open-requirements ledger.
2. **Mixed BAM/CRAM input.** `file_type` is derived from the element datatype; the
   pre-conversion FastQC branch and the CRAM `--reference` branch must filter on that
   datatype (`__APPLY_RULES__` filter by `ext`), not on a metadata column.
3. **Empty reference.** `fasta` is optional, but a CRAM element without one cannot be
   decoded. Documented on the input; not enforceable structurally.
4. **`chr` subsetting** adds `SAMTOOLS_VIEW` + `SAMTOOLS_INDEX` steps and renames element
   identifiers to the subset file's basename in the source. The Galaxy counterpart must
   decide whether to keep the original element identifier (preferred) instead of mimicking
   the basename rename.

## 6. Amendment from the data-flow phase

A required `layout` select input (`paired` | `single`, default `paired`) was added; it gates
the two conversion subgraphs. See `nextflow-galaxy-data-flow.md` §0 and the ledger entry
`checkpairedend-auto-detection-dropped`. The per-sample `CHECKPAIREDEND` detection is dropped.
