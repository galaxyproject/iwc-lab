# Galaxy data-flow brief: nf-core/bamtofastq

Inputs: `summary-nextflow.json`, `nextflow-galaxy-interface.md`, `nextflow-galaxy-reference-data.md`, `open-requirements.ledger.yml`. Abstract only — no Tool Shed wrappers are chosen here. Confidence is per node (high/medium/low).

## Granularity rationale
The source has four local subworkflows (`PREPARE_INDICES`, `PRE_CONVERSION_QC`, `ALIGNMENT_TO_FASTQ`, and the main body). Granularity follows them: one Galaxy step per source process, except the plumbing the Galaxy engine does for free (BAM/CRAM indexing, FASTA indexing, `versions.yml` collation, version topics, params summary). No subworkflow boundaries are introduced: every gate (`chr`, `no_read_QC`, `no_stats`) covers one to three steps, so inline `when:` is used (conditional note: short cascades ⇒ inline).

## Inputs (from interface brief)
`Alignments` (list of bam/cram), `Reference FASTA` (optional), `chr` (text), `no_read_QC`, `no_stats`, `samtools_collate_fast`, `reads_in_memory`.

## Nodes

| # | Abstract operation | Source process | In → Out (shape) | Gate | Tool need (what it must *do*) | Conf. |
|---|---|---|---|---|---|---|
| N1 | Extract reads in a region | `SAMTOOLS_CHR` (+ `SAMTOOLS_CHR_INDEX`) | `list` bam/cram → `list` bam/cram (same ids) | `when` `chr` non-empty | Filter an alignment file to a region/contig, keep header, keep BAM/CRAM; index implicit | medium (the source renames ids with the region; carried as ledger gap `chr-region-id-rename`) |
| N2 | Alignment flag statistics | `SAMTOOLS_FLAGSTAT` | `list` alignment → `list` text | `!no_stats` | samtools flagstat per alignment | high |
| N3 | Per-contig read counts | `SAMTOOLS_IDXSTATS` | `list` alignment → `list` tabular | `!no_stats` | samtools idxstats per alignment | high |
| N4 | Alignment stats | `SAMTOOLS_STATS` | `list` alignment (+ reference) → `list` text | `!no_stats` | samtools stats per alignment, reference for CRAM | high |
| N5 | FastQC on input alignments | `FASTQC_PRE_CONVERSION` | `list` bam → `list` html + `list` raw data | `!no_read_QC` | FastQC reading BAM (source runs it only for `bam`) | medium (CRAM cannot be read; see OQ) |
| N6 | Select mapped–mapped pairs | `SAMTOOLS_VIEW_MAP_MAP` (`-b -f1 -F12`) | `list` alignment (+ref) → `list` bam | – | filter reads by SAM flag (require 0x1; exclude 0x4,0x8) | high |
| N7 | Select unmapped–unmapped pairs | `SAMTOOLS_VIEW_UNMAP_UNMAP` (`-b -f12 -F256`) | same → `list` bam | – | filter by SAM flag | high |
| N8 | Select unmapped–mapped | `SAMTOOLS_VIEW_UNMAP_MAP` (`-b -f4 -F264`) | same → `list` bam | – | filter by SAM flag | high |
| N9 | Select mapped–unmapped | `SAMTOOLS_VIEW_MAP_UNMAP` (`-b -f8 -F260`) | same → `list` bam | – | filter by SAM flag | high |
| N10 | Merge the three "unmapped" subsets per sample | `SAMTOOLS_MERGE_UNMAP` | N7,N8,N9 (3 `list`s, same ids) → `list` bam | – | merge several BAM per identifier (fan-in of N7/N8/N9 by identifier) | medium: Galaxy merge tools take a *list of datasets per call*; merging three **collections element-wise** needs a reshape (`__ZIP_COLLECTION__`/`__BUILD_LIST__` + `__APPLY_RULES__` to a `list:list`, then map-over a merge tool). Placeholder shape-change recorded below. |
| N11 | Name-collate + extract mapped reads to FASTQ | `COLLATE_FASTQ_MAP` | N6 → `list:paired` fastq.gz (R1,R2) | `-f -r <reads_in_memory>` when fast mode; `-N` | samtools collate → fastq (paired output, name-suffix `/1 /2`) | high |
| N12 | Name-collate + extract unmapped reads to FASTQ | `COLLATE_FASTQ_UNMAP` | N10 → `list:paired` fastq.gz | same | same | high |
| N13 | Concatenate mapped + unmapped, per mate | `CAT_FASTQ` | N11,N12 → `list:paired` fastq.gz (`<id>_1/2.merged.fastq.gz`) | – | concatenate datasets per element and per mate (fan-in N11.forward+N12.forward, N11.reverse+N12.reverse) | medium: needs `__UNZIP_COLLECTION__` ×2, element-wise concatenate, `__ZIP_COLLECTION__` back to paired (placeholders recorded below) |
| N14 | FastQC on converted reads | `FASTQC_POST_CONVERSION` | N13 → `list` html (+raw) ; **per mate** in source (`test.post_conversion_1/2`) | `!no_read_QC` | FastQC on fastq.gz of each mate | medium: source runs once per mate (two reports per sample); Galaxy equivalent: flatten paired → mates |
| N15 | FASTQ integrity check | `FASTQUTILS_INFO` | N13 → `list` text | – (not gated by `no_read_QC` in config) | `fastq_info` check of read pairing/validity | medium: tool availability unknown here; discovery to decide |
| N16 | Aggregate QC | `MULTIQC` | N2,N3,N4,N5,N14 → html | – | MultiQC over the QC outputs | medium (see deviation) |

