---
title: "Data Visualization Fundamentals"
category: "Foundations & Prerequisites"
date: "2026-08-15"
image: "images/data-visualization-fundamentals.png"
excerpt: "Read QC plots, PCA, heatmaps, UMAPs, and volcano plots without overstating biological conclusions."
author: "Nasir Mahmood Abbasi, PhD"
---

<div class="mb-10 text-xl text-gray-600 leading-relaxed">
  <p>A plot is an argument about data. Good visualization reveals uncertainty, sample structure, and potential artifacts while preserving units and context. This lesson gives learners a practical checklist for reading and creating bioinformatics figures.</p>
</div>

## Learning Objectives & Prerequisites

**By the end of this lesson, you should be able to:**

- Select plots that match a question and data type.
- Read distributions, PCA, heatmaps, UMAPs, volcano plots, and coverage plots.
- Use labels, scales, palettes, and legends responsibly.
- Separate visual patterns from statistical and biological evidence.

**Prerequisites:**

- Basic R or Python plotting.
- Complete [Quality Control Fundamentals](quality-control-fundamentals.html).

## 1. Start with the question

Use a distribution to inspect spread, a scatter plot to compare measurements, PCA to summarize major variation, a heatmap to inspect patterns, and UMAP to visualize local neighborhoods. No plot proves a mechanism by itself.

```python
import seaborn as sns
import matplotlib.pyplot as plt

# Always label units and groups
sns.boxplot(data=df, x="batch", y="pct_mt", hue="condition", showfliers=False)
sns.stripplot(data=df, x="batch", y="pct_mt", hue="condition", dodge=True, color="black", alpha=0.55)
plt.xlabel("Batch")
plt.ylabel("Mitochondrial reads (%)")
plt.legend(title="Condition")
```
```r
library(ggplot2)

# Always label units and groups
ggplot(df, aes(x = batch, y = pct_mt, color = condition)) +
  geom_boxplot(outlier.shape = NA) + geom_jitter(width = .15) +
  labs(x="Batch", y="Mitochondrial reads (%)")
```

## 2. PCA and UMAP

PCA axes are linear summaries; UMAP is a neighborhood visualization whose geometry depends on parameters. Report preprocessing, dimensions, neighbors, metric, and random seed.

```python
sc.tl.pca(adata, n_comps=30, random_state=7)
sc.pp.neighbors(adata, n_neighbors=15, n_pcs=20, random_state=7)
sc.tl.umap(adata, random_state=7)
```

## 3. Heatmaps and volcano plots

Cluster and scale deliberately. A volcano plot combines effect size and significance; a small p-value alone is not a large or meaningful biological effect.

```text
Figure checklist: title, units, n, group definition, preprocessing, color meaning, and scale.
```

## 4. Honest visual interpretation

Use colorblind-safe palettes, avoid truncated axes when they mislead, show individual points when possible, and state limitations in the caption.

```text
Caption template: Dataset; preprocessing; n; statistic; software/version; interpretation; limitation.
```

## Practical Exercise

Create one QC plot and one between-group plot using a small table. Add a caption that states n, units, preprocessing, and one limitation.

**Pass criteria:** A reader can understand the axes, groups, sample count, and what the figure does not prove.

## Troubleshooting

If colors are indistinguishable, use a palette designed for color-vision accessibility and add shapes or labels rather than relying on color alone.

## Knowledge Check & Assessment

### 1. Concept Verification

Write short answers explaining the main concepts, the assumptions behind them, and one way a careless workflow could produce a misleading result.

### 2. Practical Execution

Complete the practical exercise above and save the command, script, table, or figure in the project structure. **Pass Criteria:** A reader can understand the axes, groups, sample count, and what the figure does not prove.

### 3. Troubleshooting

Explain what you would inspect first if the output were empty, malformed, unexpectedly large, or failed because of a missing file, package, permission, memory, or metadata problem.

## Next Steps

Continue with [scRNA-seq Basics](scrna-seq-basics.html) and [Research Reporting and Interpretation](research-reporting-interpretation.html). Record the software versions, dataset or example inputs, and any decisions you made.
