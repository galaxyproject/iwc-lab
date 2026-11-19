#!/usr/bin/env python3
"""Iteration 52: concretize phyloseq + insert export_tree producer; rewire output ref."""

DRAFT = "/home/abennett/nf-core-ampliseq/galaxy-workflow-draft.gxwf.yml"

def emb(p):
    return "\n".join(("      " + ln) if ln else "" for ln in open(p).read().splitlines())

step = f"""  export_tree:
    label: export_tree
    doc: >-
      Newick export of the rooted tree qza for the R-object consumers - the source's
      tree channel into ROBJECT_WORKFLOW is already tree_nwk (QIIME2_DIVERSITY/PPLACE/
      SIDLE export inside their producers); the draft's producer emits a qza, so the
      export is realized here as a shared producer (phyloseq and tse consume it).
    when: "!$(inputs.skip_diversity_indices) || !$(inputs.skip_alpha_rarefaction)"
    in:
      tree_qza: qiime2_tree/rooted_tree
    out: [ {{id: tree_nwk}} ]
    run:
{emb("/home/abennett/nf-core-ampliseq/udt-export-tree.yml")}
  phyloseq:
    label: phyloseq
    doc: >-
      PHYLOSEQ export (table + taxonomy + metadata + tree) - module R body verbatim
      (phyloseq 1.50.0 image; module's own _confidence/classifier/database column filters),
      sam/tree optional ports realize the source's ifEmpty('EMPTY') file.exists branches,
      fixed phyloseq.rds output name (source prefix = classifier id, multi-classifier mix
      collapsed by the single consolidated knot table). FASTA port dropped - the module
      takes no FASTA (template mis-wire, picrust/phyloseq lineage precedent).
    when: '!$(inputs.skip_phyloseq)'
    in:
      otu: asv_table_knot/data_param
      tax: tax_table_knot/data_param
      sam: metadata
      tree: export_tree/tree_nwk
    out: [ {{id: rds}} ]
    run:
{emb("/home/abennett/nf-core-ampliseq/udt-phyloseq.yml")}
"""

text = open(DRAFT).read()
start_key = "  phyloseq:\n    tool_id: TODO"
end_key = "  tse:\n    tool_id: TODO"
assert text.count(start_key) == 1, "phyloseq anchor not unique"
assert text.count(end_key) == 1, "tse anchor not unique"
i = text.index(start_key)
j = text.index(end_key)
assert i < j
new = text[:i] + step + text[j:]

frame_old = "contains_steps: [phyloseq, tse,"
assert new.count(frame_old) == 1, "frame anchor not unique"
new = new.replace(frame_old, "contains_steps: [export_tree, phyloseq, tse,")

out_old = "phyloseq_objects: { outputSource: phyloseq/TODO_phyloseq_rds, label: phyloseq_objects }"
assert new.count(out_old) == 1, "output ref not unique"
new = new.replace(out_old, "phyloseq_objects: { outputSource: phyloseq/rds, label: phyloseq_objects }")

open(DRAFT, "w").write(new)
print("spliced phyloseq+export_tree:", j - i, "->", len(step), "; frame + output ref updated")
