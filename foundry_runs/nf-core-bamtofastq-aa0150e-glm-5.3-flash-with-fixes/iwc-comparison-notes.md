# IWC exemplar comparison — nf-core/bamtofastq

Corpus: `~/.foundry/iwc` @ c07557f (pulled during this phase).

## Exemplar selection

Searched all IWC workflows for bam/cram-touching inputs and samtools tool families.
No IWC workflow converts BAM→FASTQ (no `samtools fastq`, no `samtools collate`, no
bamtofastq equivalent anywhere in the corpus — verified by tool-id and content grep).
Ranked candidates by feature hierarchy:

| candidate | domain | topology | tool families | confidence |
|---|---|---|---|---|
| `microbiome/host-contamination-removal/host-contamination-removal-short-reads/host-or-contamination-removal-on-short-reads` | read filtering/QC against a host reference | `list:paired` fastq input; parallel branch on reference source (built-in index vs history file) resolved by `map_param_value` → `when:` + `pick_value(first)`; MultiQC report out | bowtie2 + multiqc + pick_value | **Medium** |
| `epigenetics/atacseq/atacseq` | alignment QC + peaks | `list:paired` fastq in, samtools idxstats + samtools_view + MultiQC | bowtie2/picard/samtools | Low–medium |
| `variant-calling/generic-variant-calling-wgs-pe` | variant calling | fastp → bwa-mem → samtools_view → samtools_stats → MultiQC | bwa/samtools/multiqc | Low |

**Nearest exemplar: host-or-contamination-removal-on-short-reads (Medium).** Same broad
domain (genomics read processing against a reference), same input topology family (a
collection mapped over alignment steps), same conditional motif we chose (inline `when:`
branches joined by `pick_value`), MultiQC report as the single aggregate output. Not
canonical: its science is filtering-not-converting and its input is fastq not bam.

Secondary structural signals taken from atacseq + generic-variant-calling: samtools
stats/idxstats as published QC outputs; MultiQC consuming tool outputs.

## Structural diff vs our briefs

| aspect | exemplar | our brief | finding → owner |
|---|---|---|---|
| branch selection | `map_param_value` (text→boolean) steps feed `when: $(inputs.when)` on tool steps | data-flow chose inline `when:` with boolean params `no_read_qc`/`no_stats` directly from workflow inputs | **match** — exemplar maps a string enum to booleans because the source param is a selector; ours are booleans already, no `map_param_value` step needed. Template: connect workflow input → `when` directly. |
| peer-alternative rejoin | `pick_value` with `pick_style: first`, two pick_value steps (ref-file vs index branch) | `pick_value(first_or_skip)` ×2 for chr branch (bam + index) | **match** — confirms pick_value-as-tool-step idiom (iuc/pick_value 0.2.0). Template: use `style_cond|pick_style: first_or_skip`. |
| collection input | `data_collection_input`, `collection_type: list:paired`, `doc:` on input | plain `list` of bam/cram | **exemplar adds `doc:` on every input and renamed `out:` entries** — apply to template. |
| output promotion | outputs with stable names like `Bowtie2 Mapping Statistics from Local Index`; per-branch duplicates rather than conditional single output | both when-gated QC outputs exposed even when skipped | exemplar never exposes a skipped step's output — it duplicates outputs per branch instead. Our null-output exposure is a deviation; test style must tolerate nulls (recorded in test plan). |
| aggregate report | single MultiQC step consuming prior tool outputs | same | **match**. |
| tests | `-tests.yml` with `class: Collection`, `element_tests:` on members, `has_text`/`has_n_lines` asserts; zenodo-hosted fixtures | test plan phase to decide | **test issue** — follow this fixture/assertion style; defer to phase 9/10. |

## Inline excerpt (relevant subgraph: branch + pick_value + when wiring)

From `microbiome/host-contamination-removal/.../host-or-contamination-removal-on-short-reads` (converted, compact; fuller view in `iwc-exemplar.gxwf.yml`):

```yaml
  - id: Bowtie2-map reads against a built in reference genome
    label: Bowtie2-map reads against a built in reference genome
    in:
      - id: library|input_1
        source: Short-reads
      - id: reference_genome|index
        source: Host/Contaminant Reference Genome
      - id: when
        source: _unlabeled_step_4/output_param_boolean
    out:
      - id: mapping_stats
        rename: Bowtie2 mapping statistics
      - id: output_unaligned_read_pairs
        rename: Reads without host or contaminant reads
    tool_state:
      library: {type: paired_collection, __current_case__: 1, input_1: {__class__: ConnectedValue}}
    when: $(inputs.when)
  - id: _unlabeled_step_6          # pick_value feeding the history-file branch
    tool_id: .../iuc/pick_value/pick_value/0.2.0
    in:
      - id: style_cond|type_cond|pick_from_0|value
        source: Reference genome file
    state:
      style_cond:
        pick_style: first
        type_cond: {param_type: data, pick_from: [{}]}
```

## Guidance for the template Mold

1. Label every input, output and step descriptively; add `doc:` on inputs (exemplar convention).
2. Wire boolean workflow inputs directly into step `when: $(inputs.no_stats)` — no map_param_value indirection.
3. Use iuc `pick_value` (0.2.0) steps with `pick_style: first_or_skip` for the chr-branch rejoin; connect both branch outputs to `pick_from_N|value`.
4. Promote outputs with stable user-facing names; per-branch duplicates are acceptable IWC style, but our when-gated outputs stay single (accepting nulls).
5. MultiQC as the terminal aggregate step consuming FastQC zips.
