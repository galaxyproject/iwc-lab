#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/open-requirements.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("runtime check deferred to phase 11'") or t.rstrip().endswith("phase 11'"), "unexpected ledger tail"
assert "summary-report-simplified-rmd" not in t
entry = """
- id: summary-report-simplified-rmd
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'summary_report concretized as embedded UDT ampliseq_summary_report pinning the
    module''s exact mulled container (quay.io/biocontainers/mulled-v2-b2ec1fea... with the
    full tag in the evidence item; verified present on quay; env r-base=4.2.3 +
    r-rmarkdown/r-knitr/r-data.table): rmarkdown::render mirroring the module''s call, an
    AUTHORED simplified template.Rmd (title/abstract passthrough + abundance overview from
    the long counts table + taxonomy overview from the consolidated table), inputs
    counts(optional)/tax/abstract(optional)/report_title(text), fixed
    summary_report.html output rewired to the summary_report workflow output.'
  rationale: 'The module renders the pipeline''s bundled template.Rmd with ~70 params from
    every pipeline output plus css/logo assets - assets the draft interface excluded
    (excluded-params note) and the step plan explicitly ruled ("render a simplified
    report"). Embedding the 1000+ line untrusted template and feeding it phantom params
    would fail on the first unguarded params$ access, so the simplified Rmd is authored
    content (deviation stated in tool help and here). The two summary tables mirror the
    interface''s kept summary outputs (counts + taxonomy; the Parquet pair from
    parquet-two-jobs). Optional counts/abstract reproduce the module''s per-entry
    channel-presence guards via empty-path file.exists branches (skip_abundance_tables
    drops the counts section exactly as the empty channel does upstream). *.svg passthrough
    output dropped (simplified report writes no standalone svgs); versions.yml dropped
    (pipeline_info precedent). The report_abstract data input matches the module''s staged
    file input - no text-injection surface.'
  evidence:
  - 'modules/local/summary_report/main.nf (full input list + params_list_named assembly +
    render call quoted in help) + environment.yml (r-base=4.2.3, r-rmarkdown=2.22,
    r-knitr=1.43, r-data.table=1.14.8)'
  - 'quay tags list for mulled-v2-b2ec1fea5791d428eebb8c8ea7409c350d31dada: exactly the
    pinned tag a447f6b7a6afde38352b24c30ae9cd6e39df95c4-1'
  - 'not run locally: no Rscript/rmarkdown; simplified Rmd is authored content, first
    render check deferred to phase 11'
"""
open(L, "w").write(t.rstrip() + "\n" + entry.lstrip("\n"))
print("appended summary-report-simplified-rmd")
