#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/open-requirements.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("deferred to phase 11 test runs'"), "unexpected ledger tail"
assert "expected-comparison-chain-realization" not in t
entry = """
- id: expected-comparison-chain-realization
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'The template''s two drafty comparison steps could not compute their outputs as wired - the source''s
    compare_expected_abundances IS COMPARE_PERFORMANCE, which consumes the alignment-derived matches.tsv from
    COMPARE_SEQUENCES, which consumes VSEARCH_USEARCHGLOBAL over observed-vs-expected sequences. Realized the whole
    chain in place as three steps. expected_alignment: embedded UDT ampliseq_usearch_global_compare
    (quay.io/biocontainers/vsearch:2.31.0--hd2be7a0_0, the module''s exact pin) with similarity 0.80 (fixed in
    comparison_wf), the conf/modules.config batch-mode args (--strand both --maxaccepts 0 --maxrejects 0 --dbmask
    none --qmask none --output_no_hits), userfields query+target+ql+tl+qilo+qihi+tilo+tihi+gaps+mism+qstrand and
    --userout vsearch_usearchglobal.tsv; query = asv_fasta_knot/data_param, db = expected_sequences.
    compare_expected_sequences: embedded UDT ampliseq_compare_sequences (r-base:4.2.1) embedding bin/compare_sequences.r
    BYTE-VERBATIM (verified 8867-byte diff), args (matches-table, observed table = asv_table_knot/data_param,
    expected abundances, empty prefix, 0.80, expected_sequences_region), optional expabund port reproducing the
    source''s ifEmpty([]) staging (skipped input substitutes empty, file.exists("") is FALSE in R - compare against
    all sequences); out matches (nucleotide-differences.tsv) + per-sample tsv/svg/png list collections.
    compare_expected_abundances: embedded UDT ampliseq_compare_performance (r-base:4.2.1) embedding
    bin/compare_performance.r BYTE-VERBATIM (17968-byte diff); fbeta=2 and mismatch_threshold=0 fixed shell literals
    (modules.config ext.fbeta=2; expected_sequences_mismatches schema default 0 with no draft interface input,
    mismatches-0-fixed), merge_mode from expected_sequences_merge; out performance_summary.tsv,
    performance_per-sample.tsv, abundances_per-sample.tsv + svg/png collections. Guards: sequences chain on
    expected_sequences != null; abundances on BOTH expected inputs (source fires COMPARE_PERFORMANCE only when the
    matches producer ran and the expected-abundance channel is non-empty - an empty path input never triggers the
    task). expected_alignment added to frame_postfilters.'
  rationale: 'Same bounded-structural-edit precedent mode as the decontam knots: a when-guarded two-port step cannot
    express a multi-process producer chain. FASTA/table keys align with the source (dada2 ASV ids are sequences, this
    draft''s tables are keyed by sequence, so the alignment query column joins the table ID column directly).
    Deviations: the run_qiime2 && !skip_abundance_tables branch of the COMPARISON_WF call site
    (workflows/ampliseq.nf:1337-1339, QIIME2_EXPORT abs_fasta/rel_tsv/rel_tax as observed inputs) is not carried -
    v1 keeps the main ch_asv_fasta/ch_asv_table branch (recorded here; compare_expected_profile''s own iteration
    revisits the profile pick); the first script argument tag is the source''s val_md5sum_version (md5 of params +
    version, a constant per run) replaced by a constant text input ampliseq (pipeline_info artifacts dropped
    precedent); nucleotide-differences.log/performance.log/Warnings.txt/md5sum_version.txt/versions.yml are not
    published (stderr stays in the job output); per-sample plots are list collections instead of .collect() fan-in;
    vsearch --threads 1 fixed.'
  evidence:
  - subworkflows/local/comparison_wf/main.nf (full: VSEARCH_USEARCHGLOBAL_BM(observed.map{[[id:val_md5sum_version],file]},
    expected, "0.80", userout, userfields) -> COMPARE_SEQUENCES(ifEmpty([]) expected, region, ...) ->
    COMPARE_PERFORMANCE(matches relabeled, observed, expected non-optional channel) -> COMPARE_PROFILE; emit
    mismatch_barplot png/svg only)
  - modules/nf-core/vsearch/usearchglobal/main.nf (container quay.io/biocontainers/vsearch:2.31.0--hd2be7a0_0 exact;
    command shape --usearch_global/--db/--id/--threads/$args/${columns}/${outfmt}; outoption userout -> *.tsv)
  - 'conf/modules.config BM args for USEARCHGLOBAL (--strand both --maxaccepts 0 --maxrejects 0 --dbmask none --qmask
    none --output_no_hits, prefix vsearch_usearchglobal) and COMPARE_PERFORMANCE ext.fbeta=2,
    ext.mismatch_threshold=params.expected_sequences_mismatches, ext.merge_mode=params.expected_sequences_merge'
  - modules/local/compare_sequences/main.nf + compare_performance/main.nf (command lines with "" prefix / meta.id tag;
    container biocontainers/r-base:4.2.1 matching both environment.yml pins; output globs *nucleotide-differences.tsv,
    *_per-sample.tsv, *.svg, *.png, performance_summary.tsv, performance_per-sample.tsv, abundances_per-sample.tsv)
  - 'bin/compare_sequences.r + bin/compare_performance.r read in full; argv contracts (6 and 7 args), SAMPLES overlap
    logic, merge-mode branches, svg/png device calls; embedded content byte-identical to source after splice'
  - 'workflows/ampliseq.nf:1331-1344 (COMPARISON_WF gated on expected_sequences||expected_profile; observed
    channels; val_md5sum_version = params.md5()+version); nextflow_schema.json defaults region=observed,
    merge=all, mismatches=0'
  - 'not run locally: no vsearch binary and no Rscript on this host - the two R replicas are byte-verbatim
    transcriptions and the vsearch command mirrors the module line; runtime check deferred to phase 11'
"""
open(L, "w").write(t.rstrip() + "\n" + entry.lstrip("\n"))
print("appended expected-comparison-chain-realization")
