#!/usr/bin/env python3
"""Iteration 53: concretize summary_counts; rewire counts_table workflow output."""

DRAFT = "/home/abennett/nf-core-ampliseq/galaxy-workflow-draft.gxwf.yml"

def emb(p):
    return "\n".join(("      " + ln) if ln else "" for ln in open(p).read().splitlines())

step = f"""  summary_counts:
    label: summary_counts
    doc: >-
      SUMMARY_TABLE_COUNTS - long-format counts checkpoint (asv_id, sample, count > 0,
      gzipped tsv; module R body and wave container verbatim; first column renamed
      positionally - the draft's tables are keyed by sequence with non-standardized headers,
      the source renamed the literal ASV_ID header).
    when: '!$(inputs.skip_abundance_tables)'
    in:
      table: asv_table_knot/data_param
    out: [ {{id: tsv}} ]
    run:
{emb("/home/abennett/nf-core-ampliseq/udt-summary-counts.yml")}
"""

text = open(DRAFT).read()
start_key = "  summary_counts:\n    tool_id: TODO"
end_key = "  import_table:\n    label: import_table"
assert text.count(start_key) == 1, "summary_counts anchor not unique"
assert text.count(end_key) == 1, "import_table anchor not unique"
i = text.index(start_key)
j = text.index(end_key)
assert i < j
new = text[:i] + step + text[j:]

out_old = "counts_table: { outputSource: summary_counts/TODO_counts_long, label: counts_table"
assert new.count(out_old) == 1, "counts_table ref not unique"
new = new.replace(out_old, "counts_table: { outputSource: summary_counts/tsv, label: counts_table")

open(DRAFT, "w").write(new)
print("spliced summary_counts:", j - i, "->", len(step), "; counts_table rewired")
