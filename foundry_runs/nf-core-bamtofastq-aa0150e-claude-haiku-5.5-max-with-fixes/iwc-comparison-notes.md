# IWC comparison notes: nf-core/bamtofastq (aa0150e)

**Status:** review guidance for the template step. Not a template, and no tool is resolved here.
**Produced by:** compare-against-iwc-exemplar.
**Upstream briefs:** `nextflow-galaxy-interface.md` (phase 3), `nextflow-galaxy-data-flow.md` (phase 4), `nextflow-galaxy-reference-data.md` (phase 2).
**Corpus:** IWC `galaxyproject/iwc` at commit `c07557f` (2026-11-12), a shallow sparse clone of `workflows/` kept inside the run directory at `iwc/`. It contains 133 workflow files (`.ga` and `.gxwf.yml`).
**Sibling artifact:** `iwc-exemplar.gxwf.yml` (bounded gxformat2 slice of the nearest exemplar, section 4).

## 1. Result

- **Nearest exemplar: `data-fetching/sra-manifest-to-concatenated-fastqs/sra-manifest-to-concatenated-fastqs`. Confidence: medium, not canonical.**
  - Shared with our design: FASTQ production for a sample collection, per-sample concatenation of several read parts, and separate paired and single outputs.
  - Not shared: the domain is SRA download, not BAM conversion. It has no samtools steps, and its inputs are accessions, not alignments.
- **Secondary, low confidence: `epigenetics/atacseq/atacseq`.** It uses `samtools_view` to filter alignments by flag, `samtools_idxstats` and MultiQC. Its input is a `list:paired` FASTQ collection, so it is useful as a pattern for flag selection only.
- **No nearest exemplar:** `transcriptomics/rnaseq-pe/rnaseq-pe` (shares only generic tools and a paired collection input), and the variant-calling and virology workflows.
- **A partial BAM-to-FASTQ precedent exists (correction to the first draft of this section).** `iuc samtools_fastx` 1.22+galaxy2 exports alignments to `fastqsanger` with SAM-flag filters in two IWC workflows: `microbiome/host-contamination-removal/host-contamination-removal-long-reads/host-or-contamination-removal-on-long-reads.ga` and `microbiome/pathogen-identification/nanopore-pre-processing/Nanopore-Pre-Processing.ga`. The search of all 133 workflow files found no `samtools_collate`, `bam2fastq` or `bamtofastq` tool id and no BAM-to-FASTQ title. Name collation has no precedent. `samtools_sort` (devteam 2.0.8, 16 uses) is the nearest alternative for name order.

## 2. Ranking evidence (feature hierarchy)

| Candidate | Domain | Input topology | Tool families | DAG motifs | Outputs | Tests | Confidence |
|---|---|---|---|---|---|---|---|
| sra-manifest-to-concatenated-fastqs | FASTQ production (SRA); adjacent to ours | tabular manifest → per-run collection → per-sample collections | fasterq_dump, split_file_to_collection, relabel, Apply Rules, cat_multi_datasets | split, map, relabel by table, group by identifier, concatenate by strand | `paired_output` (list:paired) and `single_output` (list) | element tests, size only | Medium |
| atacseq | Epigenetics (alignment processing) | `list:paired` FASTQ | bowtie2, fastp, samtools_view, samtools_idxstats, MultiQC | map, flag filter, reduce | BAM and QC reports | not read | Low |
| rnaseq-pe | Transcriptomics | `list:paired` FASTQ | fastp, STAR, featureCounts, MultiQC, pick_value | map, reduce | counts and reports | not read | No nearest |
| variant-calling and virology | Variant calling | FASTQ | BWA, samtools, GATK-like callers | map, merge | VCF | not read | No nearest |

Domain comes first, so the SRA exemplar is ranked above the others on topology and outputs, and its domain difference is recorded. The ATAC-seq workflow matches on tools but not on topology, so it stays at low confidence.

## 3. Structural diff: our design against the nearest exemplar

