# Galaxy interface brief — nf-core/oncoanalyser 3.0.0 (WGTS, core DNA spine)

Inputs read: `summary-nextflow.json` (primary workflow `WGTS`), `nextflow-galaxy-reference-data.md`, `open-requirements.ledger.yml`. Galaxy target: test.galaxyproject.org (27.0.dev0).

## 0. Scope (user decision, 2026-11-11)

**Core DNA somatic spine, matched tumor/normal, one subject per invocation:**

`READ_ALIGNMENT_DNA` (bwa-mem2) → `REDUX_PROCESSING` → `AMBER_PROFILING`, `COBALT_PROFILING`, `SAGE_CALLING` (somatic + germline), `ESVEE_CALLING` → `PAVE_ANNOTATION` (somatic + germline) → `PURPLE_CALLING` → `LINX_ANNOTATION` (somatic + germline).

Everything else in WGTS is recorded as `kind: dropped` in the ledger (§5). Evidence that drove the cut, checked 2026-11-11:
- None of the ~25 hmftools are installed on test.galaxyproject.org (`GET /api/tools?q=<tool>`).
- None are in the main Tool Shed (`/api/repositories?q=hmftools|purple|esvee|gridss|virusbreakend` → no hits).
- Each kept hmftools stage therefore needs a user-defined tool. The account can list them: `GET /api/unprivileged_tools` → 200.

Testing decision: test plan and fixtures are designed, but the Galaxy test run is not executed. References are ~59 GB against a 10.7 GB quota.

## 1. Workflow inputs

### Sample data

The source samplesheet is long format, one row per file, regrouped per `group_id` by `Utils.parseInput`. A Galaxy `sample_sheet*` collection doesn't fit cleanly:
- `sample_sheet` must be outermost and has no cross-row tumor↔normal pairing expression.
- Within one group, tumor and normal are different roles, not repeated rows of one shape.

**Decision:** one subject per invocation, with tumor and normal as two parallel collections. This follows the channel-shape rule for heterogeneous tuples (parallel inputs). Confidence: medium-high.

| Label | type | collection_type / format | optional | Source evidence | Notes |
|---|---|---|---|---|---|
| `tumor_dna_reads` | collection | `list:paired`, elements `fastqsanger.gz` | no | samplesheet rows `sample_type=tumor, sequence_type=dna, filetype=fastq`; `filepath` = `R1;R2`; `info` = `library_id:<id>;lane:<n>` | one element per library/lane; identifier `<library_id>_<lane>` (test: `library_1_001`). REDUX merges lanes |
| `normal_dna_reads` | collection | `list:paired`, elements `fastqsanger.gz` | no | rows `sample_type=normal, sequence_type=dna, filetype=fastq` | same identifier rule |
| `tumor_sample_id` | string | — | no | samplesheet `sample_id` (tumor row); hmftools `-tumor` name and output-file prefix | test: `subject_a.tumor`; regex `^\S+$` |
| `normal_sample_id` | string | — | no | `sample_id` (normal row); hmftools `-reference` name | test: `subject_a.normal`; regex `^\S+$` |

`group_id` and `subject_id` are not carried. With one subject per invocation they only label output directories (`subject_a/…`). Galaxy history and invocation naming covers that.

### Reference data (from the reference-data brief, restricted to the spine)

| Label | type | format | optional | NF param | Consumers in scope |
|---|---|---|---|---|---|
| `reference_genome` | data | `fasta` | no | `ref_data_genome_fasta` | bwa-mem2, REDUX, AMBER, COBALT, SAGE, ESVEE, PAVE, PURPLE |
| `reference_genome_fai` | data | `fai` | yes; built once by a workflow-tier `samtools faidx` step when absent | `ref_data_genome_fai` | REDUX, AMBER, COBALT, SAGE, ESVEE, PAVE, PURPLE |
| `reference_genome_dict` | data | `data` (sequence dictionary; verify the extension on the target) | yes; built once by a workflow-tier step when absent | `ref_data_genome_dict` | REDUX, SAGE, ESVEE, PURPLE |
| `reference_genome_bwa_img` | data | `data` | **no**: ESVEE declares `path genome_img` and no Galaxy builder exists | `ref_data_genome_img` | ESVEE |
| `hmf_pipeline_resources` | data | `tar` (fallback `data`) | no | `ref_data_hmf_data_path` | every hmftools step (member extraction by HMF relative path) |
| `driver_gene_panel` | data | `tabular` | yes; defaults to `common/DriverGenePanel.38.tsv` in the bundle | `driver_gene_panel` | SAGE, PAVE, PURPLE, LINX |

