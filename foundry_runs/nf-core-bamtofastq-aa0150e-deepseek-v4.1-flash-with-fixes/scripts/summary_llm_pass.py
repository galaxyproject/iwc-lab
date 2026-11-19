#!/usr/bin/env python3
"""LLM post-pass over foundry's deterministic summarize-nextflow output.

Fills processes[].script_summary and replaces workflow.edges with the
reconciled data-flow, per the summarize-nextflow Mold's LLM-pass split.
Run with python3 -I so no planted module in cwd/source can shadow imports.
"""
import json
import sys

path = sys.argv[1]
with open(path) as fh:
    s = json.load(fh)

SUMMARIES = {
    "CHECKPAIREDEND": (
        "Samples up to 1000 alignment records with samtools view and writes a "
        "paired.txt or single.txt marker depending on whether every sampled read "
        "is paired (FLAG 0x1)."
    ),
    "SAMTOOLS_INDEX": "Builds a BAM/CRAM index (BAI/CSI/CRAI) with samtools index.",
    "SAMTOOLS_FAIDX": "Builds a FASTA index (.fai) for the reference with samtools faidx.",
    "SAMTOOLS_FLAGSTAT": "Summarises alignment flag counts per BAM/CRAM with samtools flagstat.",
    "SAMTOOLS_IDXSTATS": "Reports per-contig mapped/unmapped read counts with samtools idxstats.",
    "SAMTOOLS_STATS": "Computes detailed alignment statistics with samtools stats, optionally against the reference.",
    "FASTQC": "Runs FastQC to produce per-sample HTML/ZIP quality-control reports.",
    "SAMTOOLS_VIEW": (
        "Subsets a BAM/CRAM with samtools view using FLAG filters (mapped/unmapped "
        "read pairs), optional region selection, and optional indexing."
    ),
    "SAMTOOLS_MERGE": "Merges the three unmapped BAM/CRAM subsets per sample with samtools merge.",
    "SAMTOOLS_COLLATEFASTQ": (
        "Converts BAM/CRAM to FASTQ with `samtools collate | samtools fastq`, "
        "splitting read pairs, singletons and remaining ('other') reads."
    ),
    "CAT_FASTQ": "Concatenates mapped and unmapped read pairs into the final merged R1/R2 FASTQ.gz per sample.",
    "FASTQUTILS_INFO": "Validates the converted FASTQ files with fastq_info and writes a per-sample confirmation .txt.",
    "MULTIQC": "Aggregates QC reports and collated software versions into one MultiQC HTML report.",
}

for p in s["processes"]:
    summary = SUMMARIES.get(p["name"])
    if summary is None:
        raise SystemExit(f"no script_summary authored for process {p['name']}")
    p["script_summary"] = summary

E = s["workflow"]["edges"] = []


def edge(src, dst, via=None, notes=None):
    e = {"from": src, "to": dst}
    if via:
        e["via"] = via
    if notes:
        e["notes"] = notes
    E.append(e)


# --- entry / index preparation
edge("ch_samplesheet", "PREPARE_INDICES")
edge("fasta_fai", "PREPARE_INDICES")
edge("ch_input", "SAMTOOLS_INDEX", ["PREPARE_INDICES.out.ch_input_indexed"],
     "only for samples whose samplesheet row has no index")
edge("ch_input_indexed", "PRE_CONVERSION_QC")
edge("ch_fasta_fai", "PRE_CONVERSION_QC")
edge("ch_input_indexed", "CHECKPAIREDEND")
edge("ch_fasta_fai", "CHECKPAIREDEND")

# --- pre-conversion QC (inside PRE_CONVERSION_QC)
edge("ch_input_indexed", "SAMTOOLS_IDXSTATS", notes="subworkflow PRE_CONVERSION_QC")
edge("ch_input_indexed", "SAMTOOLS_FLAGSTAT", notes="subworkflow PRE_CONVERSION_QC")
edge("ch_input_indexed", "SAMTOOLS_STATS", notes="subworkflow PRE_CONVERSION_QC")
edge("ch_fasta_fai", "SAMTOOLS_STATS", notes="subworkflow PRE_CONVERSION_QC")
edge("ch_input_indexed", "FASTQC_PRE_CONVERSION", ["branch { filetype == 'bam' }"],
     "subworkflow PRE_CONVERSION_QC; CRAM inputs are skipped for pre-conversion FastQC")

# --- single/paired classification into the conversion-ready channel
edge("ch_input_indexed", "ch_input_new", ["join(CHECKPAIREDEND.out.single_end)",
                                          "join(CHECKPAIREDEND.out.paired_end)", "mix"])
edge("CHECKPAIREDEND.out.single_end", "ch_input_new")
edge("CHECKPAIREDEND.out.paired_end", "ch_input_new")

# --- optional chromosome subsetting
edge("ch_input_new", "SAMTOOLS_CHR", notes="only when params.chr is set")
edge("ch_fasta_fai", "SAMTOOLS_CHR", notes="only when params.chr is set")
edge("SAMTOOLS_CHR.out.bam", "SAMTOOLS_CHR_INDEX", notes="only when params.chr is set")
edge("SAMTOOLS_CHR.out.cram", "SAMTOOLS_CHR_INDEX", notes="only when params.chr is set")
edge("SAMTOOLS_CHR_INDEX.out.index", "ch_input_chr", ["join(CHECKPAIREDEND-classified channel)"],
     "ch_input_new is rebound to the chr-subset channel")

