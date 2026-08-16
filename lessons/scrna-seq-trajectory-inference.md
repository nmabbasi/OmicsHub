---
title: "Trajectory Inference"
date: "2026-08-13"
author: "Nasir Mahmood Abbasi, PhD"
category: "Single-Cell RNA-seq"
excerpt: "Learn the basics of inferring cellular trajectories and pseudotime using industry-standard tools like PAGA in Python and Monocle3/Slingshot in R."
image: "images/trajectory-inference.png"
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
    <li><strong>Prerequisites:</strong> Complete scRNA-seq Basics, including QC, clustering, and marker interpretation; use data with a plausible continuous process.</li>
    <li><strong>Objective:</strong> Infer and interpret pseudotime or lineage trajectories while separating computational ordering from directly observed developmental time.</li>
    <li><strong>Expected Output:</strong> A trajectory figure with root rationale, branch interpretation, gene trends, and explicit validation limits.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Academy Pathway</a> to review any prerequisite stage before continuing.</p>
</div>



## Understanding Trajectory Inference

Single-cell RNA sequencing provides static snapshots of cellular states. However, biology is highly dynamic. Processes like differentiation, immune activation, and cellular exhaustion are continuous transitions.

**Trajectory inference (TI)** algorithms attempt to order cells along a learned trajectory based on their transcriptional similarities, creating a "pseudotime" axis. This allows us to track gene expression changes as cells differentiate.

In this tutorial, we will explore the foundational tools for TI in both Python and R.

---

## 1. PAGA (Python)

**Partition-based Graph Abstraction (PAGA)** is integrated directly into the Scanpy ecosystem. It generates a coarse-grained map of cellular connectivity and provides a robust scaffold for embedding and pseudotime calculation.

```python
import scanpy as sc
import scvelo as scv

# Assuming `adata` is already preprocessed, clustered (e.g., 'leiden'), and has a UMAP
# We must first re-compute the neighborhood graph if it's been altered
sc.pp.neighbors(adata, n_neighbors=15, n_pcs=40)

# 1. Run PAGA
sc.tl.paga(adata, groups='leiden')

# 2. Plot the coarse-grained PAGA graph
sc.pl.paga(adata, plot=False)

# 3. Use PAGA initialization to recompute a more continuous UMAP
sc.tl.umap(adata, init_pos='paga')
sc.pl.umap(adata, color=['leiden'], legend_loc='on data')

# 4. Calculate Diffusion Pseudotime (DPT)
# First, identify a root cell (e.g., the stem cell or progenitor cluster)
# Assuming cluster '0' is the known progenitor state
adata.uns['iroot'] = np.flatnonzero(adata.obs['leiden']  == '0')[0]

# Compute pseudotime
sc.tl.dpt(adata)

# Visualize pseudotime progression across the manifold
sc.pl.umap(adata, color='dpt_pseudotime', cmap='viridis')
```

---

## 2. Monocle3 & Slingshot (R)

In the R ecosystem, **Monocle3** and **Slingshot** are the leading frameworks for trajectory inference. Slingshot is highly favored for its simplicity and ability to handle branching trajectories effectively from existing Seurat objects.

```r
library(Seurat)
library(slingshot)
library(SingleCellExperiment)
library(RColorBrewer)

# Convert Seurat object to SingleCellExperiment (SCE)
sce <- as.SingleCellExperiment(pbmc)

# 1. Run Slingshot
# We use the existing UMAP embedding and specify a starting cluster
sce <- slingshot(sce, clusterLabels = 'ident', reducedDim = 'UMAP', start.clus = '0')

# 2. Extract pseudotime and plot
colors <- colorRampPalette(brewer.pal(11, 'Spectral'))[-11]
plotcol <- colors[cut(sce$slingPseudotime_1, breaks=100)]

plot(reducedDims(sce)$UMAP, col = plotcol, pch=16, asp = 1)
lines(SlingshotDataSet(sce), lwd=2, col='black')
```

```r
library(monocle3)
library(SeuratWrappers)

# Convert Seurat to CellDataSet (CDS)
cds <- as.cell_data_set(pbmc)

# 1. Calculate size factors and cluster cells within Monocle
cds <- estimate_size_factors(cds)
cds <- cluster_cells(cds)

# 2. Learn the principal graph (trajectory)
cds <- learn_graph(cds)

# 3. Order cells in pseudotime
# (This will open an interactive prompt to select the root nodes)
cds <- order_cells(cds)

# 4. Visualize the trajectory and pseudotime
plot_cells(cds,
           color_cells_by = "pseudotime",
           label_cell_groups=FALSE,
           label_leaves=FALSE,
           label_branch_points=FALSE,
           graph_label_size=1.5)
```

## Conclusion

Trajectory inference shifts our perspective from discrete clusters to continuous cellular development. Whether you rely on PAGA's graph abstractions in Python or Slingshot's branching lineage logic in R, establishing a solid pseudotime framework is the key to identifying the gene regulatory networks driving cellular transitions.


<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why does pseudotime not prove that one observed cell literally becomes another?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Run or inspect a trajectory analysis, state the root choice, identify one branch, and plot expression of a relevant dynamic gene. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If the inferred path contradicts known biology, how will you check rooting, cell selection, batch effects, doublets, and alternative trajectory methods?</p>
    </div>
  </div>
</div>
