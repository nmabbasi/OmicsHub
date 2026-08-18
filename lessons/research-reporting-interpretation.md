---
title: "Research Reporting and Interpretation"
category: "Foundations & Prerequisites"
date: "2026-08-15"
image: "images/research-reporting-interpretation-workstation.webp"
excerpt: "Write reproducible methods, figure legends, limitations, and evidence-based biological interpretations."
author: "Nasir Mahmood Abbasi, PhD"
---

<div class="mb-10 text-xl text-gray-600 leading-relaxed">
  <p>A successful analysis is not complete when a command finishes. It is complete when another researcher can understand what was done, reproduce the result, and distinguish evidence from speculation.</p>
</div>

## Learning Objectives & Prerequisites

**By the end of this lesson, you should be able to:**

- Write a methods paragraph with data, software, versions, parameters, and references.
- Create an informative figure legend.
- Separate observation, interpretation, and limitation.
- Preserve provenance and report negative or ambiguous results honestly.

**Prerequisites:**

- Complete [Data Visualization Fundamentals](data-visualization-fundamentals.html).
- Have one small analysis result or QC plot to describe.


### Expected Output

By the end of this lesson, you should have: **A concise analysis report that states the question, data provenance, methods and versions, results, limitations, and the distinction between observation and conclusion.**

## 1. Methods as a reproducibility record

State data source and access date, sample design, preprocessing, software versions, parameters, reference versions, statistical model, and where scripts are available. Avoid vague phrases such as “standard pipeline.”

```text
Data: public dataset accession and download date
Reference: assembly and annotation release
Software: package versions
Parameters: thresholds, dimensions, seeds
Statistics: model, contrast, correction
```

## 2. Figure legends

A legend should define the dataset, groups, visual encodings, preprocessing, statistic, sample count, and abbreviation. It should not make a claim that the figure cannot support.

```text
Figure 1. Mitochondrial QC by condition. Each point is a cell; boxes show median and IQR. Cells were filtered at the pre-specified threshold. n is shown in the panel.
```

## 3. Observation versus interpretation

Observation describes what is visible or measured. Interpretation proposes why it may matter. Limitation states what alternative explanations remain.

```text
Observation: treated samples have higher median expression.
Interpretation: treatment may alter the pathway.
Limitation: donors and batch are not fully balanced.
```

## 4. Shareable provenance

Publish scripts, environment files, checksums, README, and a license where permitted. Do not publish identifiable human data or credentials.

```bash
 git status
 git log --oneline -1
 sha256sum results/figures/qc.png
```

## Practical Exercise

Write a 150-word methods paragraph and figure legend for one plot. Mark each sentence as method, observation, interpretation, or limitation.

**Pass criteria:** The report includes enough detail to reproduce the plot and does not confuse association with causation or statistical significance with biological importance.

## Troubleshooting

If the result is ambiguous, report the ambiguity. Do not change thresholds or omit samples solely to obtain a preferred conclusion.

## Knowledge Check & Assessment

### 1. Concept Verification

Write short answers explaining the main concepts, the assumptions behind them, and one way a careless workflow could produce a misleading result.

### 2. Practical Execution

Complete the practical exercise above and save the command, script, table, or figure in the project structure. **Pass Criteria:** The report includes enough detail to reproduce the plot and does not confuse association with causation or statistical significance with biological importance.

### 3. Troubleshooting

Explain what you would inspect first if the output were empty, malformed, unexpectedly large, or failed because of a missing file, package, permission, memory, or metadata problem.

## Next Steps

Continue with [Introduction to Bioinformatics](introduction-to-bioinformatics.html) and [Experimental Design and Batch Effects](experimental-design-batch-effects.html). Record the software versions, dataset or example inputs, and any decisions you made.
