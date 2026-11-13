# Data-flow brief — nf-core/bamtofastq → Galaxy

Source: `nf-core/bamtofastq` @ `aa0150e`.
Reads: `summary-nextflow.json`, `nextflow-galaxy-reference-data.md`,
`nextflow-galaxy-interface.md`, `open-requirements.ledger.yml`.
Mold: `nextflow-summary-to-galaxy-data-flow`.

This brief is Galaxy-shaped, not gxformat2: it names operations and shapes, not tool ids
or parameters.

## 0. Amendment to the interface

The interface brief exposed only data inputs. This phase adds one scalar:

| id | type | values | default | required |
|---|---|---|---|---|
| `layout` | select/string | `paired`, `single` | `paired` | yes |

**Why.** `CHECKPAIREDEND` makes a *per-sample* decision and routes each sample into one of
two structurally different subgraphs (`ALIGNMENT_TO_FASTQ` vs
`SAMTOOLS_COLLATEFASTQ_SINGLE_END`). Galaxy's `when:` is a workflow-level gate evaluated
over workflow inputs, not a per-element classifier; the per-element route (per-element
boolean dataset → `param_value_from_file` → mapped `when` → `pick_value`) is documented but
requires a wrapper that does not exist for `CHECKPAIREDEND` plus mapped-gate machinery this
run does not attempt. All source test fixtures are layout-homogeneous (the `chr` fixture is
the only single-end one), so a workflow-level layout selector reproduces every test case.
This is a recorded drop, not a silent one — see the ledger.

Resulting shape: two `when:`-gated sibling branches, each with its own workflow outputs.
No `pick_value` rejoin is needed because the two branches expose different outputs.

## 1. Node list (abstract)

Shapes: `L<T>` = list of T, `LP<T>` = list:paired of T, `F` = single dataset.

### 1.1 Input preparation

| # | Node | In | Out | Galaxy idiom | Confidence |
|---|---|---|---|---|---|
| 1 | index alignments | `input` L<bam\|cram> | L<bai\|crai> | `samtools index` mapped | high |
| 2 | subset to `chr` (gated `chr` non-empty) | `input`, `chr` | L<bam\|cram> | `samtools view` with region args, mapped | high |
| 3 | index subset (same gate) | node 2 | L<bai\|crai> | `samtools index` mapped | high |
| 4 | choose subset or original | node 2 + node 3 vs `input` + node 1 | L<bam\|cram> + L<index> | `pick_value` (`first_non_null`) on each of the two streams | medium |

Node 2/3/4 exist only when `chr` is non-empty; Galaxy skips a step whose `when:` is false and
`pick_value` tolerates the skipped input. `chr` is a *workflow-level* gate, so `when:` is the
right primitive here (unlike the layout branch, no per-element part is involved).

### 1.2 Pre-conversion QC (shared by both branches)

| # | Node | In | Out | Galaxy idiom | Confidence |
|---|---|---|---|---|---|
| 5 | flagstat (gate `!no_stats`) | L<bam\|cram>, L<index> | L<txt> | `samtools flagstat` mapped | high |
| 6 | idxstats (gate `!no_stats`) | L<bam\|cram>, L<index> | L<txt> | `samtools idxstats` mapped | high |
| 7 | stats (gate `!no_stats`) | L<bam\|cram>, L<index>, `fasta` | L<txt> | `samtools stats` mapped | high |
| 8 | keep BAM elements only | `input` | L<bam> | `__APPLY_RULES__` filter `ext == 'bam'` | medium |
| 9 | FastQC pre-conversion (gate `!no_read_QC`) | node 8 output | L<html>, L<zip> | `fastqc` mapped | high |

Node 8 exists because the source runs pre-conversion FastQC on BAM only
(`fastqc_input.bam`). CRAM elements are dropped from that branch, which is a filter on the
element datatype, not a metadata column.

### 1.3 Paired-end conversion branch (gate `layout == 'paired'`)

