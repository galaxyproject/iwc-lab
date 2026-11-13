# Workflow debug report

## Final classification

- **Status:** failed assertion, not an execution failure.
- **Failure modality:** `assertion-mismatch`.
- **Final Planemo attempt:** 29 of 29.
- **Execution:** `02:37:04`–`02:41:02`; Planemo exit code 1.
- **Summary:** 1 test, 1 failure, 0 errors, 0 skips.
- **Invocation/history/workflow ID:** `b0dd59e79e0d15e6`.
- **Execution problem:** none. No jobs failed, and all output assertions were reached.
- **Evidence:** `results/attempt-29.json`, `results/attempt-29.html`, and `results/attempt-29.log`.
- **Retained Planemo root:** `/tmp/tmpxzvc7idw` (from the current terminal log; the JSON `problem_log` contains stale roots).

The sole remaining output problem is:

```text
Output software_versions: Expected text 'cat: 9.5'
```

The observed manifest truthfully records:

```yaml
CAT_FASTQ:
  cat: 9.4
```

This is a real process-environment compatibility gap. In the source, `CAT_FASTQ` is a separate process with a coreutils 9.5 container. In the grouped Galaxy conversion step, final read concatenation runs in the pinned samtools container, which supplies coreutils 9.4. The manifest reports the actual runtime; the source-derived assertion was not rewritten to 9.4, and no artificial version-only step was added. The gap is recorded as `cat-fastq-coreutils-version-not-preserved` in `open-requirements.ledger.yml`.

## Final verification

The native authoritative workflow has **14 tool steps** and **14 uniquely labelled public workflow outputs**. Twelve public outputs have test assertions; the two FastQC ZIP outputs remain public but untested.

Attempt 29 establishes:

- All executed workflow jobs completed successfully.
- Both paired samples converted and populated the nested `list:paired_or_unpaired` output with the expected sample and mate structure.
- All **eight exact source nf-test snapshot MD5 assertions passed**:
  - FASTQ validation: `db31682c36cde02f1e8567d130537cac` and `0222a414a69c92608af1580f3c6ce996`.
  - Flagstat: `a53f3d26e2e9851f7d528442bbfe9781` and `acbd95030a362a7e6491faa87d1b9c2c`.
  - Idxstats: `e179601fa7b8ebce81ac3765206f6c15` and `90f01313bc89c7fd096aad051cd71b66`.
  - Alignment stats: `3c3f8fa56674fa987fd912b530f49c3c` and `7e6537bde51ee4bb4a50562014ae2cd4`.
- Pre- and post-conversion FastQC HTML/raw-data identifiers, content checks, and read totals passed.
- MultiQC HTML and general-stats outputs passed their assertions.
- The mapped conversion-version logs reduced to one public YAML dataset in one aggregation job.
- Software-version assertions passed except the retained CAT_FASTQ version mismatch above.

No expected checksum was generated from a Galaxy output or substituted for a source snapshot value. The only expectation changed during final debugging was a newly introduced pre-conversion FastQC content check: its `test` total was corrected from 5,642 primary records to FastQC's actual all-record count of 5,644, including two secondary records. This was not a source snapshot assertion.

## Resolved failure surfaces

The 29-attempt sequence isolated and repaired the following distinct surfaces:

1. **Workflow import/native representation:** synchronized UDT `tool_representation` definitions; corrected native input menus and aliases; supplied explicit public output labels.
2. **Conditional invocation:** replaced unsupported data-presence guards with explicit mode controls and native scalar `when` connections; canonicalized step ordering.
3. **Tool command generation:** escaped shell expansions from UDT JavaScript evaluation and used POSIX-compatible shells in containers without Bash `pipefail`.
4. **Scientific conversion:** restored the source's conditional paired-classification pipeline so `head` does not trigger `set -e`; staged writable FASTA/FAI pairs.
5. **Collection population:** used `designation` captures with `forward`, `reverse`, and `unpaired`; corrected nested per-sample collection shapes and member access.
6. **UDT expressions and identifiers:** used `inputs.reads.elements.<designation>` and `inputs.reads.name`; preserved original alignment baselines for checksum-sensitive reports.
7. **FASTQ validation:** replaced an invalid stock-wrapper/formatter mapping with per-sample paired-or-unpaired `fastq_info`; exact source reports passed.
8. **FastQC:** implemented BAM-capable and per-sample FASTQ UDTs, extracted nested ZIP data correctly, and retained sample identity across mates.
9. **MultiQC:** supplied nonempty FastQC raw data and all six FastQC reports without sample-name collisions.
10. **Output binding:** bound native `workflow_outputs.output_name` to actual producer ports and retained public `label` names for tests.
11. **Assertions:** selected Planemo's collection verifier with real nested `element_tests`; added nested `class: Collection` discriminators required by the vendored schema.
12. **Alignment stats:** replaced stock wrapper behavior with direct samtools 1.23.1 invocations matching source argument order, threads, reference mode, and input basenames; both exact source MD5s passed.
13. **Version aggregation:** reduced mapped per-sample logs into a single manifest dataset rather than testing a collection as one file.

## Static artifacts and known export limitation

- Native workflow validation passes all 14 tool states.
- Test-file static validation passes.
- Both direct stats UDT definitions pass `gxwf validate-tool-source`.
- `galaxy-workflow.gxwf.yml` is synchronized with the final native artifact and validates all 14 tool states.
- Stateful native-to-gxformat2 conversion exits 1 with three fallbacks at stock conditional steps 12, 16, and 17: it mishandles native scalar `when` connections as ordinary tool parameters. See `results/final.gxwf-conversion.log` and `results/final.gxwf-validation.json`.
- Native `.ga` remains the authoritative runtime artifact; gxformat2 is the synchronized secondary representation.

## Test scope and remaining assumptions

The final runtime fixture covers paired BAM conversion with a supplied reference path. The direct single-end FASTQ validation branch is implemented but not exercised by this paired-only default fixture. CRAM-specific pre-conversion filtering and general CRAM-without-matching-reference validation remain open requirements. Unknown stock-wrapper package versions remain explicit nulls in the manifest rather than invented values.

## Recommended next step

Implement a real separate CAT_FASTQ step in the source coreutils 9.5 container. It must consume both mapped and unmapped read streams for paired samples, preserve the direct single-end path, and retain sample/mate identifiers through a paired/single-safe join and collection merge. Then rerun the full native Planemo test with the unchanged `cat: 9.5` assertion. Do not close the gap by changing the expected version to 9.4 or by reporting an unexecuted version string.

## Final Foundry feedback outcome

The explicit feedback review is complete. Four concrete entries were appended to `foundry-feedback.ledger.yml` during this runtime/debug phase sequence:

1. `collection-semantics-missing-udt-access-and-discovery-examples`
2. `planemo-asserts-nested-class-and-collection-verifier-guidance`
3. `gxwf-stateful-export-mishandles-native-when-connections`
4. `planemo-describe-outputs-crashes-on-unlabeled-native-output`

The final CAT_FASTQ environment/topology gap is a workflow requirement, not a new Foundry-source defect, so it is recorded only in the open-requirements ledger. No issue, comment, push, or external post was made.
