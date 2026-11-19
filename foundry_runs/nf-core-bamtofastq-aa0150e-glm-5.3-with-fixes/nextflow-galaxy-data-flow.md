# Galaxy data-flow brief — nf-core/bamtofastq → Galaxy

Source: `summary-nextflow.json` @ aa0150e, `nextflow-galaxy-interface.md`, `nextflow-galaxy-reference-data.md`. Abstract Galaxy-facing DAG per the data-flow draft contract: no gxformat2, no Tool Shed resolution. Step granularity follows the source's own subworkflow boundaries (PREPARE_INDICES, PRE_CONVERSION_QC, the conversion paths).

## Topology overview

Per-sample work runs as map-over on the `alignments` list collection (element identifier = `sample_id`); the reference FASTA is a global broadcast input. The source's per-element `branch`/runtime endedness detection becomes per-element Galaxy `when:` gating over the conversion subgraphs, recombined into one reads collection.

## Nodes (abstract operations)

### Reference tier (from reference-data brief)

| Node | Operation | Inputs → outputs | Galaxy idiom | Confidence |
|---|---|---|---|---|
| `build_fai` | index reference FASTA (samtools faidx equivalent) | `reference_fasta` (File) → `fai` (File) | single step, mirrors PREPARE_INDICES' SAMTOOLS_FAIDX half | High |
| (precedence) | effective FAI = user-supplied `reference_fai` else `build_fai` output | two Files → one File | `pick_value` (`first_non_null`) — conditional-transform-or-pass-through pattern | Medium |
| (broadcast) | samtools consumers take the reference FASTA as an optional reference input | `reference_fasta` → each samtools step | broadcast File into mapped steps | High |

Open: whether any chosen wrapper exposes an FAI input at all; if none does, `build_fai` + `reference_fai` become vestigial and are dropped with a ledger entry (the FASTA itself remains the reference carrier). CRAM decoding needs the FASTA; BAM-only runs tolerate its absence.

### Index tier (PREPARE_INDICES alignment half)

| Node | Operation | Inputs → outputs | Galaxy idiom | Confidence |
|---|---|---|---|---|
| `ensure_alignment_index` | build bai/crai per element (samtools index) | `alignments` (list) → index list paired by identifier | map-over; always-run (source rebuilds when column absent — faithful to index-absent path; ledger: `samplesheet-index-column-dropped`) | High |
| (join) | alignment + index pairing | `alignments` + index list → consumer steps | multi-input map-over with identifier-synced index collection (join recipe: file/index pairing, High) | High |

### Pre-conversion QC tier (PRE_CONVERSION_QC)

| Node | Operation | Inputs | Outputs | Gating | Confidence |
|---|---|---|---|---|---|
| `samtools_flagstat` | alignment summary stats | alignments (+index) | `flagstat` list (tabular) | `when` on `no_stats == false` | High |
| `samtools_idxstats` | per-reference counts (needs index) | alignments + index | `idxstats` list (tabular) | same gate | High |
| `samtools_stats` | full alignment stats (+optional reference) | alignments (+index, +reference_fasta) | `stats` list (tabular) | same gate | High |
| `fastqc_pre` | FastQC on input alignments | alignments (bam elements; see open question 2) | `fastqc_pre_html`, `fastqc_pre_zip` lists | `when` on `no_read_qc == false` | Medium (cram filtering unresolved) |

### Endedness detection and routing (CHECKPAIREDEND + branch)

| Node | Operation | Inputs | Outputs | Galaxy idiom | Confidence |
|---|---|---|---|---|---|
| `check_endedness` | per sample, sample ≤1000 records, emit paired/single marker txt (samtools view -c -f 1 arithmetic) | alignments (list) | per-element marker txt (list) | map-over; abstract tool need (below) | Medium |
| `derive_is_paired` / `derive_is_single` | convert marker to per-element boolean files | marker list | two boolean-file lists | mapped comparison steps (text processing), then mapped `param_value_from_file` (`param_type: boolean`) → `boolean_param` collections | Medium — the per-element `when` recipe is verified upstream (`test_run_workflow_conditional_step_map_over_expression_tool`) |
| (gating) | per-element `when:` on every conversion-path step | boolean collections → step `when` inputs | — | per-element skip; skipped elements emit typed nulls | Medium |

Two boolean derivations (not one negated expression) avoid untested `when` negation. The single-end path's steps gate on `is_single`; the paired path's on `is_paired`.

### Region-filter branch (SAMTOOLS_CHR, gated on non-empty `chr`)

