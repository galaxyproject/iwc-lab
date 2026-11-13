# IWC exemplar comparison — oncoanalyser WGTS core DNA spine

Corpus: `~/.foundry/iwc` at `ed48e2f` (2026-11-10). Inputs: `nextflow-galaxy-interface.md`, `nextflow-galaxy-data-flow.md`, `nextflow-galaxy-reference-data.md`.

## Result

**Nearest exemplar: `variant-calling/ploidy-aware-genotype-calling/genotype-variant-calling-wgs-pe`. Confidence: Low** (pattern comparison, not a domain exemplar).

| Feature (priority order) | Briefs | Exemplar | Match |
|---|---|---|---|
| 1. Domain | human cancer WGS, matched tumor/normal somatic + germline (purity/ploidy, CNV, SV, drivers) | germline short-read variant calling, any ploidy | partial: same broad area (short-read DNA variant calling), **no somatic / tumor-normal** |
| 2. Input topology | two `list:paired` (lanes of one tumor, lanes of one normal) + 2 sample-name strings + reference FASTA + HMF archive | one `list:paired` (one element per **sample**) + FASTA + GTF + int | partial |
| 3. Tool families | bwa-mem2 + hmftools (REDUX, AMBER, COBALT, SAGE, PAVE, ESVEE, PURPLE, LINX) | fastp, bwa-mem, samtools, Picard MarkDuplicates, FreeBayes, SnpEff | alignment only |
| 4. DAG motifs | twin tumor/normal chains; lane map-over **then reduce** per sample; fan-in of 5 caller outputs into PURPLE | per-sample map-over end to end; collapse at the end | partial |
| 5. Outputs | VCFs (bgzip), tabular driver catalogues, tar archives | VCF, TSV, HTML reports | partial |
| 6. Test style | single-subject simulated reads | IWC paired collection fixtures | n/a |

Corpus search: `grep -il 'tumor|somatic'` over all `.ga` files hits only unrelated workflows (VGP Hi-C, imaging). There's no Galaxy-corpus precedent for tumor/normal pairing, hmftools, or directory-archive passing between steps. The other candidates, `generic-variant-calling-wgs-pe` and `haploid-variant-calling-wgs-pe`, share the same mapping motif but are microbial/haploid with older tool versions, so they rank lower.

## Exemplar excerpt (pattern comparison only)

From `iwc-exemplar.gxwf.yml` (steps `BWA-MEM mapping`, `Samtools view`, `Mark Duplicates`; the fastp input was rewired to the raw collection for the excerpt):

```yaml
inputs:
  - id: Paired Collection
    type: collection
    collection_type: list:paired
    format: [fastqsanger, fastqsanger.gz]
  - id: Reference Genome fasta
    type: data
steps:
  - id: BWA-MEM mapping
    tool_id: toolshed.g2.bx.psu.edu/repos/devteam/bwa/bwa_mem/0.7.19+galaxy1
    in:
      - id: fastq_input|fastq_input1
        source: Paired Collection
      - id: reference_source|ref_file
        source: Reference Genome fasta
    tool_state:
      fastq_input: {fastq_input_selector: paired_collection}
      output_sort: coordinate
      reference_source: {reference_source_selector: history, index_a: auto}
      rg: {rg_selector: do_not_set}
  - id: Mark Duplicates
    tool_id: toolshed.g2.bx.psu.edu/repos/devteam/picard/picard_MarkDuplicates/3.1.1.0
    in:
      - id: inputFile
        source: Samtools view/outputsam
```

## Findings routed forward

| # | Finding | Owner |
|---|---|---|
| 1 | **In-tool index from a history FASTA is the IWC norm** (`reference_source_selector: history`, `index_a: auto`). This supports the reference brief's choice not to expose a bwa-mem2 index input. Expect the same `reference_source` conditional on `bwa_mem2`. | template / tool-step |
| 2 | **Exemplar sets no read group** (`rg_selector: do_not_set`). hmftools match `-tumor`/`-reference` against BAM `SM`, so the briefs' RG requirement (ledger `read-group-id-format`) has no exemplar backing. Set `rg` explicitly in A1/A2 with `SM` from the sample-id parameter and `ID` from the element identifier. | tool-step |
| 3 | **Collection meaning differs.** In the exemplar, `list:paired` elements are samples and stay mapped to the end. Here elements are lanes and must be **reduced** at REDUX (one job per sample). The template must wire REDUX's BAM input as `multiple: true` over the mapped BAM list, not as a map-over. | template |
| 4 | **The exemplar has an explicit Samtools view filter and Picard MarkDuplicates.** In the source, duplicate marking and the unmapping of problem regions happen inside REDUX, so **no separate filter/dedup step** should be added. | template (no change) |
| 5 | **The exemplar exposes QC (fastp HTML, MultiQC).** The briefs drop QC (ledger `qc-and-plot-stages-not-built`). This is a divergence from IWC convention that an IWC submission would need to revisit. Not blocking. | user / maturation |
| 6 | **Label style.** IWC uses human-readable ids with spaces ("Reference Genome fasta"). The interface brief uses snake_case public labels. Both are legal; keep the brief's labels because tests bind to them. Add a `doc` to every input and output. | template |
| 7 | **No corpus precedent** for twin tumor/normal chains, archive datasets between user-defined tools, the PURPLE multi-slot fan-in, or the `when:` + `pick_value` fai/dict builds. They are recorded as an open requirement so the template treats them as un-anchored. | template |
