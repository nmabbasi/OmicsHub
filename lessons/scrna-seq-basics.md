---
title: "scRNA-seq Basics"
date: "2026-08-13"
author: "Nasir Mahmood Abbasi, PhD"
category: "Single-Cell RNA-seq"
excerpt: "A complete, production-ready single-cell RNA-seq pipeline demonstrating both Python (Scanpy) and R (Seurat) workflows. Covers standard QC, PCA, UMAP, and Leiden/Louvain clustering."
image: "images/single-cell-analysis.png"
---


<div class="flex flex-wrap items-center gap-4 text-xs font-mono text-gray-500 bg-gray-50 p-3 rounded-lg border border-gray-200 mb-6">
  <div class="flex items-center gap-1">
    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
    <span><strong>Tested on:</strong> Python 3.11, R 4.3.2, Ubuntu 24.04</span>
  </div>
  <div class="flex items-center gap-1">
    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
    <span><strong>Last Review:</strong> 2026-08-15</span>
  </div>
</div>

<div class="p-6 bg-blue-50 border border-blue-100 rounded-xl mb-8">
  <h4 class="text-lg font-bold text-blue-900 mb-2">Learning Objectives & Prerequisites</h4>
  <ul class="list-disc list-inside text-blue-800 space-y-1 mb-4">
    <li><strong>Prerequisites:</strong> Complete Linux, biological data formats, and basic statistics; install current Scanpy or Seurat in an isolated environment.</li>
    <li><strong>Objective:</strong> Load a 10x count matrix, inspect QC distributions, normalize, identify variable features, run PCA/UMAP, and cluster cells without treating fixed thresholds as universal.</li>
    <li><strong>Expected Output:</strong> A reproducible AnnData or Seurat object with documented per-sample QC decisions, neighborhood graph, UMAP, and cluster labels.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>



## From Raw Counts to Biological Insights

Once the sequencing facility provides raw FASTQ files, the initial preprocessing step (using tools like Cell Ranger or STARsolo) maps the reads to a reference genome and generates a sparse count matrix. This matrix—where rows are genes and columns are cells—is the starting point for computational biologists.

In this tutorial, we will walk through a standard end-to-end analysis on a 10x Genomics dataset. We provide parallel workflows in both **Python (Scanpy)** and **R (Seurat)** so you can choose the ecosystem that best fits your needs.

---

## 1. Loading the Data

We begin by loading the sparse matrix into our core data structures: `AnnData` in Python, or a `Seurat` object in R.

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

Empty droplets or dying cells can confound downstream analysis. High mitochondrial expression or unusually low gene counts can flag low-quality cells, but the distribution must be inspected for each dataset and batch. The thresholds below are training starting points, not universal biological rules; document and justify any filtering decision.

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

Both Scanpy and Seurat support robust standard scRNA-seq workflows, but they differ in data structures, defaults, ecosystem choices, and analysis decisions. Choose one deliberately and document versions and parameters. With these clusters defined, we are ready to proceed to downstream analysis such as Trajectory Inference and Cell-Cell Communication.


<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why must QC thresholds be inspected per dataset or batch rather than copied unchanged from a tutorial?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Run the workflow on a small 10x dataset, create QC plots before filtering, document chosen thresholds, and save a clustered UMAP. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If a cluster is driven by mitochondrial content, batch, or doublets, what QC, sample-stratification, and doublet-detection checks should precede interpretation?</p>
    </div>
  </div>
</div>
