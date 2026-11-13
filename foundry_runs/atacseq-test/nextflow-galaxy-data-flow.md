# Data-flow brief — nf-core/atacseq 2.1.2 → Galaxy (core library spine)

Produced by `nextflow-summary-to-galaxy-data-flow` from `summary-nextflow.json` (edges reconciled
from `workflows/atacseq.nf`), the reference-data and interface briefs, and the ledger. Step-level
behaviour comes from the carried subworkflows/modules and `conf/modules.config` `ext.args`, cited
per node. No Tool Shed ids are chosen here.

## 1. Topology at a glance

```
reads (list:paired_or_unpaired, ids <sample>_REP<r>_T<n>)
  └─ split_pe_se ──► reads_pe (list:paired)   ─► LANE(pe) ─┐
                 └─► reads_se (list)          ─► LANE(se) ─┤
genome_fasta ─► ref_fai_sizes ─► include_regions_bed ◄─ blacklist_bed?, mito_name, keep_mito
                                                         │
LANE(mode), per run → per library:                      │
  fastqc_raw → trim_galore(+fastqc) → bwa_mem → drop_secondary → run_bam_stats
  → group_runs_to_libraries (Apply Rules) → merge_library_runs (Picard MergeSamFiles, reduce inner)
  → markduplicates → markdup_bam_stats
  → filter_library_bam [mode rules, include_regions] → (pe: name_sort → remove_orphans → coord_sort) → filtered_bam_stats
  → bam_to_bigwig [scale 1e6/mapped; pe: -pc, se: -fs fragment_size]
  → macs2_callpeak [format BAMPE|BAM] → drop_empty_peaks → frip_score, homer_annotate_peaks
                                                         │
merge_lanes: filtered BAMs, peaks, bigWigs, QC lists ────┘
  → consensus_peaks (merge across libraries, ≥ min_reps_consensus) → consensus_saf
  → homer_annotate_consensus
  → featurecounts (all library BAMs × consensus SAF) → deseq2_qc
  → multiqc (all QC logs)
```

The lane is the same chain with mode-specific settings; the template should author it once as
a Galaxy subworkflow and instantiate it twice (`pe`, `se`). Justification: the source itself
branches on `meta.single_end` at six places in this chain (see §3), and Galaxy cannot read a
per-element "single_end" flag after alignment collapses the inner `paired`/unpaired shape into a
flat list of BAMs. Splitting at the input keeps the flag as collection membership.

## 2. Reference preparation (once, broadcast)

| Node | Does | In → Out | Source | Confidence |
|---|---|---|---|---|
| `ref_fai_sizes` | FASTA index + chromosome sizes (cols 1–2 of fai) | `fasta` → `fai`, `len`/tabular | `CUSTOM_GETCHROMSIZES` | high |
| `include_regions_bed` | sort blacklist by sizes, complement against genome → include regions; drop `mito_name` contigs unless `keep_mito`. No blacklist → whole genome from sizes, minus mito | sizes + optional `bed` + text + bool → `bed` | `GENOME_BLACKLIST_REGIONS` (`sortBed … \| complementBed … \| awk '$1 !~ /mito/'`) | medium — optional-input branch |

Not needed under the chosen scope (only consumed by dropped stages): `GTF2BED` gene BED
(deepTools), `TSS_EXTRACT` (deepTools, ataqv), `GET_AUTOSOMES` (ataqv). `genome_gtf` goes directly
to HOMER. BWA index is built in-tool from `genome_fasta` (reference brief).

## 3. Per-run and per-library lane

Element identifiers: per-run nodes keep `<sample>_REP<r>_T<n>`; after `group_runs_to_libraries`
outer identifiers are `<sample>_REP<r>`, unique per library (sample + replicate). The `_T<n>`
suffix numbers runs within one library, not mates — it is never a pairing key.

