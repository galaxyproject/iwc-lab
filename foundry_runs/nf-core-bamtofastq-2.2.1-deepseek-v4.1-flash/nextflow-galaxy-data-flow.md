# Galaxy data-flow brief — nf-core/bamtofastq

Source: `nf-core/bamtofastq` @ `aa0150e` (v2.4.0). Inputs: `summary-nextflow.json`, `nextflow-galaxy-interface.md`, `nextflow-galaxy-reference-data.md`.

Scope: `workflow BAMTOFASTQ` plus `PREPARE_INDICES`, `PRE_CONVERSION_QC`, `ALIGNMENT_TO_FASTQ`. nf-core init/completion plumbing is dropped.

## Interface addition forced by the source

`CHECKPAIREDEND` (`modules/local/checkpairedend`) **decides single vs paired by reading the BAM flags** (`samtools view -c -f 1` over the first 1000 records) and routes the sample to either `SAMTOOLS_COLLATEFASTQ_SINGLE_END` or `ALIGNMENT_TO_FASTQ`. Galaxy workflows cannot branch on file content, so the decision must be a workflow input:

- **`input_layout`** — `string` with restrictions `single` / `paired`, required, no Galaxy default.
- `single` gates the single-end collate step; `paired` gates the four `samtools view` subset steps + merge + two collate steps + `CAT_FASTQ`.
- `CHECKPAIREDEND` itself is dropped (it is a detector, not a transformation); this is recorded as a `dropped` ledger entry.

## Abstract nodes

| id | operation | inputs | outputs | confidence | evidence |
|---|---|---|---|---|---|
| `in_alignments` | workflow input | — | `list` of `bam`/`cram` | high | interface |
| `index_inputs` | index any alignment lacking an index | `list` bam/cram | `index_bai` (`list` of `bai`), `index_crai` (`list` of `crai`) | high | `PREPARE_INDICES`: `SAMTOOLS_INDEX` on the `to_index` branch |
| `chr_extract` | keep only reads on the requested contigs | `list` bam/cram, `chr` string | `chr_bam` (`list` of `bam`) | high | `SAMTOOLS_CHR` (`samtools view -hb <chr>`) |
| `chr_index` | index the extracted alignment | `chr_bam` | `chr_index` (`list` of `bai`) | high | `SAMTOOLS_CHR_INDEX` |
| `select_alignments` | pick the chr-extracted alignment when the chr step ran, else the original | original + chr outputs | `work_alignments` (`list`) | medium | `if (params.chr) { ch_input_new = ch_input_chr … }` |
| `flagstat` | per-sample flag statistics | `work_alignments` | `flagstat` (`list` of `txt`) | high | `SAMTOOLS_FLAGSTAT` |
| `idxstats` | per-contig index statistics | `work_alignments` + index | `idxstats` (`list` of `txt`) | high | `SAMTOOLS_IDXSTATS` |
| `stats` | per-sample samtools stats | `work_alignments`, `fasta` | `stats` (`list` of `txt`) | high | `SAMTOOLS_STATS` |
| `pre_fastqc` | QC the BAM input | `work_alignments` | `pre_fastqc_html` (`list` of `html`) | medium | `FASTQC_PRE_CONVERSION` on the bam branch only; Galaxy FastQC must accept BAM |
| `collate_single` | collate + convert a single-end alignment | `work_alignments`, `fasta` | `reads_single` (`list` of `fastq.gz`) | high | `SAMTOOLS_COLLATEFASTQ_SINGLE_END` → `fastq_other` |
| `view_map_map` | keep properly paired mapped reads (`-b -f1 -F12`) | `work_alignments`, `fasta` | `mm` (`list` of `bam`) | high | `SAMTOOLS_VIEW_MAP_MAP` |
| `view_unmap_unmap` | keep unmapped reads with unmapped mate (`-b -f12 -F256`) | `work_alignments`, `fasta` | `uu` (`list` of `bam`) | high | `SAMTOOLS_VIEW_UNMAP_UNMAP` |
| `view_unmap_map` | keep unmapped reads with mapped mate (`-b -f4 -F264`) | `work_alignments`, `fasta` | `um` (`list` of `bam`) | high | `SAMTOOLS_VIEW_UNMAP_MAP` |
| `view_map_unmap` | keep mapped reads with unmapped mate (`-b -f8 -F260`) | `work_alignments`, `fasta` | `mu` (`list` of `bam`) | high | `SAMTOOLS_VIEW_MAP_UNMAP` |
| `merge_unmapped` | merge the three unmapped subsets | `uu`, `um`, `mu` | `unmapped` (`list` of `bam`) | high | `SAMTOOLS_MERGE_UNMAP`; `join … remainder: true` |
| `collate_unmapped` | collate + convert the unmapped reads | `unmapped`, `fasta` | `reads_unmapped` (`list` of `fastq.gz`) | high | `COLLATE_FASTQ_UNMAP` |
| `collate_mapped` | collate + convert the mapped reads | `mm`, `fasta` | `reads_mapped` (`list` of `fastq.gz`) | high | `COLLATE_FASTQ_MAP` |
| `concat_paired` | concatenate mapped+unmapped reads per sample | `reads_mapped`, `reads_unmapped` | `reads_paired` (`list` of `fastq.gz`) | high | `CAT_FASTQ` (`reads/*.fastq.gz`) |
| `post_fastqc` | QC the converted reads | `reads_single` + `reads_paired` | `post_fastqc_html` (`list` of `html`) | high | `FASTQC_POST_CONVERSION` over `ch_reads_post_qc` |
| `fastqutils` | FASTQ integrity report | `reads_single` + `reads_paired` | `fastqutils_info` (`list` of `txt`) | high | `FASTQUTILS_INFO` |
| `multiqc` | aggregate all QC outputs | fastqc html/raw + stats/flagstat/idxstats + fastqutils | `multiqc_report` (`html`) | high | `MULTIQC(ch_multiqc_files…)` |

