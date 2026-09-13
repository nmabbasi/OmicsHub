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
ggsave("results/read_qc.webp", width = 6, height = 4, dpi = 150)
```

## 4. Missing values and joins

Use `is.na()` to identify missing data and verify identifiers before joining metadata to measurements. A silent many-to-many join can duplicate observations.

```r
samples |> summarise(across(everything(), ~sum(is.na(.x))))
stopifnot(!anyDuplicated(samples$sample_id))
```


## 5. Reading and Writing Data

In bioinformatics, you will frequently import CSV, TSV, and Excel files. Use the `readr` package (part of tidyverse) for consistent parsing and explicit column type detection.

```r
# Read a tab-separated gene expression matrix
expr <- read_tsv("data/raw/gene_counts.tsv", show_col_types = TRUE)

# Inspect dimensions and first rows
dim(expr)
head(expr)

# Write results with consistent formatting
write_csv(expr, "data/processed/filtered_counts.csv")
```

**Common pitfall:** Excel silently converts gene names like `MARCH1` and `SEPT2` to dates. Always use plain-text formats (CSV/TSV) for bioinformatics data and verify gene name integrity after import.

## 6. Reshaping Data: Wide vs. Long Format

Many bioinformatics datasets arrive in wide format (one column per sample), but most R analysis and plotting functions expect long (tidy) format.

```r
# Wide format: each sample is a column
wide_data <- data.frame(
  gene = c("TP53", "BRCA1", "MYC"),
  sample_A = c(150, 320, 890),
  sample_B = c(175, 280, 920)
)

# Pivot to long format for ggplot and statistical testing
long_data <- wide_data |>
  pivot_longer(
    cols = starts_with("sample_"),
    names_to = "sample",
    values_to = "expression"
  )

# Now each row is one gene-sample measurement
print(long_data)
# Output:
# gene   sample    expression
# TP53   sample_A  150
# TP53   sample_B  175
# BRCA1  sample_A  320
# ...
```

## 7. Factors and Categorical Variables

Factors are essential for controlling group order in plots and statistical models. Always set factor levels explicitly rather than relying on alphabetical order.

```r
# Without explicit levels, R uses alphabetical order
samples$condition <- factor(samples$condition, levels = c("control", "treated"))

# This ensures "control" appears first in plots and is the reference level in models
levels(samples$condition)
# [1] "control" "treated"
```

**Why this matters:** In differential expression analysis, the reference level of a factor determines the direction of fold-change calculations. If "treated" is accidentally set as the reference, all log2FC values will be inverted.

## 8. Error Handling and Defensive Programming

Before running an analysis pipeline, validate your inputs programmatically:

```r
# Check that required columns exist
stopifnot(
  "sample_id" %in% colnames(samples),
  "condition" %in% colnames(samples),
  nrow(samples) > 0
)

# Check for unexpected NA values in critical columns
na_counts <- samples |> summarise(across(everything(), ~sum(is.na(.x))))
print(na_counts)

# Assert no duplicate sample IDs
if (anyDuplicated(samples$sample_id)) {
  stop("Duplicate sample IDs detected – check your metadata file.")
}
```

## 9. Reproducible R Sessions

Always record your R session information at the end of every analysis script. This captures the exact R version, loaded packages, and operating system.

```r
# At the end of your script
sink("logs/session_info.txt")
sessionInfo()
sink()

# Expected output includes:
# R version 4.4.1 (2024-06-14)
# Platform: x86_64-pc-linux-gnu
# attached packages: tidyverse 2.0.0, ggplot2 3.5.1, dplyr 1.1.4 ...
```

| Troubleshooting Issue | Likely Cause | Solution |
|---|---|---|
| `Error: package 'X' is not available` | R version too old for the package | Update R or use BiocManager for Bioconductor packages |
| Plot appears blank | Factor levels don't match data values | Check `levels()` and ensure data contains matching values |
| `Joining, by = ...` warning | Implicit join columns | Specify `by = "column_name"` explicitly |
| Gene names converted to dates | Excel auto-formatting | Re-import from original TSV; never open bioinformatics files in Excel |


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
