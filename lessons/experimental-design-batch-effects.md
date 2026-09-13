---
title: "Experimental Design and Batch Effects"
category: "Foundations & Prerequisites"
date: "2026-08-15"
image: "images/experimental-design-batch-effects-workstation.webp"
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


## 5. Experimental Design Principles

Good experimental design prevents confounding before data generation. The key principles are:

| Principle | Definition | Example |
|---|---|---|
| **Randomization** | Assign samples to groups randomly | Randomly assign mice to treatment cages |
| **Replication** | Include biological replicates (not technical) | ≥3 biological replicates per condition |
| **Blocking** | Group known sources of variation | Process all conditions on the same sequencing lane |
| **Balancing** | Equal sample sizes across groups | Same number of samples per condition per batch |

```text
# GOOD: Balanced design – each batch processes both conditions
Batch 1: Control_1, Control_2, Treated_1, Treated_2
Batch 2: Control_3, Control_4, Treated_3, Treated_4

# BAD: Confounded design – batch = condition
Batch 1: Control_1, Control_2, Control_3, Control_4
Batch 2: Treated_1, Treated_2, Treated_3, Treated_4
```

**Why the bad design fails:** Any difference between groups could be caused by the biological condition OR by batch-specific technical variation (different reagent lots, different operators, different sequencing lanes). These effects are mathematically inseparable.

## 6. Identifying Batch Effects

Before correction, you must first detect whether batch effects exist. Use dimensionality reduction (PCA) to visualize sample clustering:

```r
library(DESeq2)

# Perform variance-stabilizing transformation
vsd <- vst(dds, blind = TRUE)

# PCA plot colored by condition, shaped by batch
plotPCA(vsd, intgroup = c("condition", "batch")) +
  labs(title = "PCA: Check for Batch Effects") +
  theme_minimal()
```

**Interpretation guide:**
- If samples cluster primarily by **condition** → minimal batch effect, proceed.
- If samples cluster primarily by **batch** → strong batch effect, correction needed.
- If batch and condition are **confounded** → correction is impossible; redesign the experiment.

## 7. Batch Correction Methods

| Method | Package | When to Use | Limitation |
|---|---|---|---|
| **Include batch as covariate** | DESeq2, limma | Batch is known, not confounded with condition | Requires balanced design |
| **ComBat** | sva | Remove batch effects from normalized data | Can over-correct if groups are unbalanced |
| **Harmony** | harmony | Single-cell integration across batches | May merge genuine biological differences |
| **limma::removeBatchEffect** | limma | Visualization only (corrected values for PCA/heatmaps) | Do NOT use corrected values for DE testing |

```r
# Correct approach: include batch in the DESeq2 model
design(dds) <- ~ batch + condition

# The condition effect is estimated AFTER accounting for batch
dds <- DESeq(dds)
results <- results(dds, contrast = c("condition", "treated", "control"))
```

**Critical warning:** Never use batch-corrected expression values as input for differential expression testing. Instead, include batch as a covariate in the statistical model. Using corrected values can deflate variance estimates and inflate false positive rates.

## 8. Sample Size and Power Considerations

Underpowered experiments waste resources and produce unreliable results. Use power analysis before designing your experiment:

```r
# RNA-seq power analysis (rough estimate)
library(RNASeqPower)
rnapower(
  depth = 20,        # millions of reads per sample
  cv = 0.4,          # biological coefficient of variation
  effect = 1.5,      # minimum fold change to detect
  alpha = 0.05,      # significance level
  power = 0.8        # desired power
)
# Output: n = 5 samples per group needed
```

| Biological CV | Typical System | Recommended Replicates |
|---|---|---|
| 0.1 – 0.2 | Cell lines | 3 per group |
| 0.3 – 0.4 | Inbred mice | 4–6 per group |
| 0.5 – 1.0 | Human clinical | 8–15+ per group |


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