## Edges

```
in_alignments ─> index_inputs ─┬─> flagstat
                               ├─> idxstats  (also takes index)
                               ├─> stats     (also takes fasta)
                               ├─> pre_fastqc (when no_read_QC == false)
                               ├─> collate_single      (when layout == single)
                               └─> view_{mm,uu,um,mu}  (when layout == paired)
chr ─> chr_extract ─> chr_index ─> select_alignments <─ in_alignments
select_alignments ─> everything downstream (replaces the original list)
view_{uu,um,mu} ─> merge_unmapped ─> collate_unmapped ─┐
view_mm ─────────────────────────> collate_mapped ─────┴─> concat_paired
collate_single ─────────────────────────────> reads_single
reads_single/reads_paired ─> post_fastqc, fastqutils
all QC outputs ─> multiqc
```

Map-over is the rule: every step above maps one element of the input `list` to one output element. There is **no reduction** in the conversion path; `multiqc` is the single reduction (it consumes the collected QC lists).

## Collection decisions

- Element identifiers are the samplesheet `sample_id` values (test: `test3`, and after chr extraction `test3.chrX_chrY_X_Y` as in the snapshot). No positional mate suffixes are used as identifiers.
- `merge_unmapped` needs a **per-sample keyed join** of three lists (`uu`, `um`, `mu`) that may legitimately have empty members. Nextflow uses `join(..., remainder: true)`. Galaxy has no null-tolerant join; this is a shape risk (see Placeholder transformations).
- The chr branch replaces the input list wholesale in source; in Galaxy the two lists carry different identifiers (`test3` vs `test3.chrX_chrY_X_Y`), so a plain `pick_value` over element-sets cannot mix them. Options: (a) run the whole downstream on the chr list only (identifier mismatch is fine because every downstream step is map-over), or (b) pre-extract with one `samtools view` that takes the chr list argument and skip the replacement entirely. **Chosen: (a)** — a `pick_value` (`first_non_null`) between two *whole lists* works because each branch is either fully present or skipped, and identifiers stay internally consistent.
- `index_bai`/`index_crai` are parallel lists, not attached to the BAMs. `idxstats` is the only consumer that needs the index.

## Placeholder transformations

| id | need | candidate idiom | confidence |
|---|---|---|---|
| `select_alignments` | choose chr-extracted list vs original list | `pick_value` (`first_non_null`) on the two whole collections | medium — the skipped step yields null whole-list output |
| `merge_unmapped` | per-sample merge of three possibly-empty BAM lists | `__APPLY_RULES__` to align identifiers + `samtools merge` on a sample-scoped list-of-lists, or three sequential merges (`uu+um`, `+mu`) where missing lists are tolerated | low — **open question**; Galaxy cannot do a null-tolerant join |

## Conditional disposition

| source condition | Galaxy form | rationale |
|---|---|---|
| `if (params.chr)` | inline `when:` on `chr_extract`/`chr_index` + `pick_value` for rejoin | short cascade, one rejoin point |
| `meta.filetype == 'bam'` for pre-conversion FastQC | inline `when:` on `pre_fastqc` filtered to bam elements | the branch is per-element in source; Galaxy cannot filter by datatype inside a collection, so the step is documented as BAM-only (test data are BAM) |
| `!params.no_read_QC` | inline `when:` on both FastQC steps | two independent steps |
| `!params.no_stats` | inline `when:` on flagstat/idxstats/stats | three independent steps |
| single vs paired (CHECKPAIREDEND result) | `input_layout` input + inline `when:` per branch | content-dependent branch has no Galaxy expression |

## Galaxy tool needs

| node | what the tool must do |
|---|---|
| `index_inputs` | `samtools index` a BAM or CRAM, emitting `.bai`/`.crai` |
| `chr_extract` | `samtools view -hb <regions>` filtered to named contigs |
| `flagstat` / `idxstats` / `stats` | the three samtools statistics reports |
| `pre_fastqc` / `post_fastqc` | FastQC HTML (+ raw data) from BAM, FASTQ |
| `collate_single` / `collate_unmapped` / `collate_mapped` | `samtools collate` + `samtools fastq` in one tool, emitting `*_other.fq.gz` / `*_{1,2}.fq.gz` |
| `view_*` | `samtools view -b` with the four flag filters |
| `merge_unmapped` | `samtools merge` N BAMs into one |
| `concat_paired` | concatenate R1 of mapped+unmapped, R2 of mapped+unmapped |
| `fastqutils` | FASTQ integrity summary text |
| `multiqc` | aggregate reports into one HTML |

## Dropped

| source unit | reason |
|---|---|
| `CHECKPAIREDEND` module | a content-dependent detector; replaced by the `input_layout` input |
| `PREPARE_INDICES`' "index provided" branch | Galaxy always indexes inputs it is given (pre-built-index input dropped in the interface) |
| `versions.yml` collation, workflow summary/methods YAML, `PIPELINE_INITIALISATION`/`COMPLETION` | nf-core reporting plumbing |

## Confidence and open questions

- High confidence on the conversion path shape (view subsets → merge → collate → cat) and on stats/QC wiring.
- **Low confidence** on `merge_unmapped`: a null-tolerant keyed join of three lists has no direct Galaxy recipe. This is the workflow's main translation risk and a ledger entry.
- Medium confidence on `pick_value` over whole collections for the chr branch.
- Open question: does Galaxy's FastQC wrapper accept BAM (required for pre-conversion QC)?
