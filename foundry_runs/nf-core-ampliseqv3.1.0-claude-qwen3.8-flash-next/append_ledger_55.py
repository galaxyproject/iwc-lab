#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/open-requirements.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("runtime check deferred to\n    phase 11'"), "unexpected ledger tail"
assert "filter-samples-r-intersect-identity-correction" not in t
entry = """
- id: filter-samples-r-intersect-identity-correction
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'filter_samples concretized as embedded UDT ampliseq_filter_samples - the
    LOCAL modules/local/filter_samples base-R mutual sample intersect (meta[,1] in abund
    columns AND abund columns in meta[,1], both rewritten, stop() on empty intersection)
    on quay.io/biocontainers/r-base:4.2.1 (module''s exact container; conda r-base=4.2.1,
    base R only) - identity corrected from the template-pinned q2d2
    qiime2__feature_table__filter_samples. Realized at the source''s channel position:
    in = (metadata, asv_table_knot), out = (metadata, table); NEW pick_value knot
    asv_table_for_import (first_or_skip: filter_samples/table else asv_table_knot/data_param)
    now feeds import_table (was the bare knot), and the six QIIME2 consumers (core_metrics,
    alpha_rarefaction, barplots, ancom, ancombc, adonis) rewired from filter_samples/TODO_table
    to import_table/qza. Step keeps the template when metadata != null.'
  rationale: 'The q2d2 wrapper cannot compute this step: q2 feature-table filter-samples is
    a no-op without --p-where and there is no static expression for "keep samples present
    in the metadata dataset" (wrapper-choice mismatch -> author branch, import_table
    identity-correction precedent). Template wiring also inverted the source order: the
    source runs FILTER_SAMPLES before QIIME2_INASV and REBINDS ch_asv_table
    (workflows/ampliseq.nf:1144-1146), so QIIME2 only ever sees the intersected table -
    reproducing the rebind needs the pick knot (draft-first_or_skip-knot idiom,
    asv_table_knot; bounded edit, export_tree precedent). The knot is sound because the
    fallback branch is always non-null, and priority order makes the filtered table win
    when both exist. Display-only *.log outputs dropped: filenames are the messages
    themselves, consumed only by log.warn echo; the fatal stop() path is kept. CARRIED
    FORWARD: the source also rebinds ch_metadata (same lines) - future QIIME2 metadata
    consumers (core_metrics metadata qza etc.) should prefer filter_samples/metadata when
    metadata != null; phyloseq/tse sam stays on the raw metadata input (v1 bounded
    deviation: filtered-vs-raw differ only by samples absent from the ASV table).'
  evidence:
  - 'modules/local/filter_samples/main.nf + environment.yml (inline R script quoted in the
    UDT configfile - 17-line verbatim proof modulo $var->args, heredoc dedent, \\\\t
    unescape; container depot/biocontainers r-base:4.2.1)'
  - 'workflows/ampliseq.nf:1142-1147 (if (params.metadata && !params.multiregion)
    FILTER_SAMPLES(ch_metadata, ch_asv_table); both channels reassigned; out.log only
    echoed via log.warn) and :1150 QIIME2_INASV(ch_asv_table) consuming the rebound table'
  - 'decontam_run sheet: metadata left on the raw input - decontam precedes FILTER_SAMPLES
    in the source, unaffected by the rebind'
  - 'not run locally: no Rscript; runtime check deferred to phase 11'
"""
open(L, "w").write(t.rstrip() + "\n" + entry.lstrip("\n"))
print("appended filter-samples-r-intersect-identity-correction")
