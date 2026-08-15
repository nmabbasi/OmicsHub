---
title: "Trajectory Inference"
date: "2026-08-13"
author: "Nasir Mahmood Abbasi, PhD"
category: "Single-Cell RNA-seq"
excerpt: "Learn the basics of inferring cellular trajectories and pseudotime using industry-standard tools like PAGA in Python and Monocle3/Slingshot in R."
image: "images/scrna_heterogeneity.png"
---

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