# --- conversion branches
edge("conversion_input.ch_single", "SAMTOOLS_COLLATEFASTQ_SINGLE_END", ["branch { meta.single_end == true }"],
     "single-end path")
edge("ch_fasta_fai", "SAMTOOLS_COLLATEFASTQ_SINGLE_END")
edge("conversion_input.ch_paired", "ALIGNMENT_TO_FASTQ", ["branch { meta.single_end == false }"],
     "paired-end path")
edge("ch_fasta_fai", "ALIGNMENT_TO_FASTQ")

# --- inside ALIGNMENT_TO_FASTQ
edge("input", "SAMTOOLS_VIEW_MAP_MAP", ["ext.args='-b -f1 -F12'"], "subworkflow ALIGNMENT_TO_FASTQ")
edge("input", "SAMTOOLS_VIEW_MAP_UNMAP", ["ext.args='-b -f8 -F260'"], "subworkflow ALIGNMENT_TO_FASTQ")
edge("input", "SAMTOOLS_VIEW_UNMAP_MAP", ["ext.args='-b -f4 -F264'"], "subworkflow ALIGNMENT_TO_FASTQ")
edge("input", "SAMTOOLS_VIEW_UNMAP_UNMAP", ["ext.args='-b -f12 -F256'"], "subworkflow ALIGNMENT_TO_FASTQ")
edge("ch_fasta_fai", "SAMTOOLS_VIEW_MAP_MAP")
edge("ch_fasta_fai", "SAMTOOLS_VIEW_MAP_UNMAP")
edge("ch_fasta_fai", "SAMTOOLS_VIEW_UNMAP_MAP")
edge("ch_fasta_fai", "SAMTOOLS_VIEW_UNMAP_UNMAP")
edge("SAMTOOLS_VIEW_UNMAP_UNMAP.out.bam", "SAMTOOLS_MERGE_UNMAP",
     ["join(UNMAP_MAP.out.bam, remainder: true)", "join(MAP_UNMAP.out.bam, remainder: true)"])
edge("SAMTOOLS_VIEW_UNMAP_MAP.out.bam", "SAMTOOLS_MERGE_UNMAP")
edge("SAMTOOLS_VIEW_MAP_UNMAP.out.bam", "SAMTOOLS_MERGE_UNMAP")
edge("SAMTOOLS_VIEW_UNMAP_UNMAP.out.cram", "SAMTOOLS_MERGE_UNMAP", ["mix with bam branch"])
edge("SAMTOOLS_MERGE_UNMAP.out.bam", "COLLATE_FASTQ_UNMAP", ["mix(cram)"])
edge("SAMTOOLS_MERGE_UNMAP.out.cram", "COLLATE_FASTQ_UNMAP")
edge("SAMTOOLS_VIEW_MAP_MAP.out.bam", "COLLATE_FASTQ_MAP", ["mix(cram)"])
edge("SAMTOOLS_VIEW_MAP_MAP.out.cram", "COLLATE_FASTQ_MAP")
edge("COLLATE_FASTQ_MAP.out.fastq", "CAT_FASTQ", ["join(COLLATE_FASTQ_UNMAP.out.fastq)",
                                                  "map to 4-file list"])
edge("COLLATE_FASTQ_UNMAP.out.fastq", "CAT_FASTQ")

# --- post-conversion QC
edge("SAMTOOLS_COLLATEFASTQ_SINGLE_END.out.fastq_other", "ch_reads_post_qc", ["mix"])
edge("CAT_FASTQ.out.reads", "ch_reads_post_qc")
edge("ch_reads_post_qc", "FASTQC_POST_CONVERSION")
edge("ch_reads_post_qc", "FASTQUTILS_INFO")

# --- versions + MultiQC
edge("versions_topic", "ch_collated_versions", ["channel.topic('versions')", "softwareVersionsToYAML"])
edge("ch_collated_versions", "MULTIQC")
edge("multiqc_config", "MULTIQC", ["file(..., checkIfExists: true)"])
edge("multiqc_logo", "MULTIQC")
edge("ch_workflow_summary", "MULTIQC")
edge("ch_methods_description", "MULTIQC")
edge("MULTIQC.out.report", "multiqc_report")

s.setdefault("warnings", []).extend([
    "MultiQC receives only the collated software versions, the params summary and the "
    "methods description: the mix of FASTQC_PRE_CONVERSION.out.zip and "
    "ALIGNMENT_TO_FASTQ.out.zip into ch_multiqc_files is commented out in workflows/bamtofastq.nf "
    "(lines 171-172), so per-sample FastQC reports are published but not aggregated.",
    "ALIGNMENT_TO_FASTQ outputs only CAT_FASTQ.out.reads; SAMTOOLS_FLAGSTAT/IDXSTATS/STATS and "
    "FASTQC_PRE_CONVERSION outputs are emitted by PRE_CONVERSION_QC but not consumed further.",
])

with open(path, "w") as fh:
    json.dump(s, fh, indent=1)
    fh.write("\n")

print("post-pass wrote", path)
print("processes:", len(s["processes"]), "edges:", len(E))
