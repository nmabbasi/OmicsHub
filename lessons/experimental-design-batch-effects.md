---
title: "Experimental Design and Batch Effects"
category: "Foundations & Prerequisites"
date: "2026-08-15"
image: "images/experimental-design-batch-effects.png"
excerpt: "Plan biological replicates, record covariates, recognize confounding, and reduce batch effects before sequencing."
author: "Nasir Mahmood Abbasi, PhD"
---

<div class="mb-10 text-xl text-gray-600 leading-relaxed">
  <p>Many bioinformatics problems are created before the first command is run. A balanced design, enough biological replicates, and complete metadata protect the analysis from confounding and make downstream models interpretable.</p>
</div>

## Learning Objectives & Prerequisites

**By the end of this lesson, you should be able to:**

- Define experimental units, biological replicates, technical replicates, and batches.
- Recognize confounding and avoid designs where condition equals batch.
- Create a metadata table suitable for modeling.
- Plan randomization, blocking, and QC before analyzing outcomes.

**Prerequisites:**

- Complete [Statistics for Bioinformatics](statistics-for-bioinformatics.html).
- Understand that batch correction cannot reliably recover information absent from the design.


### Expected Output

By the end of this lesson, you should have: **A design table that defines the biological question, experimental unit, covariates, replicates, randomization or blocking plan, and possible batch effects.**

## 1. Experimental units

The experimental unit is the entity independently assigned to a condition, such as a donor, animal, or culture. Cells from one donor are not automatically independent biological replicates.

```text
donor,condition,batch,library_id
D01,control,1,L01
D02,control,2,L02
D03,treated,1,L03
D04,treated,2,L04
```

## 2. Confounding

If every control is processed in batch 1 and every treated sample in batch 2, condition and batch are indistinguishable. No algorithm can prove which caused a difference. Balance batches when possible.

```text
Good: each batch contains control and treated samples.
Risky: batch 1 contains only controls and batch 2 only treated samples.
```

## 3. Metadata validation

Treat metadata as data. Check unique IDs, missing values, valid factor levels, and agreement with filenames before running a pipeline.

```python
import pandas as pd
meta = pd.read_csv("metadata.csv")
assert meta.sample_id.is_unique
assert meta.condition.notna().all()
print(pd.crosstab(meta.batch, meta.condition))
```
```r
meta <- read.csv("metadata.csv", stringsAsFactors = FALSE)
stopifnot(!anyDuplicated(meta$sample_id))
stopifnot(all(!is.na(meta$condition)))
with(meta, table(batch, condition))
```

## 4. Analysis consequences

Include pre-specified covariates in the design, document exclusions, and distinguish biological correction from technical removal. Over-correction can erase real biology.

```text
Design formula example: ~ batch + condition
Only use it when the design contains enough information to estimate both terms.
```

## Practical Exercise

Create a balanced two-condition metadata table with at least four biological replicates across two batches. Use a crosstab to prove each batch contains both conditions.

**Pass criteria:** IDs are unique, no required metadata is missing, both conditions occur in every batch, and the analysis design is written before inspecting results.

## Troubleshooting

If condition and batch are perfectly confounded, report the limitation and avoid claiming a batch-corrected causal result.

## Knowledge Check & Assessment

### 1. Concept Verification

Write short answers explaining the main concepts, the assumptions behind them, and one way a careless workflow could produce a misleading result.

### 2. Practical Execution

Complete the practical exercise above and save the command, script, table, or figure in the project structure. **Pass Criteria:** IDs are unique, no required metadata is missing, both conditions occur in every batch, and the analysis design is written before inspecting results.

### 3. Troubleshooting

Explain what you would inspect first if the output were empty, malformed, unexpectedly large, or failed because of a missing file, package, permission, memory, or metadata problem.

## Next Steps

Continue with [Reference Genomes and Annotation Databases](reference-genomes-annotation.html) and [Reproducible Project Structure](reproducible-project-structure.html). Record the software versions, dataset or example inputs, and any decisions you made.
