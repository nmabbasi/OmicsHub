---
title: "Advanced scRNA-seq Analysis: Metabolic Heterogeneity and Pathway Analysis"
date: "2026-08-13"
author: "Bioinformatics Workflow Hub"
category: "Single-cell RNA-seq"
excerpt: "Learn how to use single-cell transcriptomics to identify metabolic dependencies in specific cellular subclones, and how to run Gene Set Enrichment Analysis (GSEA) on single-cell data."
image: "images/single-cell-analysis.png"
---

## Uncovering Metabolic Heterogeneity in Single Cells

A major frontier in single-cell biology is identifying specific metabolic states within a heterogeneous population. For example, within a complex tissue or a tumor microenvironment, distinct subclones often rewire their metabolism (e.g., shifting toward glycolysis or oxidative phosphorylation) to adapt to local conditions like hypoxia.

Single-cell RNA-sequencing (scRNA-seq) allows us to identify these metabolic shifts at the subclonal level, revealing potential functional dependencies.

In this tutorial, we will demonstrate how to score cells for specific metabolic phenotypes and identify the transcriptional pathways that co-occur with these metabolic shifts.

---

## 1. Setting Up and Loading Data

We will use Scanpy to evaluate metabolic transcriptional networks within a subset of cells.

```python
import scanpy as sc
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Load an annotated dataset
adata = sc.read_h5ad('./data/annotated_dataset.h5ad')

# Isolate the specific cell compartment of interest for focused analysis
# Assuming 'cell_type' contains an annotation 'Target_Population'
subset_cells = adata[adata.obs['cell_type'] == 'Target_Population'].copy()
```

---

## 2. Creating a "Glycolytic / Hypoxia" Module Score

To identify metabolically hyperactive or hypoxic cells, we shouldn't rely on a single gene. Instead, we evaluate whether the entire metabolic machinery is co-upregulated by creating a module score (or signature score).

```python
# Define a general metabolic/hypoxia gene signature
metabolic_signature = [
    'LDHA',     # Glycolysis (Lactate Dehydrogenase)
    'ENO1',     # Glycolysis (Enolase)
    'GAPDH',    # Glycolysis
    'SLC2A1',   # Glucose transporter (GLUT1)
    'SLC16A1',  # Lactate transporter
    'HIF1A',    # Hypoxia-inducible factor
    'VEGFA'     # Angiogenesis marker
]

# Ensure genes are actually present in the dataset's vocabulary
valid_metabolic = [g for g in metabolic_signature if g in subset_cells.var_names]

# Score the cells for this metabolic phenotype
sc.tl.score_genes(subset_cells, gene_list=valid_metabolic, score_name='glycolytic_score')

# Visualize the distribution of the metabolic score across different clusters
sc.pl.violin(subset_cells, 'glycolytic_score', groupby='leiden', 
             stripplot=False, inner='box')

# Map the score onto the UMAP to see spatial distribution in the manifold
sc.pl.umap(subset_cells, color=['leiden', 'glycolytic_score'], wspace=0.3, cmap='viridis')
```

If the `glycolytic_score` is highly enriched in a specific cluster, this suggests that the cluster represents a metabolically distinct subpopulation adapting to its microenvironment.

---

## 3. Differential Expression: Identifying Co-Dependencies

If we want to understand what else is driving this high-glycolysis population, we can perform differential expression (DE) comparing the metabolically "High" cells to the "Low" cells.

```python
# Categorize cells into High and Low metabolic states
# We use the 75th percentile as a cutoff for "High"
score_threshold = np.percentile(subset_cells.obs['glycolytic_score'], 75)

subset_cells.obs['Metabolic_State'] = 'Low'
subset_cells.obs.loc[subset_cells.obs['glycolytic_score'] > score_threshold, 'Metabolic_State'] = 'High'

# Run DE analysis comparing High vs Low
sc.tl.rank_genes_groups(subset_cells, groupby='Metabolic_State', 
                        groups=['High'], reference='Low', method='wilcoxon')

# Extract top upregulated genes in the metabolically active population
de_results = pd.DataFrame(subset_cells.uns['rank_genes_groups']['names'])
top_genes_high_metabolism = de_results['High'].head(20).tolist()

print("Top co-expressed genes with the glycolytic signature:")
print(top_genes_high_metabolism)
```

---

## 4. Gene Set Enrichment Analysis (GSEA)

To understand the broader biological pathways driving these differentially expressed genes, we can export the results for pathway analysis using `gseapy`.

```python
# Install gseapy if you haven't already: pip install gseapy
import gseapy as gp

# Extract the ranked list of genes based on log fold changes
ranked_genes = sc.get.rank_genes_groups_df(subset_cells, group='High')
ranked_genes = ranked_genes[['names', 'logfoldchanges']].sort_values('logfoldchanges', ascending=False)

# Run GSEA against the KEGG pathways database
gsea_results = gp.prerank(rnk=ranked_genes, gene_sets='KEGG_2021_Human',
                          permutation_num=1000, outdir=None)

# Plot the top enriched pathways
terms = gsea_results.res2d.sort_values('NES', ascending=False).head(5)
gp.plot.barplot(terms, column="NES", title="Pathways Enriched in High-Metabolism Cells")
```

---

## Conclusion

By isolating specific sub-populations based on module scores, scRNA-seq allows us to reconstruct the metabolic landscape of a tissue or disease state. 

This workflow (moving from gene signatures to module scoring, followed by subpopulation thresholding and GSEA) is a standard, robust approach for uncovering functional dependencies that are completely invisible in bulk RNA-sequencing data.
