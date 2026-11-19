#!/usr/bin/env python3
"""Iteration 51: concretize import_table (identity-corrected UDT); rewire filter_samples ref."""

DRAFT = "/home/abennett/nf-core-ampliseq/galaxy-workflow-draft.gxwf.yml"
out = []
for ln in open("/home/abennett/nf-core-ampliseq/udt-import-table.yml").read().splitlines():
    out.append(("      " + ln) if ln else "")
udt = "\n".join(out)

step = f"""  import_table:
    label: import_table
    doc: >-
      QIIME2 import of the (filtered) feature table - QIIME2_INASV verbatim
      (biom header sed + biom convert + qiime tools import FeatureTable[Frequency] on
      qiime2/qiime2:2026.4). Identity corrected from the pinned q2d2
      qiime2_core__tools__import - that wrapper cannot do the tsv-to-biom pre-conversion
      (import_taxonomy precedent); the plain ASV-sequence-keyed table is a valid simple
      BIOM text table for biom-format's load_table.
    in:
      table: asv_table_knot/data_param
    out: [ {{id: qza}} ]
    run:
{udt}
"""

text = open(DRAFT).read()
start_key = "  import_table:\n    tool_id: toolshed.g2.bx.psu.edu/repos/q2d2/qiime2_core__tools__import/qiime2_core__tools__import"
end_key = "  import_taxonomy:"
assert text.count(start_key) == 1, "import_table anchor not unique"
assert text.count(end_key) == 1, "import_taxonomy anchor not unique"
i = text.index(start_key)
j = text.index(end_key)
assert i < j
new = text[:i] + step + text[j:]

cons = "      TODO_table: import_table/TODO_qza"
assert new.count(cons) == 1, "consumer ref count unexpected"
new = new.replace(cons, "      TODO_table: import_table/qza")

open(DRAFT, "w").write(new)
print("spliced import_table:", j - i, "->", len(step), "; consumer rewired")
