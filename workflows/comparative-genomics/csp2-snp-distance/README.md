# CSP2 SNP distance analysis from assemblies

This workflow runs the [CFSAN SNP Pipeline 2 (CSP2)](https://github.com/CFSAN-Biostatistics/CSP2),
version v.0.9.7.8, in its `snp` run mode. Given a collection of bacterial genome assemblies it
estimates pairwise SNP distances between isolates, relative to one or more reference isolates
drawn from the same collection.

CSP2's own scripts do the science, unmodified, from the image the CSP2 authors publish
(`cfsanbiostatistics/csp2:v.0.9.7.8-galaxy`). The workflow splits the pipeline into Galaxy
steps so that each alignment and each reference is its own job:

1. Choose references. Either the isolates named in `Reference isolate IDs`, or, when that is
   left empty, RefChooser (Mash sketch, Mash triangle and CSP2's `chooseRefs.py`).
2. Align every isolate against every reference with MUMmer `dnadiff` and compile each alignment
   into CSP2's `.snpdiffs` format with `compileMUMmer.py`.
3. Summarise all alignments with `saveSNPDiffs.py`.
4. Run the SNP analysis once per reference with `runSNPPipeline.py`.
5. Optionally build a tree per reference with IQ-TREE.

## Inputs

- **Query assemblies**: a list collection with one FASTA assembly per isolate. The element
  identifier is the isolate ID. This is the whole isolate pool, references included.
- **Reference isolate IDs** (optional): comma-separated identifiers from the collection to use
  as references. Leave empty to have references chosen automatically.
- **Number of references to select**: how many references RefChooser picks when none are named
  (default 1).

Isolate IDs may use only letters, digits, `.`, `_` and `-`, and may not start with `-`. CSP2 builds file names and command
arguments from these IDs, so anything else is rejected before alignment.

The remaining parameters are CSP2's quality thresholds, with CSP2's defaults: minimum reference
coverage (85%), minimum alignment length (500) and identity (99%), reference and query contig
edge distances (150), SNP density windows (`1000,125,15`) and the maximum SNPs per window
(`3,2,1`), maximum missing data per site (50%), and whether to rescue query-edge SNPs. The tree
step takes a switch, a substitution model (`MFP+MERGE+ASC`) and bootstrap settings.

## Outputs

- **Reference IDs**: the reference isolates used.
- **SNPDiffs**: one alignment summary per query and reference pair, named `<query>:<reference>`.
- **Raw MUMmer summary** and **Isolate data**: tables covering every alignment and every isolate.
- Per reference: **Pairwise SNP distances**, **SNP distance matrix**, **SNP list**,
  **SNP alignment** and **Reference screening**, plus "preserved" versions of the distances,
  matrix, list and alignment, which keep only the sites that pass the missing-data threshold.
- **Phylogenetic tree**: one tree per reference with more than three sequences, when enabled.

## Requirements

Four steps are Galaxy user-defined tools embedded in the workflow, so the Galaxy server needs
`enable_beta_tool_formats` set and the user needs permission to run user-defined tools. Those
steps run in a Docker container.

## What is not covered

Only `snp` mode is implemented. The workflow starts from assemblies, so read assembly with SKESA
is not included, and CSP2's `screen`, `align` and `assemble` modes are not carried. CSP2 keeps
one alignment per pair of references; this workflow aligns both directions. The tree step uses
the Tool Shed IQ-TREE wrapper, which is a newer IQ-TREE than the one in the CSP2 image.

## Validation

The tests run two cases, both from the soil isolates in the CSP2 test data. One names Sample_A as
the reference for three isolates with the tree switched off; its expected outputs come from
running upstream's own Nextflow pipeline on the same three assemblies, and they agree with the
published 15-isolate values for those isolates. The other runs all 15 isolates with every setting
at its default, so RefChooser picks the reference and the tree is built, and compares against the
expected outputs CSP2's authors publish for that run.

In both cases the snpdiffs, summary tables, reference screening, pairwise distances, distance
matrices, SNP list and SNP alignment, raw and preserved, are checked on their content. Assembly
paths are left out of those checks. CSP2 writes the screening rows and the preserved SNP list in
an order that changes from run to run, so they are sorted before comparing, and the preserved
alignment is checked by size and per-isolate base counts. The tree comes from a newer IQ-TREE than
upstream's, so only its shape is checked. Choosing more than one reference has no published
expected output and is not tested.
