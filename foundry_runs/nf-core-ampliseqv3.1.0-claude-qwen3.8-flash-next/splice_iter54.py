#!/usr/bin/env python3
"""Iteration 54: concretize tse (TreeSummarizedExperiment); rewire tse_objects output."""

DRAFT = "/home/abennett/nf-core-ampliseq/galaxy-workflow-draft.gxwf.yml"

def emb(p):
    return "\n".join(("      " + ln) if ln else "" for ln in open(p).read().splitlines())

step = f"""  tse:
    label: tse
    doc: >-
      TREESUMMARIZEDEXPERIMENT export - module R body verbatim (TreeSummarizedExperiment
      2.10.0 image), tuple vars -> positional args, sam/tree optional ports realize the
      source's ifEmpty('EMPTY') file.exists branches, fixed TreeSummarizedExperiment.rds
      output name (source prefix = classifier id; single consolidated knot upstream -
      same deviation as phyloseq). Template hinted three inputs on the module's qza tree
      port; realized on the module's actual four-port tuple: sam: metadata added (the
      source ch_meta.ifEmpty channel, as in phyloseq) and tree rewired to
      export_tree/tree_nwk (module reads Newick via ape::read.tree).
    when: '!$(inputs.skip_tse)'
    in:
      otu: asv_table_knot/data_param
      tax: tax_table_knot/data_param
      sam: metadata
      tree: export_tree/tree_nwk
    out: [ {{id: rds}} ]
    run:
{emb("/home/abennett/nf-core-ampliseq/udt-tse.yml")}
"""

text = open(DRAFT).read()
start_key = "  tse:\n    tool_id: TODO"
end_key = "  parquet_tables:\n    tool_id: TODO"
assert text.count(start_key) == 1, "tse anchor not unique"
assert text.count(end_key) == 1, "parquet_tables anchor not unique"
i = text.index(start_key)
j = text.index(end_key)
assert i < j
new = text[:i] + step + text[j:]

out_old = "tse_objects: { outputSource: tse/TODO_tse_rds, label: tse_objects }"
assert text.count(out_old) == 1, "output ref not unique"
new = new.replace(out_old, "tse_objects: { outputSource: tse/rds, label: tse_objects }")
assert "tse/TODO" not in new, "residual tse/TODO reference"

open(DRAFT, "w").write(new)
print("spliced tse:", j - i, "->", len(step), "; tse_objects rewired")
