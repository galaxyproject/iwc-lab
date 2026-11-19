#!/usr/bin/env python3
"""Generate the two comparison UDTs with the source R scripts embedded verbatim."""
import sys

def block(path, indent):
    with open(path) as fh:
        lines = fh.read().splitlines()
    out = []
    for ln in lines:
        out.append((indent + ln) if ln else "")
    return "\n".join(out)

HELP_B = """Galaxy replica of the nf-core/ampliseq COMPARE_SEQUENCES process
    (modules/local/compare_sequences/main.nf) as invoked by
    subworkflows/local/comparison_wf/main.nf:33-41 with similarity_threshold "0.80" and
    query_or_target = params.expected_sequences_region (schema enum alignment|observed|expected,
    default observed - exactly the values compare_sequences.r accepts). The R script
    bin/compare_sequences.r is embedded verbatim as a configfile; the command line mirrors
    the module script block (blast6 table, observed abundance table, expected abundance table,
    empty prefix, threshold, region). The optional expected-abundance input reproduces the
    source's ch_expected_abundances.ifEmpty([]) staging - when it is absent the substitution
    is empty, file.exists(\"\") is FALSE in R and the script compares against all sequences,
    which is the source behavior. FASTA/table key note - this draft's tables are keyed by
    ASV sequence, matching the source (dada2 ids are sequences), so the alignment 'query'
    column joins the table 'ID' column directly. Recorded deviations: the
    nucleotide-differences.log, Warnings.txt and md5sum_version.txt publications are not
    emitted (log/stderr stays in the job output; pipeline_info artifacts dropped precedent);
    per-sample barplots and per-sample tables are published as list collections instead of
    Nextflow .collect() fan-in."""

HELP_C = """Galaxy replica of the nf-core/ampliseq COMPARE_PERFORMANCE process
    (modules/local/compare_performance/main.nf) as invoked by
    subworkflows/local/comparison_wf/main.nf:47-51 on COMPARE_SEQUENCES.out.matches. The R
    script bin/compare_performance.r is embedded verbatim as a configfile. Arguments follow
    the module script block; fbeta=2 and mismatch_threshold=0 are the source values
    (conf/modules.config ext.fbeta = 2; ext.mismatch_threshold = params.expected_sequences_mismatches,
    schema default 0, and this draft has no interface input for mismatches - fixed, recorded).
    merge_mode maps to the expected_sequences_merge interface input (enum all|observed|expected|none,
    default all). The source fires this process only when the expected-abundance channel is
    non-empty (an empty path input never triggers the task); here the step carries a when
    guard over both expected inputs instead. Deviations: the first script argument tag is the
    source's val_md5sum_version (md5 of params + pipeline version) used only as a constant
    column in the tsv outputs - here it is a constant text input (pipeline_info artifacts
    dropped precedent); performance.log and Warnings.txt are not published (stderr stays in
    the job output); per-sample svgs and the boxplots are published as list collections."""

def udt(tid, name, desc, help_text, inputs, outputs, shell, rsrc, rname):
    return f"""class: GalaxyUserTool
id: {tid}
version: 1.0.0
name: {name}
description: {desc}
license: GPL-3.0-or-later
help:
  format: markdown
  content: >-
{'    ' + help_text.lstrip() if help_text == help_text.lstrip() else help_text}
container: quay.io/biocontainers/r-base:4.2.1
inputs:
{inputs}outputs:
{outputs}configfiles:
- filename: {rname}
  content: |
{block(rsrc, "    ")}
shell_command: |
  {shell}
"""

INPUTS_B = """- name: alignment
  type: data
  format:
  - tabular
  - tsv
  label: Alignment table (userfields)
  help: vsearch --userout table with columns query,target,ql,tl,qilo,qihi,tilo,tihi,gaps,mism,qstrand (no header).
- name: observed
  type: data
  format:
  - tabular
  - tsv
  label: Observed ASV count table
  help: ASV table keyed by sequence, first column then one column per sample.
- name: expabund
  type: data
  format:
  - tabular
  - tsv
  optional: true
  label: Expected abundance table
  help: Optional expected-abundance tsv; when absent the script compares against all sequences (source ifEmpty([]) staging).
- name: similarity
  type: float
  label: Similarity threshold
  value: 0.8
  help: Alignment similarity used by the alignment step; only affects the ">=20%" mismatch bucket label (source 0.80).
- name: region
  type: text
  label: Mismatch region
  value: observed
  help: Whose mismatches to count - observed, expected or alignment (params.expected_sequences_region).
"""

