#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/open-requirements.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("documented in its tool help)'"), "unexpected ledger tail"
assert "phyloseq-export-and-tree-nwk-producer" not in t
entry = """
- id: phyloseq-export-and-tree-nwk-producer
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'phyloseq concretized as embedded UDT ampliseq_phyloseq
    (quay.io/biocontainers/bioconductor-phyloseq:1.50.0--r44hdfd78af_0, the module''s exact
    container/conda pin): the module''s inline R body verbatim (otu/tax read.table row.names=1,
    module''s own _confidence/classifier/database column drop, integer otu cast, optional
    sample_data + phy_tree behind the file.exists guards, saveRDS), Nextflow tuple vars ->
    positional args, fixed phyloseq.rds output name. sam and tree are optional:true ports
    wired to metadata and the NEW export_tree step; the step keeps its !skip_phyloseq when.
    Bounded structural edit: inserted export_tree (UDT ampliseq_export_tree, qiime2:2026.4,
    qiime tools export rooted qza -> tree.nwk) ahead of phyloseq, guarded with qiime2_tree''s
    when, added to frame_exports; phyloseq_objects workflow output rewired to phyloseq/rds.'
  rationale: 'qiime2_tree''s pinned q2d2 wrapper emits rooted_tree as a qza (verified in the
    cached manifest), while PHYLOSEQ consumes Newick - the source''s tree channel into
    ROBJECT_WORKFLOW is tree_nwk because each source tree producer exports internally
    (QIIME2_DIVERSITY.out.tree_nwk / PPLACE grafted / SIDLE nwk; ch_tree_for_robject
    assignment workflows/ampliseq.nf:1310-1316) and the qiime2_tree step doc already deferred
    the export to the consumers. One shared export producer serves phyloseq now and tse in
    its own iteration. The sam/tree optional ports reproduce the source''s
    .ifEmpty(''EMPTY'') staging (robject_workflow/main.nf:30-38): a skipped optional input
    substitutes empty, file.exists("") is FALSE, the EMPTY branch. The TODO_fasta wiring in
    the template was a mis-wire - the module has no FASTA input (tax keyed by ASV id joins
    the otu table directly; picrust/phyloseq mis-wire correction precedent). Fixed output
    name because the source prefix is the per-classifier tuple id and the draft consolidates
    a single taxonomy table upstream (one rds not N).'
  evidence:
  - 'modules/local/phyloseq/main.nf (R script quoted in the UDT configfile; container tag
    verified on quay /v2/biocontainers/bioconductor-phyloseq/tags/list: 1.50.0--r44hdfd78af_0;
    environment.yml bioconductor-phyloseq=1.50.0 r-base=4.4.2)'
  - 'subworkflows/local/robject_workflow/main.nf:26-45 (combine/ifEmpty EMPTY/map strip,
    ch_for_r_objects tuple val(prefix),tax,otu,sam,tree, no FASTA)'
  - 'workflows/ampliseq.nf:1310-1316 (ch_tree_for_robject = PPLACE grafted / SIDLE nwk /
    QIIME2_DIVERSITY tree_nwk / empty) and :1492 (phyloseq out collected into
    phyloseq_objects)'
  - 'tool-cache manifest for qiime2__phylogeny__align_to_tree_mafft_fasttree: output
    rooted_tree.qza (qza format) - drives the export_tree producer'
  - 'not run locally: no Rscript; R body is the module verbatim, runtime check deferred to
    phase 11'
"""
open(L, "w").write(t.rstrip() + "\n" + entry.lstrip("\n"))
print("appended phyloseq-export-and-tree-nwk-producer")
