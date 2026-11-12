**Title:** Template frames lack step positions, breaking workflow save in Galaxy

> Posted by an AI assistant on <user>'s behalf.

## Summary

The workflow produced by the `nextflow-to-galaxy` pipeline for nf-core/demo imported and ran fine on usegalaxy.be. Saving it in the workflow editor failed:

```
Saving workflow failed...
Error: Input should be a valid number in ('frame', 'position', 0)
       Input should be a valid number in ('frame', 'position', 1)
```

The template step (`nextflow-summary-to-galaxy-template`) writes `comments:` frames with fixed `position`/`size` but no position for any input or step. Galaxy places position-less steps in a pile at the top left, so the frames no longer contain the steps they claim (`child_steps`). An empty frame then sets off a Galaxy editor bug that turns its position into `null` on save.

## How the error is caused

1. **Foundry output.** The gxformat2 workflow has two frames, "Read QC and trimming" at `[0, 0]` (620×420) and "Reporting" at `[660, 0]` (420×320). No step or input has a `position`.
2. **Import.** Galaxy assigns placeholder positions 10 px apart: `(0,0)`, `(10,10)`, …, `(60,60)`. MultiQC, the only step of the "Reporting" frame, lands at `(60,60)`, far outside the frame at x = 660. The frame encloses nothing.
3. **Galaxy editor.** On `release_26.1`, `FrameComment.vue` `onFitToContent` builds an `AxisAlignedBoundingBox`, whose default corner is `x = y = Infinity` (`client/src/utils/geometry.ts`). It is only replaced when a step or comment lies inside the frame. For an empty frame, the editor emits `move([Infinity, Infinity])`.
4. **Save.** `JSON.stringify(Infinity)` gives `null`, and the server's comment model rejects it: "Input should be a valid number in ('frame', 'position', 0/1)".

## Evidence

- **Error:** observed in the usegalaxy.be editor (Galaxy 26.1.2.dev0) when saving the imported workflow "nf-core/demo (Galaxy translation, no cowpy)".
- **Stored workflow is valid:** `GET /api/workflows/<id>/download?style=editor` returns numeric frame positions `[0.0, 0.0]` and `[660.0, 0.0]`, and step positions `{left: 0..60, top: 0..60}` in 10 px increments. The invalid value is therefore created client-side, after load.
- **Mismatch:** in the stored workflow, the "Reporting" frame spans x 660–1080, but its child step MultiQC is at (60,60).
- **Code (release_26.1):** `client/src/utils/geometry.ts` initialises `AxisAlignedBoundingBox` with `x = Infinity; y = Infinity`. `client/src/components/Workflow/Editor/Comments/FrameComment.vue` `onFitToContent` emits `move([targetAABB.x, targetAABB.y])` even when nothing was fitted.
- **Control:** a v2 of the same workflow with explicit step positions and frames sized around their steps imported with every step inside its frame (API check). The editor saved it without error, and the workflow reran 14/14 jobs OK on usegalaxy.be with outputs identical to the Nextflow run.
- **Validators didn't catch it:** `gxwf validate --strict`, `draft-validate` and `planemo workflow_lint` all accept frames whose `child_steps` lie outside their rectangle, and steps without positions.
- Not confirmed: the exact editor action before saving. Fit-to-content is the code path that produces `Infinity`.

## Solution applied in this run

Every input and step got an explicit `position`, laid out in columns: inputs, then flatten → FastQC/seqtk, then MultiQC. Each frame's `position`/`size` was set to enclose its `child_steps`:

```yaml
steps:
  fastqc:
    position: {left: 520, top: 0}
  ...
comments:
- type: frame
  title: Read QC and trimming
  contains_steps: [flatten_reads, fastqc, seqtk_trim]
  position: [220, -40]
  size: [560, 520]
- type: frame
  title: Reporting
  contains_steps: [multiqc]
  position: [820, -40]
  size: [300, 520]
```

The workflow was re-converted to `.ga` (`gxwf-to-native`), passed `planemo workflow_lint`, was imported to usegalaxy.be as "… v2 - fixed layout" and was re-run with the nf-core test data.

## Reasoning

- A frame is a box drawn around steps. Its coordinates only make sense relative to the steps' coordinates. Emitting one without the other guarantees a mismatch after import.
- Galaxy's placeholder layout for position-less steps is not meant as a real layout, so frames can never line up with it.
- Galaxy should not write `null` for an empty frame (forward upstream). The Foundry can avoid the trigger completely by never producing an empty or misaligned frame.

## What would help the Foundry (proposed changes)

1. **`nextflow-summary-to-galaxy-template` (and the other template Molds):** when emitting `comments:` frames, also emit a `position` for every input and step, and derive each frame's `position`/`size` from the steps it contains (bounding box plus padding). If no layout is produced, emit no frames.
2. **Static gate:** in the template and per-step loop validation (or `gxwf validate --strict`), fail when a frame's `child_steps` lie outside its rectangle, or when frames exist but steps have no positions.
3. **`galaxy-workflow-comments` note:** state that frame geometry must match step positions, and that `position`/`size` are required (related: #580).
4. **Upstream (Galaxy, for forwarding):** `onFitToContent` should leave the frame unchanged when its bounding box is empty, and the editor should reject or clamp non-finite comment coordinates before saving.

## Environment

- Galaxy: usegalaxy.be 26.1.2.dev0 (error); local Galaxy master `7c18ab768ac` (tests).
- Planemo 0.75.48; Foundry main `94ce4ea2` (2026-11-09).
- Template Mold `nextflow-summary-to-galaxy-template` rev 10, sha256 `77f885d640900cca7dac4a3bbb33308d4d8065e871c919c672487db61caf93ab`.
- Feedback ledger entries: `template-frames-without-step-positions`, `galaxy-editor-frame-fit-empty-bounds-infinity`.