| # | Node | Does | Shape in → out | Mode difference | Source evidence | Confidence |
|---|---|---|---|---|---|---|
| 0 | `split_pe_se` | split mixed collection into paired and unpaired sub-collections | `list:paired_or_unpaired` → `list:paired` + `list` | — | `meta.single_end` set by `check_samplesheet.py` | medium (built-in availability on target unverified) |
| 1 | `fastqc_raw` | FastQC per run | map | — | `FASTQ_FASTQC_UMITOOLS_TRIMGALORE:FASTQC` | high |
| 2 | `trim_galore` | adapter trim + FastQC on trimmed; optional clip/nextseq unset | map, `paired`→`paired` / file→file | PE: `--paired` | `TRIMGALORE` args `--fastqc …` | high |
| 3 | `bwa_mem` | align to `genome_fasta` (index built in-tool), `-M`, optional `-T bwa_min_score`, read group from element id | map → `bam` per run | PE vs SE input | `BWA_MEM` args `-M`, `-T`, `-R` | high |
| 4 | `drop_secondary` | remove secondary alignments (`-F 0x0100`), coordinate sort | map | — | `BWA_MEM` `ext.args2 = '-bhS -F 0x0100 -O BAM'`, then `BAM_SORT_STATS_SAMTOOLS` | high |
| 5 | `run_bam_stats` | samtools stats / flagstat / idxstats | map → 3 lists | — | `BAM_SORT_STATS_SAMTOOLS` → MultiQC | high |
| 6 | `group_runs_to_libraries` | regroup by identifier: strip `_T\d+$` | `list` → `list:list` | — | `ch_genome_bam.map{ meta.id - ~/_T\d+$/ }.groupTuple` | high |
| 7 | `merge_library_runs` | merge runs of one library, coordinate sort | map over outer, reduce inner → `list` of `bam` | — | `PICARD_MERGESAMFILES_LIBRARY` `--SORT_ORDER coordinate` | high |
| 8 | `markduplicates` | mark (not remove) duplicates | map → `bam` + metrics `txt` | — | `PICARD_MARKDUPLICATES` `--REMOVE_DUPLICATES false` | high |
| 9 | `markdup_bam_stats` | samtools stats / flagstat / idxstats | map | — | `BAM_MARKDUPLICATES_PICARD` | high |
| 10 | `filter_library_bam` | `samtools view -F 0x004` (+PE `-F 0x0008 -f 0x001`) `-F 0x0400` unless `keep_dups`, `-q 1` unless `keep_multi_map`, `-L include_regions_bed`; then bamtools filter: `NM:<=4` and no soft-clipped CIGAR; PE adds insert size within ±2000 | map | flags + rule set | `BAMTOOLS_FILTER` args; `assets/bamtools_filter_{pe,se}.json` | high (rules), medium (one vs two tools) |
| 11 | `remove_orphans` (pe only) | name-sort, drop reads whose mate was filtered and keep only FR pairs, coordinate-sort + index | map | PE only; SE: index only | `SAMTOOLS_SORT -n` → `BAM_REMOVE_ORPHANS` (`bampe_rm_orphan.py --only_fr_pairs`) → `BAM_SORT_STATS_SAMTOOLS` | medium — pipeline-bundled script |
| 12 | `filtered_bam_stats` | samtools stats / flagstat / idxstats | map | — | `BAM_SORT_STATS_SAMTOOLS` / `BAM_STATS_SAMTOOLS` | high |
| 13 | `bam_to_bigwig` | CPM-like scaling (1e6 / mapped reads from flagstat), coverage bedGraph, sort, bigWig with chrom sizes | map (bam + its flagstat, matched by identifier) + sizes → `bigwig` | PE: `-pc`; SE: `-fs fragment_size` | `BEDTOOLS_GENOMECOV` + `UCSC_BEDGRAPHTOBIGWIG` | high (intent), medium (a single coverage tool may cover scaling) |
| 14 | `macs2_callpeak` | `--keep-dup all --nomodel`, broad (`--broad --broad-cutoff`) unless `narrow_peak`; optional `-p`/`-q`; `-g macs_gsize`; no control | map → peaks (`broadPeak`/`narrowPeak` as `bed`/`interval`) | `--format BAMPE` vs `BAM` | `MACS2_CALLPEAK` args | high |
| 15 | `drop_empty_peaks` | remove elements with empty peak files | collection filter | — | `.filter { peaks.size() > 0 }` | high |
| 16 | `frip_score` | reads overlapping peaks (`intersectBed -bed -c -f 0.20`, summed) ÷ mapped reads → `<id>\t<frip>` | map (bam + peaks by identifier) → `tabular` | — | `FRIP_SCORE` | medium — needs bam/peak identifier sync after step 15 |
| 17 | `homer_annotate_peaks` | `annotatePeaks.pl <peaks> <fasta> -gid -gtf <gtf>` | map + fasta + gtf → `tabular` | — | `HOMER_ANNOTATEPEAKS` `-gid` | high |

Identifier synchronisation: steps 13 and 16 pair two per-library collections. Both descend from
the same library list, so identifiers match; after `drop_empty_peaks` the peak list can be a
subset — step 16 must filter the BAM list to the surviving identifiers (source does
`ch_bam.join(ch_macs2_peaks)`). Placeholder: "filter collection by identifiers of another".

## 4. Fan-in after the lanes

