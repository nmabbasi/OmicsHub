---
title: "Single-cell RNA-seq Basics: End-to-End Analysis (Python & R)"
date: "2026-08-13"
author: "Bioinformatics Workflow Hub"
category: "Single-cell RNA-seq"
excerpt: "A complete, production-ready single-cell RNA-seq pipeline demonstrating both Python (Scanpy) and R (Seurat) workflows. Covers standard QC, PCA, UMAP, and Leiden/Louvain clustering."
image: "images/single-cell-analysis.png"
---

## From Raw Counts to Biological Insights

Once the sequencing facility provides raw FASTQ files, the initial preprocessing step (using tools like Cell Ranger or STARsolo) maps the reads to a reference genome and generates a sparse count matrix. This matrix—where rows are genes and columns are cells—is the starting point for computational biologists.

In this tutorial, we will walk through a standard end-to-end analysis on a 10x Genomics dataset. We provide parallel workflows in both **Python (Scanpy)** and **R (Seurat)** so you can choose the ecosystem that best fits your needs.

---

## 1. Loading the Data

We begin by loading the sparse matrix into our core data structures: `AnnData` in Python, or a `Seurat` object in R.

    
        <button class="code-tab-btn active" data-lang="python" onclick="switchCodeTab('tab-group-1', 'python')">Python (Scanpy)</button>
        
    
    
    <div class="code-tab-content active" data-lang="python">
```python
import scanpy as sc
import pandas as pd
import numpy as np

sc.settings.verbosity = 3
sc.logging.print_header()

# Load 10x data
adata = sc.read_10x_mtx(
    'data/filtered_feature_bc_matrix/', 
    var_names='gene_symbols', 
    cache=True
)

adata.var_names_make_unique()
```
    
    
    
```r
library(Seurat)
library(dplyr)
library(patchwork)

# Load 10x data
data_dir <- "data/filtered_feature_bc_matrix/"
pbmc.data <- Read10X(data.dir = data_dir)

# Initialize the Seurat object
pbmc <- CreateSeuratObject(counts = pbmc.data, project = "pbmc3k", min.cells = 3, min.features = 200)
```
    

---

## 2. Quality Control (QC)

Empty droplets or dying cells can confound downstream analysis. A universal rule of thumb is to filter cells with excessively high mitochondrial gene expression (which indicates ruptured cell membranes) or unusually low gene counts.

    
        <button class="code-tab-btn active" data-lang="python" onclick="switchCodeTab('tab-group-2', 'python')">Python (Scanpy)</button>
        
    
    
    <div class="code-tab-content active" data-lang="python">
```python
# Identify mitochondrial genes
adata.var['mt'] = adata.var_names.str.startswith('MT-')

# Calculate QC metrics
sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], percent_top=None, log1p=False, inplace=True)

# Filter cells
adata = adata[adata.obs.n_genes_by_counts < 2500, :]
adata = adata[adata.obs.pct_counts_mt < 5, :]

print(f"Cells remaining after QC: {adata.n_obs}")
```
    
    
    
```r
# Calculate mitochondrial percentage
pbmc[["percent.mt"]] <- PercentageFeatureSet(pbmc, pattern = "^MT-")

# Filter cells
pbmc <- subset(pbmc, subset = nFeature_RNA > 200 & nFeature_RNA < 2500 & percent.mt < 5)

print(paste("Cells remaining after QC:", ncol(pbmc)))
```
    

---

## 3. Normalization, Scaling, and PCA

Because different droplets capture different total amounts of RNA, we must normalize the data to a common scale (usually 10,000 counts per cell), log-transform it, and extract the most highly variable genes for dimensionality reduction.

    
        <button class="code-tab-btn active" data-lang="python" onclick="switchCodeTab('tab-group-3', 'python')">Python (Scanpy)</button>
        
    
    
    <div class="code-tab-content active" data-lang="python">
```python
# Normalize and log transform
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

# Find highly variable genes
sc.pp.highly_variable_genes(adata, min_mean=0.0125, max_mean=3, min_disp=0.5)

# Save the raw data before scaling
adata.raw = adata

# Scale data and run PCA
sc.pp.scale(adata, max_value=10)
sc.tl.pca(adata, svd_solver='arpack')
sc.pl.pca_variance_ratio(adata, log=True)
```
    
    
    
```r
# Normalize
pbmc <- NormalizeData(pbmc, normalization.method = "LogNormalize", scale.factor = 10000)

# Find highly variable genes
pbmc <- FindVariableFeatures(pbmc, selection.method = "vst", nfeatures = 2000)

# Scale data
all.genes <- rownames(pbmc)
pbmc <- ScaleData(pbmc, features = all.genes)

# Run PCA
pbmc <- RunPCA(pbmc, features = VariableFeatures(object = pbmc))
ElbowPlot(pbmc)
```
    

---

## 4. Neighborhood Graph and Clustering

We compute the k-nearest neighbors graph in PCA space, embed it into 2D space using UMAP, and cluster the cells to identify transcriptionally distinct subpopulations.

    
        <button class="code-tab-btn active" data-lang="python" onclick="switchCodeTab('tab-group-4', 'python')">Python (Scanpy)</button>
        
    
    
    <div class="code-tab-content active" data-lang="python">
```python
# Compute neighbors and UMAP
sc.pp.neighbors(adata, n_neighbors=10, n_pcs=40)
sc.tl.umap(adata)

# Cluster using the Leiden algorithm
sc.tl.leiden(adata, resolution=0.5)

# Visualize
sc.pl.umap(adata, color=['leiden'])
```
    
    
    
```r
# Compute neighbors
pbmc <- FindNeighbors(pbmc, dims = 1:10)

# Cluster using Louvain/Leiden
pbmc <- FindClusters(pbmc, resolution = 0.5)

# Run UMAP
pbmc <- RunUMAP(pbmc, dims = 1:10)

# Visualize
DimPlot(pbmc, reduction = "umap", label = TRUE)
```
    

## Conclusion

Both Scanpy and Seurat offer extremely robust, highly-optimized pipelines for standard scRNA-seq analysis. Transitioning between them is primarily a matter of syntax. With these clusters defined, we are ready to proceed to downstream analysis such as Trajectory Inference and Cell-Cell Communication.
