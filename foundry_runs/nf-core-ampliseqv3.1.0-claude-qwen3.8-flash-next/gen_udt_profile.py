#!/usr/bin/env python3
"""Generate the compare_profile UDT with verbatim R/configfile embeddings."""
import sys

src = sys.argv[1]
out = sys.argv[2]

def block(path, indent="    "):
    lines = open(path).read().splitlines()
    return "\n".join((indent + ln) if ln else "" for ln in lines)

def text(s, indent="    "):
    return "\n".join((indent + ln) if ln else "" for ln in s.splitlines())

ADJUDICATE = """#!/usr/bin/env python3
# Decide which QIIME2_INTAX pre-processing path the knot-carried table needs.
import sys

with open(sys.argv[1]) as fh:
    first = fh.readline().rstrip("\\n").split("\\t")
    second = fh.readline()

if first and first[0] == "ASV_ID":
    mode = "parse"                 # wide table: source parse_dada2_taxonomy.r path
elif len(first) == 2 and first[1] == "Taxon":
    mode = "strip_header"          # raw QIIME2 export: Feature ID<TAB>Taxon
elif len(first) >= 2 and second and len(second.rstrip("\\n").split("\\t")) == len(first):
    # headerless two-column (SIDLE filttax): first row is data, not header
    mode = "passthrough"
else:
    mode = "parse"
print(mode)
"""

BUILD = """#!/usr/bin/env Rscript
# Build the observed taxonomic profile table (taxon x sample) that the source's
# QIIME2_EXPORT rel_tax / rel-table-<level>.tsv supplies on its QIIME2-input branch.
# tax.tsv is the normalized two-column table (ASV sequence, lineage string) produced by
# the import_taxonomy-identical adjudication; the abundance table is keyed by ASV sequence.
# Lineage labels are trimmed and rejoined with "; " to match the QIIME2 rel_tax style the
# source compares against (its observed side is a QIIME2-exported rel-table).
args <- commandArgs(trailingOnly = TRUE)
tax <- read.table(args[1], sep = "\\t", header = FALSE, stringsAsFactors = FALSE, quote = "", comment.char = "")
abund <- read.table(args[2], sep = "\\t", header = TRUE, stringsAsFactors = FALSE, check.names = FALSE, comment.char = "", quote = "")
for (i in 2:ncol(abund)) { abund[[i]] <- suppressWarnings(as.numeric(abund[[i]])) }
abund[[1]] <- as.character(abund[[1]])
colnames(abund)[1] <- "ID"

lineage <- vapply(tax$V2, function(x) paste(trimws(strsplit(x, ";")[[1]]), collapse = "; "), character(1))
names(lineage) <- tax$V1

keep <- abund$ID %in% names(lineage)
if (!all(keep)) {
	print(paste("WARN -", sum(!keep), "observed sequences have no taxonomy entry and are omitted from the profile:", paste(abund$ID[!keep], collapse = ",")))
}
d <- abund[keep, ]
lab <- lineage[d$ID]

m <- as.matrix(d[, -1, drop = FALSE])
storage.mode(m) <- "numeric"
rs <- rowsum(m, factor(lab))
out <- data.frame(taxon = rownames(rs), rs, check.names = FALSE)
write.table(out, "observed_profile.tsv", sep = "\\t", quote = FALSE, row.names = FALSE, na = "")
"""