| Node | Does | In → Out | Source | Confidence |
|---|---|---|---|---|
| `merge_lanes` | merge PE and SE per-library collections (filtered BAMs, flagstats, peaks, bigWigs, FRiP, annotations, QC logs) | 2 × `list` → `list` | `.mix` / shared downstream channels | high |
| `consensus_peaks` | sort all library peak files, `mergeBed -c 2..9 -o collapse` (narrow: 2..10), expand to boolean per-library membership, keep intervals in ≥ `min_reps_consensus` libraries; emit BED (`chr,start,end,name,0,+`) and SAF (`GeneID,Chr,Start,End,Strand`) | `list` reduce → `bed` + SAF `tabular` | `MACS2_CONSENSUS` + `macs2_merged_expand.py --min_replicates` | low — bundled Python script; runs only when >1 library |
| `homer_annotate_consensus` | annotatePeaks on consensus BED | `bed` + fasta + gtf → `tabular` | consensus `HOMER_ANNOTATEPEAKS` `-gid` | high |
| `featurecounts` | count all filtered library BAMs against consensus SAF: `-F SAF -O --fracOverlap 0.2`, `-p` (source meta has no `single_end`, so `-p` is passed for every BAM) | `list` reduce + SAF → counts matrix `tabular` + summary | `SUBREAD_FEATURECOUNTS` | medium — Galaxy wrappers usually run per BAM; matrix may need a join step |
| `deseq2_qc` | DESeq2 on counts (`--id_col 1 --count_col 7`, VST when `deseq2_vst`): PCA + sample-distance heatmap, PDF + MultiQC tables | counts → `pdf` + `tabular` | `DESEQ2_QC` (`bin/deseq2_qc.r`) | low — bundled R script |
| `multiqc` | aggregate FastQC (raw + trimmed), Trim Galore logs, samtools stats/flagstat/idxstats (run, markdup, filtered), MarkDuplicates metrics, featureCounts summary, FRiP/peak counts, DESeq2 tables | many lists reduce → `html` | `MULTIQC` | high (intent); custom-content sections medium |

## 5. Galaxy tool needs (abstract)

| Need | Shapes | Notes for discovery |
|---|---|---|
| split paired_or_unpaired collection | collection op | built-in on recent Galaxy |
| FastQC; Trim Galore | per-run map | — |
| BWA-MEM from history FASTA, read group from identifier | per-run map | reference brief ledger `bwa-index-rebuild-unverified-wrapper-param` |
| samtools view (flags, `-L` BED, `-q`), sort (coord / name), index, stats, flagstat, idxstats | per-element | — |
| Apply Rules regex regroup | `list` → `list:list` | — |
| Picard MergeSamFiles (multi-input), MarkDuplicates | reduce inner / map | — |
| bamtools filter with tag/cigar/insertSize rules | per-element | rules from `assets/bamtools_filter_*.json` |
| remove orphan / non-FR pairs from name-sorted PE BAM | per-element | pipeline script `bin/bampe_rm_orphan.py`; candidate substitute: samtools fixmate/view `-f 0x2` |
| scaled coverage → bigWig | per-element + sizes | genomecov+bedGraphToBigWig or one coverage tool with equivalent scaling |
| MACS2 callpeak (no control) | per-element | target has `iuc/macs2/macs2_callpeak/2.2.9.1+galaxy0` (seen in reference phase) |
| filter empty elements; filter collection by identifiers of another | collection ops | — |
| FRiP computation | per-element pair | bedtools intersect + arithmetic |
| HOMER annotatePeaks with user FASTA + GTF | per-element / single | — |
| bedtools merge with collapse + support-count filter + SAF projection | reduce | bundled `macs2_merged_expand.py` |
| featureCounts with SAF annotation | reduce or map+join | — |
| DESeq2 PCA / distance QC from count matrix | single | bundled `deseq2_qc.r` |
| MultiQC | reduce | — |

## 6. Dropped inside the carried scope

`PLOT_MACS2_QC`, `PLOT_HOMER_ANNOTATEPEAKS`, `MULTIQC_CUSTOM_PEAKS` (MultiQC header plumbing), and
the consensus intersect UpSet plot (`plot_peak_intersect.r`) — pipeline R/Python plot scripts with
no interface output; ledger `peak-qc-plot-scripts`. `CUSTOM_DUMPSOFTWAREVERSIONS` — Galaxy records
tool versions itself.

## 7. Handoff notes

- Template: author `LANE` as one subworkflow with a `mode`-dependent parameter set (or two
  explicit copies if subworkflow parameterisation proves awkward); outputs per lane merged in §4.
- dbkey: keep any user `dbkey` on reads through map-overs; not required.
- Test sizing: 8 runs → 3 PE libraries (T0_PE REP1, T0_PE REP2, T15_PE REP1 from two runs) and
  3 SE libraries (T100_SE REP1, T100_SE REP2, T150_SE REP1 from two runs); consensus runs over 6
  libraries.

## 8. Open questions

1. Does the target expose the split-paired-and-unpaired and filter-by-identifiers collection
   built-ins? (ledger `collection-builtins-unverified`)
2. Orphan-pair removal, consensus expansion, and DESeq2 QC rely on bundled scripts — discovery
   may find no wrapper (ledger entries).
3. featureCounts matrix shape (single multi-BAM job vs per-BAM + column join).
