# CSP2 screening of query assemblies against reference assemblies

This workflow runs the [CFSAN SNP Pipeline 2 (CSP2)](https://github.com/CFSAN-Biostatistics/CSP2),
version v.0.9.7.8, in its `screen` run mode. Given a collection of bacterial query assemblies and
a collection of reference assemblies, it reports for every query and reference pair whether the
query covers the reference well enough to compare, and how many SNPs separate the two after
CSP2's quality filters. A typical use is checking new assemblies against a lab control strain
for contamination.

CSP2's own scripts do the science, unmodified, from the image the CSP2 authors publish
(`cfsanbiostatistics/csp2:v.0.9.7.8-galaxy`). The workflow splits the pipeline into Galaxy
steps so that each alignment is its own job:

1. Align every query against every reference with MUMmer `dnadiff` and compile each alignment
   into CSP2's `.snpdiffs` format with `compileMUMmer.py`.
2. Summarise all alignments with `saveSNPDiffs.py`.
3. Screen all alignments in one job with `screenSNPDiffs.py`.

## Inputs

- **Query assemblies**: a list collection with one FASTA assembly per query isolate.
- **Reference assemblies**: a list collection with one FASTA assembly per reference isolate.

Each element identifier is used unchanged as the isolate ID. CSP2 takes the ID from the file
name with its extension removed, so if a collection is built from uploads named `sample.fasta`,
rename the elements to `sample` to get the names CSP2 would report.

The two collections are kept apart: queries are compared with references, never with each
other. An isolate ID that appears in both collections is used as a reference only, and its
reference-collection file is the one aligned (CSP2 would take the file given on the query side).
If that leaves no queries at all, there is nothing to pair and the run fails, as CSP2 does.

Isolate IDs may use only letters, digits, `.`, `_` and `-`, and may not start with `-` or
contain `__vs__` (CSP2 joins the two IDs of a pair with `__vs__` in file names). CSP2 builds
file names and command arguments from these IDs, so anything else is rejected before
alignment.

The remaining parameters are CSP2's quality thresholds, with CSP2's defaults: minimum reference
coverage (85%), minimum alignment length (500) and identity (99%), reference and query contig
edge distances (150), SNP density windows (`1000,125,15`) and the maximum SNPs per window
(`3,2,1`).

## Outputs

- **Screening results**: one row per query and reference pair, with the screen category (`Pass`,
  `Low_Coverage`, `Low_Quality_Coverage` or `SNP_Cutoff`), the SNP count after filtering, the
  percentage of each genome aligned and the number of sites removed by each filter. Rows are in
  no particular order.
- **Screening SNP tables**: for each pair that passed with at least one SNP, every SNP, indel
  and invalid site and the filter that removed it. Named `<query>__vs__<reference>`.
- **Screening logs**: CSP2's screening log for each pair, named the same way.
- **SNPDiffs**: one alignment summary per pair, named `<query>:<reference>`.
- **Raw MUMmer summary** and **Isolate data**: tables covering every alignment and every isolate.
- **Reference IDs**: the reference isolates used.

## Requirements

Three steps are Galaxy user-defined tools embedded in the workflow, so the Galaxy server needs
`enable_beta_tool_formats` set and the user needs permission to run user-defined tools. Those
steps run in a Docker container.

## What is not covered

Only `screen` mode with references is implemented; CSP2's `snp` mode is the separate workflow
`csp2-snp-distance`, and `align` and `assemble` are not carried. The workflow starts from
assemblies, so read assembly with SKESA is not included. CSP2 can also screen all queries
against each other when no reference is given, take reference IDs from a pooled set of
assemblies (`--ref_id`), re-screen existing `.snpdiffs` files, exclude isolates by ID and trim
a common string from isolate names; none of these is exposed.

## Validation

For the contamination screen published with the CSP2 test data (two query assemblies against
one lab control), the screening results and the screening SNP tables are identical to the
expected outputs, and the `.snpdiffs` files differ only in the assembly paths in their header
line.
