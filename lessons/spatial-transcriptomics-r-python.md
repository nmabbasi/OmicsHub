---
title: "Spatial Transcriptomics"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Spatial Transcriptomics"
excerpt: "Learn how to analyze spatial transcriptomics data to map gene expression directly onto tissue architecture, with parallel code examples in both R (Seurat) and Python (Squidpy)."
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



# Spatial Transcriptomics: Bridging RNA and Anatomy

## Introduction to Spatial Biology

Traditional single-cell RNA-seq requires dissociating tissues, which destroys the physical architecture and context of the cells. **Spatial Transcriptomics** (such as 10x Genomics Visium or Xenium) solves this by mapping gene expression directly onto intact histological tissue slices (like H&E stains).

This tutorial provides the foundational workflows for processing spatial data in both R and Python.

---

## 1. Loading and Preprocessing Spatial Data

Spatial data objects are unique because they contain two distinct types of data: the gene expression matrix (counts) and the spatial coordinates/images.

### R (Seurat) Approach
In R, the `Seurat` package has native spatial support.

```r
library(Seurat)
library(ggplot2)

# Load 10x Visium Data (points to the directory containing spatial/ and filtered_feature_bc_matrix.h5)
spatial_data <- Load10X_Spatial(data.dir = "visium_brain_data/")

# Normalize the data using SCTransform (recommended for spatial data)
spatial_data <- SCTransform(spatial_data, assay = "Spatial", verbose = FALSE)
```

### Python (Squidpy / Scanpy) Approach
In Python, `Scanpy` handles the RNA, and `Squidpy` handles the spatial graphs.

```python
import scanpy as sc
import squidpy as sq

# Load 10x Visium Data
adata = sq.read.visium("visium_brain_data/")

# Normalize and log-transform
sc.pp.normalize_total(adata, inplace=True)
sc.pp.log1p(adata)
sc.pp.highly_variable_genes(adata, flavor="seurat", n_top_genes=2000)
```

---

## 2. Visualizing Gene Expression on Tissue

The power of spatial transcriptomics is seeing exactly *where* a gene is highly expressed across the physical tissue.

### R (Seurat)
Use the `SpatialFeaturePlot` function to overlay gene expression onto the H&E image.

```r
# Visualize a specific marker gene (e.g., a neuron marker in a brain slice)
SpatialFeaturePlot(spatial_data, features = c("Snap25", "Mbp")) +
  theme(legend.position = "right")
```

### Python (Squidpy)
Use the `sc.pl.spatial` function.

```python
# Visualize marker genes over the tissue image
sc.pl.spatial(adata, color=["Snap25", "Mbp"], alpha_img=0.5, cmap="magma")
```

---

## 3. Spatial Clustering

Just like scRNA-seq, we can cluster the "spots" based on their transcriptional profiles to find spatial domains (e.g., cortical layers in a brain, or tumor microenvironments).

### R (Seurat)

```r
# Standard clustering workflow
spatial_data <- RunPCA(spatial_data, assay = "SCT", verbose = FALSE)
spatial_data <- FindNeighbors(spatial_data, reduction = "pca", dims = 1:30)
spatial_data <- FindClusters(spatial_data, verbose = FALSE)

# Plot the clusters onto the physical tissue
SpatialDimPlot(spatial_data, label = TRUE, label.size = 3)
```

### Python (Squidpy)

Squidpy goes a step further by calculating a **spatial neighbor graph**, ensuring that clusters take physical proximity into account, not just transcriptional similarity.

```python
# Compute PCA and neighbors
sc.tl.pca(adata)
sc.pp.neighbors(adata)
sc.tl.leiden(adata, key_added="clusters")

# Compute the spatial graph
sq.gr.spatial_neighbors(adata)

# Plot the transcriptional clusters on the tissue
sc.pl.spatial(adata, color="clusters", alpha_img=0.4)
```

## Summary

Both ecosystems are incredibly powerful. **Seurat (R)** provides an easy, out-of-the-box experience that is very familiar if you already do scRNA-seq. **Squidpy (Python)** provides superior tools for graph-based spatial statistics, such as testing if two cell types physically co-occur in the tissue.


---

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
