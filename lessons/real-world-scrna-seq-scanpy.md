---
title: "Real-World Workflow: End-to-End scRNA-seq Analysis with Scanpy (2024)"
date: "2026-08-13"
author: "Bioinformatics Workflow Hub"
category: "Single-cell RNA-seq"
excerpt: "A complete, production-ready single-cell RNA-seq pipeline using the scverse ecosystem (Scanpy). Covers standard QC, Leiden clustering, and marker gene identification on a 10x Genomics dataset."
image: "images/single-cell-analysis.png"
---

## From Raw Counts to Biological Insights

This tutorial demonstrates a modern (2024-2025), production-ready workflow for analyzing single-cell RNA-sequencing (scRNA-seq) data using **Scanpy** and the broader **scverse** Python ecosystem. 

We will walk through the standard steps required to transform raw 10x Genomics count matrices into annotated cell clusters, emphasizing community best practices for Quality Control (QC) and dimensionality reduction.

---

## 1. Environment Setup

First, ensure you have a clean environment with the necessary tools. Refer to our [Conda Guide](conda-bioinformatics-guide.md) if you need help with this step.

```bash
# Create and activate environment
mamba create -n scverse python=3.10 -c conda-forge
conda activate scverse

# Install the scverse stack
mamba install -c conda-forge scanpy anndata jupyter matplotlib seaborn leidenalg
```

Launch Jupyter Notebook and import the libraries:

```python
import scanpy as sc
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set scanpy plotting defaults (makes plots look publication-ready)
sc.settings.verbosity = 3
sc.settings.set_figure_params(dpi=100, facecolor='white')
```

---

## 2. Loading the Data

We will use a standard 10x Genomics output folder. The `read_10x_mtx` function efficiently loads the sparse matrix into an `AnnData` object, which is the foundational data structure of the scverse ecosystem.

```python
# Path to your 10x output directory containing matrix.mtx, barcodes.tsv, genes.tsv
data_dir = './data/10x_pbmc3k/filtered_gene_bc_matrices/hg19/'

# Load data
adata = sc.read_10x_mtx(
    data_dir,
    var_names='gene_symbols',  # Use gene symbols for variables (columns)
    cache=True                 # Cache data for faster subsequent loading
)

# Ensure gene names are unique
adata.var_names_make_unique()

print(adata)
# Output: AnnData object with n_obs × n_vars = 2700 × 32738
```
*Here, `n_obs` represents the number of cells (2,700) and `n_vars` represents the number of genes (32,738).*

---

## 3. Quality Control (QC)

QC is critical to remove dying cells, empty droplets, and multiplets (two cells trapped in one droplet). 

We assess quality using three primary metrics:
1. **Total counts (UMIs) per cell**: High counts may indicate doublets; very low counts indicate empty droplets.
2. **Number of genes expressed per cell**: Follows the same logic as total counts.
3. **Mitochondrial gene fraction**: Dying cells often leak cytoplasmic RNA, leaving behind a high proportion of mitochondrial transcripts.

```python
# Identify mitochondrial genes (starting with 'MT-' or 'mt-')
adata.var['mt'] = adata.var_names.str.startswith('MT-')

# Calculate QC metrics (adds total_counts, n_genes_by_counts, pct_counts_mt to adata.obs)
sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], percent_top=None, log1p=False, inplace=True)

# Visualize QC metrics as violin plots
sc.pl.violin(adata, ['n_genes_by_counts', 'total_counts', 'pct_counts_mt'],
             jitter=0.4, multi_panel=True)
```

**Applying the filters:**
*Thresholds should be determined by examining your specific plots, but standard heuristics are applied below.*

```python
# Filter cells
sc.pp.filter_cells(adata, min_genes=200)       # Remove empty droplets
sc.pp.filter_cells(adata, max_genes=2500)      # Remove potential doublets
adata = adata[adata.obs.pct_counts_mt < 5, :]  # Remove dying cells

# Filter genes (remove genes expressed in fewer than 3 cells)
sc.pp.filter_genes(adata, min_cells=3)

print(adata)
# Output reflects the filtered dimensions (e.g., ~2600 cells × ~13700 genes)
```

---

## 4. Normalization and Log Transformation

Raw counts must be normalized to account for differences in sequencing depth across cells.

```python
# Save raw counts in a separate layer before modifying the main matrix
adata.layers["counts"] = adata.X.copy()

# Total-count normalize (library-size correct) the data matrix to 10,000 reads per cell
sc.pp.normalize_total(adata, target_sum=1e4)

# Logarithmize the data (log(x + 1))
sc.pp.log1p(adata)
```

---

## 5. Feature Selection: Highly Variable Genes (HVGs)

Most genes are not informative for distinguishing cell types. We identify highly variable genes to reduce computational burden and focus on biological signal.

