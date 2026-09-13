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
 sha256sum results/figures/qc.webp
```


## 5. Reporting Standards in Bioinformatics

Different analysis types have community-agreed reporting standards. Following these ensures your work is reviewable and reproducible.

| Analysis Type | Reporting Guideline | Key Requirements |
|---|---|---|
| RNA-seq differential expression | MINSEQE / ENCODE | Raw data in GEO/SRA, normalization method, statistical test, FDR threshold |
| Variant calling | GA4GH / ACMG | Reference genome, caller + version, filter criteria, pathogenicity evidence |
| Metagenomics | MIMARKS / MIxS | Sample metadata, sequencing platform, database version, classification method |
| Single-cell RNA-seq | scRNA-tools reporting | Cell count, QC thresholds, clustering resolution, marker genes |
| Machine learning | TRIPOD / PROBAST | Training/test split, performance metrics, cross-validation strategy |

## 6. Writing a Methods Section

A complete Methods section should allow another researcher to reproduce your analysis from raw data to final figures. Include:

```markdown
## Methods

### Data acquisition
RNA-seq reads for 12 tumor/normal pairs were obtained from GEO (GSE123456).
Raw FASTQ files were validated with FastQC v0.12.1 and trimmed with
Trim Galore v0.6.10 (--quality 20 --length 36).

### Alignment and quantification
Reads were aligned to GRCh38 (GENCODE v46) using STAR v2.7.11b
(--outSAMtype BAM SortedByCoordinate). Gene-level counts were obtained
with featureCounts v2.0.6 (-t exon -g gene_id -s 2).

### Differential expression
DESeq2 v1.42.0 was used with default shrinkage (apeglm). Genes with
adjusted p-value < 0.05 and |log2FC| > 1 were considered significant.

### Software environment
All analyses were run on Ubuntu 22.04 with R 4.4.1 and Python 3.11.
A complete conda environment specification is available in the repository.
```

## 7. Figure and Table Best Practices

Figures and tables are often the first (and sometimes only) elements reviewers examine. Follow these principles:

- **Self-contained:** Every figure should be interpretable without reading the full text.
- **Labeled axes:** Include units, sample sizes, and statistical annotations.
- **Color-blind friendly:** Use colorblind-safe palettes (e.g., viridis, ColorBrewer).
- **Resolution:** Minimum 300 DPI for publication; vector formats (PDF, SVG) preferred.

```r
# Example: a publication-quality volcano plot
library(ggplot2)
ggplot(deg_results, aes(x = log2FoldChange, y = -log10(padj))) +
  geom_point(aes(color = significant), size = 1, alpha = 0.6) +
  scale_color_manual(values = c("grey70", "#E41A1C")) +
  labs(
    x = expression(log[2]~"Fold Change"),
    y = expression(-log[10]~"Adjusted p-value"),
    title = "Differential Expression: Tumor vs. Normal",
    subtitle = paste(sum(deg_results$significant), "significant genes (FDR < 0.05, |log2FC| > 1)")
  ) +
  theme_minimal(base_size = 14) +
  geom_hline(yintercept = -log10(0.05), linetype = "dashed", color = "blue")
```

## 8. Common Reporting Errors to Avoid

| Error | Why It's Problematic | Correction |
|---|---|---|
| Reporting p-values without multiple testing correction | Inflates false positive rate | Always report adjusted p-values (FDR, Bonferroni) |
| Showing bar plots for continuous distributions | Hides data distribution and outliers | Use box plots, violin plots, or dot plots |
| Omitting sample sizes | Readers cannot assess statistical power | State n per group in every figure legend |
| Cherry-picking genes for validation | Confirmation bias | Report all tested genes with effect sizes and confidence intervals |
| Using "significant" without defining the threshold | Ambiguous and non-reproducible | State the exact threshold: "FDR < 0.05 and |log2FC| > 1" |

## 9. Interpretation vs. Over-interpretation

The most common scientific writing error is stating conclusions that exceed the evidence. Follow this hierarchy:

1. **Observation:** "Gene X shows a 3.2-fold increase in expression (FDR = 0.001) in tumor samples."
2. **Interpretation:** "This is consistent with the known role of Gene X in cell proliferation pathways."
3. **Over-interpretation (avoid):** "Gene X causes tumor growth." ← Requires functional validation, not just differential expression.


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
