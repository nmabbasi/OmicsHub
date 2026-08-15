---
title: "Inferring Copy Number Variation (inferCNV)"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Advanced Single-Cell Analysis"
excerpt: "Learn how to use inferCNV to detect large-scale chromosomal copy number alterations in single-cell RNA-seq data, essential for identifying malignant tumor cells."
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



# Inferring Copy Number Variation with inferCNV

## Introduction

In oncology and cancer single-cell RNA-seq, distinguishing malignant tumor cells from normal, healthy cells in the microenvironment is the most critical first step. Because cancer is fundamentally driven by genomic instability, malignant cells often have massive chromosomal amplifications or deletions.

**inferCNV** is a powerful R package that uses single-cell RNA expression as a proxy for DNA copy number variation (CNV). By comparing the expression of genes across the genome in a suspect cell against a known "normal" reference cell, it can identify these large-scale chromosomal alterations.

---

## 1. Preparing Data for inferCNV

You need three inputs for inferCNV:
1. A raw count matrix.
2. A metadata file mapping each cell to its annotation (e.g., "Tumor", "Normal_T_cell", "Normal_B_cell").
3. A gene ordering file mapping each gene to its physical position on the chromosome.

```r
library(infercnv)

# Assuming you have extracted counts from your Seurat object
raw_counts <- GetAssayData(seurat_obj, slot = "counts")

# Create the inferCNV object
infercnv_obj <- CreateInfercnvObject(
  raw_counts_matrix = raw_counts,
  annotations_file = "cell_annotations.txt",
  delim = "\t",
  gene_order_file = "gene_ordering_hg38.txt",
  ref_group_names = c("Normal_T_cell", "Normal_B_cell") # Define the healthy reference!
)
```

---

## 2. Running the inferCNV Pipeline

inferCNV applies a series of smoothing steps, moving averages, and hidden Markov models (HMM) to denoise the RNA data and uncover the true DNA copy number signal.

```r
# Run the core inferCNV algorithm
infercnv_obj <- infercnv::run(
  infercnv_obj,
  cutoff = 0.1, # 0.1 for 10x Genomics, 1 for Smart-seq2
  out_dir = "infercnv_output/",
  cluster_by_groups = TRUE,
  denoise = TRUE,
  HMM = TRUE,
  num_threads = 8
)
```

### Key Considerations
*   **Cutoff:** Use `0.1` for sparse data like 10x Genomics, and `1.0` for full-length methods like Smart-seq2.
*   **Denoising:** Always use `denoise = TRUE` to remove background noise using the residual distributions.
*   **HMM:** The Hidden Markov Model predicts the actual integer copy number (e.g., 2 copies, 3 copies, or complete deletion).

---

## 3. Interpreting the Output

inferCNV automatically generates a heatmap in your output directory (`infercnv_output/infercnv.png`).

*   **Rows** are individual cells.
*   **Columns** are genes, ordered strictly by their physical location from Chromosome 1 to Chromosome X/Y.
*   **Colors:** Red indicates chromosomal amplification (e.g., Trisomy). Blue indicates chromosomal deletion.

If a cluster of cells shows massive, coordinated blocks of red and blue across entire chromosome arms, those cells are undoubtedly malignant. The reference cells (which you provided) will show a flat, neutral color, confirming they have a standard diploid genome.

This technique is the absolute gold standard for computationally validating malignant clusters before performing downstream differential expression.


---

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