| Node | Operation | Notes |
|---|---|---|
| `samtools_chr_view` | view alignments restricted to `chr` regions (`-hb` + region args), per element; needs index | `when` gated on `chr` non-empty (mechanism pinned after exemplar comparison) |
| `samtools_chr_index` | index the filtered alignments | same gate |
| (rejoin) | effective conversion input = chr-filtered alignments else original alignments | `pick_value` `first_non_null` — conditional-transform-or-pass-through |
| (identifier rename) | in chr mode the source renames each sample id to the output file's baseName (per-element identifier change) | placeholder transformation: relabel element identifiers from the filtered output's filename; **open question 3** — chr mode is untested by the selected test |

### Conversion — paired-end path (ALIGNMENT_TO_FASTQ; each node per-element, gated `is_paired`)

Source semantics: split reads by pairing/mapping flag combination, collate mapped and unmapped subsets separately, concatenate R1s and R2s.

| Node | Operation (verbatim args from `conf/modules.config`) | Outputs |
|---|---|---|
| `samtools_view_map_map` | filter `-b -f1 -F12` (proper pairs) | bam list |
| `samtools_view_unmap_unmap` | filter `-b -f12 -F256` | bam list |
| `samtools_view_unmap_map` | filter `-b -f4 -F264` | bam list |
| `samtools_view_map_unmap` | filter `-b -f8 -F260` | bam list |
| `samtools_merge_unmap` | merge the three unmapped subsets per sample (multi-input mapped step) | merged bam list |
| `collate_fastq_unmap` | samtools collate + fastq on merged unmapped (`-N`; optional `-f -r N` when `samtools_collate_fast`) | per-element `_1`/`_2` fq.gz |
| `collate_fastq_map` | samtools collate + fastq on map-map subset (same args) | per-element `_1`/`_2` fq.gz |
| `cat_fastq` | concatenate mapped R1+unmapped R1 → `_1.merged.fastq.gz`, mapped R2+unmapped R2 → `_2.merged.fastq.gz` | two per-element outputs (`paired_r1`, `paired_r2` lists) |

### Conversion — single-end path (gated `is_single`)

| Node | Operation | Outputs |
|---|---|---|
| `collate_fastq_single` | samtools collate + fastq with `-N` (`-1 … -s … -0 {prefix}_other.fq.gz`); the source publishes `fastq_other` (singleton had empty reads — famosab note in source) | `single_reads` list (one fq.gz per single-end element) |

### Post-conversion tier

| Node | Operation | Inputs | Outputs | Gating |
|---|---|---|---|---|
| (identifier relabel) | append `_1`/`_2` read suffixes to `paired_r1`/`paired_r2` element identifiers | paired read lists | relabeled lists | placeholder transformation (Apply Rules / relabel recipe); keeps merged reads identifiers unique (`{sample}_1`, `{sample}_2`, `{sample}`) |
| (reads assembly) | `reads` = merge of null-filtered `single_reads`, `paired_r1`, `paired_r2` | three lists | one flat list `fastqsanger.gz` | filter-null (typed skip sentinels) then `__MERGE_COLLECTION__`-style list assembly; materialized collection required here |
| `fastqc_post` | FastQC on converted reads | `reads` | `fastqc_post_html`, `fastqc_post_zip` lists | always run |
| `fastq_utils_info` | fastq_utils `fastq_info` sanity check per read file | `reads` | `fastqutils_info` list (txt) | always run |

### Dropped tier: MULTIQC

The source's MULTIQC step, **at this commit, receives only nf-core boilerplate**: the collated versions yml, the workflow-summary mqc yaml, and the methods-description yaml — the FastQC wiring into `ch_multiqc_files` is commented out with a debugging note (`workflows/bamtofastq.nf:171-172`), and the default-test snapshot's `multiqc_data/` confirms no fastqc/samtools tables in the report. All three boilerplate inputs are themselves dropped (Galaxy owns provenance; ledger: `pipeline-info-outputs-dropped`). A MultiQC step whose every input is dropped is dead code; carrying it would fabricate an aggregation the source does not perform.

**Decision: MULTIQC is not carried.** Consequences: `multiqc_config` workflow input and `multiqc_report` workflow output (interface brief) are withdrawn. Ledger entry `multiqc-step-dropped` records the drop with this citation. The FastQC/samtools QC outputs remain directly exposed as workflow outputs.

## Edges (abstract)

