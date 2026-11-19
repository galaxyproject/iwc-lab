# Galaxy workflow change-set — nf-core-demo-deepseek revision

Baseline: `galaxy-workflow.before-revision.gxwf.yml` (= `starting-galaxy-workflow.gxwf.yml`).
Source of the requested changes: `orchestrator-findings-2026-11-10.md` §1 (Galaxy's "Issues loading this workflow" list). §2 reports no frame problems, so no frame edit is requested.

Review note: every finding is Galaxy reporting that an **optional** parameter key is absent from `state`, so the editor substitutes its default (`RuntimeValue` for optional datasets, `''` for the comment). None of these parameters is set to a non-default value by nf-core/demo (`FASTQC` gets only `--quiet`; `MULTIQC` gets no comment and no image content), so "unset" is the correct intent. Two encodings were tested with `gxwf validate --strict`: an explicit `null` is **rejected for optional data-typed parameters** (`contaminants: Expected never, actual null`) and for `image_content_input`, but accepted for the optional integer `min_length` and legal for the text `comment`. The change-set therefore makes explicit exactly what the schema can express and leaves the rest as the correct unconnected-input representation.

| # | kind | anchor | decision | acceptance |
|---|---|---|---|---|
| 1 | change-parameter | step `fastqc`, state key `adapters` | **Left unchanged.** Optional data input; nf-core/demo supplies no adapter list, and `gxwf` rejects an explicit null. Omitted key = unconnected optional input, which is the correct representation. | Key stays absent; FastQC behaviour unchanged (verified by the planemo test). |
| 2 | change-parameter | step `fastqc`, state key `contaminants` | **Left unchanged** for the same reason (`Expected never, actual null`). | Key stays absent. |
| 3 | change-parameter | step `fastqc`, state key `limits` | **Left unchanged** (same optional-data encoding rule). | Key stays absent. |
| 4 | change-parameter | step `fastqc`, state key `min_length` | **Applied: `min_length: null`.** Integer parameter; explicit null states "no lower length limit" rather than leaving the key out. | `state.min_length` present and null; strict tool-state validation passes. |
| 5 | change-parameter | step `multiqc`, state key `comment` | **Applied: `comment: ""`** — the wrapper's default and nf-core's behaviour, now explicit. | `state.comment` present and empty. |
| 6 | change-parameter | step `multiqc`, state key `image_content_input` | **Left unchanged.** Optional data input; `gxwf` rejects `null` (`Expected undefined, actual null`) and the wrapper declares no other "unset" value. Omitted key is the correct unconnected-input form. | Key stays absent. |

## Applied diff (whole change-set)

```
72a73
>     min_length: null
113a115
>     comment: ''
```

## Out of scope (explicitly not changed)

- Canvas/frame `position` and `size`: excluded by the task rules.
- Step set, wiring, tool versions, outputs: the findings name none, and the applied diff touches nothing else.

## Carried obligations

`open-requirements.ledger.yml` is passed through unchanged; this change-set adds no obligation.
