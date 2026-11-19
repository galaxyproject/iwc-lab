#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/open-requirements.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("(14 layers) for tag a6608bc81b0e6546'"), "unexpected ledger tail"
assert "tse-udt-and-plan-hint-correction" not in t
entry = """
- id: tse-udt-and-plan-hint-correction
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'tse concretized as embedded UDT ampliseq_tse pinning the module''s exact
    container quay.io/biocontainers/bioconductor-treesummarizedexperiment:2.10.0--r43hdfd78af_0
    (tag verified on quay), TREESUMMARIZEDEXPERIMENT inline R body verbatim (counts assay
    integer cast, taxonomy _confidence/classifier/database drop + rownames match, sequence
    column to referenceSeq when present, file.exists-guarded colData/rowTree, saveRDS),
    tuple vars -> positional args, fixed TreeSummarizedExperiment.rds output. Wiring on
    the module''s real four-port tuple: otu/tax knots, sam: metadata and tree:
    export_tree/tree_nwk; tse_objects workflow output rewired to tse/rds (only consumer).'
  rationale: 'The template hint was wrong on two counts and the module is authoritative:
    (1) _plan_context named modules/local/robjects/tse.R, which does not exist - the R body
    is inline in modules/local/treesummarizedexperiment/main.nf; (2) the TODO in: block
    listed three inputs with tree wired to qiime2_tree/rooted_tree, but the module input is
    tuple val(prefix),tax,otu,sam,tree and ape::read.tree needs Newick - sam: metadata added
    (source ch_meta.ifEmpty, same as phyloseq iter 52) and tree re-pointed at the shared
    export_tree producer built for phyloseq ("one shared export producer serves phyloseq now
    and tse in its own iteration"). Prefix -> fixed name drops because the draft
    consolidates one taxonomy knot upstream (phyloseq precedent). Verbatim-embedding proof:
    42 R lines byte-identical after documented interpolations ($var -> args, \\$ -> $,
    Nextflow heredoc dedent and \\\\t unescape).'
  evidence:
  - 'modules/local/treesummarizedexperiment/main.nf (inline script quoted in the UDT
    configfile; container depot/biocontainers tag 2.10.0--r43hdfd78af_0 verified via quay
    /v2/biocontainers/bioconductor-treesummarizedexperiment/tags/list)'
  - 'environment.yml (bioconductor-treesummarizedexperiment=2.10.0, r-base=4.3.2)'
  - 'subworkflows/local/robject_workflow/main.nf:41-43 (ch_for_r_objects tuple into
    TREESUMMARIZEDEXPERIMENT behind if (!params.skip_tse)); draft step keeps !skip_tse when'
  - 'not run locally: no Rscript; R body is the module verbatim, runtime check deferred to
    phase 11'
"""
open(L, "w").write(t.rstrip() + "\n" + entry.lstrip("\n"))
print("appended tse-udt-and-plan-hint-correction")
