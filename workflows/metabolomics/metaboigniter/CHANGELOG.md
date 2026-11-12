# Changelog

## 0.1 - 2026-11-12

- Initial Format-2 conversion of nf-core/metaboigniter 2.0.1 (paired MS1/MS12 model).
- Added the quantification, requantification, identification (SIRIUS/FingerID, MS2Query) and C13
  branches, source-layout table exports and a MultiQC report.
- Validated the quantification-only branch against the Nextflow `test` profile: the 57,386-row
  table matches numerically; only random feature identifiers and sample-column order differ.
- Identification and requantification branches are not covered by tests yet.
