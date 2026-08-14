---
title: "Pseudobulk DE Analysis"
date: "2026-08-14"
author: "OmicsHub Team"
category: "Single-Cell RNA-seq"
excerpt: "A comprehensive pipeline for performing differential gene expression (DGE) analysis using DESeq2 for bulk RNA-seq and adapting it for modern pseudobulk scRNA-seq approaches."
image: "images/bioinformatics-intro.png"
---

# Transcriptomics: Differential Gene Expression Analysis

## Introduction

Whether you are analyzing traditional Bulk RNA-seq or performing state-of-the-art Single-Cell RNA-seq, the ultimate goal is often the same: identifying which genes are significantly upregulated or downregulated between two conditions (e.g., Healthy vs. Disease, or Control vs. Treated). 

This is called **Differential Gene Expression (DGE)** analysis. This tutorial covers the gold-standard pipeline using **DESeq2** in R, which applies to both Bulk and Pseudobulk data.

---

## 1. Preparing the Count Matrix

Differential expression requires raw, un-normalized counts. Do not use TPM, FPKM, or normalized data for DESeq2, as the mathematical model specifically relies on the raw integer counts to estimate variance.

```r
library(DESeq2)
library(ggplot2)

# Load your count matrix (genes in rows, samples in columns)
counts_data <- read.csv("raw_counts.csv", row.names = 1)

# Load sample metadata
metadata <- read.csv("sample_metadata.csv", row.names = 1)

# Ensure the column names in counts match the row names in metadata exactly
all(colnames(counts_data) %in% rownames(metadata))
```

---

## 2. Running the DESeq2 Pipeline

DESeq2 normalizes the data (accounting for library size differences), estimates data dispersion, and fits a negative binomial generalized linear model to test for significance.

```r
# 1. Create the DESeq2 object
dds <- DESeqDataSetFromMatrix(countData = counts_data,
                              colData = metadata,
                              design = ~ condition) # 'condition' is a column in metadata

# 2. Filter out lowly expressed genes to improve statistical power
keep <- rowSums(counts(dds)) >= 10
dds <- dds[keep,]

# 3. Set the reference level (Control) so log2FoldChanges are calculated relative to it
dds$condition <- relevel(dds$condition, ref = "Control")

# 4. Run the core DESeq2 pipeline
dds <- DESeq(dds)
```

---

## 3. Extracting and Visualizing Results

Once the model is fit, we extract the results comparing the "Treated" group to the "Control" group.

```r
# Extract results
res <- results(dds, contrast=c("condition", "Treated", "Control"))

# Order by adjusted p-value
resOrdered <- res[order(res$padj),]

# View the top significant genes
head(resOrdered)
```

### Visualizing with a Volcano Plot

A Volcano Plot is the standard way to visualize DGE results, mapping statistical significance (-log10 p-value) against biological magnitude (log2FoldChange).

```r
# Convert results to a data frame
res_df <- as.data.frame(res)

# Create a basic Volcano Plot
ggplot(res_df, aes(x = log2FoldChange, y = -log10(padj))) +
  geom_point(aes(color = padj < 0.05 & abs(log2FoldChange) > 1), alpha=0.8) +
  scale_color_manual(values = c("grey", "red")) +
  theme_minimal() +
  labs(title = "Volcano Plot: Treated vs Control",
       x = "Log2 Fold Change",
       y = "-Log10 Adjusted P-value") +
  theme(legend.position = "none")
```

---

## 4. Modern Adaptation: Pseudobulk for Single-Cell Data

If you are working with single-cell RNA-seq data (scRNA-seq), performing DGE on individual cells is statistically flawed (it artificially inflates your sample size, creating massive false positives). 

The modern best practice is **Pseudobulking**: aggregating all cells of a specific cell type from the same biological replicate into a single "bulk" sample, and then running DE analysis.

There are two primary ways to do this:

### Option A: Manual Aggregation (Seurat)

```r
# Example using Seurat
library(Seurat)

# Aggregate counts per cell type per patient
pseudobulk_obj <- AggregateExpression(seurat_object, 
                                      group.by = c("cell_type", "patient_id", "condition"),
                                      return.seurat = TRUE)

# Extract the raw aggregated counts for a specific cell type (e.g., T-cells)
tcell_counts <- GetAssayData(subset(pseudobulk_obj, cell_type == "T_cell"), slot = "counts")

# You can now feed 'tcell_counts' directly into DESeqDataSetFromMatrix!
```

### Option B: The Libra Framework (Recommended)

To drastically simplify this workflow, the **Libra** R package (developed by the NeuroRestore group) provides a unified interface. Instead of manually extracting counts, building matrices, and managing metadata loops for every single cell type, `Libra` performs the aggregation and runs your preferred DE algorithm (edgeR, DESeq2, limma) across all cell types simultaneously in one line of code.

```r
library(Libra)

# Ensure your Seurat object has standard metadata columns:
# seurat_obj$cell_type (the clusters/identities)
# seurat_obj$replicate (patient/sample ID)
# seurat_obj$label (Condition: e.g., Treated vs Control)

# Run pseudobulk DE across all cell types automatically
de_results <- run_de(seurat_obj, 
                     de_family = "pseudobulk", 
                     de_method = "edgeR", # Can swap seamlessly to 'DESeq2' or 'limma'
                     de_type = "LRT")     # Likelihood ratio test

# View results for a specific cell type
head(de_results$T_cell)
```

By leveraging `Libra`, you ensure statistically rigorous, replicate-aware differential expression testing while completely avoiding the massive false-discovery rates of traditional cell-level tests.
