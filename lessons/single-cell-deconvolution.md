---
title: "Bulk RNA-seq Deconvolution using scRNA-seq"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Advanced Single-Cell Analysis"
excerpt: "Learn how to use high-resolution single-cell data as a reference to mathematically deconvolute the cell type proportions in massive bulk RNA-seq clinical cohorts."
image: "images/single-cell-analysis.png"
---

# Cell Type Deconvolution: Bridging Bulk and Single-Cell

## Introduction

Single-cell RNA-seq provides incredible resolution into cell states, but it is expensive and difficult to scale to hundreds or thousands of patients. Bulk RNA-seq is cheap and highly scalable, but the output is a "smoothie"—the gene expression is an average of all the thousands of cells in the tissue chunk.

**Deconvolution** is the mathematical process of taking a high-quality single-cell dataset (the reference "ingredients list") and using it to estimate the exact proportions of each cell type present in a bulk RNA-seq dataset (the "smoothie").

---

## 1. The Principle of Deconvolution

If a bulk RNA-seq sample shows high expression of *CD8A* and *GZMB*, is it because there are many CD8+ T cells, or because a few CD8+ T cells are expressing those genes at astronomically high levels?

Deconvolution algorithms like **CIBERSORTx**, **MuSiC**, or **Cell2Location** solve this by building a "signature matrix" from your single-cell reference, mapping exactly how much of each gene a typical cell of type X produces.

---

## 2. Using MuSiC in R

**MuSiC** (Multi-subject Single Cell deconvolution) is a fantastic tool because it accounts for biological variance across different subjects in your single-cell reference, rather than just taking a flat average.

### Preparing the Data

```r
library(MuSiC)
library(ExpressionSet)

# 1. Prepare your Bulk Data
# 'bulk_counts' is a matrix of genes (rows) by bulk samples (columns)
bulk.eset <- ExpressionSet(assayData = as.matrix(bulk_counts))

# 2. Prepare your Single-Cell Reference
# 'sc_counts' is the raw count matrix, 'sc_meta' has the cell types and patient IDs
sc.eset <- ExpressionSet(assayData = as.matrix(sc_counts), 
                         phenoData = AnnotatedDataFrame(sc_meta))
```

### Running the Deconvolution

```r
# Estimate the cell type proportions in the bulk data
music_results <- music_prop(bulk.mtx = exprs(bulk.eset), 
                            sc.eset = sc.eset, 
                            clusters = 'cell_type', # The column in sc_meta with annotations
                            samples = 'patient_id') # The column indicating biological replicates
```

---

## 3. Visualizing the Results

The output of MuSiC is a matrix showing the estimated percentage of each cell type in every bulk sample. We can easily visualize this using standard `ggplot2` stacked bar charts.

```r
library(ggplot2)
library(reshape2)

# Extract the estimated proportions
estimated_props <- music_results$Est.prop.weighted

# Melt the data for ggplot
plot_data <- melt(estimated_props)
colnames(plot_data) <- c("Bulk_Sample", "Cell_Type", "Proportion")

# Create a stacked bar plot of cell type proportions across clinical samples
ggplot(plot_data, aes(x = Bulk_Sample, y = Proportion, fill = Cell_Type)) +
  geom_bar(stat = "identity") +
  theme_minimal() +
  labs(title = "Deconvoluted Cell Type Proportions in Bulk Cohort",
       y = "Relative Proportion",
       x = "Patient Sample") +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
```

## Conclusion

Deconvolution is arguably the most powerful translational bioinformatics technique today. It allows you to take a 5-patient single-cell experiment, extract the signatures of a novel disease-driving cell state, and immediately scan for that state across historical 1,000-patient bulk RNA-seq clinical trials to test for survival outcomes.