HELP = """Galaxy replica of the nf-core/ampliseq COMPARE_PROFILE process
    (modules/local/compare_profile/main.nf, r-base:4.2.1 container pin matched) as invoked by
    subworkflows/local/comparison_wf/main.nf:54-59 with ext.mode=level and ext.fbeta=2
    (conf/modules.config:1322-1324). bin/compare_profile.r is embedded verbatim; the profile
    summary/per-sample tsv and the lineplot svg/png are published, profile.log is not (stderr
    stays in the job output; log/warnings dropped precedent). The source's observed input is
    the max-level QIIME2_EXPORT rel-table-<level>.tsv, which the source only produces on the
    run_qiime2 && !skip_abundance_tables input branch - on the main branch the channel is
    empty and this process never runs. This v1 realization instead derives the observed
    profile from the main-path taxonomy and abundance tables (tax_table_knot + asv_table_knot,
    the template's wiring): the import_taxonomy-identical shape adjudication (adjudicate.py +
    verbatim bin/parse_dada2_taxonomy.r, or header-strip/passthrough) normalizes the knot table
    to sequence+lineage, and build_profile.R joins it to the abundance table and aggregates
    raw abundances per lineage string. Lineage labels are trimmed and rejoined with '; ' to
    match the QIIME2 rel_tax style the source's expected files are written against; passing
    full-depth lineage is equivalent-or-better than the source's max-level slice because
    compare_profile.r evaluates every level 1..max_lev from the lineage strings either way.
    ASVs without a taxonomy row are skipped with a warning (a null knot - no classifier ran -
    leaves the required tax input unsatisfied and Galaxy skips the step, the import_taxonomy
    precedent, mirroring the source's absent-observed-channel behavior). fbeta=2 and
    mode=level are fixed shell literals (source ext values, no interface params); the tag
    column is a constant (val_md5sum_version dropped with pipeline_info, precedent)."""

INPUTS = """- name: tax
  type: data
  format:
  - tabular
  - tsv
  - txt
  label: ASV taxonomy table (branch knot)
  help: The one taxonomy table chosen by tax_table_knot (wide ASV_ID+ranks, Feature ID/Taxon, or headerless two-column).
- name: table
  type: data
  format:
  - tabular
  - tsv
  label: ASV count table
  help: Abundance table keyed by ASV sequence (asv_table_knot), first column then one column per sample.
- name: expected
  type: data
  format:
  - tabular
  - tsv
  label: Expected taxonomic profile
  help: Expected profile tsv (taxon lineage in column one, one abundance column per sample; params.expected_profile).
- name: tag
  type: text
  label: Run tag column
  value: ampliseq
  help: Constant written to the tag column of the tsv outputs (source val_md5sum_version, dropped with pipeline_info).
"""

OUTPUTS = """- name: performance
  type: data
  format: tsv
  from_work_dir: profile_summary.tsv
  label: Profile summary per level and metric
- name: performance_per_sample
  type: data
  format: tsv
  from_work_dir: profile_per-sample.tsv
  label: Per-sample per-level profile metrics
- name: svg
  type: data
  format: svg
  from_work_dir: profile_lineplot.svg
  label: Profile metrics lineplot (svg)
- name: png
  type: data
  format: png
  from_work_dir: profile_lineplot.png
  label: Profile metrics lineplot (png)
"""

SHELL = """MODE="$(python3 adjudicate.py $(inputs.tax.path))";
  echo "input taxonomy shape: $MODE" >&2;
  if [ "$MODE" = "strip_header" ]; then
    tail -n +2 "$(inputs.tax.path)" > tax.tsv
  elif [ "$MODE" = "passthrough" ]; then
    cp "$(inputs.tax.path)" tax.tsv
  else
    Rscript parse_dada2_taxonomy.r "$(inputs.tax.path)"
  fi;
  Rscript build_profile.R tax.tsv "$(inputs.table.path)";
  Rscript compare_profile.r "$(inputs.tag.value)" observed_profile.tsv "$(inputs.expected.path)" 2 level > profile.log"""

text_out = f"""class: GalaxyUserTool
id: ampliseq_compare_profile
version: 1.0.0
name: Observed-vs-expected taxonomic profile comparison (ampliseq)
description: Per-level profile classification/distance/correlation metrics comparing the pipeline taxonomy profile to an expected profile
license: GPL-3.0-or-later
help:
  format: markdown
  content: >-
{'    ' + HELP}
container: quay.io/biocontainers/r-base:4.2.1
inputs:
{INPUTS}outputs:
{OUTPUTS}configfiles:
- filename: adjudicate.py
  content: |
{text(ADJUDICATE)}
- filename: parse_dada2_taxonomy.r
  content: |
{block(f"{src}/bin/parse_dada2_taxonomy.r")}
- filename: build_profile.R
  content: |
{text(BUILD)}
- filename: compare_profile.r
  content: |
{block(f"{src}/bin/compare_profile.r")}
shell_command: |
  {SHELL}
"""
open(out, "w").write(text_out)
print("wrote", out, len(text_out))
