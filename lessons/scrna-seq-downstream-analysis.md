---
title: "Downstream Analysis"
date: "2026-08-13"
author: "Nasir Mahmood Abbasi, PhD"
category: "Single-Cell RNA-seq"
excerpt: "Explore foundational advanced downstream analyses: mapping cell-cell communication networks, inferring Transcription Factor (TF) activities, and generating publication-ready plots (SCpubr)."
image: "images/scrna_metabolism.png"
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
    <li><strong>Prerequisites:</strong> Basic understanding of the Linux terminal and bioinformatics concepts. (See <a href="start-here.html" class="underline">Start Here</a>)</li>
    <li><strong>Objective:</strong> Master the core concepts and practical commands of this topic.</li>
    <li><strong>Expected Output:</strong> A reproducible workflow and a clear understanding of the methodology.</li>
  </ul>
</div>



## Beyond Clustering: Functional Single-Cell Biology

Once cells are clustered and annotated, the focus shifts to understanding *how* these populations function and interact. This involves interrogating **Transcription Factor (TF) activity**, inferring **Cell-Cell Communication**, and creating high-quality visualizations.

In this tutorial, we cover the foundational tools for these advanced downstream steps across both R and Python.

---

## 1. Cell-Cell Communication (Receptor-Ligand)

To understand how populations (e.g., T-cells and Macrophages) interact, we can map the expression of known Ligand-Receptor pairs. **CellChat** (R) and **CellPhoneDB** (Python) are the industry standards.

```r
library(CellChat)
library(patchwork)

# 1. Create CellChat object from Seurat
cellchat <- createCellChat(object = pbmc, group.by = "ident")

# 2. Set the ligand-receptor database
CellChatDB <- CellChatDB.human 
cellchat@DB <- CellChatDB

# 3. Preprocessing and Network Inference
cellchat <- subsetData(cellchat)
cellchat <- identifyOverExpressedGenes(cellchat)
cellchat <- identifyOverExpressedInteractions(cellchat)
cellchat <- computeCommunProb(cellchat)

# Filter out interactions in very few cells
cellchat <- filterCommunication(cellchat, min.cells = 10)

# Calculate aggregated communication network
cellchat <- computeCommunProbPathway(cellchat)
cellchat <- aggregateNet(cellchat)

# 4. Visualization (Circle Plot)
groupSize <- as.numeric(table(cellchat@idents))
netVisual_circle(cellchat@net$count, vertex.weight = groupSize, 
                 weight.scale = T, label.edge= F, title.name = "Number of interactions")
```
```python
# In Python, CellPhoneDB is typically run via the command line on exported count matrices.
# First, export your Scanpy AnnData object to raw counts and metadata.

import pandas as pd
import scanpy as sc

# Export metadata
df_meta = pd.DataFrame(adata.obs['leiden'])
df_meta['cell'] = df_meta.index
df_meta = df_meta[['cell', 'leiden']]
df_meta.to_csv('meta.tsv', sep='\t', index=False)

# Export counts
counts = pd.DataFrame(adata.raw.X.toarray(), index=adata.obs.index, columns=adata.raw.var_names)
counts = counts.T
counts.to_csv('counts.tsv', sep='\t')
```

```bash
# Run CellPhoneDB via terminal
cellphonedb method statistical_analysis meta.tsv counts.tsv \
    --counts-data=hgnc_symbol \
    --output-path=out_cpdb \
    --threads=8
```

---

## 2. Transcription Factor (TF) Activity

Gene expression alone doesn't prove a Transcription Factor is active. Using tools like **Decoupler** (Python) or **DoRothEA** (R), we can infer TF activity based on the expression of its known downstream target genes.

```python
import decoupler as dc
import scanpy as sc

# 1. Retrieve the DoRothEA gene regulatory network (GRN) for humans
net = dc.get_dorothea(organism='human', levels=['A','B','C'])

# 2. Run multivariate linear model (MLM) to estimate TF activities
# We use the raw, log-normalized counts
dc.run_mlm(mat=adata, net=net, source='source', target='target', weight='weight', verbose=True)

# The results are stored in obsm. We can visualize the activity of a specific TF (e.g., STAT1)
sc.pl.umap(adata, color='STAT1', cmap='RdBu_r', vcenter=0)
```
```r
library(dorothea)
library(Seurat)

# 1. Load the human regulons (confidence levels A, B, C)
dorothea_regulon_human <- get(data("dorothea_hs", package = "dorothea"))
regulon <- dorothea_regulon_human %>%
    dplyr::filter(confidence %in% c("A", "B", "C"))

# 2. Run VIPER algorithm to calculate TF activity
pbmc <- run_viper(pbmc, regulon,
                  options = list(method = "scale", minsize = 4, 
                                 eset.filter = FALSE, cores = 1, verbose = FALSE))

# 3. Visualize TF activity
DefaultAssay(pbmc) <- "dorothea"
FeaturePlot(pbmc, features = "STAT1", cols = c("blue", "white", "red"))
```

---

## 3. Publication-Ready Plotting (SCpubr)

While Seurat's base plotting functions are good, the **SCpubr** package in R generates highly polished, publication-ready graphics automatically.

```r
library(SCpubr)

# Generate a premium UMAP with custom labels, density contours, and refined aesthetics
SCpubr::do_DimPlot(sample = pbmc, 
                   group.by = "ident",
                   label = TRUE,
                   label.box = TRUE,
                   repel = TRUE,
                   font.size = 14,
                   legend.position = "none")

# Generate a publication-quality DotPlot for marker genes
markers <- c("CD3D", "IL7R", "CD8A", "MS4A1", "CD14")
SCpubr::do_DotPlot(sample = pbmc,
                   features = markers,
                   group.by = "ident",
                   colors.use = c("lightgrey", "darkblue"))
```

## Conclusion

Mastering these downstream analysis techniques allows you to graduate from simply classifying cells to understanding the mechanistic networks and interactions driving tissue biology. Both R and Python offer robust, highly developed tools to accomplish these goals.


<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
