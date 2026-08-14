---
title: "Advanced Single-Cell Visualization & QC"
date: "2026-08-14"
author: "OmicsHub Team"
category: "Advanced Single-Cell Analysis"
excerpt: "Elevate your single-cell data from basic plots to publication-ready figures using advanced mathematical QC metrics (LISI, Silhouette) and cutting-edge visualization packages (SCpubr, plot1cell)."
image: "images/single-cell-analysis.png"
---

# Advanced Single-Cell Visualization & Quality Control

## Introduction

Basic Seurat functions like `DimPlot` and `FeaturePlot` are excellent for exploratory data analysis. However, when preparing a manuscript for a high-impact journal, two things are strictly required:
1.  **Mathematical Validation:** You must mathematically prove that your integration worked and your clusters are distinct.
2.  **Publication-Ready Aesthetics:** Your figures must be visually flawless, high-resolution, and perfectly annotated.

This tutorial covers advanced Quality Control (QC) metrics (LISI, Silhouette Scores) and modern R packages designed specifically for generating premium visualizations (`SCpubr`, `plot1cell`).

---

## 1. Mathematical Quality Control

How do you prove to a reviewer that your batch integration (e.g., Harmony or CCA) actually worked? You cannot rely on "it looks mixed on the UMAP." You must measure it.

### Local Inverse Simpson's Index (LISI)
**LISI** is the gold standard for quantifying batch mixing. 
*   An **iLISI** (integration LISI) score close to the number of batches means perfect mixing.
*   A **cLISI** (cell-type LISI) score close to 1 means cell types remain perfectly separated.

```r
library(lisi)

# Extract PCA or Harmony embeddings and metadata
embeddings <- Embeddings(seurat_obj, reduction = "harmony")
meta_data <- seurat_obj@meta.data

# Compute LISI scores for batch (patient_id) and biology (cell_type)
lisi_res <- compute_lisi(embeddings, meta_data, c("patient_id", "cell_type"))

# A successful integration will have high patient_id LISI and low cell_type LISI
head(lisi_res)
```

### Silhouette Scores
To prove that your clusters are biologically distinct (and not just over-clustered artifacts), you use **Silhouette Scores**. A high score indicates a cell is well-matched to its own cluster and poorly matched to neighboring clusters.

```r
library(cluster)

# Calculate distance matrix on PCA embeddings
dist_matrix <- dist(Embeddings(seurat_obj, reduction = "pca"))

# Calculate Silhouette widths
sil <- silhouette(as.numeric(seurat_obj$seurat_clusters), dist_matrix)

# Visualize cluster robustness
plot(sil, border = NA, main = "Cluster Silhouette Plot")
```

---

## 2. Publication-Ready Visualization Packages

Once your data is mathematically validated, it is time to generate the figures. While `ggplot2` is powerful, customizing single-cell plots from scratch is incredibly time-consuming.

### SCpubr
**SCpubr** is an automated package designed specifically to generate highly customized, publication-ready Seurat plots instantly. It handles all the complex `ggplot2` theme configurations behind the scenes.

```r
library(SCpubr)

# Generate a premium UMAP with a clean legend and high contrast
SCpubr::do_DimPlot(sample = seurat_obj, 
                   group.by = "cell_type", 
                   label = TRUE, 
                   repel = TRUE, 
                   font.size = 14, 
                   legend.position = "right")

# Generate a premium FeaturePlot with a custom color gradient
SCpubr::do_FeaturePlot(sample = seurat_obj, 
                       features = "GeneA", 
                       colors.use = c("lightgrey", "darkred"))
```

### plot1cell
**plot1cell** is an advanced visualization library that goes beyond basic UMAPs, offering complex multi-omic and highly customized plotting capabilities. It is particularly useful for circular plots (Circos plots) mapping cell-to-cell communication or complex metadata overlays.

```r
library(plot1cell)

# plot1cell excels at visualizing complex cellular proportions and metadata distributions
# Example: Generate a robust cellular composition bar plot across patients
plot_cell_fractions(seurat_obj, 
                    groupby = "patient_id", 
                    celltype = "cell_type")
```

## Conclusion

By incorporating **LISI** and **Silhouette** scores into your pipeline, you bulletproof your analysis against peer-review criticism. By switching your final outputs to **SCpubr** and **plot1cell**, you ensure your figures meet the rigorous aesthetic standards of top-tier journals.
