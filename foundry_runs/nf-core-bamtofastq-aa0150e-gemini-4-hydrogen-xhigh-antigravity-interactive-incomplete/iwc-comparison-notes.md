# IWC Exemplar Comparison — nf-core/bamtofastq

## Verdict

- **Result:** **No nearest exemplar**
- **Reason:** The local IWC corpus (`~/.foundry/iwc/workflows`, inspected 2026-11-13) contains no workflow whose primary domain or analysis intent is converting BAM/CRAM alignment collections into raw paired-end and single-end FASTQ reads with read-flag splitting and FASTQ integrity verification.
- **Sibling exemplar file (`iwc-exemplar.gxwf.yml`) & inline excerpt:** Omitted per `compare-against-iwc-exemplar` rules when no nearest domain exemplar exists.

## Corpus Search & Candidates Evaluated

| Candidate IWC Workflow | Domain / Intent | Input Topology | Shared Tools / Patterns | Confidence / Disposition |
|---|---|---|---|---|
| `microbiome/host-contamination-removal/host-contamination-removal-long-reads` | Microbiome host read depletion starting from long-read FASTQ | `list` of `fastqsanger` (vs `list` of `bam`/`cram`) | Uses `samtools_fastx` (`1.22+galaxy2`) on unmapped BAM output (`outputs: [other]`, `fastqsanger`) + `multiqc` | **No nearest exemplar** (wrong input topology and domain; single unmapped-read extraction step only) |
| `read-preprocessing/short-read-qc-trimming` | Short-read FASTQ quality trimming and QC | `list:paired` `fastqsanger(.gz)` | Uses `multiqc` collection reduction over per-sample QC (`fastp`) and standard `list:paired` I/O conventions | **No nearest exemplar** (starts from FASTQ rather than alignments; shares only generic QC aggregation) |
| `transcriptomics/rnaseq-pe` | Paired-end RNA-seq quantification | `list:paired` `fastqsanger(.gz)` | Conditional `when:` branches merged via `iuc/pick_value` (`0.2.0`), separate MultiQC branches + `pick_value` for optional QC inputs | **Cross-domain pattern reference only** (unrelated science domain; structurally informative for conditional MultiQC and `pick_value`) |
| `variant-calling/generic-variant-calling-wgs-pe` | WGS PE variant calling | `list:paired` `fastqsanger(.gz)` | Uses `iuc/samtools_view`, `devteam/samtools_stats`, and `iuc/multiqc` | **Cross-domain pattern reference only** (unrelated science domain; downstream alignment QC only) |

## Structural Comparison Against Upstream Galaxy Design Briefs

Comparing `nextflow-galaxy-interface.md` and `nextflow-galaxy-data-flow.md` against IWC conventions across the sampled corpus:

| Design Area | Proposed Upstream Design | Corpus / Schema Observation | Routing Surface |
|---|---|---|---|
| Primary input topology (`alignments`) | `list` collection accepting `bam` and `cram` datasets; dataset metadata replaces external index columns | Matches IWC flat sample-indexed `list` conventions (sample ID = `element_identifier`); mixed `[bam, cram]` format acceptance on `type: collection` needs schema verification in `gxformat2` | **Template** (`alignments-mixed-bam-cram-datatype`) |
| Single-end & unmapped BAM -> FASTQ (`samtools_collatefastq*`) | Map `samtools` collate/fastq over `alignments` split into `paired_alignments` and `single_alignments` | `host-contamination-removal-long-reads` confirms `iuc/samtools_fastx` exists for simple extraction, while `nf-core/bamtofastq` specifically uses `samtools collate` semantics (name-collation, `-f`, `-r reads_in_memory`, split `-1/-2` + `-0` + `-s` handling). Wrapper capability must be settled in tool discovery | **Tool-step** (`discover-shed-tool` / `author-galaxy-tool-wrapper`) |
| Conditional `chr` filter (`samtools_chr` -> `pick_value`) | Inline `when: chr` on `samtools_chr` + `pick_value` (`first_non_null`) merging `[samtools_chr_out, alignments]` | Cross-domain `rnaseq-pe` uses `iuc/pick_value` (`0.2.0`) on mutually exclusive single datasets (`param_type: data`). Here `alignments` is always non-null while `samtools_chr` is conditional over a `list` collection; `pick_value` collection-mode (`param_type: collection`) and null-branch ordering must be confirmed during template/step authoring | **Template** + **Tool-step** (`chr-pick-value-collection-compatibility`) |
| Optional QC branches feeding `MultiQC` (`!no_read_qc`, `!no_stats`) | Single `multiqc` step receiving `samtools_flagstat`, `samtools_idxstats`, `samtools_stats`, `fastqc_pre_conversion_zip`, and `fastqc_post_conversion_zip`, gated by `!(no_read_qc && no_stats)` | `rnaseq-pe` duplicates `multiqc` across branches + merges HTML via `pick_value` because optional `software_cond` inputs that receive skipped (`NO_REPLACEMENT`) collections can fail or misbind depending on wrapper optionality; with 2 independent flags (`no_read_qc`, `no_stats`) plus CRAM-skipped `fastqc_pre_conversion`, inspect `iuc/multiqc` optional input behavior carefully before locking topology | **Tool-step** (`multiqc-partial-skip-input-tolerance`) -> **Template/Repair** if split needed |
| Output labels, hiding intermediates, and collections | Descriptive snake/human labels for 11 outputs (`paired_reads`, `single_end_reads`, etc.) | Matches IWC practice: expose explicit public outputs and `hide: true` all intermediate BAMs, filter flags, and intermediate FASTQs; preserve `list` / `list:paired` identifiers for tests | **Template** |
| Test strategy & assertions | Exact MD5 / content checks grounded in `tests/default.nf.test.snap` (`test`, `test2` paired FASTQs, `flagstat`, `idxstats`, `stats`, `fastqutils_info`) + structural checks for reports/HTML | Consistent with `iwc-shortcuts-anti-patterns.md` and `iwc-test-data-conventions.md`: do not degrade deterministic text/FASTQ checks to broad `sim_size` or existence checks; inspect tool-level nondeterminism (e.g., FASTQ headers, MultiQC timestamps) before choosing `checksum` vs `diff` / `assert_has_text` | **Test-plan** (`nextflow-test-to-galaxy-test-plan`, `implement-galaxy-workflow-test`) |

## Ledger Obligations Summary

- All prior entries in `open-requirements.ledger.yml` remain open (`0` resolved by corpus exemplar because no BAM/CRAM-to-FASTQ domain exemplar exists in IWC).
- Added corpus discoveries documenting the absence of a BAM-to-FASTQ domain exemplar and the cross-domain `pick_value` / `multiqc` conditional patterns to verify in Phases 6–7.
