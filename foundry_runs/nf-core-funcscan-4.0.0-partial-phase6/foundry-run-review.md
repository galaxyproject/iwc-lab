# Foundry run review: nf-core/funcscan, partial (phases 1 to 6 of 13)

Written by Ivy Chen with help from an AI assistant (Claude). Numbers about the draft come from the run agent's own final status unless marked as checked by me.

## Summary

- I ran the `pipeline-nextflow-to-galaxy` pipeline on nf-core/funcscan as part of BioHackathon Europe 2026, project 31.
- The run completed phases 1 to 5 and phase 6. It stopped before phase 7 (the draft-step loop). Phases 7 to 13 were not run.
- Phase 6 produced a gxformat2 draft that passes `gxwf draft-validate` with no errors and no warnings (agent-reported).
- I stopped on purpose. The remaining phases are long, phases 11 and 12 need a Galaxy server and test account that I did not have, and I did not want to spend more resources on a run that could not finish.

## Setup

- Pipeline: `pipeline-nextflow-to-galaxy`, 13 phases.
- Tool: Claude Code, run through the e-infra gateway with open-weight models, so cost figures are estimates. Which model sits behind each gateway name (agentic, thinker, mini) is unconfirmed.
- Dates: phases 1 to 4 on 10 Nov, phase 5 on 11 Nov, phase 6 on 12 Nov 2026.
- I approved only read-only prompts and writes inside the run folder and a scratch folder.

## What each phase produced

- Phase 1, summarize-nextflow: `summary-nextflow.json` (55 processes, 220 parameters).
- Phase 2, reference data: `nextflow-galaxy-reference-data.md`.
- Phase 3, interface: `nextflow-galaxy-interface.md` (61 inputs). Not amended, still under operator review.
- Phase 4, data flow: `nextflow-galaxy-data-flow.md`.
- Phase 5, compare against an IWC exemplar: `iwc-comparison-notes.md` and `iwc-exemplar.gxwf.yml`.
- Phase 6, template: `galaxy-workflow-draft.gxwf.yml` (agent-reported):
  - 62 inputs and 14 promoted outputs.
  - 95 outer steps (84 Deferred, 9 Identity-pinned, 2 draft subworkflows) and 38 inner steps.
  - 94 gated steps, 232 edges, 10 stage frames.
  - 505 TODOs and 0 Resolved.
  - `gxwf draft-validate`: exit 0, 0 structure, 0 topology, 0 semantic errors, 0 warnings.
  - `draft-next-step` walks the draft and the nested subworkflow steps are visible to phase 7.

## Human review

I reviewed phases 2 to 5 as a Galaxy user. In phases 2, 4 and 5 I read only the sections that bear on decisions (phase 2 sections 3, 4.2 and 5, phase 4 sections 17 to 19, phase 5 sections 3.5 and 7). I did not review phase 1, which is machine-made JSON, or the phase 6 draft line by line.

### Phase 2, reference-data brief

- Section 3 (Galaxy posture): the v1 default has every database supplied or rebuilt by the user. funcscan has up to 11, and users should not have to upload databases. A data-table option, with upload as the fallback, would be friendlier where the server has the data.
- Sections 4.2 and 5 (inputs): the HMM model inputs for AMP and BGC screening are required when their option is on but are shown as optional, so a run can fail late. Database inputs for a switched-off stage are silently ignored. Group inputs by stage and say in each help text when the input is used.

### Phase 3, interface brief

- The sample sheet as four parallel lists is confusing. Sample names have to be aligned by hand, and nothing checks that protein and gbk files belong together.
- Users should not have to upload databases.
- Expose the Prokka kingdom, the antiSMASH taxon and the RGI aligner.
- Per-tool detailed outputs and per-sample folders are wanted.
- I wrote a one-page user review of the brief. The agent offered to amend phase 3 with four findings. I did not amend it, so the brief is unchanged.

### Phase 4, data-flow brief (section 17, interface deltas)

Items are numbered as in the brief.

- Item 1, `versions` output: drop it. Galaxy already records tool versions with each job.
- Item 2, `bgc_mincontiglength`: add it as a numeric input. It changes which samples are screened, so users should be able to set it.
- Item 3, antiSMASH database: users should not upload databases. This conflicts with the brief's recommendation of an uploaded `.tar.gz`.
- Item 4, RGI "my CARD is already processed" checkbox: most users cannot answer it. If the workflow supplies the databases, the question goes away.
- Item 5, `.gz` in the sample-sheet patterns: keep it. Users often have compressed files.
- Item 7, annotation tool: users should be told when the workflow switches prodigal to pyrodigal. A help-text warning is the minimum. The silent switch and the other lost warnings (section 8) are a user-experience risk.
- Item 6, `interproscan_table` bound to the wrong producer, is a bug fix with no user decision.

