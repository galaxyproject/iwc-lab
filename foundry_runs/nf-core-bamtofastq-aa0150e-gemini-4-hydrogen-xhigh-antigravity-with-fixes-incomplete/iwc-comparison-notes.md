# IWC Exemplar Comparison Notes: nf-core/bamtofastq

- **Corpus searched**: Local IWC checkout (`~/.foundry/iwc`, `galaxyproject/iwc` commit `c07557f`)
- **Upstream briefs reviewed**: `nextflow-galaxy-interface.md`, `nextflow-galaxy-data-flow.md`, `open-requirements.ledger.yml`
- **Overall nearest exemplar verdict**: **No nearest domain exemplar** (no High- or Medium-confidence BAM/CRAM-to-FASTQ workflow exists in IWC). Low-confidence cross-domain pattern matches are documented below for specific Galaxy DAG motifs (`sync-collections-by-identifier`, mixed `[bam, cram]` list input, `samtools_fastx`, `cat1` + `__UNZIP_COLLECTION__`, and `when:` + `pick_value` + `MultiQC`). Per `compare-against-iwc-exemplar` rules, `iwc-exemplar.gxwf.yml` is omitted because no High or Medium domain exemplar was found.

## 1. Candidate Workflows Evaluated

| IWC Workflow ID | Domain | Confidence | Shared Features | Why Not a Domain Exemplar |
|---|---|---|---|---|
| `microbiome/pathogen-identification/nanopore-pre-processing/Nanopore-Pre-Processing` | Microbiome Nanopore QC & host removal | **Low** (cross-domain tool pattern) | Uses `samtools_fastx` (`outputs: ["other"]`, `fastqsanger.gz`), `fastqc`, and `multiqc` on mapped/unmapped BAM subsets. | Input is raw Nanopore `list[fastqsanger]`; BAM comes from internal `minimap2` + `bamtools_split_mapped`, with no CRAM, no paired-end R1/R2 split, and no `samtools` stats/collate. |
| `epigenetics/correlation-of-samples-on-peaks/correlation-of-samples-on-peaks` | Epigenetics peak correlation | **Low** (input topology match) | Only IWC workflow accepting `collection_type: list` with `format: [cram, bam]`. | Runs `deeptools_multi_bam_summary` and `plotCorrelation`; shares no `samtools`, `fastqc`, `multiqc`, or FASTQ conversion steps. |
| `amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-its/mgnify-amplicon-pipeline-v5-its` | Amplicon ITS classification | **Low** (DAG motif match) | Exact 3-step `sync-collections-by-identifier` recipe (`__FILTER_EMPTY_DATASETS__` -> `collection_element_identifiers` -> `__FILTER_FROM_FILE__`). | Completely different domain (rRNA/ITS annotation); no alignment/BAM/FASTQ tools. |
| `microbiome/samestr-shared-strain-detection/samestr-shared-strain-detection` | Microbiome strain profiling | **Low** (DAG motif match) | Uses `cat1`, `__UNZIP_COLLECTION__`, `when: $(inputs.when)` with `map_param_value`, `pick_value`, and `__FILTER_EMPTY_DATASETS__`. | Consumes `list:paired` FASTQ rather than BAM/CRAM; no FASTQ extraction or MultiQC. |
| `VGP-assembly-v2/Scaffolding-HiC-VGP8/Scaffolding-HiC-VGP8` | Vertebrate genome scaffolding | **Low** (tool & conditional pattern) | Uses `samtools_merge`, `samtools_stats` (with `addref_cond.addref_select: history` taking FASTA directly), `when:` + `pick_value`, and `multiqc`. | Hi-C scaffolding domain; no BAM-to-FASTQ or FastQC. |
| `transcriptomics/rnaseq-pe/rnaseq-pe` | RNA-seq quantification | **Low** (conditional QC pattern) | Uses `when: $(inputs.when)` on `featurecounts` and extra QC subworkflow wired to conditional `multiqc` + `pick_value`. | RNA-seq domain; `rnaseq-pe-tests.yml` sets `Use featureCounts: true` and `Generate additional QC reports: true`, so partial-skip MultiQC behavior is not test-verified. |