| # | Node | In | Out | Galaxy idiom | Confidence |
|---|---|---|---|---|---|
| 10 | mapped/mapped reads | L<bam>, L<index>, `fasta` | L<bam> | `samtools view -b -f1 -F12` mapped | high |
| 11 | unmapped/unmapped | same | L<bam> | `samtools view -b -f12 -F256` mapped | high |
| 12 | unmapped/mapped | same | L<bam> | `samtools view -b -f4 -F264` mapped | high |
| 13 | mapped/unmapped | same | L<bam> | `samtools view -b -f8 -F260` mapped | high |
| 14 | merge the three unmapped subsets | nodes 11+12+13 | L<bam> | `samtools merge` over 3 synchronized lists (multi-input map-over) | high |
| 15 | unmapped → FASTQ | node 14, `fasta` | LP<fastq.gz> | `samtools collate | samtools fastq` (`-1 -2 -s`) mapped | medium |
| 16 | mapped → FASTQ | node 10, `fasta` | LP<fastq.gz> | same tool, mapped | medium |
| 17 | R1 = mapped R1 + unmapped R1 | node 16 forward + node 15 forward | L<fastq.gz> | `cat` (concatenate) mapped over two collections | high |
| 18 | R2 = mapped R2 + unmapped R2 | node 16 reverse + node 15 reverse | L<fastq.gz> | `cat` mapped | high |
| 19 | pair R1/R2 | nodes 17, 18 | **LP<fastq.gz>** | `__ZIP_COLLECTION__` (identifiers from R1) | high |

Nodes 15/16 must be one step each, but the source's `samtools collate | samtools fastq`
pipeline is one shell block inside `SAMTOOLS_COLLATEFASTQ`; a single Galaxy wrapper that does
both is required for md5 fidelity (see §3).

Note the *order* of concatenation: source builds `[mapped_r1, mapped_r2, unmapped_r1,
unmapped_r2]` and `CAT_FASTQ` assigns even/odd positions, so R1 = mapped_r1 + unmapped_r1.
Reproducing that order is required for the snapshot md5s.

### 1.4 Single-end conversion branch (gate `layout == 'single'`)

| # | Node | In | Out | Galaxy idiom | Confidence |
|---|---|---|---|---|---|
| 20 | collate + fastq, single-end | L<bam>, L<index>, `fasta` | L<fastq.gz> (`_other`), L<fastq.gz> (`_singleton`) | `samtools collate | samtools fastq` with `-1 _1 -0 _other -s _singleton` mapped | medium |
| 21 | select the `other` stream | node 20 | **L<fastq.gz>** | output selection (wiring) | high |

The source uses `SAMTOOLS_COLLATEFASTQ_SINGLE_END.out.fastq_other` (a comment records that
`fastq_singleton` was empty). No concat/merge steps are needed on this branch.

### 1.5 Post-conversion QC

| # | Node | In | Out | Galaxy idiom | Confidence |
|---|---|---|---|---|---|
| 22 | FastQC paired (gate `!no_read_QC && layout == paired`) | node 19 | LP<html> | `fastqc` mapped over `list:paired` | high |
| 23 | fastq_info paired (always) | node 19 | L<txt> | `fastq_info` mapped over the paired members | medium |
| 24 | FastQC single (gate `!no_read_QC && layout == single`) | node 21 | L<html> | `fastqc` mapped | high |
| 25 | fastq_info single (always) | node 21 | L<txt> | `fastq_info` mapped | medium |
| 26 | MultiQC | nodes 5, 6, 22, 24 (+ per-sample QC) | F<html> | `multiqc` over an assembled list of reports | medium |

Node 26 deviates from the source deliberately: the source's `ch_multiqc_files` never receives
the FastQC outputs (the mix is commented out at `workflows/bamtofastq.nf:171-172`), so its
MultiQC report aggregates nothing but the versions/summary stubs. The translated workflow
feeds MultiQC the QC collections so the report carries the FastQC and samtools sections. The
nf-test fixture does not assert MultiQC content (multiqc output is in `tests/.nftignore`), so
this deviation cannot break the test; recorded on the ledger as a decision.

## 2. Element identifiers

