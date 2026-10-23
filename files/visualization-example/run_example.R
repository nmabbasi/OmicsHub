#!/usr/bin/env Rscript
# Reproducible, deliberately synthetic example for the Omics Hub visualization tutorial.
# Run from the repository root: Rscript files/visualization-example/run_example.R
# Tested with the exact package versions recorded in run-evidence.txt.

SEED <- 20261023L
set.seed(SEED)

root <- normalizePath(getwd(), mustWork = TRUE)
example_dir <- file.path(root, "files", "visualization-example")
figure_dir <- file.path(root, "images", "tutorial-figures")
if (!file.exists(file.path(root, "tutorials", "advanced-visualization-packages.html"))) {
  stop("Run this script from the repository root.")
}
if (!requireNamespace("Seurat", quietly = TRUE) || !requireNamespace("ggplot2", quietly = TRUE)) {
  stop("This core example requires Seurat and ggplot2. SCpubr and dittoSeq are not required.")
}
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

# Deterministic toy counts: 48 cells, 36 features, three arbitrary labels.
# Marker-like count shifts are simulation parameters, not biological observations.
cell_types <- c("Type_A", "Type_B", "Type_C")
samples <- sprintf("Sample_%02d", 1:4)
metadata <- expand.grid(
  replicate = 1:4,
  sample_id = samples,
  cell_type = cell_types,
  KEEP.OUT.ATTRS = FALSE,
  stringsAsFactors = FALSE
)
metadata <- metadata[order(metadata$sample_id, metadata$cell_type, metadata$replicate), ]
metadata$condition <- ifelse(metadata$sample_id %in% samples[1:2], "Control", "Treated")
rownames(metadata) <- sprintf("cell_%03d", seq_len(nrow(metadata)))
metadata$replicate <- NULL

features <- sprintf("Gene%02d", 1:36)
lambda <- matrix(1.2, nrow = length(features), ncol = nrow(metadata),
                 dimnames = list(features, rownames(metadata)))
for (i in seq_along(cell_types)) {
  marker_rows <- ((i - 1L) * 4L + 1L):(i * 4L)
  cells <- metadata$cell_type == cell_types[i]
  lambda[marker_rows, cells] <- 6.0
}
# A small condition-associated shift is included only to make the fixture varied.
lambda[13:14, metadata$condition == "Treated"] <- 2.5
counts <- matrix(rpois(length(lambda), lambda = as.vector(lambda)),
                 nrow = nrow(lambda), dimnames = dimnames(lambda))

counts_path <- file.path(example_dir, "synthetic_counts.csv")
metadata_path <- file.path(example_dir, "synthetic_metadata.csv")
write.csv(data.frame(feature = rownames(counts), counts, check.names = FALSE),
          counts_path, row.names = FALSE, quote = FALSE)
write.csv(data.frame(cell = rownames(metadata), metadata, check.names = FALSE),
          metadata_path, row.names = FALSE, quote = FALSE)

# Reload the published fixture files so these are the actual inputs used below.
counts_table <- read.csv(counts_path, row.names = 1, check.names = FALSE)
metadata_table <- read.csv(metadata_path, row.names = 1, check.names = FALSE)
counts <- as.matrix(counts_table)
storage.mode(counts) <- "integer"
stopifnot(identical(colnames(counts), rownames(metadata_table)),
          all(counts >= 0), all(counts == floor(counts)),
          ncol(counts) == 48L, nrow(counts) == 36L,
          all(c("cell_type", "condition", "sample_id") %in% colnames(metadata_table)))

seurat_obj <- Seurat::CreateSeuratObject(counts = counts, meta.data = metadata_table,
                                         project = "synthetic_visualization_example",
                                         min.cells = 0, min.features = 0)
seurat_obj <- Seurat::NormalizeData(seurat_obj, verbose = FALSE)
seurat_obj <- Seurat::FindVariableFeatures(seurat_obj, selection.method = "vst",
                                          nfeatures = 24, verbose = FALSE)
seurat_obj <- Seurat::ScaleData(seurat_obj, features = Seurat::VariableFeatures(seurat_obj),
                                verbose = FALSE)
seurat_obj <- Seurat::RunPCA(seurat_obj, features = Seurat::VariableFeatures(seurat_obj),
                             npcs = 8, verbose = FALSE)
set.seed(SEED)
seurat_obj <- Seurat::RunUMAP(seurat_obj, reduction = "pca", dims = 1:8,
                              n.neighbors = 12, min.dist = 0.3, seed.use = SEED,
                              verbose = FALSE)

p_umap <- Seurat::DimPlot(seurat_obj, reduction = "umap", group.by = "cell_type",
                          pt.size = 1.5) +
  ggplot2::labs(title = "Synthetic cells by assigned label", subtitle = "Toy data; no biological inference")
