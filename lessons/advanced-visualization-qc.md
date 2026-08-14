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

### scplotter
**scplotter** provides an intuitive, high-level interface for creating complex, multi-layered visualizations that are difficult to build in raw ggplot2. It is especially powerful for Immune Repertoire (TCR/BCR) visualizations and feature-rich scatter plots.

```r
library(scplotter)

# Example: Generate a detailed scatter plot highlighting specific cellular subsets
sc_scatter(seurat_obj, 
           group.by = "cell_type", 
           split.by = "condition",
           palette = "Set1")
```

### dittoSeq
**dittoSeq** is a universal visualization package highly regarded for its color-blind friendly default palettes and its ability to rapidly generate cellular composition barplots and expression heatmaps.

```r
library(dittoSeq)

# Generate a color-blind friendly cellular composition barplot across samples
dittoBarPlot(seurat_obj, var = "cell_type", group.by = "patient_id")

# Generate a multi-annotation heatmap for top marker genes
dittoHeatmap(seurat_obj, genes = top_10_markers, annot.by = c("cell_type", "condition"))
```

### scCustomize
**scCustomize** is a collection of functions created to improve and extend the default Seurat visualizations. It is highly valued for automatically configuring intuitive color palettes, handling complex multi-gene overlays, and easily customizing axes and legends without raw ggplot2 code.

```r
library(scCustomize)

# Create a customized FeaturePlot with a continuous viridis color scale
FeaturePlot_scCustom(seurat_obj, features = "GeneA", colors_use = viridis::viridis(50))

# Create a clustered dot plot (hierarchically grouping both genes and cell types)
Clustered_DotPlot(seurat_obj, features = top_10_markers, group.by = "cell_type")
```

### SeuratExtend
**SeuratExtend** is an incredibly powerful toolkit that bridges the gap between basic Seurat analysis and advanced pathway/enrichment plotting. It excels at generating publication-ready heatmaps and GSEA enrichment plots directly from the Seurat object.

```r
library(SeuratExtend)

# Generate a complex Gene Set Enrichment Analysis (GSEA) waterfall plot directly
Plot_GSEA(seurat_obj, pathway = "HALLMARK_HYPOXIA", group.by = "condition")
```

### SCP (SingleCellPlot)
**SCP** provides a massive suite of high-level wrappers designed specifically for "multi-omics" and spatial transcriptomics visualization. If you need to generate highly complex, data-dense figures (like volcano plots embedded inside UMAPs or spatial gene expression maps), SCP is unmatched.

```r
library(SCP)

# Example: Generate a highly annotated, split violin plot for gene expression
CellStatPlot(seurat_obj, 
             stat.by = "cell_type", 
             group.by = "condition", 
             plot_type = "violin")
```

### Radar Plots (Pathway Visualization)
When you have multiple pathway enrichment scores (e.g., from GSEA or PROGENy) across different clusters, a standard bar chart is often insufficient. **Radar Plots** (or Spider Plots) allow you to compare the multidimensional signaling state of different cell types simultaneously.

```r
library(ggradar)
library(ggplot2)

# Assuming 'pathway_data' is a data frame of normalized pathway scores per cluster
ggradar(pathway_data,
        grid.min = 0, grid.mid = 0.5, grid.max = 1,
        group.line.width = 1, 
        group.point.size = 3) +
  theme(legend.position = "bottom") +
  labs(title = "Pathway Activity Radar Plot")
```

## Conclusion

By incorporating **LISI** and **Silhouette** scores into your pipeline, you bulletproof your analysis against peer-review criticism. By switching your final outputs to **SCpubr** and **plot1cell**, you ensure your figures meet the rigorous aesthetic standards of top-tier journals.
