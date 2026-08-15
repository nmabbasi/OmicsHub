---
title: "Cell-Cell Communication"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Advanced Single-Cell Analysis"
excerpt: "Learn how to infer cell-to-cell signaling networks from scRNA-seq data using state-of-the-art tools like LIANA and CellChat."
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



# Cell-Cell Communication Analysis

## Introduction

In multi-cellular organisms, cells do not exist in isolation. They constantly communicate through secreted ligands and membrane-bound receptors. Single-cell RNA-seq allows us to infer these communication networks by looking at the simultaneous expression of a ligand in one cell type and its cognate receptor in another cell type.

Two of the most powerful tools in R for inferring these networks are **LIANA** and **CellChat**.

---

## 1. LIANA (Ligand-Receptor Analysis Framework)

LIANA is incredibly powerful because it is not just one method—it is a wrapper that runs *multiple* cell-cell communication methods (like CellPhoneDB, NATMI, Connectome, and SingleCellSignalR) simultaneously and aggregates the results, giving you a consensus ranking of the most likely interactions.

### Running LIANA

```r
library(liana)
library(SCpubr)

# Run the LIANA wrapper on your Seurat or SingleCellExperiment object
liana_output <- liana_wrap(seurat_obj)

# Aggregate the results across all methods to get consensus rankings
liana_aggregate <- liana_aggregate(liana_output)

# Save the results
write.csv(liana_aggregate, "liana_aggregate_results.csv", row.names = FALSE)
```

### Visualizing LIANA Results

The `SCpubr` package works seamlessly with LIANA to create publication-ready plots.

```r
# Create a DotPlot of the top Ligand-Receptor interactions
p1 <- SCpubr::do_LigandReceptorPlot(liana_output = liana_output,
                                    top_interactions = 15)
p1
```

---

## 2. CellChat

While LIANA is great for getting a consensus list of interactions, **CellChat** shines at pathway-level analysis and visualizing the structural topology of the communication networks (e.g., Circle plots and Hierarchy plots).

### Running CellChat

```r
library(CellChat)

# 1. Create the CellChat object from Seurat
cellchat <- createCellChat(object = seurat_obj, group.by = "cell_type")

# 2. Set the database (e.g., Human or Mouse)
CellChatDB <- CellChatDB.human
cellchat@DB <- CellChatDB

# 3. Preprocess and infer communications
cellchat <- subsetData(cellchat)
cellchat <- identifyOverExpressedGenes(cellchat)
cellchat <- identifyOverExpressedInteractions(cellchat)
cellchat <- computeCommunProb(cellchat)
cellchat <- computeCommunProbPathway(cellchat)
cellchat <- aggregateNet(cellchat)
```

### Visualizing CellChat Networks

```r
# Visualize the communication network as a Circle Plot
netVisual_circle(cellchat@net$count, vertex.weight = groupSize, weight.scale = T, 
                 label.edge= F, title.name = "Number of interactions")
```

## Summary

*   Use **LIANA** when you want a highly robust, consensus-driven list of specific Ligand-Receptor pairs.
*   Use **CellChat** when you want to visualize pathway-level communication networks and create beautiful network topologies.


---

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
