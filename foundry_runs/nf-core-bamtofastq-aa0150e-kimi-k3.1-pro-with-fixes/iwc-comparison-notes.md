# IWC exemplar comparison — nf-core/bamtofastq

## Result: no nearest exemplar

IWC corpus `c07557fbb01b5bf0b7d18a5d2473c1f1ef838f60` was searched locally by workflow content and path. No `.ga` or `.gxwf.yml` workflow contained `bamtofastq`, `collatefastq`, `fastq_info`, `samtools_fastq`, or a recognizable BAM/CRAM-to-FASTQ conversion phrase. Generic MultiQC and samtools matches alone were excluded by the feature hierarchy.

| Candidate considered | Alignment | Why it is not a nearest exemplar |
|---|---|---|
| `data-fetching/sra-manifest-to-concatenated-fastqs/sra-manifest-to-concatenated-fastqs` | FASTQ collection outputs and concatenation theme | Different domain and input topology: accession/download workflow, not BAM/CRAM records or flag-class conversion. Its generic collection test idioms can be consulted later, but it is not a domain exemplar. |
| Variant-calling workflows with BAM inputs and samtools/QC steps | Alignment inputs, some samtools and MultiQC operations | Primary intent is variant analysis, not read extraction. They lack CHECKPAIREDEND, four-flag-class conversion, collate+fastq, mate concatenation and fastq_info. |
| General read-preprocessing workflows | FASTQ and FastQC | They begin with FASTQ rather than BAM/CRAM and do not exercise the source conversion DAG. |

No confidence-rated exemplar and no `iwc-exemplar.gxwf.yml` are emitted, as required for a no-match result. A cross-domain excerpt would risk normalizing away the most important source behavior.

## Structural diff guidance for template authoring

1. **Preserve the novel conversion spine.** There is no IWC support for collapsing the four `samtools view` flag classes, three-way unmapped merge, mapped/unmapped collate operations and mate-wise concatenation into fewer convenience steps. Treat data-flow nodes as authoritative.
2. **Use explicit keyed synchronization.** The BAM/CRAM+index sample-record shape and paired/unpaired conversion branch need concrete collection wiring with sample identifiers. This has no direct nearest-exemplar validation.
3. **Keep index builders shared.** Workflow-tier alignment/FASTA index steps followed by fan-out remain preferable to duplicating hidden rebuild behavior in each wrapper.
4. **Do not infer a test oracle from IQC/IWC style.** The source nf-test snapshot is stronger evidence than generic IWC smoke checks. Preserve source checksums for stable FASTQ, fastq_info and samtools statistics outputs. Type/count-only assertions on FastQC and MultiQC must be labelled as smoke checks.
5. **Use general test conventions only.** Stable input identifiers, nested element assertions, remote fixture hashes and exact/content-first comparisons from IWC conventions remain applicable independently of a domain exemplar.

## Open requirement

Record the absence of a corpus-backed BAM/CRAM-to-FASTQ pattern for the template and per-step implementation. This is an evidence gap, not permission to drop or simplify source steps.

## Autonomous location choice

The skill's default corpus location is `~/.foundry/iwc`; this run cloned the same public corpus into `iwc-corpus/` under the mandated run directory to honor the instruction to work only there. No existing conversion output was read.
