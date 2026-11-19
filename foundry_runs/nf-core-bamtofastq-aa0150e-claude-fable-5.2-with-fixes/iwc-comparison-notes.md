# IWC exemplar comparison — nf-core/bamtofastq

Corpus: `galaxyproject/iwc` at `c07557f` (2026-11-12), in `~/.foundry/iwc` (`git pull --ff-only`: already up to date). Searched `workflows/**/*.ga` for: `samtools_fastx`, `bamtofastq` / `SamToFastq`, `samtools_idxstats`, `__FILTER_FROM_FILE__`. Candidates converted with `gxwf convert --to format2 --compact --no-stateful`.

## Result

| Rank | IWC workflow | Confidence | Why |
|---|---|---|---|
| 1 | `microbiome/host-contamination-removal/host-contamination-removal-long-reads/host-or-contamination-removal-on-long-reads` | **Low to medium** | Same core operation (BAM → FASTQ with `samtools_fastx`, mapped over a `list`), same report shape (MultiQC, promoted reads output). Different domain (contamination removal starts from reads, maps them, keeps the unmapped part), long reads only, no pairing, no pre/post QC of the conversion. |
| 2 | `virology/influenza-isolates-consensus-and-subtyping/influenza-consensus-and-subtyping` | **Low (cross-domain pattern match)** | Unrelated science. But it contains the exact plumbing motif planned for nodes 6–8: collapse a mapped collection into a table with identifiers → filter rows → cut the identifier column → `__FILTER_FROM_FILE__`. |
| — | `transcriptomics/rnaseq-pe`, `epigenetics/atacseq` | not exemplars | Only share generic QC tools (`samtools_idxstats`, MultiQC). |

**There is no IWC workflow whose purpose is converting alignments back to reads.** No hit for `bamtofastq`, `SamToFastq` or `bedtools bamtofastq`; `samtools_fastx` appears in two workflows, both as a late clean-up step. So: no domain exemplar; two partial matches used for idiom only. Do not treat either as canonical.

## Structural diff against the briefs

| Feature | Briefs | Exemplar 1 (host removal) | Exemplar 2 (influenza) | Finding → owner |
|---|---|---|---|---|
| Input topology | one `list` of `bam` | `list` of reads + reference `string` | `list:paired` + `list` | Starting from BAM is not represented in IWC. No change. → none |
| BAM → FASTQ | `samtools collate` + `samtools fastq -N`, READ1/READ2 for paired, `-0` for single-end, gzip | `samtools_fastx` with `outputs: other`, `output_fmt_select: fastqsanger`, `exclusive_filter: ['256','2048']`, `read_numbering: ''` | — | The wrapper exposes an output selector (`outputs`), a read-numbering option and flag filters — all three are things nodes 11/12/16 need. Whether it collates is not visible in the workflow file. → tool-step (per-step loop) |
| Flag-based BAM split | `samtools view` flag filters (nodes 9, 10) | `bamtools_split_mapped` (mapped vs unmapped only) | `samtools_view` 1.22+galaxy2 | The exemplar's splitter cannot express "both mates mapped" vs "a mate unmapped"; keep the planned flag filters. → none |
| Per-sample routing by a computed class | classifier → table → ids → split (nodes 5–8) | none | `collapse_dataset` (`add_name: true`, `place_name: same_multiple`, `change_datatype: tabular`) → `Filter1` (`cond`) → `Cut1` (`c1`) → `__FILTER_FROM_FILE__` (`how_filter: remove_if_absent`), using only `output_filtered` | Corpus precedent for the motif. The brief's node 7 (one step: filter + cut) is two steps in IWC (`Filter1`, `Cut1`). The exemplar hides `output_discarded`; the brief uses **both** outputs — no IWC precedent found for consuming `output_discarded`. → template: split node 7 into two steps; ledger entry for the discarded side |
| Empty collection after a split | must be tolerated (single-end side is empty in the default test) | — | not exercised | No corpus evidence either way. → test (planemo run decides) |
| QC reporting | MultiQC over FastQC + samtools stats/flagstat/idxstats | MultiQC over one flattened QualiMap collection, `__FLATTEN__` before it | MultiQC absent | `__FLATTEN__` before a reducing consumer matches node 17's role. MultiQC `results` is a repeat with one `software_cond` per tool. → tool-step |
| Output promotion | 13 labelled outputs | 4 labelled outputs; intermediates `hide: true`; `rename:` post-job action on promoted outputs | — | Idiom to copy: hide every non-output `out`, give outputs readable names. → template |
| Output format | `fastqsanger.gz` | `fastqsanger` (uncompressed) | — | The exemplar emits uncompressed FASTQ. The briefs keep gzip because the source publishes `.fastq.gz`; uncompressed output is the fallback if decompressed-content assertions turn out impossible on gzip outputs. → test-plan |
| Test style | md5 of decompressed reads, text checks on flagstat/idxstats | (not inspected: test style is not a retrieval feature) | | → test-plan phase |

