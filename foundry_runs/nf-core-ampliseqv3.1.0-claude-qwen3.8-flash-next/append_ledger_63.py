#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/open-requirements.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("phase 11'"), "unexpected ledger tail"
assert "picrust-dada2-branch-single-result" not in t
entry = """
- id: picrust-dada2-branch-single-result
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'picrust (last drafty step) concretized as embedded UDT ampliseq_picrust
    (quay.io/biocontainers/picrust2:2.6.3--pyhdfd78af_0, the exact module container tag
    - present on quay): picrust2_pipeline.py -s -i -o all_output -p 1 --in_traits EC,KO
    --verbose then the three add_descriptions.py calls, module script verbatim. DADA2
    branch realization: seq = asv_fasta_knot (ch_fasta is NOT rebound by the
    filter-samples block), abund = asv_table_for_import/data_param (ch_asv_table IS
    rebound at workflows/ampliseq.nf:1146 before the PICRUST call at :1304, so the
    post-filter-samples wide table is what the source DADA2 call actually passes). The
    template mis-wired the abundance port to import_table/qza - qza is unreadable by
    picrust2_pipeline.py; corrected to the TSV. QIIME2 branch (taxon-filtered abs
    exports + biom header tail-strip) dropped: draft has no QIIME2 abs-export producer.
    Single result port = METACYC_path_abun_unstrat_descrip.tsv, exposed via NEW workflow
    output picrust_result (nothing consumed the step; source feeds pathways into
    MULTIQC, which the draft does not wire).'
  rationale: 'Author branch confirmed (shed has no picrust2_pipeline wrapper; _plan_context
    predicted it). Branch choice follows the draft''s existing channels rather than
    inventing a producer: the wired fasta knot is the DADA2 chain, so pairing it with
    the QIIME2-filtered table would mislabel provenance (the val message strings differ
    per branch upstream). METACYC pathway descriptions = the pathways emit''s
    interpretable member; static from_work_dir cannot publish the 3-file glob nor the
    all_output folder, and EC/KO descrip files + message.txt + picrust.args.txt are
    MultiQC/full-report inputs (drop precedent). $args = task.ext.args unset at the call
    site -> nothing to reproduce; -p uses 1 (single-core precedent); versions dropped.'
  evidence:
  - 'modules/local/picrust/main.nf (container biocontainers/picrust2:2.6.3--pyhdfd78af_0;
    QIIME2-source tail -n +2 strip; pipeline + 3x add_descriptions; outputs
    outfolder/pathways/args/message/versions) and workflows/ampliseq.nf:1297-1305
    (branch condition; DADA2 call with ch_fasta, ch_asv_table)'
  - 'workflows/ampliseq.nf:1142-1147 (rebind covers ch_metadata + ch_asv_table only -
    ch_fasta stays raw) ; quay tags/list: 2.6.3--pyhdfd78af_0 present'
  - 'gate: exit 0, tool_state 76 ok/0 fail/0 skip, strict [], todo 0/[]/[]; then
    draft-next-step reports draft false - loop endstate'
"""
open(L, "w").write(t.rstrip() + "\n" + entry.lstrip("\n"))
print("appended picrust-dada2-branch-single-result")
