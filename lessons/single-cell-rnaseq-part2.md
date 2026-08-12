---
title: "Single-cell RNA-seq: Quality Control, Normalization, and Dimensionality Reduction"
date: "2025-08-12"
author: "OmicsHub Team"
category: "Single-cell RNA-seq"
excerpt: "Step-by-step guide to filtering low-quality cells, normalizing count data, selecting highly variable genes, and performing PCA and UMAP for visualization."
image: "images/single-cell-analysis.png"
---

## The scRNA-seq Analysis Workflow

### 1. Quality Control: Separating Good Cells from Bad

The first step in any scRNA-seq analysis is quality control. We need to identify and remove:

**Low-quality cells**:
- Cells with very few detected genes (empty droplets or dying cells)
- Cells with extremely high gene counts (potential doublets)

**High mitochondrial gene expression**:
- Often indicates stressed or dying cells
- Mitochondrial genes are well-captured, so high percentages suggest cytoplasmic RNA loss

```r
# Load libraries
library(Seurat)
library(ggplot2)
library(dplyr)

# Load 10x data
data <- Read10X(data.dir = "filtered_feature_bc_matrix/")
seurat_obj <- CreateSeuratObject(counts = data, project = "scRNA_analysis")

# Calculate QC metrics
seurat_obj[["percent.mt"]] <- PercentageFeatureSet(seurat_obj, pattern = "^MT-")
seurat_obj[["percent.ribo"]] <- PercentageFeatureSet(seurat_obj, pattern = "^RP[SL]")

# Visualize QC metrics
VlnPlot(seurat_obj, features = c("nFeature_RNA", "nCount_RNA", "percent.mt"), ncol = 3)

# Filter cells
seurat_obj <- subset(seurat_obj, subset = nFeature_RNA > 200 & nFeature_RNA < 5000 & percent.mt < 20)
```

### 2. Normalization: Making Cells Comparable

Raw count data needs normalization because:
- Different cells have different sequencing depths
- Technical factors affect capture efficiency
- We want to compare expression levels across cells

**Log-normalization** is the most common approach:
```r
# Normalize data
seurat_obj <- NormalizeData(seurat_obj, normalization.method = "LogNormalize", scale.factor = 10000)
```

**SCTransform** is a newer, more sophisticated method:
```r
# Alternative normalization
seurat_obj <- SCTransform(seurat_obj, vars.to.regress = "percent.mt")
```

### 3. Feature Selection: Finding Informative Genes

Not all genes are equally informative for distinguishing cell types. We identify highly variable genes (HVGs) that show more variation than expected by chance:

```r
# Find variable features
seurat_obj <- FindVariableFeatures(seurat_obj, selection.method = "vst", nfeatures = 2000)

# Plot variable features
top10 <- head(VariableFeatures(seurat_obj), 10)
plot1 <- VariableFeaturePlot(seurat_obj)
plot2 <- LabelPoints(plot = plot1, points = top10, repel = TRUE)
plot2
```

### 4. Scaling and Principal Component Analysis

Before dimensionality reduction, we scale the data to give equal weight to all genes:

```r
# Scale data
all.genes <- rownames(seurat_obj)
seurat_obj <- ScaleData(seurat_obj, features = all.genes)

# Run PCA
seurat_obj <- RunPCA(seurat_obj, features = VariableFeatures(object = seurat_obj))

# Visualize PCA
DimPlot(seurat_obj, reduction = "pca")
VizDimLoadings(seurat_obj, dims = 1:2, reduction = "pca")
```

### 5. Dimensionality Reduction: Visualizing High-dimensional Data

High-dimensional data is hard to visualize and analyze. We use dimensionality reduction techniques to project cells into 2D space while preserving important relationships:

**UMAP (Uniform Manifold Approximation and Projection)**:
```r
# Run UMAP
seurat_obj <- RunUMAP(seurat_obj, dims = 1:10)
DimPlot(seurat_obj, reduction = "umap")
```

**t-SNE (t-distributed Stochastic Neighbor Embedding)**:
```r
# Run t-SNE
seurat_obj <- RunTSNE(seurat_obj, dims = 1:10)
DimPlot(seurat_obj, reduction = "tsne")
```

### 6. Clustering: Identifying Cell Groups

Clustering groups cells with similar expression profiles:

```r
# Find neighbors
seurat_obj <- FindNeighbors(seurat_obj, dims = 1:10)

# Find clusters
seurat_obj <- FindClusters(seurat_obj, resolution = 0.5)

# Visualize clusters
DimPlot(seurat_obj, reduction = "umap", label = TRUE)
```

The `resolution` parameter controls cluster granularity:
- Lower values (0.1-0.3): Fewer, broader clusters
- Higher values (0.8-1.2): More, finer clusters

### 7. Marker Gene Discovery

Once we have clusters, we want to understand what makes each cluster unique:

```r
# Find markers for all clusters
cluster_markers <- FindAllMarkers(seurat_obj, only.pos = TRUE, min.pct = 0.25, logfc.threshold = 0.25)

# View top markers for cluster 0
cluster_markers %>% filter(cluster == 0) %>% head(10)

# Find markers for a specific cluster
cluster0_markers <- FindMarkers(seurat_obj, ident.1 = 0, min.pct = 0.25)

# Visualize marker expression
VlnPlot(seurat_obj, features = c("CD3D", "CD8A", "CD4"))
FeaturePlot(seurat_obj, features = c("CD3D", "CD8A", "CD4"))
```

### 8. Cell Type Annotation

The final step is assigning biological identities to clusters based on marker genes:

```r
# Manual annotation based on known markers
new.cluster.ids <- c("Naive CD4 T", "Memory CD4 T", "CD14+ Mono", "B", "CD8 T", 
                     "FCGR3A+ Mono", "NK", "DC", "Platelet")
names(new.cluster.ids) <- levels(seurat_obj)
seurat_obj <- RenameIdents(seurat_obj, new.cluster.ids)

# Visualize annotated clusters
DimPlot(seurat_obj, reduction = "umap", label = TRUE, pt.size = 0.5) + NoLegend()
```
