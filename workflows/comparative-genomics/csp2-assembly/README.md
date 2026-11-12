# CSP2 assembly of paired reads with SKESA

This workflow runs the read assembly of the
[CFSAN SNP Pipeline 2 (CSP2)](https://github.com/CFSAN-Biostatistics/CSP2), version v.0.9.7.8,
which is its `assemble` run mode. Given a collection of paired bacterial reads it makes one
SKESA assembly per isolate. CSP2's other modes start from assemblies, so this is the step that
lets read data into them.

SKESA 2.4.0 runs from the image the CSP2 authors publish
(`cfsanbiostatistics/csp2:v.0.9.7.8-galaxy`), with nothing added: no trimming, no quality
control, no filtering, and SKESA's defaults for everything but the read arguments. Each isolate
is its own job.

## Two assembly modes

**Paired-end (default).** SKESA gets both files of a pair,
`skesa --cores <n> --reads <forward>,<reverse> --contigs_out <out>`, which is the form SKESA
documents for mates in two files. Both mates are assembled and the pairing is used.

**Reproduce CSP2 v.0.9.7.8 assembly (forward reads only).** CSP2 v.0.9.7.8 calls
`skesa --cores <n> --use_paired_ends --fastq <forward> <reverse> --contigs_out <out>`. SKESA
takes one value per `--fastq`, and the reverse file, separated by a space, is dropped without a
message: SKESA reports only the forward read count, and the result is the same when the reverse
file is missing or is not a FASTQ file. The forward reads are assembled alone, as single-end
reads. With this switch on, the workflow runs that command unchanged. Use it to match
assemblies made by CSP2 itself at that version, for example to compare with earlier CSP2 results;
leave it off for new work.

The default therefore differs from what CSP2 v.0.9.7.8 produces. On the Week_42 reads of the
CSP2 test data (318,725 pairs, reads of up to 251 bases, a 4.6 Mb genome):

| | Contigs | Total bases | N50 | Largest contig |
|---|---|---|---|---|
| Paired-end (default) | 137 | 4,612,997 | 64,029 | 237,699 |
| Forward reads only (CSP2 v.0.9.7.8) | 372 | 4,561,747 | 24,332 | 97,467 |

The forward-only assembly is, byte for byte, the one published with CSP2's expected test output.
These figures are from that one dataset.

## Inputs

- **Paired reads**: a `list:paired` collection with one forward/reverse pair of FASTQ files per
  isolate, plain or gzipped (`fastqsanger` or `fastqsanger.gz`). The identifier of each pair is
  the isolate ID. The two files must list the mates in the same order: SKESA pairs them by
  position, fails if the reverse file has fewer reads than the forward file, and ignores reverse
  reads beyond the last forward read.
- **Reproduce CSP2 v.0.9.7.8 assembly (forward reads only)**: off by default. See above.

Isolate IDs cannot contain whitespace, `,`, `/` or `:`. These are the characters the other CSP2
workflows refuse, and an ID that has one fails here, before the assembly runs.

## Outputs

- **Assemblies**: a list collection with one FASTA assembly per isolate, named by isolate ID.
  Contigs are named `Contig_<number>_<k-mer coverage>` and are at least 200 bases long. The
  assembly does not depend on the number of cores the job gets.

A job fails when SKESA fails, which includes reads that cannot be assembled at all. If SKESA
succeeds without reporting a contig, the assembly is an empty dataset, as it is in CSP2.

## Using the assemblies in the other CSP2 workflows

**Assemblies** is the collection the other two workflows take, with the isolate IDs already in
place as element identifiers:

- `csp2-snp-distance`: use it as **Query assemblies**.
- `csp2-screen`: use it as **Query assemblies** or as **Reference assemblies**.

Isolates that are already assembled can be added by merging their FASTA files into the same
list (Galaxy's "Merge collections"), which is what CSP2 does when it is given reads and
assemblies together.

## Requirements

One step is a Galaxy user-defined tool embedded in the workflow, so the Galaxy server needs
`enable_beta_tool_formats` set and the user needs permission to run user-defined tools. That
step runs in a Docker container. The job uses as many cores as Galaxy gives it; CSP2 itself
gives SKESA at most 4 cores and 12 GB of memory. Assembling the Week_42 reads took up to about 3.5 GB
paired-end and about 2 GB forward-only.

## What is not covered

Only paired reads are taken. CSP2 also assembles single-end reads (`skesa --fastq <reads>`),
which is not carried as a separate input; in every case tried it gave the same assembly as the
forward-only mode gives for a pair with those reads as its forward file. CSP2 finds and pairs read files by file name suffix in a directory and can trim a common
string from isolate names; here the pairing and the names come from the input collection. The
`Assembly_Data.tsv` table CSP2 writes in this mode, which lists the read and assembly paths of
each isolate, is not produced. CSP2's `snp` and `screen` modes are the separate workflows
`csp2-snp-distance` and `csp2-screen`, and `align` is not carried.

## Validation

For the Week_42 reads published with the CSP2 test data, the forward-only mode gives, byte for
byte, the SKESA assembly published with the expected output of CSP2's contamination screen, and
the paired-end mode gives the same assembly as SKESA 2.5.1 does for the same command. Both modes
gave the same bytes with 1, 2, 4 and 8 cores on the test reads. The tests run three small
isolates in each mode: two are the Week_42 read pairs that cover one contig each of that
published assembly, and one is simulated.
