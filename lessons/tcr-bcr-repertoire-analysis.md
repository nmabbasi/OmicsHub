---
title: "Immune Repertoire Analysis"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Advanced Single-Cell Analysis"
excerpt: "A guide to analyzing T-cell and B-cell receptor (TCR/BCR) repertoires from single-cell data using scRepertoire to track clonal expansion in diseases like Sézary Syndrome."
image: "images/cat_advanced_sc.png"
---

<div class="p-6 bg-blue-50 border border-blue-100 rounded-xl mb-8">
  <h4 class="text-lg font-bold text-blue-900 mb-2">Learning Objectives & Prerequisites</h4>
  <ul class="list-disc list-inside text-blue-800 space-y-1 mb-4">
    <li><strong>Prerequisites:</strong> Basic understanding of the Linux terminal and bioinformatics concepts. (See <a href="start-here.html" class="underline">Start Here</a>)</li>
    <li><strong>Objective:</strong> Master the core concepts and practical commands of this topic.</li>
    <li><strong>Expected Output:</strong> A reproducible workflow and a clear understanding of the methodology.</li>
  </ul>
</div>



# Immune Repertoire Analysis

## Introduction

In immunology and oncology, tracking the expansion of specific T-cells or B-cells is crucial. Every T-cell has a unique T-Cell Receptor (TCR) sequence created by V(D)J recombination. When an immune cell recognizes a specific antigen (like a virus or a tumor), it rapidly clones itself.

By sequencing the TCRs at the single-cell level (scTCR-seq), we can measure **clonal expansion**. This is especially critical in T-cell lymphomas, such as **Sézary Syndrome**, where a single malignant T-cell clone expands uncontrollably.

This tutorial covers the basics of analyzing V(D)J single-cell data using the `scRepertoire` package in R.

---

## 1. Preparing V(D)J Data

Typically, 10x Genomics Cell Ranger provides a `filtered_contig_annotations.csv` file containing the TCR Alpha and Beta chain sequences for every cell barcode.

```r
library(scRepertoire)
library(Seurat)

# Load the Cell Ranger V(D)J output
contig_data <- read.csv("filtered_contig_annotations.csv")

# Convert the contig list into a combined TCR format for scRepertoire
combined_tcr <- combineTCR(contig_data, 
                           samples = "Patient1", 
                           ID = "Timepoint1", 
                           cells = "T-AB")
```

---

## 2. Visualizing Clonal Expansion

Once the TCR chains are combined, we can visualize the diversity of the immune repertoire. In a healthy patient, the repertoire is highly diverse. In a Sézary Syndrome patient, you will see massive clonal dominance.

```r
# Plot the relative abundance of the top clones
quantContig(combined_tcr, cloneCall="gene+nt", scale = TRUE)

# Visualize clonal space homeostasis (the proportion of the repertoire occupied by rare vs hyperexpanded clones)
clonalHomeostasis(combined_tcr, cloneCall="gene+nt")
```

---

## 3. Integrating TCR Data with Seurat (scRNA-seq)

The true power of modern immune profiling is linking the *identity* of the clone (the TCR) with its *phenotype* (the RNA expression). We can overlay the clonal expansion data directly onto a Seurat UMAP.

```r
# Assume 'seurat_obj' is your standard processed scRNA-seq object
# Merge the TCR data into the Seurat metadata using the cell barcodes
seurat_obj <- combineExpression(combined_tcr, seurat_obj, cloneCall="gene+nt")

# The Seurat object now has a 'cloneType' column!
# We can visualize where the highly expanded clones sit on the UMAP
DimPlot(seurat_obj, group.by = "cloneType") + scale_color_viridis_d()
```

### Finding Markers of Malignant Clones

Once integrated, you can easily find the biological markers driving the disease by comparing the hyperexpanded clone against all other normal T-cells.

```r
# Set the identity to the clonal grouping
Idents(seurat_obj) <- "cloneType"

# Find genes upregulated in the 'Hyperexpanded' clone compared to 'Rare' clones
malignant_markers <- FindMarkers(seurat_obj, ident.1 = "Hyperexpanded", ident.2 = "Rare")

head(malignant_markers)
```

This workflow forms the bioinformatics foundation for identifying targetable biomarkers in cutaneous T-cell lymphomas and other immune-driven diseases.


---

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
