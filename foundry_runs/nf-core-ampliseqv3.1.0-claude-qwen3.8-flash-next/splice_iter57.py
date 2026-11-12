#!/usr/bin/env python3
"""Iteration 57: concretize summary_report as simplified-report UDT; rewire output."""

DRAFT = "/home/abennett/nf-core-ampliseq/galaxy-workflow-draft.gxwf.yml"

def emb(p):
    return "\n".join(("      " + ln) if ln else "" for ln in open(p).read().splitlines())

step = f"""  summary_report:
    label: summary_report
    doc: >-
      SUMMARY_REPORT - simplified HTML report (module pins its mulled container verbatim
      and keeps the summary_report.html name; the bundled template/css/logo assets the
      interface excluded are replaced by an authored simplified Rmd covering title +
      abstract passthrough and the counts + taxonomy summaries, per the step plan).
    when: '!$(inputs.skip_report)'
    in:
      counts: summary_counts/tsv
      tax: tax_table_knot/data_param
      abstract: report_abstract
      report_title: report_title
    out: [ {{id: report}} ]
    run:
{emb("/home/abennett/nf-core-ampliseq/udt-summary-report.yml")}
"""

text = open(DRAFT).read()
start_key = "  summary_report:\n    tool_id: TODO"
end_key = "\ncomments:\n"
assert text.count(start_key) == 1, "summary_report anchor not unique"
assert text.count(end_key) == 1, "comments anchor not unique"
i = text.index(start_key); j = text.index(end_key)
assert i < j
new = text[:i] + step + text[j:]

out_old = "summary_report: { outputSource: summary_report/TODO_report, label: summary_report }"
assert new.count(out_old) == 1, "summary_report ref not unique"
new = new.replace(out_old, "summary_report: { outputSource: summary_report/report, label: summary_report }")
assert "summary_report/TODO" not in new, "residual summary_report/TODO"

open(DRAFT, "w").write(new)
print("spliced summary_report:", j - i, "->", len(step), "; output rewired")