```python
# Identify highly variable genes
sc.pp.highly_variable_genes(adata, min_mean=0.0125, max_mean=3, min_disp=0.5)

# Plot dispersion versus mean expression
sc.pl.highly_variable_genes(adata)

# Freeze the object state (keep only HVGs for downstream PCA/UMAP)
# We set raw to the normalized data so we can still plot expression of non-HVGs later
adata.raw = adata
adata = adata[:, adata.var.highly_variable]
```

---

## 6. Dimensionality Reduction

### PCA (Principal Component Analysis)
PCA is a linear transformation that captures the axes of greatest variation.

```python
# Scale the data to unit variance and zero mean (clips extreme outliers)
sc.pp.scale(adata, max_value=10)

# Run PCA
sc.tl.pca(adata, svd_solver='arpack')

# Plot variance ratio to determine how many PCs to keep (usually the 'elbow' point)
sc.pl.pca_variance_ratio(adata, log=True)
```

### The Neighborhood Graph and UMAP
We construct a neighborhood graph based on the first few Principal Components (usually 10-30), which is then used for both clustering (Leiden) and non-linear visualization (UMAP).

```python
# Compute the neighborhood graph (using the first 10 PCs)
sc.pp.neighbors(adata, n_neighbors=10, n_pcs=10)

# Compute UMAP
sc.tl.umap(adata)

# Visualize UMAP (currently uncolored)
sc.pl.umap(adata)
```

---

## 7. Clustering (Leiden Algorithm)

The **Leiden algorithm** has superseded the Louvain algorithm in modern workflows due to its improved guarantee of well-connected communities.

```python
# Run Leiden clustering (resolution controls the number of clusters)
# Higher resolution = more clusters
sc.tl.leiden(adata, resolution=0.5)

# Visualize clusters on the UMAP
sc.pl.umap(adata, color=['leiden'], legend_loc='on data')
```

---

## 8. Identifying Marker Genes

To annotate the biological identity of each Leiden cluster, we identify genes that are differentially expressed between clusters.

```python
# Rank genes for characterizing groups (uses Wilcoxon rank-sum test by default in modern scanpy)
sc.tl.rank_genes_groups(adata, 'leiden', method='wilcoxon')

# Plot the top 5 marker genes per cluster
sc.pl.rank_genes_groups(adata, n_genes=5, sharey=False)

# Extract marker genes into a pandas DataFrame for closer inspection
pd.DataFrame(adata.uns['rank_genes_groups']['names']).head(10)
```

### Visualizing Specific Markers

Once you identify potential markers (or if you have known canonical markers from literature), you can visualize their expression across the clusters to confirm cell identities.

```python
# Known canonical markers for PBMC populations
marker_genes = {
    'B-cell': ['CD79A', 'MS4A1'],
    'T-cell': ['CD3D', 'CD3E'],
    'CD8 T': ['CD8A', 'CD8B'],
    'NK': ['GNLY', 'NKG7'],
    'Myeloid': ['CST3', 'LYZ'],
    'Monocytes': ['FCGR3A', 'MS4A7']
}

# Dotplot is highly effective for visualizing marker specificity
sc.pl.dotplot(adata, marker_genes, groupby='leiden', dendrogram=True)
```

---

## 9. Cell Type Annotation

Based on the marker analysis, you map the numeric cluster IDs to biological annotations.

```python
# Dictionary mapping cluster numbers to cell types (example assignments)
new_cluster_names = {
    '0': 'CD4 T cells',
    '1': 'CD14+ Monocytes',
    '2': 'B cells',
    '3': 'CD8 T cells',
    '4': 'NK cells',
    '5': 'FCGR3A+ Monocytes',
    '6': 'Dendritic cells',
    '7': 'Megakaryocytes'
}

# Create a new column with the annotations
adata.obs['cell_type'] = adata.obs['leiden'].map(new_cluster_names).astype('category')

# Final UMAP with biological annotations
sc.pl.umap(adata, color='cell_type', legend_loc='on data', title='Annotated PBMC')
```

---

## 10. Saving the Results

Finally, save the processed, annotated `AnnData` object to disk. The `.h5ad` format is HDF5-based, highly compressed, and can be read natively in Python or converted to R objects via `reticulate` or `SeuratDisk`.

```python
# Save the results
adata.write('./data/pbmc3k_annotated.h5ad', compression='gzip')
```

## Next Steps

This tutorial covers a basic, single-sample workflow. In modern research, you will likely need to perform:
1. **Data Integration**: Combining samples from multiple donors or conditions (e.g., using `scVI` or `Harmony`).
2. **Pseudobulk Differential Expression**: Finding state differences between conditions.
3. **Trajectory Inference**: Mapping developmental changes.

*For advanced integration methods, see our [2024 Modern Methods Review](modern-bioinformatics-methods-2024.md).*
