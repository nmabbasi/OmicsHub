---
title: "Multi-Omics: CITE-seq & WNN Integration"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Advanced Single-Cell Analysis"
excerpt: "Learn how to process and integrate CITE-seq data, bridging the gap between RNA expression and surface protein abundance using Weighted Nearest Neighbor (WNN) analysis."
image: "images/cite-seq-wnn-multiomics.png"
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
    <li><strong>Prerequisites:</strong> Complete scRNA-seq Basics and have paired RNA/protein or multi-modal data with clearly documented feature names.</li>
    <li><strong>Objective:</strong> Integrate CITE-seq or multi-modal data with WNN while evaluating modality quality, weighting, and biological agreement.</li>
    <li><strong>Expected Output:</strong> A multi-modal object with modality-specific QC, WNN embedding, feature interpretation, and documented modality contributions.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>



## Multi-Omics: CITE-seq & WNN Integration

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

<figure class="lesson-figure">
  <img src="images/tutorial-figures/wnn-multimodal-embedding.webp" alt="WNN embedding comparison with cluster view on the left and predicted cell-type view on the right, illustrating joint RNA and antibody-derived tag analysis." loading="lazy" width="960" height="576">
  <figcaption>
    <strong>Figure: A joint WNN embedding can connect clusters with multimodal cell-type interpretation.</strong> The left panel shows a joint neighborhood structure; the right panel illustrates how predicted identities can be compared against the same embedding. Treat predictions as evidence to verify with RNA markers, ADT signal, and biological context - not as final labels by themselves.
    <span class="figure-source">Author-provided non-clinical teaching figure. This panel is included to demonstrate multi-modal interpretation rather than to report a disease-specific result.</span>
  </figcaption>
</figure>

By leveraging WNN integration, you unlock a much higher resolution of cellular heterogeneity than standard scRNA-seq can provide.



### Matched Python and R weighted-nearest-neighbour workflow

Preprocess RNA and protein modalities separately before computing a joint graph. Compare modality weights and marker evidence before interpreting the resulting clusters.

```python
import muon as mu
import scanpy as sc

sc.pp.neighbors(mdata["rna"])
sc.pp.neighbors(mdata["prot"])
mu.pp.neighbors(mdata, key_added="wnn")
mu.tl.umap(mdata, neighbors_key="wnn")
sc.tl.leiden(mdata, neighbors_key="wnn", key_added="leiden_wnn")
```
```r
library(Seurat)

seurat_obj <- FindMultiModalNeighbors(
  seurat_obj,
  reduction.list = list("pca", "apca"),
  dims.list = list(1:30, 1:18),
  modality.weight.name = "RNA.weight"
)
seurat_obj <- RunUMAP(seurat_obj, nn.name = "weighted.nn", reduction.name = "wnn.umap")
seurat_obj <- FindClusters(seurat_obj, graph.name = "wsnn", resolution = 0.5)
```

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why should RNA and protein modalities be quality-controlled and interpreted separately before drawing conclusions from a joint embedding?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Create or inspect a WNN analysis and compare an RNA marker, an antibody-derived tag, and the resulting joint neighborhood structure. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If RNA and protein disagree, how will you inspect antibody background, feature normalization, batch effects, doublets, and biology such as post-transcriptional regulation?</p>
    </div>
  </div>
</div>
