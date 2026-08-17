---
title: "R and Tidyverse Fundamentals"
category: "Foundations & Prerequisites"
date: "2026-08-15"
image: "images/r-tidyverse-bioinformatics-workstation.webp"
excerpt: "Learn R vectors, data frames, factors, plots, and tidy data operations for biological analysis."
author: "Nasir Mahmood Abbasi, PhD"
---

<div class="mb-10 text-xl text-gray-600 leading-relaxed">
  <p>R is widely used for statistical analysis and visualization in bioinformatics. This lesson focuses on the data-frame operations and plots that learners will use later with RNA-seq and single-cell data.</p>
</div>

## Learning Objectives & Prerequisites

**By the end of this lesson, you should be able to:**

- Create vectors, data frames, and factors.
- Filter, transform, group, and summarize tabular data with tidyverse.
- Build a clear QC plot and save it reproducibly.
- Distinguish missing values from zero measurements.

**Prerequisites:**

- Install R and RStudio or use an R terminal.
- Complete [Biological Data Formats](biological-data-formats.html).


### Expected Output

By the end of this lesson, you should have: **A small reproducible R script that imports a tidy biological table, performs one documented transformation, and saves a labeled table or plot.**

## 1. Objects and data frames

R stores columns as vectors. A data frame should have meaningful column names and explicit types.

```r
samples <- data.frame(
  sample_id = c("S01", "S02", "S03"),
  condition = factor(c("control", "treated", "treated")),
  reads = c(1200000, 1450000, 1310000)
)
str(samples)
```

## 2. Tidy transformations

The tidyverse makes transformations readable. Always inspect the result after filtering or joining.

```r
install.packages(c("tidyverse", "here"))
library(tidyverse)
samples |>
  mutate(millions = reads / 1e6) |>
  group_by(condition) |>
  summarise(mean_reads = mean(millions), .groups = "drop")
```

## 3. Visualize a QC metric

Plots should show units, labels, and the biological grouping used in the analysis.

```r
ggplot(samples, aes(condition, millions, color = condition)) +
  geom_point(size = 3) +
  labs(x = "Condition", y = "Reads (millions)") +
  theme_minimal()
ggsave("results/read_qc.png", width = 6, height = 4, dpi = 150)
```

## 4. Missing values and joins

Use `is.na()` to identify missing data and verify identifiers before joining metadata to measurements. A silent many-to-many join can duplicate observations.

```r
samples |> summarise(across(everything(), ~sum(is.na(.x))))
stopifnot(!anyDuplicated(samples$sample_id))
```

## Practical Exercise

Create a table with sample ID, condition, and one QC metric. Produce one labeled plot, save it to `results/`, and write one sentence interpreting the pattern without overstating it.

**Pass criteria:** The table has correct types, the plot has units and labels, and the learner can explain how missing values and duplicate IDs would affect analysis.

## Troubleshooting

If a package will not install, record the R version and use a project library. If a plot is empty, inspect factor levels and missing values before changing the code.

## Knowledge Check & Assessment

### 1. Concept Verification

Write short answers explaining the main concepts, the assumptions behind them, and one way a careless workflow could produce a misleading result.

### 2. Practical Execution

Complete the practical exercise above and save the command, script, table, or figure in the project structure. **Pass Criteria:** The table has correct types, the plot has units and labels, and the learner can explain how missing values and duplicate IDs would affect analysis.

### 3. Troubleshooting

Explain what you would inspect first if the output were empty, malformed, unexpectedly large, or failed because of a missing file, package, permission, memory, or metadata problem.

## Next Steps

Continue with [Statistics for Bioinformatics](statistics-for-bioinformatics.html) and [Data Visualization Fundamentals](data-visualization-fundamentals.html). Record the software versions, dataset or example inputs, and any decisions you made.
