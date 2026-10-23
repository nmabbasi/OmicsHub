# A useful tutorial earns the learner's next step

Before adding a page, answer: **What can this reader do or decide afterward that they could not do before?** Improve an existing lesson when it already serves that outcome. More pages, longer prose, tool lists and screenshots are not substitutes for teaching.

## Start with the reader and one outcome

State the audience, what they should already know, and whether the page is a hands-on lab, conceptual guide, advanced template or reference. Link the relevant prerequisite. Distinguish required preparation from optional depth, accounts, HPC access and paid tools. Do not require both R and Python unless the exercise genuinely uses both.

## Match the evidence to the format

- **Hands-on lab:** provide accessible public or invented inputs, a bounded route, environment requirements, an inspectable result, a deliberate failure or troubleshooting case, and a small variation with feedback. Test the code displayed on the page, not an unlinked replacement.
- **Conceptual guide:** teach a specific decision through a worked scenario, a contrasting case, and an explained answer. Runnable code is not mandatory.
- **Advanced template:** make required objects, identifiers, data scale, independent samples, adaptation points and outputs explicit. Clearly identify what was not executed. A complete-looking script is not proof that the reader's inputs meet its assumptions.
- **Reference:** organize for lookup, demonstrate common traps and show the limits of each check. Do not turn a reference into an invented end-to-end pipeline.

## Make the learner think, inspect and explain

Use a short loop: question → prediction → bounded task → observed result → explanation → small variation. Give worked feedback or an answer rubric. Explain what would count as failure and why. Reuse suitable public teaching inputs across related lessons instead of resetting the environment at every step.

## Protect the scientific question

Preserve sample and cell identifiers, original grouping labels and data provenance. Make expression layers, count scales, reference builds and filter status explicit. A plot-preparation fallback must not silently change the groups used for inference. More cells do not replace independent biological samples. A successful command, stable checksum, plausible plot or model score does not establish biological validity.

## Report the tested boundary honestly

Record exact versions and the operation actually exercised. Separate full workflow execution from a tiny fixture, syntax check, mocked failure path or source review. State untested platforms and steps. Do not imply that a package lock guarantees identical results on every machine. Do not describe synthetic records or saved model outputs as biological observations.

Use only authorized public or invented teaching inputs. Record their origin and license/usage terms where applicable. Never publish private research datasets, saved private outputs, credentials, patient identifiers or confidential project paths.

## Finish with a sensible continuation

Use `tools/learning-paths.json` for prerequisite-aware choices. Explain why a next lesson fits, and return to the relevant Start Here branch when there is no universal next analysis. HPC and question-specific methods remain optional where their prerequisites are absent.

After editing the manifest, run:

```bash
python3 tools/generate_learning_paths.py
python3 tools/generate_learning_paths.py --check
python3 tests/validate_tutorials.py
python3 -m unittest discover -s tests -v
```

Tests with optional scientific executables can skip in a minimal environment. Record those skips; enable the documented integration prerequisites before claiming runtime verification. Inspect important pages at narrow and wide widths, check actual links, and update modification dates only for substantive content changes—not merely navigation propagation.

## Review before publication

Keep the pull request reviewable: summarize the learner outcome, changes, exact checks, and remaining limits. Do not merge or publish before owner approval. These standards support useful teaching; they are not a promise of advertising approval or measured learner retention.

Teaching approach: [The Carpentries lesson-development guidance](https://carpentries.org/lesson-development/). Tool behavior should be grounded in each project's primary documentation.
