---
title: "Immune Repertoire Analysis"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Advanced Single-Cell Analysis"
excerpt: "A guide to analyzing T-cell and B-cell receptor (TCR/BCR) repertoires from single-cell data using scRepertoire to track clonal expansion in diseases like Sézary Syndrome."
image: "images/cat_advanced_sc.png"
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
    <li><strong>Prerequisites:</strong> Complete scRNA-seq Basics and understand TCR/BCR clonotypes, paired chains, and appropriate study-design metadata.</li>
    <li><strong>Objective:</strong> Analyze immune-receptor repertoire features while distinguishing clone abundance, diversity, expansion, and antigen specificity claims.</li>
    <li><strong>Expected Output:</strong> A repertoire summary with clonotype definition, chain handling, diversity metric, sample denominator, and cautious interpretation.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>



## Immune Repertoire Analysis

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


<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why does clonal expansion not by itself identify antigen specificity or functional state?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Calculate or inspect clone-size distributions for two samples and report the clonotype definition and normalization used. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If one sample appears oligoclonal, how will you check sequencing depth, cell recovery, doublets, chain pairing, and technical batch effects?</p>
    </div>
  </div>
</div>