## 2. Structural Diff Against Upstream Galaxy Design Briefs

### Template / Data-Flow Guidance (for `nextflow-summary-to-galaxy-template`)

1. **`sync-collections-by-identifier` concrete 3-step realization (`n_keep_*_ids` -> `n_sync_*`)**:
   - Upstream brief (`nextflow-galaxy-data-flow.md`) used an abstract `sync-collections-by-identifier` placeholder.
   - IWC (`mgnify-amplicon-pipeline-v5-its` steps `_unlabeled_step_2`, `_unlabeled_step_3`, `_unlabeled_step_4`; also `mgnify-amplicon-pipeline-v5-complete`) resolves this cleanly with:
     1. `__FILTER_EMPTY_DATASETS__` on the marker collection;
     2. `collection_element_identifiers` (`iuc/collection_element_identifiers/0.0.3`) to extract surviving element IDs into a text list;
     3. `__FILTER_FROM_FILE__` (`how.how_filter: remove_if_absent`, `how.filter_source` <- extracted IDs, `input` <- `active_alignments`, `output_filtered` -> downstream).
   - **Action**: Materialize `collection_element_identifiers` + `__FILTER_FROM_FILE__` directly in Phase 6 for both `paired_alignments` and `single_alignments`.

2. **`input_alignments` collection shape (`list` of `[cram, bam]`)**:
   - Upstream brief (`nextflow-galaxy-interface.md`) chose `type: collection`, `collection_type: list`, `format: [bam, cram]`.
   - Confirmed by `correlation-of-samples-on-peaks` (`format: [cram, bam]`, `collection_type: list`). No interface change needed.

3. **Mixed `[bam, cram]` datatype filtering before `FASTQC_PRE_CONVERSION` (`n_filter_bam`)**:
   - No IWC workflow filters a mixed `[bam, cram]` list by dataset datatype prior to FastQC.
   - **Action**: Carry `cram-mixed-list-preqc-filtering` open into Phase 6/7; emit a placeholder/drafty step in Phase 6 and realize it in Phase 7 (for example, an expression tool or lightweight UDT that separates or passes only BAM datasets without failing on CRAM).

4. **Conditional pass-through (`n_samtools_chr` + `n_pick_active`) and `when:` wiring**:
   - IWC workflows (`samestr-shared-strain-detection`, `rnaseq-pe`, `metagenomic-assembly`) wire `when: $(inputs.when)` using explicit `when` inputs (via `map_param_value` or boolean workflow inputs) and merge conditional vs fallback paths with `toolshed.g2.bx.psu.edu/repos/iuc/pick_value/pick_value/0.2.0` (`pick_style: first` or `only`, `param_type: data`, mapped over collections).
   - **Action**: Verify in Phase 6/7 that `chr` (an optional `string` input) converts cleanly to a boolean `when` trigger (e.g., `$(inputs.chr !== null && inputs.chr !== "")` or `map_param_value`) and that `pick_value` selects `n_samtools_chr` output over `input_alignments` cleanly when `chr` is null.

5. **Paired FASTQ concatenation (`n_pe_cat_r1`, `n_pe_cat_r2`)**:
   - `samestr-shared-strain-detection` (`Concatenate paired and orphaned reads`) uses built-in `cat1` (`input1` + `queries_0|input2`) before `__UNZIP_COLLECTION__`.
   - **Action**: Retain `cat-fastq-gzip-parity` open for Phase 7 to verify `cat1` (or `tp_cat`) produces valid multi-member `.fastqsanger.gz` compatible with `fastqc` and `fastq_info`.

### Tool-Step Issues (Deferred to Phase 7 `advance-galaxy-draft-step`)

1. **`samtools_fastx` vs `samtools collate ... -O | samtools fastq -N`**:
   - `Nanopore-Pre-Processing` demonstrates `iuc/samtools_fastx` (`outputs: ["other"]`, `output_fmt_select: fastqsanger.gz`) for single-end read extraction. Phase 7 must check whether `samtools_fastx` collates by read name or requires an upstream `samtools_collate` / combined UDT (especially for paired-end R1/R2 ordering and `samtools_collate_fast` / `reads_in_memory`). Keep `samtools-collate-fastq-wrapper-gap` open.