OUTPUTS_B = """- name: matches
  type: data
  format: tsv
  from_work_dir: nucleotide-differences.tsv
  label: Alignment table with mismatch_final column (COMPARE_SEQUENCES matches)
- name: matches_per_sample
  type: collection
  collection_type: list
  format: tsv
  label: Per-sample mismatch counts
  discover_datasets:
  - discover_via: pattern
    pattern: '*_nucleotide-differences_per-sample.tsv'
- name: svg
  type: collection
  collection_type: list
  format: svg
  label: Per-sample nucleotide-distance barplots (svg)
  discover_datasets:
  - discover_via: pattern
    pattern: '*_nucleotide-differences_barplot.svg'
- name: png
  type: collection
  collection_type: list
  format: png
  label: Per-sample nucleotide-distance barplots (png)
  discover_datasets:
  - discover_via: pattern
    pattern: '*_nucleotide-differences_barplot.png'
"""

INPUTS_C = """- name: alignment
  type: data
  format:
  - tabular
  - tsv
  label: Matches table with mismatch_final
  help: The nucleotide-differences.tsv emitted by ampliseq_compare_sequences (header included).
- name: observed
  type: data
  format:
  - tabular
  - tsv
  label: Observed ASV count table
  help: ASV table keyed by sequence, first column then one column per sample.
- name: expabund
  type: data
  format:
  - tabular
  - tsv
  optional: true
  label: Expected abundance table
  help: Expected-abundance tsv; required in practice (the step when-guard mirrors the source channel gating).
- name: tag
  type: text
  label: Run tag column
  value: ampliseq
  help: Constant written to the tag column of the tsv outputs (source val_md5sum_version, dropped with pipeline_info).
- name: merge
  type: text
  label: Merge mode
  value: all
  help: Aggregate matched observed/expected IDs before stats - all, observed, expected or none (params.expected_sequences_merge).
"""

OUTPUTS_C = """- name: performance
  type: data
  format: tsv
  from_work_dir: performance_summary.tsv
  label: Performance summary (median/mean/min/max per metric)
- name: performance_per_sample
  type: data
  format: tsv
  from_work_dir: performance_per-sample.tsv
  label: Per-sample performance metrics
- name: abundance_table_per_sample
  type: data
  format: tsv
  from_work_dir: abundances_per-sample.tsv
  label: Per-sample merged expected/observed abundances
- name: svg
  type: collection
  collection_type: list
  format: svg
  label: Abundance barplots, scatter and rank-abundance svgs (per sample + boxplot)
  discover_datasets:
  - discover_via: pattern
    pattern: '*.svg'
- name: png
  type: collection
  collection_type: list
  format: png
  label: Performance boxplots (png)
  discover_datasets:
  - discover_via: pattern
    pattern: '*.png'
"""

SHELL_B = ('Rscript compare_sequences.R "$(inputs.alignment.path)" "$(inputs.observed.path)" '
           '"$(inputs.expabund.path)" "" "$(inputs.similarity.value)" "$(inputs.region.value)" '
           '> nucleotide-differences.log')
SHELL_C = ('Rscript compare_performance.R "$(inputs.tag.value)" "$(inputs.alignment.path)" '
           '"$(inputs.observed.path)" "$(inputs.expabund.path)" 2 0 "$(inputs.merge.value)" '
           '> performance.log')

src = sys.argv[1]
out = sys.argv[2]
which = sys.argv[3]
if which == "B":
    text = udt("ampliseq_compare_sequences",
               "Nucleotide-difference comparison to expected sequences (ampliseq)",
               "Derive per-ASV mismatch counts from the observed-vs-expected alignment and per-sample mismatch barplots",
               HELP_B, INPUTS_B, OUTPUTS_B, SHELL_B,
               f"{src}/bin/compare_sequences.r", "compare_sequences.R")
else:
    text = udt("ampliseq_compare_performance",
               "Expected-vs-observed performance metrics (ampliseq)",
               "Per-sample absence/presence (precision, recall, F-beta, ...) and abundance-error metrics from the matches table",
               HELP_C, INPUTS_C, OUTPUTS_C, SHELL_C,
               f"{src}/bin/compare_performance.r", "compare_performance.R")
with open(out, "w") as fh:
    fh.write(text)
print("wrote", out, len(text))