`ref_data_genome_bwamem2_index` is **not exposed**. The installed bwa-mem2 wrapper (`toolshed.g2.bx.psu.edu/repos/iuc/bwa_mem2/bwa_mem2/2.3+galaxy1`) indexes a history FASTA in-tool (per the reference brief). A pre-built bwa-mem2 index input is a v2 / server-cache concern, so it is recorded as dropped. Confidence: medium until phase 7 confirms the wrapper's reference-source options.

### Scalar parameters

| Label | type | default | optional | NF param | Reason kept |
|---|---|---|---|---|---|
| `genome_version` | string, restrictions `["38","37"]` | `38` | no | derived `genome_version` (from `genome` key) | passed as `-ref_genome_version` to every hmftools step; selects HMF bundle member names (`*.38.*`) |
| `sequencing_platform` | string, restrictions `["illumina","sbx","ultima"]` | `illumina` | no | `sequencing_platform` (nextflow_schema enum; default null → treated as illumina by WorkflowMain) | selects the PON members (`Utils.getSequencingPlatformPons`) and REDUX/SAGE platform args |
| `purple_min_purity` | float | — | yes | `withName: 'PURPLE' ext.args` in `conf/test.config` | test profile forces `-min_purity 1 -max_purity 1 -min_ploidy 2 -max_ploidy 2`; without these the Galaxy test can't reproduce source outputs |
| `purple_max_purity` | float | — | yes | same | same |
| `purple_min_ploidy` | float | — | yes | same | same |
| `purple_max_ploidy` | float | — | yes | same | same |

## 2. Workflow outputs (public labels)

hmftools write whole output directories, which are the inter-step currency in the source (`topic: amber_dir` etc.). Galaxy has no stable directory dataset passable between user-defined tools. **Decision:** each hmftools step emits its directory as one archive output (`tar`, fallback `data`) plus the specific files below as first-class datasets. The archives feed downstream steps; the named files are the user/test surface. The data-flow brief owns the archive mechanics.

| Label | format | Producer | Source file (snapshot `tests/profile_test.nf.test.snap`) | Role |
|---|---|---|---|---|
| `tumor_redux_bam` | `bam` | REDUX | `alignments/<tumor>/<tumor>.redux.bam` | user output |
| `normal_redux_bam` | `bam` | REDUX | `alignments/<normal>/<normal>.redux.bam` | user output |
| `tumor_redux_duplicate_freq` | `tabular` | REDUX | `<tumor>.redux.duplicate_freq.tsv` (md5-stable in snapshot) | **checkpoint** |
| `tumor_redux_dir` / `normal_redux_dir` | `tar` | REDUX | jitter/ms tables needed by SAGE | inter-step |
| `amber_dir` | `tar` | AMBER | `amber/` | inter-step + user |
| `amber_qc` | `txt` | AMBER | `<tumor>.amber.qc` | **checkpoint** |
| `cobalt_dir` | `tar` | COBALT | `cobalt/` | inter-step + user |
| `esvee_dir` | `tar` | ESVEE | `esvee/` | inter-step |
| `esvee_somatic_vcf` | `vcf_bgzip` | ESVEE | `<tumor>.esvee.somatic.vcf.gz` | user output |
| `sage_somatic_vcf` | `vcf_bgzip` | SAGE somatic | `sage/somatic/<tumor>.sage.somatic.vcf.gz` | user output |
| `sage_germline_vcf` | `vcf_bgzip` | SAGE germline | `sage/germline/<tumor>.sage.germline.vcf.gz` | user output |
| `pave_somatic_vcf` | `vcf_bgzip` | PAVE somatic | `pave/somatic/<tumor>.pave.somatic.vcf.gz` | inter-step + user |
| `pave_germline_vcf` | `vcf_bgzip` | PAVE germline | `pave/germline/<tumor>.pave.germline.vcf.gz` | inter-step + user |
| `purple_dir` | `tar` | PURPLE | `purple/` | inter-step (LINX) + user |
| `purple_purity` | `tabular` | PURPLE | `<tumor>.purple.purity.tsv` | **checkpoint** (purity = 1, ploidy = 2 under test args) |
| `purple_qc` | `txt` | PURPLE | `<tumor>.purple.qc` | **checkpoint** (QCStatus) |
| `purple_somatic_vcf` | `vcf_bgzip` | PURPLE | `<tumor>.purple.somatic.vcf.gz` | user output |
| `purple_germline_vcf` | `vcf_bgzip` | PURPLE | `<tumor>.purple.germline.vcf.gz` | user output |
| `purple_sv_vcf` | `vcf_bgzip` | PURPLE | `<tumor>.purple.sv.vcf.gz` | user output |
| `purple_cnv_somatic` | `tabular` | PURPLE | `<tumor>.purple.cnv.somatic.tsv` | user output |
| `purple_driver_catalog_somatic` | `tabular` | PURPLE | `<tumor>.purple.driver.catalog.somatic.tsv` | **checkpoint** |
| `linx_somatic_dir` | `tar` | LINX somatic | `linx/somatic_annotations/` | user output |
| `linx_driver_catalog` | `tabular` | LINX somatic | `<tumor>.linx.driver.catalog.tsv` | **checkpoint** |
| `linx_fusions` | `tabular` | LINX somatic | `<tumor>.linx.fusion.tsv` | user output |
| `linx_svs` | `tabular` | LINX somatic | `<tumor>.linx.svs.tsv` | user output |
| `linx_germline_driver_catalog` | `tabular` | LINX germline | `<tumor>.linx.germline.driver.catalog.tsv` | user output |