```
reference_fasta ──────────────────────────────────┬─> build_fai ──> pick_value(reference_fai, ·)   [effective fai; possibly unused]
                                                  └─> (optional reference input on samtools steps)
alignments ──> ensure_alignment_index ──> (alignments, index) ──> samtools_flagstat / idxstats / stats   [when: no_stats==false]
                                             └─────────────────> fastqc_pre                          [when: no_read_qc==false]
                                             └─────────────────> check_endedness ──> derive_is_paired/is_single
                                                                        │ (per-element when gates)
alignments ──> [chr branch: samtools_chr_view + index, pick_value rejoin]
        └──> paired path: view×4 ──> merge_unmap ──> collate_unmap ─┐
              view_map_map ──────────────────────────> collate_map ─┴─> cat_fastq ──> paired_r1/r2
        └──> single path: collate_fastq_single ──> single_reads
paired_r1/r2 [relabel +1/_2] + single_reads [filter null] ──> reads ──> fastqc_post, fastq_utils_info, (output)
```

## Collection map/reduce choices

- `alignments`: `list` (interface brief). Map-over everywhere; identifier-synced index list joins by element identifier (High).
- Broadcast FASTA into mapped steps: standard Galaxy multi-input with one File + one list (Medium-High).
- Per-element boolean gating: mapped `param_value_from_file` → `boolean_param` connected to step `when` inputs (recipe verified upstream; Medium here because the marker-derivation steps are bespoke).
- `reads`: flat `list` assembled from null-filtered branch outputs; identifier relabeling keeps elements unique. `list:paired` rejected (runtime-variable per-sample read count — see interface brief).
- Stats outputs: `list` per output kind; one element per sample, identifier = sample id.
- FastQC outputs: `list` per kind; pre-conversion elements keyed by sample, post-convention elements keyed by read file.

## Unresolved tool needs (for discovery/authoring; no availability claims)

| Need | Shape | Notes |
|---|---|---|
| samtools flagstat / idxstats / stats / view / index / merge / collate+fastq / faidx equivalents | list→list (mapped), reference-optional, flag/region parameterizable | The four view variants differ only in `-f/-F` flags and prefix; one wrapper parameterized four ways, or a UDT. collatefastq is a two-stage pipe (collate \| fastq) — may need a UDT if no wrapper composes it. |
| `check_endedness` | list → per-element marker | bespoke (local module CHECKPAIREDEND); likely a small UDT running the samtools check. |
| marker → boolean derivation | list(txt) → list(boolean file) | mapped text comparison; simple text-processing step. |
| FastQC | list(bam/fastq) → html/zip lists | exists in Galaxy; cram acceptance unresolved (open question 2). |
| fastq_utils info | list(fastq.gz) → list(txt) | probably no wrapper; UDT candidate (biocontainer `fastq_utils:0.25.3`). |
| cat fastqs (gzip) | per-element 2 inputs → 2 outputs | Galaxy concatenate may suffice; per-element pairing by identifier. |

## Operator translation audit (from summary workflow edges)

| Source operator | Disposition |
|---|---|
| `branch` (PREPARE_INDICES index/no-index; fasta fai/no-fai) | channel-only — always-run rebuild replaces the branch (faithful to the absent-index path). |
| `join` (bam+index, alignments+endedness marker) | Galaxy collection semantics — identifier-synced multi-input map-over. High. |
| `branch { ch_single / ch_paired }` (endedness) | per-element `when:` gating over two step subgraphs (see above). |
| `mix` (unmapped bam/cram channels; reads_post_qc) | explicit list assembly after null-filtering (materialized collection required). The bam/cram mixes inside ALIGNMENT_TO_FASTQ collapse because Galaxy collections are datatype-heterogeneous — one list serves both. |
| `join(remainder: true)` (unmapped subsets) | multi-input mapped step (merge) — collections already share identifiers. |
| `collectFile` (versions, summaries) | dropped with the MultiQC/pipeline_info tier. |
| `channel.topic('versions')` | dropped (Galaxy provenance). |
| `map` (id rename in chr mode; single_end meta injection) | chr-mode rename = placeholder transformation (open); single_end meta = subsumed by the per-element when gates. |

## Confidence summary

High: input/output shapes, index/stats/flagstat/idxstats tiers, reads assembly semantics, datatype choices. Medium: per-element when mechanics at implementation level, endedness marker derivation, collatefastq/cat parameterization, fai precedence. Low: chr-mode identifier rename, cram elements through fastqc_pre.

## Open questions

1. **`when:` expression mechanics** (string/boolean workflow inputs vs connected boolean inputs; negation avoidance) — pin against an IWC exemplar in the next phase; the conditionals corpus pattern is `when: $(inputs.when)` with the boolean connected as a step input.
2. **CRAM elements in `fastqc_pre`** — the source runs pre-conversion FastQC on BAM only; a mixed list has no per-element datatype filter in stock Galaxy. Default test is BAM-only; record as limitation, revisit if a cram test is added.
3. **chr-mode identifier rename** — relabel from output filename; untested by the selected test.
4. **FAI utility** — whether any chosen wrapper consumes an FAI input (else drop the fai precedence plumbing with a ledger entry).