| Collection | Identifier source | Uniqueness |
|---|---|---|
| `input` | samplesheet `sample_id` (`test`, `test2`) | unique per fixture row; required by nf-schema |
| every mapped output | inherited from `input` | map-over preserves identifiers |
| `reads_paired` members | `forward` / `reverse` from `__ZIP_COLLECTION__` | one pair per sample |
| `reads_single` | inherited from `input` | one dataset per sample |

The fixtures use `sample_id` values `test`, `test2`; the `chr` fixture uses `test3`. No
column repeats, so element naming is stable without extra disambiguation.

## 3. Fidelity constraints the translation must preserve

1. **`samtools collate` + `samtools fastq` in one step.** The nf-test snapshot pins md5 of
   the merged FASTQ files (`test_1.merged.fastq.gz:md5,9b0c08862a5e47e842a485ddad31b871`,
   …). The `collate` stage determines read order inside the FASTQ; splitting it from
   `fastq` or reordering records changes the md5. The wrapper must run the same two-stage
   shell pipeline with `-O` (collate output to stdout) as the module does.
2. **Four-way FLAG split.** `-f1 -F12`, `-f12 -F256`, `-f4 -F264`, `-f8 -F260` must be
   reproduced exactly; they are what peers the mapped/unmapped mates and fix the order
   mapped-then-unmapped in the concatenated FASTQ.
3. **`-N` on `samtools fastq`.** `ext.args2 = '-N'` is set for all three collate steps.
4. **gzip passthrough in concatenation.** Inputs are `.gz`; the source's `cat` does not
   recompress. Galaxy's concatenate tool must concatenate bytes, not decompress/recompress.

## 4. Galaxy tool needs (abstract, not resolved)

| Need | Shape in → out | Notes |
|---|---|---|
| index an alignment | L<bam\|cram> → L<bai\|crai> | `samtools index` |
| subset by region | L<bam\|cram> + L<index> + string → L<bam\|cram> | `samtools view` with region arguments; needs the reference for CRAM |
| flag-based subset | L<bam\|cram> + L<index> + FLAG set → L<bam> | four distinct parameterizations of one wrapper |
| merge alignments per sample | 3 × L<bam> → L<bam> | multi-input map-over |
| collate + fastq | L<bam> + F<fasta> → LP<fastq.gz> / L<fastq.gz> | must accept `-N`, `-0`, `-s`; single-end uses the `_other` output |
| concatenate FASTQ | 2 × L<fastq.gz> → L<fastq.gz> | byte-level concatenation |
| FastQC | L<fastq.gz> or LP<fastq.gz> → reports | must accept BAM for the pre-conversion branch |
| fastq_info | L<fastq.gz> → L<txt> | validates converted reads |
| flagstat / idxstats / stats | L<bam\|cram> (+ index, + fasta) → L<txt> | three `samtools` subcommands |
| MultiQC | list of reports → html | |

Built-in collection operations needed: `__APPLY_RULES__` (datatype filter), `__ZIP_COLLECTION__`
(pair R1/R2), `__BUILD_LIST__` or flattening for the MultiQC input, `pick_value` for the
`chr` branch.

## 5. Confidence and risks

- **High**: input indexing, flag splits, merge, concatenation, zip, FastQC, samtools stats.
- **Medium**: the `chr` pick_value pair (two streams must be picked consistently — if the
  alignment and its index are picked from different branches the ids mismatch);
  `samtools collate`+`fastq` as one Galaxy wrapper; MultiQC input assembly.
- **Low**: none blocking. The largest uncertainty is whether a Galaxy wrapper exists for
  `samtools collate | samtools fastq` with all four output streams (`-1`, `-2`, `-0`, `-s`)
  and `-N`; if it does not, a user-defined tool must reproduce the module's shell block
  verbatim.

## 6. Open questions

1. `pick_value` for `chr`: the alignment stream and the index stream must be picked
   independently but consistently. A safer alternative is to skip the early index step and
   index only after the `chr` decision, so only one `pick_value` is needed. Decide in the
   template phase; recorded on the ledger.
2. Whether `samtools collate | samtools fastq` is available as one wrapper.
3. MultiQC input assembly across differently-typed collections.
