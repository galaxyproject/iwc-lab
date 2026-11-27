# Metaboigniter: mzML quantification and compound identification

Galaxy (Format-2) conversion of [nf-core/metaboigniter](https://github.com/nf-core/metaboigniter)
2.0.1 (commit `55d82547604fcae3b6557fe7a3c442b623184f34`), covering the paired MS1/MS12
quantification path plus the optional requantification and identification branches.

The workflow detects and quantifies features per sample with OpenMS, aligns the feature maps and
retention times across the cohort, annotates adducts (and optionally C13 patterns), links features
into consensus features, and exports the source-layout quantification table. Optionally it can
requantify features missing from the consensus, and run SIRIUS/FingerID and MS2Query on mapped MS2
spectra. A MultiQC report is produced from the active branch's table.

## Inputs

| Input | Type | Description |
| --- | --- | --- |
| `quantification_samples` | list collection of `mzml` | Centroided mzML files, one element per sample. Use only rows that the source sample sheet marks as `MS1` or `MS12`; the element identifier is used as the sample ID. |
| `requantification` | boolean (default `false`) | Detect and requantify consensus features that are missing from some samples. |
| `identification` | boolean (default `false`) | Map MS2 spectra and run the identification branch. Requires MS12 samples. |
| `polarity` | `positive` or `negative` (default `positive`) | Used for adduct decharging, C13 detection and MS2Query model selection. |
| `run_sirius` | boolean (default `false`) | Run SIRIUS (and FingerID when `run_fingerid` is set). Requires `identification`. |
| `run_fingerid` | boolean (default `false`) | Run CSI:FingerID structure search together with SIRIUS. Requires `run_sirius`. |
| `run_ms2query` | boolean (default `false`) | Download the polarity-specific MS2Query models and score mapped spectra. Requires `identification`. |

## Outputs

| Output | Produced when |
| --- | --- |
| `Quantification table` | quantification only (`identification` and `requantification` off) |
| `Requantified quantification table` | `requantification` on, `identification` off |
| `Identified quantification table` | `identification` on, `requantification` off |
| `Identified and requantified quantification table` | `identification` and `requantification` on |
| `MultiQC report` | always |

## Scope and known differences from the Nextflow pipeline

- Only the source's default **paired** MS2 collection model is implemented. The
  `ms2_collection_model=separate` mode is not available.
- Centroiding (`OPENMS_PEAKPICKERHIRES`) is **not** included; input mzML files must already be
  centroided (`skip_centroiding=true` in the source test profile).
- Sample-sheet parsing and MS1/MS12 filtering are not done in the workflow: supply a pre-filtered
  collection whose element identifiers match the source sample IDs.
- The unmapped-spectra identification path (`run_umapped_spectra`) and custom MS2Query model
  training (`train_library_ms2query`, MGF splitting) are not implemented. MS2Query always downloads
  the source's polarity-specific models.
- MultiQC configuration/title/logo inputs are not exposed. Unlike the Nextflow pipeline, the
  Galaxy MultiQC report includes the quantification table as a custom-content section; the nf-core
  methods-description/workflow-summary sections are not present.
- The source toggles `skip_alignment`, `skip_adduct_detection`, `parallel_linking`,
  `split_consensus_parts`, `mgf_splitmgf_pyopenms` and `sirius_split`, and the SIRIUS credential /
  database options, are not exposed.
- Nextflow publishes intermediate `quantification/`, `alignment/`, `annotation/` and `linker/`
  directories; this workflow exposes only the final tables and the MultiQC report.

## Testing status

- The **quantification-only branch is validated** against the nf-core `test` profile inputs
  (X2_Rep1, X3_Rep1, X6_Rep1; positive polarity; centroiding skipped). The 57,386-row output table
  is numerically identical to the Nextflow result for `charge`, `RT`, `mz`, `quality`, the three
  sample intensities and `adduct`; only the random OpenMS `id`/`feature_ids` and the sample-column
  order differ.
- The identification (SIRIUS/FingerID, MS2Query, C13) and requantification branches are implemented
  but have **not yet been executed** by the test suite.
- The current test asserts the quantification output line count and the presence of the
  `feature_ids` column, and that the MultiQC output looks like a MultiQC report.

## Running the test

```bash
planemo test metaboigniter.gxwf.yml
```

The test downloads the three public nf-core test-data mzML files (about 200 MB in total) and runs
the full quantification branch in Docker.

## Provenance

Converted from nf-core/metaboigniter 2.0.1 with the Foundry Nextflow-to-Galaxy pipeline. The
fidelity assessment against the reference execution, including intermediate-file comparisons, is
recorded in the conversion PR description.

Maintainer: Franziska Nicolaus (ORCID [0009-0008-4238-4117](https://orcid.org/0009-0008-4238-4117)).
