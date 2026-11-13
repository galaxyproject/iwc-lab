# CSP2 pairwise alignment of assemblies

This workflow runs the [CFSAN SNP Pipeline 2 (CSP2)](https://github.com/CFSAN-Biostatistics/CSP2),
version v.0.9.7.8, in its `align` run mode. Given a collection of bacterial genome assemblies, it
aligns isolates in pairs with MUMmer and writes one CSP2 `.snpdiffs` file per pair, the
alignment summary format the other CSP2 modes read. It also tabulates the alignment statistics
and assembly metrics recorded in those files. No quality filtering is applied and no SNP
distance is computed; that is what `csp2-screen` and `csp2-snp-distance` do.

CSP2's own scripts do the work, unmodified, from the image the CSP2 authors publish
(`cfsanbiostatistics/csp2:v.0.9.7.8-galaxy`). The workflow splits the pipeline into Galaxy
steps so that each alignment is its own job:

1. Decide which pairs to align.
2. Align each pair with MUMmer `dnadiff` and compile the alignment into CSP2's `.snpdiffs`
   format with `compileMUMmer.py`.
3. Summarise all alignments with `saveSNPDiffs.py`.

The alignment and summary steps are the same embedded tools as in `csp2-screen` and
`csp2-snp-distance`.

## Inputs

- **Query assemblies**: a list collection with one FASTA assembly per isolate. This is the
  whole isolate pool, references included.
- **Reference isolate IDs** (optional): comma-separated element identifiers from the
  collection to use as references. Spaces around each ID are ignored and repeated IDs count
  once. CSP2's `--ref_id` keeps the spaces, so there `Sample_A, Sample_B` would silently drop
  ` Sample_B`; here both are references.

Which pairs are aligned follows CSP2's `align` mode:

- With reference IDs, every isolate that is not a reference is aligned, as the query, against
  each reference. References are not aligned with each other. IDs that name no element of the
  collection are ignored; if none of them names an element, or every isolate is a reference,
  there is nothing to align and the run fails, as CSP2 does.
- Without reference IDs, every two isolates are aligned once (all-vs-all). Of the two, the one
  later in the collection is the query and the earlier one the reference. CSP2 makes that choice
  by whichever side of a Nextflow `combine` arrives first, so it can differ from run to run
  there; here it follows collection order. At least two isolates are needed.

No isolate is aligned with itself.

Each element identifier is used unchanged as the isolate ID. CSP2 takes the ID from the file
name with its extension removed, so if a collection is built from uploads named `sample.fasta`,
rename the elements to `sample` to get the names CSP2 would report.

Isolate IDs may use only letters, digits, `.`, `_` and `-`, and may not start with `-` or
contain `__vs__` (the separator in CSP2's file names). CSP2 builds file names and command
arguments from these IDs, so anything else is rejected before
alignment. So is a set of IDs where two pairs would get the same CSP2 file name, such as
`a__vs` with `b` and `a` with `vs__b` (both `a__vs__vs__b.snpdiffs`), or where the two IDs of a
pair add up to more than 240 characters, which would make that file name too long.

CSP2's `align` mode takes no thresholds, so there are no other parameters.

## Outputs

- **SNPDiffs**: one alignment summary per pair, named `<query>:<reference>`. Each is a
  tab-separated text file: a `#` header line with both isolate IDs, assembly metrics, k-mer
  similarity and the MUMmer alignment summary, `##` lines for the aligned regions, then one line
  per SNP, indel or invalid site.
- **Raw MUMmer summary**: one row per alignment with the header fields of its `.snpdiffs` file
  as columns.
- **Isolate data**: one row per isolate with its assembly metrics, marked `Reference` or
  `Query`. In all-vs-all runs every isolate is a `Query`, as in CSP2.
- **Reference IDs**: the reference isolates used, one per line; empty in all-vs-all runs.

Assembly paths in the `.snpdiffs` headers and in the two tables are job-local labels
(`fasta/<isolate ID>.fasta`), and the `SNPDiffs_File` column holds a job-local path.

## Using it with the other CSP2 workflows

The **Assemblies** output of `csp2-assembly` is a collection of this shape, with the isolate IDs
already in place as element identifiers, so it can be used directly as **Query assemblies**.
Isolates that are already assembled can be added by merging their FASTA files into the same
list (Galaxy's "Merge collections"). The same goes for a separate collection of reference
assemblies: merge it into the pool and name its isolates in **Reference isolate IDs**.

## Requirements

Three steps are Galaxy user-defined tools embedded in the workflow, so the Galaxy server needs
`enable_beta_tool_formats` set and the user needs permission to run user-defined tools. Those
steps run in a Docker container. The workflow was tested on Galaxy 26.1; older releases were not
tried.

## What is not covered

Only `align` mode from assemblies is implemented. CSP2 also takes reads, which it assembles
with SKESA first (the separate workflow `csp2-assembly` does that), and existing `.snpdiffs`
files, whose pairs it then skips; neither is carried. References are named by ID within one
collection, which is CSP2's `--ref_id`; CSP2's separate reference inputs (`--ref_fasta`,
`--ref_reads`) give the same pairs once the references are merged into the pool. Excluding
isolates by ID and trimming a common string from isolate names are not exposed.

CSP2 also keeps the raw `dnadiff` output of every pair (`MUMmer_Output/`), a log per pair from
`compileMUMmer.py`, and the list of `.snpdiffs` paths; the workflow does not collect them.

## Validation

The tests run two cases on three of the soil isolates in the CSP2 test data (Sample_A,
Sample_B and Sample_D). One names Sample_A as the reference; the other aligns all three
all-vs-all. Expected outputs come from running upstream's own Nextflow pipeline
(`CSP2.nf --runmode align`) in the CSP2 image on the same assemblies, and the two pairs against
Sample_A also match the `.snpdiffs` files CSP2's authors publish with that data. The `.snpdiffs`
files are compared in full apart from the assembly paths in their header line, and every row of
the two tables is checked.

The k-mer counts in a `.snpdiffs` header (`Shared_Kmers`, `Reference_Unique_Kmers`,
`Query_Unique_Kmers`) are allowed to be one higher than upstream's. CSP2 v.0.9.7.8 counts an
empty first attempt of its k-mer counter as an extra k-mer, which happens when the host is short
of memory; nothing else in the output changes when it does.

Shortage of memory can also do worse. With a small but positive Java heap, CSP2's k-mer counter
can run out of memory part-way, print only some of the k-mers and still exit successfully, and
CSP2 v.0.9.7.8 accepts that partial set. The run then succeeds with k-mer counts and
`Kmer_Similarity` that are wrong by much more than one (81.93 instead of 98.51 in one observed
case). The MUMmer alignment, SNP, indel and assembly metrics are not affected. The counter sizes
its heap from the host's free memory, not the container's limit, so run the alignment step where
the host has memory to spare, and treat a `Kmer_Similarity` far below what the alignment
percentages suggest as a sign of this rather than of the data.
