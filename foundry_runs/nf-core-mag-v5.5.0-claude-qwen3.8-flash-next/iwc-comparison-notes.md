# IWC comparison notes — nf-core/mag translation

Corpus: `~/.foundry/iwc` (clone, up to date at run). Ranked by the feature
hierarchy (domain → input topology → tool families → DAG motifs → outputs → tests).

## Ranking

| rank | candidate | confidence | why |
|---|---|---|---|
| 1 | **microbiome/mags-building (MAGs-generation.ga)** | **High** | Same domain (MAG generation), same input topology (`list:paired` grouped reads + optional LR/assembly inputs), same tool families (megahit, metaSPAdes, bowtie2, jgi-depths, metabat2, maxbin2, concoct-chain, comebin, semibin, quast, checkm2/checkm lineage, multiqc), same DAG motifs (assembler swap via `when:`+`pick_value`; binners fan-out → contig2bin → derep → QC column-join → multiqc). Partial output match (no bin_summary-equivalent TSV checkpoint; no taxonomy/annotation). |
| 2 | microbiome/multi-sample-binning | Medium | Binning stage only; **has `das_tool`** (our refinement stage), `__CROSS_PRODUCT_NESTED__` (bins×BAMs), `seqkit_stats`, maxbin2 depth conversion via text_processing |
| 3 | microbiome/mags-taxonomy-annotation | Medium | GTDB-Tk classify_wf branch (+kmetashot instead of CAT) |
| 4 | microbiome/host-contamination-removal-short-reads, genome-assembly/quality-and-contamination-control-raw-reads | Medium | Stage-local analogs for host/phiX removal and contamination QC |

No IWC workflow spans the whole of MAG (samplesheet→QC→assembly→binning→refine→
QC→taxonomy→annotation→MultiQC, plus aDNA/hybrid/assembly-input modalities): IWC
carves this domain into sibling stage workflows. Our single-workflow posture
(condiional-when note) is a deliberate divergence; note the reviewer risk.

## Structural diff → guidance for the template Mold

1. **Adopt the exemplar's conditional idiom verbatim.** Selector string input →
   `map_param_value` step → boolean; consumer step gets a named `when` input
   connected to it, and `when: $(inputs.when)`; rejoin via
   `toolshed...iuc/pick_value/0.2.0` (`pick_style: first`). Confirmed for our
   `clip_tool`, assembler, and long-read tool swaps. (Our additive-branch
   merge-collections choice for binners/QC stays — exemplar's binners are also all
   run and pooled; its one optional binner is gated by a plain boolean input
   "Run COMEBin", precedent for our pick-list `when:` gates.)
2. **Optional-modality inputs**: exemplar models LR/PacBio modality as `optional: true`
   collections defaulted to null in tests, consumed via `pick_value` and
   `FILTER_EMPTY_DATASETS`; "Custom Assemblies: null" + "Choose Assembler: Custom
   Assembly" is the same trick as our `input_mode` + optional assembly sheet —
   supports keeping `input_mode` (interface decision unchanged) and confirms the
   ledger's nullable fallback is corpus-attested.
3. **Bins×BAMs cross-product** (our `bins-x-bams-cross-product`): multi-sample-binning
   solves it with `__CROSS_PRODUCT_NESTED__` + apply-rules — mechanism resolved
   (ledger closed).
4. **bin_summary**: exemplar merges QC tables with `collection_column_join` (×2) —
   mechanism confirmed, but branches are never skipped there, so our
   skipped-branch tolerance question stays open.
5. **Unbinned split**: binning-evaluation uses `split_file_to_collection` — our
   split-fasta tool need has a corpus-attested shape (lowers Low→Medium).
6. **Refinement**: prefer the exemplar's `das_tool` wiring from
   multi-sample-binning (fasta_to_contig2bin per binner → das_tool) over dRep
   (mags-building's choice); MAG's source uses DAS Tool, source structure wins.
7. **Divergences to keep anyway** (reviewer notes, not fixes): samplesheet:record
   input (IWC uses plain collections); DB pick-list as user-uploaded datasets
   (exemplar's CheckM2 wrapper instead takes a DB *version string* — wrapper-managed
   DBs exist in IWC; per-step loop may prefer them, portability posture unchanged);
   Binette (exemplar) is not in MAG's tool set — GUNC stays per source.

## Nearest-exemplar gxformat2 view

Abstract ID: `microbiome/mags-building` — relevant subgraph (assembler swap:
megaspades/megahit `when:`, duplicate+relabel per-group fan-out, pick_value trio;
QC tail: collection_column_join ×2 + multiqc) in sibling **`iwc-exemplar.gxwf.yml`**
(12 steps of 69; full conversion was `gxwf convert --to format2 --compact`).

Inline excerpt (assembler-optional `pick_value`, verbatim from the sibling file):

```yaml
- id: _unlabeled_step_28
  tool_id: toolshed.g2.bx.psu.edu/repos/iuc/pick_value/pick_value/0.2.0
  in:
  - id: style_cond|type_cond|pick_from_0|value
    source: Trimmed nanopore reads from grouped samples
  - id: style_cond|type_cond|pick_from_1|value
    source: _unlabeled_step_27
  tool_state:
    style_cond:
      pick_style: first
      __current_case__: 0
      type_cond:
        param_type: data
        __current_case__: 4        # collection type
        pick_from:
        - __index__: 0
          value: {__class__: ConnectedValue}
        - __index__: 1
          value: {__class__: ConnectedValue}
```

and the gated-consumer spelling (megaspades step, same file):

```yaml
  in:
  - id: when
    source: _unlabeled_step_22/output_param_boolean   # map_param_value over $(inputs.Choose Assembler)
  when: $(inputs.when)
```

## Test-style comparison (defer to test-plan skill)

`MAGs-generation-tests.yml`: remote-zenodo fixtures, `list:paired` collections keyed
by sample id, `null` for unused optional collections, scalar job values — matches
`iwc-test-data-conventions`. Our sample_sheet inputs will need remote-URI collection
creation with `column_definitions` (API supports `rows` + `column_definitions` per
fetch endpoint) — flag for `implement-galaxy-workflow-test`.

## Routing

Items 1–6 → template skill (apply during skeleton authoring). Item 7 + wrapper-DB
question → per-step loop (tool discovery). Item 3 → closed in ledger. Test notes →
test-plan/test-impl skills.