### Shape-changing placeholders
- **P1** (before N10): bring N7, N8, N9 outputs together by identifier into one nested collection per sample (zip/rules), `list:list` of 3 BAMs per sample id, so a mapped merge runs once per sample.
- **P2** (around N13): unzip N11/N12 paired collections into forward/reverse lists, concatenate per sample per mate (collate lists `[N11.fwd, N12.fwd]`, `[N11.rev, N12.rev]`), zip back to `paired` per sample.
- **P3** (before N14): flatten `list:paired` to a `list` of mates for per-mate FastQC (identifier suffix `_1`/`_2`, both mates are paired by construction here since the whole branch is paired-end only).
- **P4** (N1): gated step outputs a collection whose elements may be null when skipped; downstream mapped steps must read either the N1 output or the original `Alignments` — resolve with `pick_value` (`first_non_null`) over [N1, `Alignments`].

### Where QC reads from
`PRE_CONVERSION_QC` (N2–N5) reads `ch_input` (all input alignments before `chr` filtering). N6–N9 read the post-`chr` collection (P4).

### Reference threading
`Reference FASTA` feeds N1, N4, N6–N10 and N11/N12 where wrappers take a reference (needed for CRAM). In-tool FASTA indexing is assumed (reference-data brief; ledger `fasta-fai-input-not-exposed`).

## Dropped / deviating from the source (recorded)
1. **CHECKPAIREDEND and the single-end branch** (`CHECKPAIREDEND`, `SAMTOOLS_COLLATEFASTQ_SINGLE_END`, single-end `ch_single_end` routing, output `Converted reads (single-end)`): not carried. The source decides per sample from file content at run time; Galaxy would need a content-derived per-element boolean plus gated, partially-null collections on every downstream step (see channel-shape note, "per-element parameters": untested for our shapes). All nf-test fixtures for this pipeline are paired-end, so the dropped branch is not exercised by the source's own tests. The brief commits to **paired-end-only conversion** and says so in the workflow annotation. (Reason is a design judgement, not a tool search.)
2. **Software-versions collation / pipeline_info** (`topic: versions` channel, `softwareVersionsToYAML`, `collectFile`), **params summary** and **methods-description** MultiQC inputs: Galaxy records tool versions per job; no equivalent step.
3. **BAM/CRAM and FASTA index creation** (`SAMTOOLS_INDEX`, `SAMTOOLS_FAIDX`, `PREPARE_INDICES`): subsumed by Galaxy datasets/wrappers (unverified for FASTA; ledger entry already open).
4. **Deviation (superset):** in the source the MultiQC call receives only versions/summary/methods files (the FastQC zip hookup is commented out "TEMPORARILY DISABLED"), so its report holds no QC data. Galaxy N16 aggregates the QC outputs — the evident intent. This is a deliberate behaviour difference.

## Collection element identifiers
Take identifiers from the input element identifiers (= `sample_id`, e.g. `test`, `test2`). Source output names: `<id>_1.merged.fastq.gz`, `<id>_2.merged.fastq.gz`, `<id>.flagstat/.idxstats/.stats`, FastQC `<id>.pre_conversion*`, `<id>.post_conversion_{1,2}*`. The `_1`/`_2` suffix is a mate suffix only because the converted-read branch is paired-only; FastQC post-conversion identifiers should be derived `<id>_1`, `<id>_2` and unique per dataset.

## Open questions
- **OQ-A (reference optionality):** optional `Reference FASTA` threads into wrappers whose reference selector may not accept an absent input. Proposal: keep optional; if the chosen wrappers require it, make the Galaxy input required for all runs and log a brief-change-level note (the nf-test default case supplies a FASTA anyway).
- **OQ-B (FastQC on CRAM):** N5 reads `bam` only in the source; a mixed list needs filtering. Proposal: run on all elements, document that all-CRAM inputs should enable `Skip read QC`.
- **OQ-C (granularity of N6–N10):** the four-view + merge + two-collate + cat sequence is a faithful transcription; a single fastx-style tool would collapse it. Proposal: keep faithful; the draft phases may simplify if a wrapper reproduces the same reads.
