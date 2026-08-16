---
title: "Mathematical Quality Control (LISI & Silhouette)"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Single-Cell RNA-seq"
excerpt: "Learn how to mathematically prove that your batch integration worked and your clusters are robust using LISI and Silhouette scores, rather than relying on subjective UMAP visuals."
image: "images/bioinformatics-intro.png"
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
    <li><strong>Prerequisites:</strong> Complete scRNA-seq Basics and have a dataset with sample or batch labels and computed QC metrics.</li>
    <li><strong>Objective:</strong> Use LISI and silhouette-style diagnostics to quantify batch mixing and biological separation without relying only on visual embeddings.</li>
    <li><strong>Expected Output:</strong> A QC/integration evaluation table that reports metrics, neighborhood settings, labels, and a balanced interpretation.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Academy Pathway</a> to review any prerequisite stage before continuing.</p>
</div>



## Mathematical Quality Control for Integration & Clustering

## The Problem with Subjective UMAPs

In single-cell RNA-seq, it is very common to run an integration algorithm (like Harmony or CCA) and assume it worked because the UMAP "looks mixed." However, high-impact journals require **mathematical proof** that batch effects were removed without destroying true biological variance.

This tutorial covers the two mathematical gold standards for validating integration and clustering.

---

## 1. Validating Batch Mixing with LISI

The **Local Inverse Simpson's Index (LISI)** mathematically quantifies how well different batches are mixed in your data.

There are two LISI metrics you must compute:
1.  **iLISI (Integration LISI):** Measures how well batches are mixed. A score close to your total number of batches (e.g., if you have 4 patients, an iLISI of ~4) means perfect mixing.
2.  **cLISI (Cell-Type LISI):** Measures how well cell types are separated. A score close to 1 means that a cell is surrounded only by its exact same cell type (perfect biological separation).

### Running LISI in R

```r
library(lisi)
library(Seurat)

# 1. Extract the mathematical embeddings (NOT the UMAP)
# UMAP is a 2D distortion. Always calculate metrics on PCA or Harmony space.
embeddings <- Embeddings(seurat_obj, reduction = "harmony")

# 2. Extract metadata
meta_data <- seurat_obj@meta.data

# 3. Compute LISI scores for batch (patient_id) and biology (cell_type)
lisi_res <- compute_lisi(embeddings, meta_data, c("patient_id", "cell_type"))

# 4. View results
# You want high values in the 'patient_id' column, and ~1.0 in the 'cell_type' column
summary(lisi_res)
```

---

## 2. Validating Cluster Robustness with Silhouette Scores

After you run `FindClusters()`, you need to know if the clusters you found are actually distinct biological entities, or if you simply "over-clustered" a single continuous cell type into arbitrary chunks.

A **Silhouette Score** calculates how similar a cell is to its own cluster compared to the next closest cluster.
*   **Score > 0:** The cell is well matched to its cluster.
*   **Score < 0:** The cell might belong to the neighboring cluster (over-clustering).

### Calculating Silhouette Widths

```r
library(cluster)

# 1. Calculate a Euclidean distance matrix on the PCA embeddings
dist_matrix <- dist(Embeddings(seurat_obj, reduction = "pca"))

# 2. Extract the cluster labels you generated
cluster_labels <- as.numeric(seurat_obj$seurat_clusters)

# 3. Compute Silhouette scores
sil <- silhouette(cluster_labels, dist_matrix)

# 4. Visualize the robustness
# A wide, positive silhouette for a cluster proves it is highly distinct
plot(sil, border = NA, col = "darkblue", main = "Cluster Silhouette Plot")
```

## Conclusion

By calculating **iLISI**, **cLISI**, and **Silhouette Scores**, you bulletproof your analysis. Instead of saying "the cells appear to group together," you can objectively state in your manuscript: *"Integration successfully removed batch effects (median iLISI = 3.8/4.0) while preserving cell-type separation (median cLISI = 1.02)."*


<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why can a high batch-mixing score be undesirable if cell identities or conditions are overcorrected?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Calculate or inspect LISI and silhouette metrics for pre- and post-integration data, then explain the trade-off in one paragraph. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If metrics disagree with a UMAP, how will you check label choice, neighborhood parameters, class imbalance, and whether the expected biology was preserved?</p>
    </div>
  </div>
</div>
