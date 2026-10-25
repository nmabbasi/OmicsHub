# A useful tutorial earns the learner's next step

Before adding a page, answer: **What can this reader do or decide afterward that they could not do before?** Improve an existing lesson when it already serves that outcome. More pages, longer prose, tool lists and screenshots are not substitutes for teaching.

## Start with the reader and one outcome

State the audience, what they should already know, and whether the page is a hands-on lab, conceptual guide, advanced template or reference. Link the relevant prerequisite. Distinguish required preparation from optional depth, accounts, HPC access and paid tools. Do not require both R and Python unless the exercise genuinely uses both.

## Keep general analysis teaching R-first

For general-purpose data analysis and visualization lessons, make R the primary worked path. Use R Markdown when a literate, reproducible report is part of the learner outcome. If a Python route teaches the same task, offer it as a clearly labelled alternate tab, with R physically first and selected by default. Preserve a reader's explicit language choice for the session, and let a code fragment reveal its own language without silently changing that preference.

Only pair examples when they perform the same function on comparable inputs, preserve the same scientific assumptions, and lead to interpretable equivalent outputs. Do not add a Python route merely for symmetry, or imply that a Python-only tool has an R equivalent. Keep language- or tool-specific instruction in its natural form, including Python fundamentals, AI and model tooling, command-line workflows, and APIs without a genuine counterpart.

When migrating a Python-led analysis lesson, first verify that the lesson is general analysis rather than tool training. Build and test the complete R route, including input checks, preprocessing, output and interpretation, before presenting Python as an alternate. Keep both source routes visible without JavaScript, fingerprint their reviewed ranges, and test tab order, the default, session preference, keyboard controls and fragment links. Migrate one lesson at a time; do not perform a sitewide language rewrite without validating each task and output.

## Make R Markdown the primary report-assembly workflow

When the learner outcome is a literate, reproducible analysis report, teach a runnable `.Rmd` workflow first. Quarto may be described as an optional alternative when a project or audience requires it; it does not replace the primary R Markdown lesson path. Keep the example bounded and avoid implying that report rendering itself validates the upstream biological analysis.

A public report example should include its `.Rmd` source, only the small public or invented input fixtures needed to run it, and any verified bibliography source. Declare the input schema and units, check required columns, identifiers, types and ranges, and stop with a useful error when assumptions fail. Explain the knit command, R and package requirements, Pandoc requirement, expected output locations and a small deliberate failure. Record the R, package, Pandoc and session versions actually used. A knit date is not a sample collection, data retrieval or experiment date. Version records aid diagnosis but do not guarantee a bitwise-identical environment.

Treat citations as evidence, not decoration. Cite the source of real data and the methods, software or publications actually used. Check author, title, year, version, DOI or URL against the cited source; do not fabricate references or leave template citations that do not support the claims. Clearly distinguish citations for report tooling from citations for scientific methods or data. Synthetic values have no scientific provenance and must never be presented or cited as observations.

Keep the public repository limited to source code, authorized public or invented teaching data, and specifically reviewed teaching figures. Do not publish knitted HTML, raw execution logs or tables, private execution outputs, research datasets, credentials, patient identifiers or confidential paths. When the owner requests analysis images, generate them by executing the linked source, declare the input provenance, label invented fixtures clearly, record the source and output fingerprints, and explain the actual execution boundary in the caption. Keep those additions unpublished until the owner approves them. A checksum verifies bytes, not privacy, provenance or biological validity.

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