## Guidance for the template

1. Keep the planned topology. Nothing in the corpus argues for a different shape.
2. Split data-flow node 7 into `Filter1` + `Cut1`-style steps (corpus-observed), or keep one text-processing step if the step loop finds one — either is fine; the two-step form has precedent.
3. For node 6, the corpus form is "collapse collection" with the element identifier added on every line and the output datatype changed to `tabular`.
4. Hide intermediates; label outputs exactly as in the data-flow brief's output table.
5. Leave tool choice for BAM → FASTQ to the step loop, but note the corpus pins `samtools_fastx` 1.22+galaxy2 and `samtools_view` 1.22+galaxy2 as currently used versions.

## Nearest exemplar (gxformat2) excerpt

Full view: `iwc-exemplar.gxwf.yml` (parts A and B; not runnable, upstream steps cut away).

Part A — `microbiome/host-contamination-removal/host-contamination-removal-long-reads/host-or-contamination-removal-on-long-reads`, steps `Split BAM` → (unlabelled `samtools_fastx`) → output `Reads without Host or Contamination`:

```yaml
A_bam_to_fastq:
  doc: Extractions of FastQ from the unmapped reads
  tool_id: toolshed.g2.bx.psu.edu/repos/iuc/samtools_fastx/samtools_fastx/1.22+galaxy2
  tool_shed_repository: {changeset_revision: 4bde991b8037, name: samtools_fastx, owner: iuc, tool_shed: toolshed.g2.bx.psu.edu}
  in:
  - {id: input, source: Split BAM/unmapped}
  out:
  - {id: output, rename: Reads without host or contamination reads}
  tool_state:
    exclusive_filter: ['256', '2048']
    idxout_cond: {idxout_select: 'no'}
    output_fmt_cond: {output_fmt_select: fastqsanger, output_quality: false, ilumina_casava: false}
    outputs: other
    read_numbering: ''
```

Part B (low-confidence, cross-domain pattern only) — `virology/influenza-isolates-consensus-and-subtyping/influenza-consensus-and-subtyping`, four unlabelled steps:

```yaml
B_collapse_with_identifiers:
  tool_id: toolshed.g2.bx.psu.edu/repos/nml/collapse_collections/collapse_dataset/5.1.0
  out: [{id: output, change_datatype: tabular, hide: true}]
  tool_state: {filename: {add_name: true, place_name: same_multiple}, one_header: false}
B_filter_rows:
  tool_id: Filter1
  tool_state: {cond: c2 > 1, header_lines: '0'}
B_cut_identifier_column:
  tool_id: Cut1
  tool_state: {columnList: c1, delimiter: T}
B_filter_collection_by_identifiers:
  tool_id: __FILTER_FROM_FILE__
  in:
  - {id: how|filter_source, source: B_cut_identifier_column/out_file1}
  - {id: input, source: <collection to split>}
  tool_state: {how: {how_filter: remove_if_absent}}
```
