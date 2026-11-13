# IWC Exemplar Comparison Notes: nf-core/bamtofastq

## Nearest Exemplar Identification
- **Exemplar ID**: `read-preprocessing/short-read-qc-trimming/short-read-quality-control-and-trimming`
- **Domain**: Read Preprocessing & Quality Control
- **Confidence**: Medium
- **Sibling File**: [iwc-exemplar.gxwf.yml](file://~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-gemini-fixed/iwc-exemplar.gxwf.yml)

## Structural Comparison

| Dimension | IWC Exemplar (`short-read-qc-trimming`) | Target Workflow (`nf-core/bamtofastq`) | Alignment & Diff Guidance |
|---|---|---|---|
| **Input Topology** | `list:paired` fastq collection | `list` of BAM/CRAM files | In `bamtofastq`, inputs are mapped alignments (`list` of BAMs) from which paired FASTQs are extracted. |
| **QC & Aggregation** | MultiQC collects report outputs from tools | MultiQC collects pre-QC, samtools stats, post-QC, and fastqutils | Same pattern: tools mapped over sample collection feed into a single MultiQC reduction step. |
| **Output Exposition** | Exposed outputs explicitly declared in `outputs[]` with `outputSource` | Exposed outputs declared for final FASTQs, QC reports, and MultiQC | Follow exemplar format for output naming and tagging. |
| **MultiQC Step Configuration** | `software_cond` per tool family in `results[]` | MultiQC takes inputs for FastQC and samtools | Follow the repeatable `results` list structure in MultiQC tool state. |

## Inlined Subgraph Excerpt from Nearest Exemplar

```yaml
  - id: MultiQC
    label: MultiQC
    doc: Aggregation of the quality controls for all samples
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/multiqc/multiqc/1.35+galaxy5
    tool_version: 1.35+galaxy5
    tool_shed_repository:
      changeset_revision: 94b6bea727ae
      name: multiqc
      owner: iuc
      tool_shed: toolshed.g2.bx.psu.edu
    in:
      - id: results_0|software_cond|input
        source: fastp/report_json
    out:
      - id: stats
        hide: true
      - id: html_report
        rename: MultiQC report
    state:
      results:
        - software_cond:
            software: fastp
```

## Guidance for Downstream Galaxy Template Authoring
1. **MultiQC Aggregation**: Ensure all QC outputs (`pre_fastqc`, `samtools_stats`, `samtools_flagstat`, `samtools_idxstats`, `post_fastqc`, `fastqutils`) connect cleanly to `results` repeats in MultiQC.
2. **Collection Output Tagging**: Propagate sample identifiers across the extraction and concatenation steps to produce a consistent `list:paired` collection.
3. **Drafting Strategy**: Template should begin with drafty steps matching the data-flow nodes, then concretize with Tool Shed wrappers (or authoring if needed).