### Phase 5, comparison with the IWC exemplar (decisions)

- Output list: keep all 61 promoted outputs. This matches the per-tool detailed outputs I asked for in phase 3. The corpus median is 8 and the maximum is 81, so 61 is large but has precedent.
- MultiQC: I want the report to show screening results. In funcscan, the MultiQC report holds only versions, a parameter summary, a methods blurb and Prokka and Bakta stats, with nothing from the screening lanes. The corpus idiom is `tooldistillator`, then `tooldistillator_summarize`, then `multiqc` (7 of 133 workflows use Tooldistillator, 36 run MultiQC, 2 do both). This changes the promoted-output list and adds steps in each lane, so it is a design cost that the next phases would need to plan for.
- Annotation tool override (`annotation-tool-override-belongs-on-the-form`): put it on the form, with help text that says what the override does, so users know when prodigal is switched to pyrodigal. The corpus pays two steps per inverted gate for this, which is cheaper than repeating the test on every step.

I did not send these notes to the agent. They are for the Foundry team to add to the feedback ledger.

## What worked

- Phases 1 to 5 each produced a usable brief that the next phase built on.
- The draft validates and can be walked by `draft-next-step`.
- The open-requirements ledger grew in a useful way: 23 discoveries, 36 entries, 23 decisions and 6 held items after phase 6 (agent-reported).

## What blocked or slowed the run

- Phase 6 stalled the first time. The emitter was one large script, and the agent kept rewriting it. The edits left duplicate code, code after a `return`, and an unclosed parenthesis. I stopped the repeated rewrites and asked for smaller files.
- The agent's first pass in phase 6 had errors that it found and recorded itself:
  - `amp_cluster_table` was promoted from the wrong producer.
  - A helper silently dropped the caller's note, so three summary picks lost their rationale.
  - It claimed the pattern pages are not packaged. That was wrong: two overview pages are packaged and name tools, but their operation pages are dead links, and one page is missing.
- Phases 11 and 12 need a Galaxy server and a test account. I did not have them.
- No per-run usage numbers were available to me, so I cannot report token use for this run.

## What I would change

- Tell the phase 6 agent to build the emitter in several small files and compile each before moving on. A single large file leads to repeated rewrites.
- Make the correction step and the ledger update one action, so a stopped run does not leave a wrong claim in the ledger.
- State at the start which phases need a Galaxy server, so an operator can decide early whether a full run is possible.
- Let the harness close a phase that I stop on purpose, so `foundry-run.yml` is not left saying "running".

## Not done

- Phases 7 to 13: the draft-step loop, test data, test plan, test implementation, validation, test run and debug.
- No phase 6 feedback entries have been appended to the feedback ledger yet. The phase 6 note lists 8 candidates.
- No GitHub issues were filed. I will file feedback issues only after review.

## Known problems in this folder

- `open-requirements.ledger.yml` still carries the wrong wording that the pattern pages are not packaged. The script that would correct it was stopped before it ran. The correction is recorded in `phase6-progress.md`, section 6.
- `foundry-run.yml` still marks phase 6 as running, with an empty artifacts list. That file belongs to the harness, so I left it as it was.

## Open decisions for the operator (me)

- Phase 5: decided, see the human review section above. The phase 6 draft was made before these decisions and promotes 14 outputs, so they are not applied to it yet.
- Phase 3: the interface brief is unamended. My findings are in the human review section.

## Feedback ledger

- `foundry-feedback.ledger.yml` has 21 entries, from phases 1 to 5.

## Files

- `summary-nextflow.json`: phase 1 source summary.
- `nextflow-galaxy-reference-data.md`: phase 2 brief.
- `nextflow-galaxy-interface.md`: phase 3 brief.
- `nextflow-galaxy-data-flow.md`: phase 4 brief.
- `iwc-comparison-notes.md`: phase 5 comparison with the nearest IWC exemplar.
- `iwc-exemplar.gxwf.yml`: phase 5 converted exemplar subgraph.
- `open-requirements.ledger.yml`: open requirements, re-emitted by phase 6.
- `galaxy-workflow-draft.gxwf.yml`: phase 6 draft.
- `phase6-progress.md`: phase 6 running note and final status.
- `foundry-run.yml`: run record.
- `foundry-feedback.ledger.yml`: feedback ledger.
