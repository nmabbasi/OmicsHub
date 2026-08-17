---
title: "Spatial Transcriptomics"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Spatial Transcriptomics"
excerpt: "Learn how to analyze spatial transcriptomics data to map gene expression directly onto tissue architecture, with parallel code examples in both R (Seurat) and Python (Squidpy)."
image: "images/spatial-transcriptomics.png"
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
    <li><strong>Prerequisites:</strong> Complete scRNA-seq Basics and understand tissue sections, spatial coordinates, counts, and histology-aware interpretation.</li>
    <li><strong>Objective:</strong> Load, QC, visualize, and interpret spatial transcriptomics data while separating spatial association from causal tissue mechanisms.</li>
    <li><strong>Expected Output:</strong> A spatial plot with tissue context, QC notes, coordinate system, feature choice, and a cautious biological interpretation.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>



## Spatial Transcriptomics: Bridging RNA and Anatomy

## Introduction to Spatial Biology

Traditional single-cell RNA-seq requires dissociating tissues, which destroys the physical architecture and context of the cells. **Spatial Transcriptomics** (such as 10x Genomics Visium or Xenium) solves this by mapping gene expression directly onto intact histological tissue slices (like H&E stains).

This tutorial provides the foundational workflows for processing spatial data in both R and Python.

---

## 1. Loading and Preprocessing Spatial Data

Spatial data objects are unique because they contain two distinct types of data: the gene expression matrix (counts) and the spatial coordinates/images.

Both ecosystems load the same count matrix and spatial metadata, but store them in different object types.

<div class="code-tabs" data-code-tabs>
  <div class="code-tab-list" role="tablist" aria-label="Spatial loading and preprocessing examples">
    <button id="spatial-load-python-tab" class="code-tab-button is-active" type="button" role="tab" aria-selected="true" aria-controls="spatial-load-python-panel">Python · Scanpy / Squidpy</button>
    <button id="spatial-load-r-tab" class="code-tab-button" type="button" role="tab" aria-selected="false" aria-controls="spatial-load-r-panel" tabindex="-1">R · Seurat</button>
  </div>
  <div id="spatial-load-python-panel" class="code-tab-panel" role="tabpanel" aria-labelledby="spatial-load-python-tab">
    <pre><code class="language-python">import scanpy as sc
import squidpy as sq

adata = sq.read.visium("visium_brain_data/")
sc.pp.normalize_total(adata, inplace=True)
sc.pp.log1p(adata)
sc.pp.highly_variable_genes(adata, flavor="seurat", n_top_genes=2000)
</code></pre>
  </div>
  <div id="spatial-load-r-panel" class="code-tab-panel" role="tabpanel" aria-labelledby="spatial-load-r-tab" hidden>
    <pre><code class="language-r">library(Seurat)
library(ggplot2)

spatial_data <- Load10X_Spatial(data.dir = "visium_brain_data/")
spatial_data <- SCTransform(spatial_data, assay = "Spatial", verbose = FALSE)
</code></pre>
  </div>
</div>

---

## 2. Visualizing Gene Expression on Tissue

The power of spatial transcriptomics is seeing exactly *where* a gene is highly expressed across the physical tissue.

Use a feature plot to overlay a marker signal on the tissue image; report the gene symbol convention, image alignment, and color scale.

<div class="code-tabs" data-code-tabs>
  <div class="code-tab-list" role="tablist" aria-label="Spatial feature-plot examples">
    <button id="spatial-plot-python-tab" class="code-tab-button is-active" type="button" role="tab" aria-selected="true" aria-controls="spatial-plot-python-panel">Python · Scanpy</button>
    <button id="spatial-plot-r-tab" class="code-tab-button" type="button" role="tab" aria-selected="false" aria-controls="spatial-plot-r-panel" tabindex="-1">R · Seurat</button>
  </div>
  <div id="spatial-plot-python-panel" class="code-tab-panel" role="tabpanel" aria-labelledby="spatial-plot-python-tab">
    <pre><code class="language-python">sc.pl.spatial(adata, color=["Snap25", "Mbp"], alpha_img=0.5, cmap="magma")
</code></pre>
  </div>
  <div id="spatial-plot-r-panel" class="code-tab-panel" role="tabpanel" aria-labelledby="spatial-plot-r-tab" hidden>
    <pre><code class="language-r">SpatialFeaturePlot(spatial_data, features = c("Snap25", "Mbp")) +
  theme(legend.position = "right")
</code></pre>
  </div>
</div>

---

## 3. Spatial Clustering

Just like scRNA-seq, we can cluster the "spots" based on their transcriptional profiles to find spatial domains (e.g., cortical layers in a brain, or tumor microenvironments).

Spatial clustering should be compared with tissue morphology and QC patterns. In Python, construct the spatial graph explicitly before using spatial statistics.

<div class="code-tabs" data-code-tabs>
  <div class="code-tab-list" role="tablist" aria-label="Spatial clustering examples">
    <button id="spatial-cluster-python-tab" class="code-tab-button is-active" type="button" role="tab" aria-selected="true" aria-controls="spatial-cluster-python-panel">Python · Scanpy / Squidpy</button>
    <button id="spatial-cluster-r-tab" class="code-tab-button" type="button" role="tab" aria-selected="false" aria-controls="spatial-cluster-r-panel" tabindex="-1">R · Seurat</button>
  </div>
  <div id="spatial-cluster-python-panel" class="code-tab-panel" role="tabpanel" aria-labelledby="spatial-cluster-python-tab">
    <pre><code class="language-python">sc.tl.pca(adata)
sc.pp.neighbors(adata)
sc.tl.leiden(adata, key_added="clusters")
sq.gr.spatial_neighbors(adata)
sc.pl.spatial(adata, color="clusters", alpha_img=0.4)
</code></pre>
  </div>
  <div id="spatial-cluster-r-panel" class="code-tab-panel" role="tabpanel" aria-labelledby="spatial-cluster-r-tab" hidden>
    <pre><code class="language-r">spatial_data <- RunPCA(spatial_data, assay = "SCT", verbose = FALSE)
spatial_data <- FindNeighbors(spatial_data, reduction = "pca", dims = 1:30)
spatial_data <- FindClusters(spatial_data, verbose = FALSE)
SpatialDimPlot(spatial_data, label = TRUE, label.size = 3)
</code></pre>
  </div>
</div>

## Summary

Both ecosystems are incredibly powerful. **Seurat (R)** provides an easy, out-of-the-box experience that is very familiar if you already do scRNA-seq. **Squidpy (Python)** provides superior tools for graph-based spatial statistics, such as testing if two cell types physically co-occur in the tissue.


<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why does spatial co-localization support a hypothesis but not prove direct cellular interaction or lineage?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Load a small spatial dataset, plot a quality metric and one marker, then describe the tissue region and uncertainty in the observed pattern. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If a spatial pattern follows low capture or tissue-edge regions, how will you inspect spot QC, histology alignment, sequencing depth, and segmentation assumptions?</p>
    </div>
  </div>
</div>