2. **Direct FASTA handling (`reference-fasta-fai-rebuild-unverified`)**:
   - `Scaffolding-HiC-VGP8` confirms `devteam/samtools_stats` accepts an explicit `fasta` file (`addref_cond.addref_select: history`) without an explicit `fasta_fai` workflow input. Phase 7 must verify the same for `samtools_view`, `samtools_merge`, and `samtools collate`/`fastq` wrappers/UDTs.
3. **`MultiQC` partial-skip tolerance (`multiqc-partial-skip-safety`)**:
   - `rnaseq-pe` pairs conditional `featurecounts` (`when:`) with `multiqc`, and splits major QC modes into two `when:`-gated `multiqc` steps joined by `pick_value`, yet its test sets both booleans `true`. Phase 7 must inspect `multiqc` XML input optionality when only one of `no_stats` or `no_read_qc` is `true` (or wire separate `when:` branches / `pick_value` if `NO_REPLACEMENT` skips `multiqc`).

### Test Issues (Deferred to Phase 9/10)

- Per `iwc-shortcuts-anti-patterns.md` and `iwc-test-data-conventions.md`, Phase 9/10 must build tests against `tests/default.nf.test.snap` (and paired/single/cram cases where feasible) using meaningful content assertions (e.g., `fastqutils` text output, `samtools` stats/flagstat/idxstats values, FASTQ headers/counts) rather than existence or broad size-only checks.

## 3. Low-Confidence Cross-Domain Pattern Excerpts

> Note: These excerpts come from **Low-confidence cross-domain pattern matches** converted via `gxwf convert --to format2 --compact --no-stateful` solely to illustrate validated Galaxy collection and conditional idioms. They are not domain exemplars.

### Pattern A: `sync-collections-by-identifier` (`amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-its/mgnify-amplicon-pipeline-v5-its`, steps `_unlabeled_step_2`..`_unlabeled_step_4`)

```yaml
  - id: _unlabeled_step_2
    tool_id: __FILTER_EMPTY_DATASETS__
    tool_version: 1.1.0
    in:
      - id: input
        source: LSU and SSU BED
  - id: _unlabeled_step_3
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/collection_element_identifiers/collection_element_identifiers/0.0.3
    tool_version: 0.0.3
    in:
      - id: input_collection
        source: _unlabeled_step_2
  - id: _unlabeled_step_4
    tool_id: __FILTER_FROM_FILE__
    tool_version: 1.1.0
    in:
      - id: how|filter_source
        source: _unlabeled_step_3
      - id: input
        source: Processed sequences
    tool_state:
      how:
        how_filter: remove_if_absent
        __current_case__: 0
        filter_source:
          __class__: ConnectedValue
```

### Pattern B: `samtools_fastx` single-end FASTQ extraction (`microbiome/pathogen-identification/nanopore-pre-processing/Nanopore-Pre-Processing`, step `_unlabeled_step_13` in `.ga`)

```yaml
  - id: extract_single_end_fastq
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/samtools_fastx/samtools_fastx/1.22+galaxy2
    tool_state:
      outputs: ["other"]
      output_fmt_cond:
        output_fmt_select: fastqsanger.gz
        __current_case__: 2
```

### Pattern C: Conditional `when:` + `pick_value` (`transcriptomics/rnaseq-pe/rnaseq-pe`, steps `MultiQC without extra QC`, `MultiQC with extra QC`, `MultiQC HTML report`)

```yaml
  - id: MultiQC HTML report
    label: MultiQC HTML report
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/pick_value/pick_value/0.2.0
    in:
      - id: style_cond|type_cond|pick_from_0|value
        source: MultiQC without extra QC/html_report
      - id: style_cond|type_cond|pick_from_1|value
        source: MultiQC with extra QC/html_report
    tool_state:
      style_cond:
        pick_style: only
        __current_case__: 3
        type_cond:
          param_type: data
          __current_case__: 4
```
