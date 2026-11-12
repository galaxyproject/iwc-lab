#!/usr/bin/env python3
"""Iteration 63: concretize picrust (last drafty step); rewire table mis-wire; add picrust_result output."""

DRAFT = "/home/abennett/nf-core-ampliseq/galaxy-workflow-draft.gxwf.yml"

def emb(p):
    return "\n".join(("      " + ln) if ln else "" for ln in open(p).read().splitlines())

step = f"""  picrust:
    label: picrust
    doc: >-
      PICRUST as embedded UDT (biocontainers/picrust2:2.6.3--pyhdfd78af_0 kept from the
      module): picrust2_pipeline.py --in_traits EC,KO then add_descriptions.py -
      DADA2-branch realization (unfiltered asv_fasta_knot + the post-filter-samples wide
      table via asv_table_for_import, matching the ch_asv_table rebind at
      workflows/ampliseq.nf:1146 before this call at :1304); the QIIME2 abs-export branch
      and its biom header strip are dropped (no such producer in this draft). Result =
      METACYC pathway abundance with descriptions; folder/args/message/versions drops in
      tool help. The template's qza-import-table wiring on the abundance port is a
      mis-wire, corrected here to the TSV table (picrust2_pipeline.py reads tabular
      counts, not qza artifacts).
    when: '$(inputs.picrust)'
    in:
      seq: asv_fasta_knot/data_param
      abund: asv_table_for_import/data_param
    out: [ {{id: result}} ]
    run:
{emb("/home/abennett/nf-core-ampliseq/udt-picrust.yml")}
"""

text = open(DRAFT).read()
start_key = "  picrust:\n    tool_id: TODO"
end_key = "  # ================= exports ================="
assert text.count(start_key) == 1, "picrust anchor not unique"
assert text.count(end_key) == 1, "exports anchor not unique"
i = text.index(start_key); j = text.index(end_key)
assert i < j
new = text[:i] + step + text[j:]

out_anchor = "  barplots: { outputSource: barplots/barplots, label: barplots }\n"
assert new.count(out_anchor) == 1, "barplots output anchor not unique"
new = new.replace(out_anchor, out_anchor + "  picrust_result: { outputSource: picrust/result, label: picrust_result }\n")

assert "TODO_fasta" not in new and "TODO_result" not in new, "residual picrust TODO ports"
assert "TODO_table" not in new, "residual TODO_table"
open(DRAFT, "w").write(new)
print("spliced picrust:", j - i, "->", len(step), "; picrust_result output added")
