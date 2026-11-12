#!/usr/bin/env python3
"""Iteration 55: concretize filter_samples (local R intersect module, identity-corrected);
insert asv_table_for_import rebind knot; rewire import_table and the six q2 consumers."""

DRAFT = "/home/abennett/nf-core-ampliseq/galaxy-workflow-draft.gxwf.yml"

def emb(p):
    return "\n".join(("      " + ln) if ln else "" for ln in open(p).read().splitlines())

step = f"""  filter_samples:
    label: filter_samples
    doc: >-
      FILTER_SAMPLES - mutual sample intersect of metadata rows and abundance columns
      (modules/local/filter_samples, base R on r-base:4.2.1 - NOT q2 feature-table
      filter-samples: the q2d2 wrapper is a no-op without --p-where and cannot compute the
      intersect, identity corrected from the pinned id, import_table precedent). Realized
      at the source's position BEFORE QIIME2_INASV: the filtered table rebinds the import
      feed via asv_table_for_import (ch_asv_table reassignment workflows/ampliseq.nf:
      1144-1146); the filtered metadata output feeds the QIIME2 metadata consumers in
      their own iterations. Display-only *.log drops documented in the tool help.
    when: "$(inputs.metadata) != null"
    in:
      meta: metadata
      table: asv_table_knot/data_param
    out: [ {{id: metadata}}, {{id: table}} ]
    run:
{emb("/home/abennett/nf-core-ampliseq/udt-filter-samples.yml")}
  asv_table_for_import:
    type: pick_value
    label: asv_table_for_import
    doc: filtered ASV table when filter_samples ran (metadata given, source ch_asv_table rebind), else the master knot table - feeds import_table (QIIME2_INASV sees only the filtered table)
    state:
      style_cond: {{ pick_style: first_or_skip, type_cond: {{ param_type: data }} }}
    in:
      pick_from_0|value: filter_samples/table
      pick_from_1|value: asv_table_knot/data_param
    out: [ {{ id: data_param }} ]
"""

text = open(DRAFT).read()
start_key = "  filter_samples:\n    tool_id: TODO"
end_key = "  core_metrics:\n    tool_id: TODO"
assert text.count(start_key) == 1, "filter_samples anchor not unique"
assert text.count(end_key) == 1, "core_metrics anchor not unique"
i = text.index(start_key); j = text.index(end_key)
assert i < j
new = text[:i] + step + text[j:]

# import_table now consumes the rebind knot (replace inside its block only)
blk_start = new.index("  import_table:\n    label: import_table")
old_line = "      table: asv_table_knot/data_param\n"
assert new.count(old_line) >= 1
k = new.index(old_line, blk_start)
assert k < new.index("    out: [ {id: qza} ]", blk_start), "import_table in-line anchor escaped its block"
new = new[:k] + "      table: asv_table_for_import/data_param\n" + new[k + len(old_line):]

# six q2 consumers: filtered table now arrives as the imported qza
old_cons = "TODO_table: filter_samples/TODO_table"
assert new.count(old_cons) == 6, f"expected 6 consumers, found {new.count(old_cons)}"
new = new.replace(old_cons, "TODO_table: import_table/qza")

# frame membership
fr_old = "qiime2_tree, filter_samples, core_metrics,"
assert new.count(fr_old) == 1, "frame anchor not unique"
new = new.replace(fr_old, "qiime2_tree, filter_samples, asv_table_for_import, core_metrics,")

assert "filter_samples/TODO" not in new, "residual filter_samples/TODO reference"
open(DRAFT, "w").write(new)
print("spliced filter_samples+knot:", j - i, "->", len(step), "; import_table + 6 consumers + frame rewired")