| Aspect | Our design (phases 3-4) | Exemplar | Diff and guidance |
|---|---|---|---|
| Input | `samplesheet` as `sample_sheet:record` of BAM or CRAM, with optional index. Already element-keyed. | Tabular SRA manifest, split into one collection element per run. | We need no split step. Expected divergence: our input is alignments. |
| Paired and single split | Per element. A classifier (N11) decides, then per-element gates (N16-N24). | The tool itself returns two collections: `list_paired` and `output_collection` (singles). No classifier. | Corpus separates read types by tool output. Our classifier has no corpus precedent (ledger `per-element-classifier-gating-no-corpus-precedent`). |
| Outputs | One `reads` collection, `list:paired_or_unpaired` (interface). Rejoin across branches at N25, open. | Two outputs, `paired_output` (list:paired) and `single_output` (list). No rejoin. | **Corpus precedent for two outputs.** Recommended as brief-change BC-1. |
| Grouping per sample | Inner join by identifier (mapped ⋈ unmapped, N24). | Relabel every element to `SRA+sample` with a table, then Apply Rules `list_identifiers` groups runs by sample. | Precedent for identifier-based grouping in place of a join. |
| Concatenation | Concatenate R1 parts and R2 parts (N24, P9). | `cat_multi_datasets` with `input_type: paired_collection` and `paired_cat_type: by_strand`. Singles use `input_type: singles`. | Precedent for by-strand concatenation of a paired collection. Use it for N24. |
| Identifier relabel (chr path, N14) | Rename `<sample>.<region>`, and re-key the per-element single_end flag. | `__RELABEL_FROM_FILE__` with tabular labels from a text tool. No flag to re-key. | Precedent for the relabel recipe. Re-keying a per-element boolean is not shown. |
| Pairing | Not needed; the source gives explicit pairs. | Apply Rules `paired_identifier` builds a list:paired from identifier columns. | Not needed for us. |
| Tools | samtools (view, collate, fastq, merge, index, faidx, flagstat, idxstats, stats), FastQC, fastq_info, MultiQC, plus a classifier | fasterq_dump, split_file_to_collection, Cut1, text tools, relabel, Apply Rules, cat_multi_datasets | samtools_view, idxstats, stats, merge and fastx have IWC pins. samtools_fastx covers the FASTQ export (two workflows). Collation has no precedent (ledger `bam-collate-fastq-no-corpus-precedent`, narrowed). |
| Outputs count | 10 public outputs, including QC tables and MultiQC | 2 outputs | Ours are richer. QC outputs have no precedent here. |
| Checks | Checkpoints: read content, count tables (phase 3, section 7) | Element tests with `has_size` and a delta. Smoke checks only. | Do not copy size-only checks for `reads`. See section 6. |
| Fixtures | Remote nf-core test-datasets (phase 8) | Local `test-data/SRA.txt` with a recorded SHA-1 | Follow the conventions: local path with a digest only after verifying it. |

## 4. Nearest exemplar: abridged excerpt (relevant subgraph)

Excerpt from `iwc-exemplar.gxwf.yml`. It is abridged: `uuid`, `tool_shed_repository` and empty fields are omitted. The full subgraph is in the sibling file. Its eight steps are: split file, fasterq_dump, two relabels, two Apply Rules and two concatenations. The manifest-preparation steps are replaced by the inputs `SRA_list` and `relabel_table`.

```yaml
outputs:
  - id: paired_output
    outputSource: _unlabeled_step_14/paired_output
  - id: single_output
    outputSource: _unlabeled_step_15/out_file1
steps:
  - id: _unlabeled_step_14
    tool_id: toolshed.g2.bx.psu.edu/repos/artbio/concatenate_multiple_datasets/cat_multi_datasets/1.4.3
    in:
      - id: global_condition|inputs
        source: _unlabeled_step_12
    out:
      - id: paired_output
        rename: Concatenated paired-end
    tool_state:
      __input_ext: fastqsanger.gz
      global_condition:
        input_type: paired_collection
        __current_case__: 1
        paired_cat_type: by_strand
  - id: _unlabeled_step_15
    tool_id: toolshed.g2.bx.psu.edu/repos/artbio/concatenate_multiple_datasets/cat_multi_datasets/1.4.3
    in:
      - id: global_condition|inputs
        source: _unlabeled_step_13
    out:
      - id: out_file1
        rename: Concatenated Single-read
    tool_state:
      __input_ext: fastqsanger.gz
      global_condition:
        input_type: singles
        __current_case__: 0
```

