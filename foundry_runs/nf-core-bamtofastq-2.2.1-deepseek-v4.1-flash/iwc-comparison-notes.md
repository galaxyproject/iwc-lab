# IWC exemplar comparison — nf-core/bamtofastq

Corpus: `~/.foundry/iwc` @ `9f111cb8661fa446e43f92ec4863e6a66972a91c` (2026-11-09), used read-only.

## Ranking

| candidate | intent | topology | tools | verdict |
|---|---|---|---|---|
| `microbiome/host-contamination-removal/host-contamination-removal-long-reads` | removes host reads from long-read sequencing (BAM→FASTQ tail is incidental) | `list` of BAM | minimap2, bamtools_split_mapped, `__FLATTEN__`, `iuc/samtools_fastx`, MultiQC | **low/medium** — the only IWC workflow that converts BAM collections to FASTQ collections; shows the Galaxy `samtools_fastx` idiom |
| `microbiome/mags-building`, `VGP-assembly-v2/hi-c-contact-map…` | assembly / Hi-C | unrelated | samtools fastq incidental | not an exemplar |
| — | no IWC workflow converts BAM/CRAM to FASTQ with collate + map/unmap recombination | — | — | **no domain exemplar exists** |

The source pipeline's central operation — four flag-filtered `samtools view` subsets, merge of the three unmapped subsets, per-subset `samtools collate` + `fastq`, then `CAT_FASTQ` — has **no IWC analogue**. That is a genuine corpus gap, not a translation error.

## Nearest exemplar — relevant subgraph

IWC id: `microbiome/host-contamination-removal/host-contamination-removal-long-reads`, steps 1 → 7 (input collection → `samtools_fastx`), minimap2/split elided. Full file: `iwc-exemplar.gxwf.yml`.

```yaml
inputs:
  - id: Long-reads
    type: collection
    collection_type: list
steps:
  - id: _unlabeled_step_7
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/samtools_fastx/samtools_fastx/1.22+galaxy2
    in:
      - id: input
        source: Long-reads
    out:
      - id: output
    tool_state:
      outputs: other
      exclusive_filter: ["256", "2048"]
      output_fmt_cond:
        output_fmt_select: fastqsanger
```

Notes: the wrapper maps over a `list` of BAMs; its `outputs` selector (`other`, `mapped`, `unmapped`, …) plus `exclusive/inclusive_filter` expresses the same flag filtering the Nextflow pipeline does with four `samtools view` calls. Output format is chosen explicitly.

## Structural diff against the briefs

| brief decision | exemplar evidence | verdict | owner |
|---|---|---|---|
| `samtools view` × 4 → merge → collate × 2 → `cat_fastq` for paired data | no exemplar | keep the source shape; this is the pipeline's own structure and the only faithful translation. Expect several mapped steps over the same collection. | template |
| `samtools collate` + `samtools fastq` are one step per subset | exemplar separates filter from conversion but still runs `samtools_fastx` on a collection | map the same way: one Galaxy step per source process, mapped over the list. If no collatefastq wrapper exists, a `samtools collate` step followed by a `samtools fastx` step reproduces the module. | discovery |
| `merge_unmapped` needs a null-tolerant keyed join of three lists | no exemplar | unresolved; IWC has no such join. Keep as the workflow's main risk (ledger). A pragmatic fallback: skip the merge and feed three `samtools fastq`/`cat` steps, matching the source's intent that all unmapped reads end up in the output. | template, with review |
| chr extraction replaces the input list | exemplar uses `__FLATTEN__` for reshaping, never `pick_value` | `pick_value` over two whole collections stays medium-confidence; a plain per-element `when` cannot express the source's list replacement. | template |
| `input_layout` (single|paired) input | no exemplar (all IWC workflows commit to one layout) | keep; content-dependent branching has no Galaxy analogue. | template |
| MultiQC over a collection | exemplar step 8 takes a collection on `results_0|software_cond|input` | matches | template |

## Guidance for the template Mold

1. Expect a wide workflow (~20 mapped steps). Do not collapse the four `samtools view` steps into one "filter" step: each carries a different flag combination and the source treats them as distinct outputs.
2. Prefer `iuc/samtools_fastx` (exemplar-proven) plus a `samtools collate` step if a combined collatefastq wrapper is not available; do not invent a combined tool.
3. Keep `merge_unmapped` as a separate node even if its Galaxy wiring needs an Apply Rules alignment step; record the risk.
4. MultiQC consumes a collection per `software_cond` slot, as in the exemplar.
5. `__FLATTEN__` is the corpus idiom for de-nesting; the chr branch may need it if the extracted list is nested.

## Pattern issues (routed, not blocking)

- No corpus workflow converts BAM→FASTQ with paired-end map/unmap recombination; this translation is novel relative to IWC. The test profile (single-end BAM) will only exercise the simpler branch.