Datatype confidence: `vcf_bgzip`, `bam`, `tabular` are high (built-in). `tar` is medium (verify on the target; fallback `data`). `.qc` files are key=value text, so `txt` is medium.

## 3. Excluded params (consolidated warning)

| Class | Params | Assessment |
|---|---|---|
| Publish / output | `outdir`, `publish_dir_mode` | safe |
| Notification | `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | safe |
| Runtime UX / CLI | `monochrome_logs`, `validate_params`, `help`, `help_full`, `show_hidden`, `version`, `trace_report_suffix`, `hmftools_log_level` | safe |
| Profile / institutional | `config_profile_*`, `custom_config_*`, `pipelines_testdata_base_path` | safe |
| Stub plumbing | `create_stub_placeholders` | safe (stub-only) |
| Reference key / location | `genome`, `force_genome`, `ref_data_*_base`, `igenomes_*`, `genome_type`, `ref_data_types`, `prepare_reference_only` | dropped in the reference brief (ledger `genome-key-plumbing-not-exposed`) |
| Performance | `max_fastq_records` (fastp chunking before bwa-mem2) | safe: chunking doesn't change alignments; data-flow may drop the split |
| Stage selection | `processes_manual`, `processes_include`, `processes_exclude` | **problematic**: they gate which stages run. Fixed at the spine design; recorded as dropped |
| Run mode | `mode`, `purity_estimate_mode`, `panel`, `force_panel` | **problematic**: they select a whole workflow. Fixed to `wgts`; recorded as dropped |
| UMI | `umi_type`, `fastp_umi_*`, `fastq_tools_umi_*`, `redux_umi_*` | **problematic**: they change REDUX duplicate handling. Fixed to the default (UMIs off); recorded as dropped |
| RNA / other stages | `isofox_*`, `gridss_config`, `enable_cn_norm_with_wgs_pct`, `target_regions_bed` | out of scope (dropped stages) |
| Reports | `multiqc_title`, `multiqc_config`, `multiqc_logo`, `multiqc_methods_description` | MultiQC is dropped from scope |

## 4. Testability

- The selected source test is `tests/profile_test.nf.test::-profile test`. Fixtures: tumor/normal DNA FASTQ pairs at `nf-core/test-datasets` `oncoanalyser/sample_data/simulated_reads/wgts/fastq/single_lane_single_library/`. These map 1:1 onto `tumor_dna_reads` / `normal_dna_reads` (one element `library_1_001` each). `tumor_sample_id=subject_a.tumor`, `normal_sample_id=subject_a.normal`.
- Checkpoints: `purple_purity` (purity and ploidy fixed by the test args → value assertions), `purple_qc` (QC status line), `amber_qc`, `tumor_redux_duplicate_freq` (snapshot md5), `purple_driver_catalog_somatic` and `linx_driver_catalog` (header + content checks).
- The test can't run on the target: references need ~59 GB (ledger `reference-data-not-test-scale`). Phases 12–13 are recorded as not run.

## 5. Open questions (carried in the ledger)

1. Can this account *create* (not only list) user-defined tools on test.galaxyproject.org? Verified in phase 7.
2. Is `tar` registered as a datatype on the target? If not, use `data` with descriptions for every archive input and output.
3. Are the hmftools bioconda/biocontainer images (e.g. `biocontainers/hmftools-purple:<ver>`) allowed as UDT containers on the target?