p_feature <- Seurat::FeaturePlot(seurat_obj, features = "Gene01", reduction = "umap",
                                 cols = c("#E9EEF2", "#8A3FFC"), order = TRUE) +
  ggplot2::labs(title = "Synthetic Gene01 counts after normalization")
p_dot <- Seurat::DotPlot(seurat_obj, features = sprintf("Gene%02d", 1:6),
                         group.by = "cell_type") +
  ggplot2::labs(title = "Toy-feature summary by assigned label", x = "Feature", y = "Label")

composition <- as.data.frame(table(sample_id = seurat_obj$sample_id,
                                   cell_type = seurat_obj$cell_type),
                             stringsAsFactors = FALSE)
composition$proportion <- ave(composition$Freq, composition$sample_id,
                              FUN = function(x) x / sum(x))
p_composition <- ggplot2::ggplot(composition,
  ggplot2::aes(x = sample_id, y = proportion, fill = cell_type)) +
  ggplot2::geom_col(width = 0.78, color = "white", linewidth = 0.25) +
  ggplot2::scale_y_continuous(labels = scales::percent, limits = c(0, 1),
                              expand = c(0, 0)) +
  ggplot2::scale_fill_manual(values = c(Type_A = "#0072B2", Type_B = "#D55E00", Type_C = "#009E73")) +
  ggplot2::labs(title = "Synthetic cell-label proportions by sample",
                subtitle = "Balanced by construction; not measured sample composition",
                x = "Synthetic sample", y = "Fraction of toy cells", fill = "Assigned label") +
  ggplot2::theme_minimal(base_size = 11) +
  ggplot2::theme(panel.grid.major.x = ggplot2::element_blank())

outputs <- c(
  umap = file.path(figure_dir, "visualization-synthetic-umap.png"),
  feature = file.path(figure_dir, "visualization-synthetic-feature.png"),
  dotplot = file.path(figure_dir, "visualization-synthetic-dotplot.png"),
  composition = file.path(figure_dir, "visualization-synthetic-composition.png")
)
ggplot2::ggsave(outputs[["umap"]], p_umap, width = 7.2, height = 5.2, dpi = 180, bg = "white")
ggplot2::ggsave(outputs[["feature"]], p_feature, width = 6.4, height = 5.2, dpi = 180, bg = "white")
ggplot2::ggsave(outputs[["dotplot"]], p_dot, width = 7.2, height = 4.6, dpi = 180, bg = "white")
ggplot2::ggsave(outputs[["composition"]], p_composition, width = 7.2, height = 4.6, dpi = 180, bg = "white")

captions <- c(
  "All panels use a deterministic, invented count matrix (36 features, 48 cells; seed 20261023), not a public or biological dataset.",
  "UMAP: cells are colored by arbitrary simulated labels after log-normalization, variable-feature selection, scaling, PCA, and UMAP. Axes and distances have no biological meaning; the embedding is not evidence of cell types or separation.",
  "Feature plot: Gene01 is a simulated feature shown from the Seurat normalized assay. Color is a display scale, not a measured biological effect.",
  "Dot plot: Seurat summarizes simulated feature expression by arbitrary label; dot size is the fraction detected and color summarizes average expression under Seurat's DotPlot scaling.",
  "Composition: each bar is the fraction of toy cells assigned to each label per synthetic sample. Counts were balanced by construction; these bars are not sample-level biological abundance estimates."
)
writeLines(captions, file.path(example_dir, "figure-captions.txt"))
writeLines(capture.output(sessionInfo()), file.path(example_dir, "session-info.txt"))
package_versions <- vapply(c("Seurat", "SeuratObject", "ggplot2", "uwot"), function(pkg) {
  if (requireNamespace(pkg, quietly = TRUE)) as.character(utils::packageVersion(pkg)) else "not installed"
}, character(1))
writeLines(c(paste("R", getRversion()), paste(names(package_versions), package_versions, sep = " ")),
           file.path(example_dir, "package-versions.txt"))
checksums <- tools::md5sum(c(counts_path, metadata_path, outputs))
relative_paths <- substring(names(checksums), nchar(root) + 2L)
writeLines(paste(relative_paths, unname(checksums)),
           file.path(example_dir, "run-checksums.txt"))
cat("Completed synthetic Seurat/ggplot2 example.\n")
cat("Seed:", SEED, "\n")
cat("Cells:", ncol(seurat_obj), " Features:", nrow(seurat_obj), "\n")
cat("Reductions:", paste(names(seurat_obj@reductions), collapse = ", "), "\n")
cat("Figures:\n", paste(outputs, collapse = "\n"), "\n")
cat("Package versions:\n", paste(names(package_versions), package_versions, collapse = "\n"), "\n")
