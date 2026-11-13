# IWC comparison — nf-core/atacseq core library spine

Produced by `compare-against-iwc-exemplar` against galaxyproject/iwc @ `5bfb694` (2026-11-11),
cloned at `~/.foundry/iwc`. Inputs: interface, data-flow, reference-data briefs and ledger.

## Ranking

| Rank | IWC workflow | Confidence | Why |
|---|---|---|---|
| 1 | `epigenetics/atacseq/atacseq` (release 2.3) | **Medium** | Same domain and intent (ATAC peaks + coverage + MultiQC); same tool families for filter (bamtools), dedup (Picard MarkDuplicates), peaks (MACS2), coverage (bigWig), report (MultiQC). Diverges on input topology (PE-only `list:paired`), aligner (Bowtie2, cached index), no run→library merge, no consensus/featureCounts/DESeq2/HOMER. |
| 2 | `epigenetics/consensus-peaks/consensus-peaks-atac-cutandrun` (1.8) | Medium (for the consensus sub-graph only) | Same domain; its "call peaks individually → multi-intersect → filter ≥ N replicates" is the Galaxy idiom for our `consensus_peaks` node. Input is already-deduplicated BAMs. |
| — | `epigenetics/chipseq-pe`, `chipseq-sr` | Low | Adjacent domain; useful only as evidence that IWC splits SE and PE into separate workflows. |

No IWC workflow covers HOMER annotation, featureCounts on consensus peaks, or DESeq2 QC for
ATAC-seq.

## Structural diff

| # | Area | Our briefs | Exemplar | Owner | Guidance |
|---|---|---|---|---|---|
| 1 | Input topology | `list:paired_or_unpaired` split into PE + SE lanes | `list:paired` only (PE); SE handled by separate chipseq-sr style workflows | template | Lane split is a valid divergence (source mixes SE/PE in one run). Keep it; IWC precedent for separate SE/PE graphs supports one lane subworkflow per mode. |
| 2 | Trimming | Trim Galore (`--fastqc`) | fastp | tool-step | Keep Trim Galore for fidelity. |
| 3 | Aligner / reference | BWA-MEM, index from history FASTA | Bowtie2, `reference_genome\|index` from a **data table** (`Reference Genome` text parameter) | template | Do not copy the data-table idiom (reference posture: no data tables). Keep `genome_fasta` data input. |
| 4 | Run → library merge | Apply Rules regroup + MergeSamFiles | absent (one dataset per sample) | template | No exemplar; keep from source. |
| 5 | Read filter | samtools view flags + `-L include_regions` then bamtools rules | **single bamtools filter** with conditions `mapQuality >=30`, `isProperPair true`, `reference !chrM`, `mateReference !MT` | tool-step | `devteam/bamtools_filter/bamFilter` expresses NM / CIGAR / insertSize / flag rules as `conditions[].filters[]` — the NF JSON rules map onto it. Region restriction (`-L include_regions_bed`) still needs samtools view (bamtools filter has no BED input). |
| 6 | Dedup | MarkDuplicates mark-only, dups dropped in filter (`-F 0x0400`) unless `keep_dups` | MarkDuplicates removing dups | tool-step | Keep source semantics (mark, then filter). |
| 7 | Peak calling input | MACS2 on BAM (`BAMPE`/`BAM`), broad, `--nomodel --keep-dup all` | BAM → BED (`bedtools_bamtobed`) → MACS2 `format: BED`, `nomodel`, `keep_dup all`, narrow + summits, `gsize` from a connected parameter | tool-step | Exemplar confirms `effective_genome_size_options_selector: user_defined` with `gsize` wired from an int workflow parameter — matches our `macs_gsize` input. Keep BAM/BAMPE input (source fidelity); BED conversion is the exemplar's Tn5-centred choice. |
| 8 | Coverage | genomecov scaled by 1e6/mapped → bigWig | MACS2 treatment pileup → `wig_to_bigWig`, then deepTools bigwigAverage with `scaleFactors` = 1e6/reads from `samtools view -c` + `column_maker` + `param_value_from_file` | template/tool-step | Exemplar shows the Galaxy idiom for a **per-element scale factor**: compute count → arithmetic column → `param_value_from_file` → wire into a tool parameter. Applies to our `bam_to_bigwig` if the coverage tool has no CPM mode. |
| 9 | FRiP | intersectBed -c -f 0.20 ÷ mapped | `bedtools_coveragebed` reads over peaks → `tp_awk_tool` → `cat1` with total reads → awk MultiQC table | tool-step | Use this chain as the FRiP pattern (adjust overlap fraction). |
| 10 | Consensus peaks | mergeBed collapse + `macs2_merged_expand.py --min_replicates` | `bedtools_multiintersectbed` over per-sample peaks → `Filter1` with condition composed by `compose_text_param` (`c4 >= N`) | template | **Closes the tool-shape gap** for counting library support: multiintersect column 4 = number of inputs covering the interval. Then bedtools merge to get regions, plus SAF projection (`Cut`/awk). Divergence: exemplar additionally calls peaks on a downsampled merge — not in source, do not copy. |
| 11 | MultiQC | many lists | multi-`results` repeat, custom content via awk "first column" tables | tool-step | Follow exemplar repeat layout. |
| 12 | Tests | — | `atacseq-tests.yml`: Zenodo-hosted fixtures, `has_size`/`has_text` style asserts | test | Defer to test-plan phase. |

## Exemplar excerpt (gxformat2)

From `epigenetics/atacseq/atacseq`, step `Call Peak with MACS2` (abridged), and
`epigenetics/consensus-peaks/consensus-peaks-atac-cutandrun` steps `generate filter rule` /
`filter multi intersect`. Fuller slice in `iwc-exemplar.gxwf.yml` (steps: Bowtie2 map, bamtools
filter, MarkDuplicates, bamtobed, MACS2, read counting, bigWig, coverage on summits, MultiQC;
consensus: call peaks individually, generate filter rule, compute multi intersect, filter multi
intersect).

```yaml
- label: Call Peak with MACS2
  tool_id: toolshed.g2.bx.psu.edu/repos/iuc/macs2/macs2_callpeak/2.2.9.1+galaxy0
  in:
  - id: effective_genome_size_options|gsize
    source: Effective genome size          # int workflow parameter
  - id: treatment|input_treatment_file
    source: convert BAM to BED to improve peak calling
  tool_state:
    advanced_options:
      broad_options: {broad_options_selector: nobroad, call_summits: true}
      keep_dup_options: {keep_dup_options_selector: all}
    control: {c_select: 'No'}
    cutoff_options: {cutoff_options_selector: qvalue, qvalue: '0.05'}
    effective_genome_size_options:
      effective_genome_size_options_selector: user_defined
      gsize: {__class__: ConnectedValue}
    format: BED
    nomodel_type: {nomodel_type_selector: nomodel}
# consensus-peaks-atac-cutandrun
- label: generate filter rule                 # compose_text_param: 'c4 >= ' + Minimum number of overlap
- label: compute multi intersect              # bedtools_multiintersectbed, tag|inputs <- per-sample peaks
- label: filter multi intersect               # Filter1, cond <- generate filter rule
```

## Ledger effects

- `consensus-expand-script`: **resolved** — exemplar gives a wrapper-only shape
  (multiintersect + composed Filter + merge + Cut) for the support-count filter and SAF projection.
- New: `per-element-scale-factor-idiom` (decision, not obligation) — use the count →
  column_maker → `param_value_from_file` chain where a tool needs a per-element numeric argument.
- Still open (no exemplar): orphan-pair removal, DESeq2 QC, featureCounts matrix, HOMER.
