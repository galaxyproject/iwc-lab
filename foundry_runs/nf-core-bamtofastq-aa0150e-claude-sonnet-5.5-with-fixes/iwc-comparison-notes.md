# IWC exemplar comparison: nf-core/bamtofastq

Corpus: `~/.foundry/iwc` (galaxyproject/iwc, HEAD c07557f, used as cached; no `git pull` run — the cache is dated the day of this run).
Searched `workflows/**` for BAM→FASTQ tool families (`bamtofastq`, `samtools_fastx`, `samtools_fastq`, `bam2fastq`, `collate`) and for samtools QC steps (flagstat/idxstats/stats).

## Nearest exemplar — confidence: **Low–Medium (partial, tool-family match only)**
`microbiome/host-contamination-removal/host-contamination-removal-long-reads/host-or-contamination-removal-on-long-reads`
(also `microbiome/pathogen-identification/nanopore-pre-processing` uses the same BAM→FASTQ tool).

- Domain: **differs** (host removal from nanopore reads; no BAM/CRAM→FASTQ re-extraction as the product). Same *tool family*: `samtools_fastx` (iuc, 1.22+galaxy2) converts a BAM to FASTQ; also MultiQC aggregation of per-sample stats and a `list` collection input with element identifiers = sample ids.
- No IWC workflow converts BAM/CRAM collections to paired FASTQ as its purpose, so **no domain exemplar** exists. The match is a pattern comparison only.

### Exemplar gxformat2 excerpt (relevant subgraph; full slice in `iwc-exemplar.gxwf.yml`)
```yaml
- id: _unlabeled_step_7
  doc: Extractions of FastQ from the unmapped reads
  tool_id: toolshed.g2.bx.psu.edu/repos/iuc/samtools_fastx/samtools_fastx/1.22+galaxy2
  in:
    - {id: input, source: Split BAM/unmapped}
  state:
    output_fmt_cond: {output_fmt_select: fastqsanger, output_quality: false, ilumina_casava: false}
    outputs: [other]
    exclusive_filter: ["256", "2048"]
```
(Steps covered: `_unlabeled_step_7` (samtools_fastx), `MultiQC`.)

## Structural diff against our briefs

| Aspect | IWC exemplar | Our design | Routed to |
|---|---|---|---|
| BAM→FASTQ | **one** `samtools_fastx` step (`outputs`: read1/read2/other/singleton choices, `exclusive_filter` for SAM flags) | 4 `samtools view` flag filters + merge + 2 collate + concat (N6–N13) | Template/data-flow: strong simplification candidate. `samtools_fastx` exposes `outputs` (including `other`) and `exclusive_filter`, so one mapped step over the input collection plausibly reproduces the source's all-reads extraction. Verify wrapper options in the per-step loop; do not rely on this guess. Ledger `merge-and-cat-need-collection-reshaping` may then close. |
| Per-sample stats | MultiQC over per-sample stats via a flatten step | N2–N4 + MultiQC | Template: consistent; MultiQC fed by collection → fine. |
| Input topology | `list` of fastq(.gz) | `list` of bam/cram | OK. |
| Conditionals | none | `when` for chr/no_read_QC/no_stats | corpus precedent elsewhere: `variant-calling/...`, `sars-cov-2-variant-calling/sars-cov-2-pe-illumina-ivar-analysis/pe-wgs-ivar-analysis` (boolean `when` + `pick_value`) — referenced from the conditional note; not converted here. |
| Optional reference | required string input | optional FASTA input | no corpus precedent found for an optional FASTA input threaded into samtools wrappers; carry the open question forward. |
| Outputs | named, `outputSource` to step ids | same plan | OK. |

## Test style and fixtures (guidance only)
The exemplar's `-tests.yml` uses remote `location:` URLs (zenodo), `class: Collection` jobs with `identifier`+`filetype`, and `element_tests` with `has_text` / `has_n_lines`. For our test, nf-core fixtures are GitHub raw URLs (test-datasets `bamtofastq` branch) with a known md5 snapshot; phase 9/10 own the assertion choices. IWC conventions (see bundled `iwc-shortcuts-anti-patterns`, `iwc-test-data-conventions`): do not use checksums from a own run as expected values unless justified; prefer `has_text`/line-count/`has_size` on stable content.

## Guidance for the template
1. Keep the **faithful** N6–N13 chain as the baseline but let the draft loop try a single `samtools_fastx` step first if the wrapper exposes read1/read2/other + flag exclusion; record whichever choice in the ledger and the log.
2. Use `inputs` with `type: collection`, `collection_type: list`; keep sample ids as identifiers.
3. Promote QC outputs as named workflow outputs (IWC does, via `outputSource`).
