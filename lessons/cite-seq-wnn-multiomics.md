---
title: "Multi-Omics: CITE-seq & WNN Integration"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Advanced Single-Cell Analysis"
excerpt: "Learn how to process and integrate CITE-seq data, bridging the gap between RNA expression and surface protein abundance using Weighted Nearest Neighbor (WNN) analysis."
image: "images/single-cell-analysis.png"
---

<div class="p-6 bg-blue-50 border border-blue-100 rounded-xl mb-8">
  <h4 class="text-lg font-bold text-blue-900 mb-2">Learning Objectives & Prerequisites</h4>
  <ul class="list-disc list-inside text-blue-800 space-y-1 mb-4">
    <li><strong>Prerequisites:</strong> Basic understanding of the Linux terminal and bioinformatics concepts. (See <a href="start-here.html" class="underline">Start Here</a>)</li>
    <li><strong>Objective:</strong> Master the core concepts and practical commands of this topic.</li>
    <li><strong>Expected Output:</strong> A reproducible workflow and a clear understanding of the methodology.</li>
  </ul>
</div>



# Multi-Omics: CITE-seq & WNN Integration

## Introduction

Traditional scRNA-seq only measures the transcriptome. However, many critical biological processes are driven by cell surface proteins (e.g., CD4, CD8, PD-1) whose abundance does not always correlate perfectly with RNA levels. 

**CITE-seq** (Cellular Indexing of Transcriptomes and Epitopes by Sequencing) solves this by using antibody-derived tags (ADTs) to simultaneously measure RNA and protein levels in the exact same cell. 

This tutorial covers the normalization of ADT data and the advanced **Weighted Nearest Neighbor (WNN)** integration method in Seurat to combine these two modalities.

---

## 1. Preparing the CITE-seq Object

A CITE-seq Seurat object contains two distinct "Assays": `RNA` (for transcripts) and `ADT` (for proteins).

```r
library(Seurat)
library(ggplot2)

# Assuming 'seurat_obj' has already been loaded with both matrices
# Verify the assays
Assays(seurat_obj)
# Output should show: "RNA", "ADT"
```

---

## 2. ADT Normalization (Margin 1 vs Margin 2)

While RNA is usually normalized via LogNormalize or SCTransform, ADT data requires **Centered Log-Ratio (CLR)** normalization. 

There are two ways to apply CLR:
*   **Margin = 1 (Across cells):** Normalizes the protein signal across all cells independently. Best when you want to compare the expression of a specific protein across different cell populations.
*   **Margin = 2 (Across proteins):** Normalizes the signal across all proteins within a single cell. Best for reducing cell-to-cell technical variations.

```r
# Set Default Assay to ADT
DefaultAssay(seurat_obj) <- 'ADT'

# Normalize using CLR (Margin 2 is standard for CITE-seq in Seurat v4+)
seurat_obj <- NormalizeData(seurat_obj, normalization.method = 'CLR', margin = 2)

# Run PCA specifically on the protein data
# (Unlike RNA, we do not find variable features; we use all ADT proteins)
seurat_obj <- ScaleData(seurat_obj)
seurat_obj <- RunPCA(seurat_obj, features = rownames(seurat_obj), reduction.name = 'apca')
```

---

## 3. Weighted Nearest Neighbor (WNN) Integration

How do you combine RNA and Protein clustering? If you simply merge them, one modality will dominate the other. 

Seurat's **WNN Analysis** solves this by calculating a "weight" for each cell. If a cell has a very clear protein profile but a noisy RNA profile, WNN assigns higher weight to the protein data for that specific cell.

```r
# Ensure RNA has also been processed (SCTransform or LogNormalize + PCA)
DefaultAssay(seurat_obj) <- 'RNA'

# Find the multi-modal neighbors using WNN
seurat_obj <- FindMultiModalNeighbors(
  seurat_obj, 
  reduction.list = list("pca", "apca"), # RNA PCA and ADT PCA
  dims.list = list(1:30, 1:18),         # Dimensions to use for each
  modality.weight.name = "RNA.weight"   # Name of the weight column
)

# Run UMAP and Clustering on the integrated WNN graph
seurat_obj <- RunUMAP(seurat_obj, nn.name = "weighted.nn", reduction.name = "wnn.umap", reduction.key = "wnnUMAP_")
seurat_obj <- FindClusters(seurat_obj, graph.name = "wsnn", algorithm = 3, resolution = 0.5)
```

---

## 4. Visualizing Multi-Omics Data

Once WNN is complete, you can visualize both modalities side-by-side to see how surface proteins perfectly define clusters that RNA alone struggles to separate (such as CD4+ Memory vs Naive T-cells).

```r
# Visualize the WNN UMAP
DimPlot(seurat_obj, reduction = 'wnn.umap', group.by = 'seurat_clusters', label = TRUE)

# Compare RNA vs Protein expression directly
FeaturePlot(seurat_obj, 
            features = c("rna_CD4", "adt_CD4"), # Prefix determines the assay
            reduction = 'wnn.umap',
            min.cutoff = 'q10', 
            max.cutoff = 'q90')
```

By leveraging WNN integration, you unlock a much higher resolution of cellular heterogeneity than standard scRNA-seq can provide.


---

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