Cross-reference: `iwc-exemplar.gxwf.yml`, steps `split file to get one SRA per file + header`, `get Fastqs from SRA IDs`, `relabel pair collec to get SRA+sample`, `relabel single collec to get SRA+sample`, `_unlabeled_step_12`, `_unlabeled_step_13`, `_unlabeled_step_14`, `_unlabeled_step_15`.

## 5. Routing findings to their authoring surface

- **Template or data-flow (for the template step):**
  1. Expose paired and single reads as two outputs, following the exemplar. This is BC-1, a recommendation pending expert review. If it is not accepted, the mixed collection stays open.
  2. Use `cat_multi_datasets` with `paired_collection` and `by_strand` for the concatenation at N24. Keep it as a conversion-level tool step.
  3. Replace the inner join at N24 with an identifier grouping (relabel to sample-level identifiers, then Apply Rules), if the template adopts the exemplar's pattern.
  4. The per-element classifier and per-element gates (N11, N16-N24) have no exemplar. The template must author them and verify them with tests. Do not present them as corpus-backed.
- **Pattern (recurring idioms, for the pattern owners):** table-driven relabel with `__RELABEL_FROM_FILE__`; grouping runs by sample with Apply Rules `list_identifiers`; splitting read types by tool output instead of per-element routing.
- **Tool-step (left to the per-step loop):** exact wrappers for samtools view, collate, fastq, merge, index, faidx, flagstat, idxstats and stats; FastQC; fastq_info; MultiQC; and the `cat_multi_datasets` version (1.4.3) the exemplar pins. Discovery decides what exists.
- **Test (left to the test-plan step):** the exemplar's element tests use size bands only. Plan content checks for `reads` and exact count tables for the samtools text outputs, following section 6.

## 6. Shortcut review (against the shortcuts note)

- The exemplar's output checks are `has_size` with a delta on each element. The note calls such checks smoke tests: they show that an output was produced, not that it is correct. Our planned checkpoint for `reads` is read content. Size alone would not catch an empty or mis-paired read set.
- Size bands for `paired_output` and `single_output` in the exemplar need a stated reason. Its own tests give none. Do not copy the bands without measuring them on our data.
- The samtools flagstat, idxstats and stats tables are text. If they are byte-stable across runs, exact file comparison is the right check. That is a test-plan decision (phase 9).

## 7. Ledger changes (summary)

- **Open entries closed by this comparison:** none. The precedent covers part of four open entries (`chr-relabel-and-rekey-recipe`, `reads-mixed-collection-type`, `reads-rejoin-mixed-types`, `paired-concat-join-drops-silently`). Those stay open, with the precedent recorded in the discoveries below.
- **New gaps (no corpus precedent):** `bam-collate-fastq-no-corpus-precedent`, `per-element-classifier-gating-no-corpus-precedent`.
- **New discoveries:** four (exemplar structure, a partial BAM-to-FASTQ precedent via samtools_fastx, the ATAC-seq flag-selection precedent, size-only exemplar tests). The BAM-to-FASTQ item was corrected in phase 6: the precedent is partial, and name collation has none.
- **Brief-change recommendation:** BC-1 (two outputs), status proposed.

## 8. Caveats

- `gxwf convert` exited with status 1 on the nearest exemplar, because its tools are not in the local tool cache. It still wrote the full conversion (387 lines). The slice was checked to parse and to resolve every step source.
- The slice replaces the manifest-preparation chain with two inputs, `SRA_list` and `relabel_table`. Those inputs are placeholders, not exemplar evidence.
- The full conversion is kept in the job temporary directory, outside the run directory, because it is not a declared artifact.
- The corpus clone is shallow and sparse (`workflows/` only), at `c07557f`. No tool discovery was run, and no workflow was executed.
