#!/usr/bin/env Rscript
# Reproducible public pbmcsca worked example: label transfer, SingleR, Harmony, and LISI.
# Uses only the supplied public SeuratData package; no private inputs or accuracy claims.
options(stringsAsFactors = FALSE, Seurat.object.assay.version = "v3")
Sys.setenv(OMP_NUM_THREADS = "1", OPENBLAS_NUM_THREADS = "1", MKL_NUM_THREADS = "1",
           VECLIB_MAXIMUM_THREADS = "1", NUMEXPR_NUM_THREADS = "1")

fail <- function(...) stop(sprintf(...), call. = FALSE)
parse_args <- function(args) {
  out <- list(data_package = NULL, output = NULL, expected_sha256 = NULL, force = FALSE)
  i <- 1L
  while (i <= length(args)) {
    a <- args[[i]]
    if (identical(a, "--force")) { out$force <- TRUE; i <- i + 1L; next }
    if (!a %in% c("--data-package", "--output", "--expected-sha256")) fail("Unknown argument: %s", a)
    if (i == length(args)) fail("Missing value after %s", a)
    key <- switch(a, "--data-package" = "data_package", "--output" = "output",
                  "--expected-sha256" = "expected_sha256")
    if (!is.null(out[[key]])) fail("Argument supplied more than once: %s", a)
    out[[key]] <- args[[i + 1L]]
    i <- i + 2L
  }
  if (is.null(out$data_package) || is.null(out$output))
    fail("Usage: Rscript run_example.R --data-package FILE --output DIR [--expected-sha256 SHA256] [--force]")
  out
}
args <- parse_args(commandArgs(trailingOnly = TRUE))
run_started <- proc.time()[["elapsed"]]
default_sha256 <- "5161e0e81ed72bb8d6f96b5cc776e04cce738600a3b439b1658fe648c2faf6cb"
checksum_source <- if (is.null(args$expected_sha256)) "pinned-in-script" else "command-line"
expected_sha256 <- if (is.null(args$expected_sha256)) default_sha256 else tolower(args$expected_sha256)
full_args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", full_args, value = TRUE)
if (length(file_arg) != 1L) fail("Cannot determine script source path")
source_path <- normalizePath(sub("^--file=", "", file_arg), mustWork = TRUE)
package_path <- normalizePath(args$data_package, mustWork = TRUE)
if (dir.exists(package_path)) fail("--data-package must name a file")
# Refuse output paths that overlap the source location, in either direction.
path_overlap <- function(a, b) identical(a, b) || startsWith(paste0(a, "/"), paste0(b, "/")) ||
  startsWith(paste0(b, "/"), paste0(a, "/"))
out_parent <- normalizePath(dirname(args$output), mustWork = TRUE)
out_path <- file.path(out_parent, basename(args$output))
if (path_overlap(source_path, out_path)) fail("Output directory may not equal, contain, or be inside the source file path")
if (file.exists(out_path) && !dir.exists(out_path)) fail("Output path exists and is not a directory")
if (!dir.exists(out_path)) dir.create(out_path, recursive = TRUE, showWarnings = FALSE)
if (length(list.files(out_path, all.files = TRUE, no.. = TRUE)) && !args$force)
  fail("Output directory is not empty; choose an empty directory or pass --force")
if (args$force) {
  # --force permits replacement of known generated files only; unrelated user files are retained.
  managed <- c("run_summary.json", "packages.csv", "sessionInfo.txt", "filtering_counts.csv",
               "annotation.csv", "annotation_per_cell.csv", "annotation_grouped_counts.csv", "annotation_label_counts.csv",
               "selected_cells.csv", "embeddings_pca.csv", "embeddings_harmony.csv", "umap_coordinates.csv",
               "lisi_per_cell.csv", "lisi_summary.csv", "lisi_by_label.csv", "lisi_paired_differences.csv",
               "marker_expression_per_cell.csv", "annotation_confusion.png", "marker_dotplot.png",
               "lisi_distributions.png", "umap_before_after.png")
  unlink(file.path(out_path, managed[file.exists(file.path(out_path, managed))]), force = TRUE)
}

required <- c("Seurat", "SeuratObject", "ggplot2", "SingleR", "scuttle", "scran", "harmony", "lisi", "jsonlite", "Matrix", "BiocParallel", "digest", "RhpcBLASctl")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) fail("Required R packages are missing: %s", paste(missing, collapse = ", "))
expected_versions <- c(R = "4.3.3", Seurat = "5.0.1", SeuratObject = "5.0.1",
                      ggplot2 = "3.4.4", SingleR = "2.4.1", scuttle = "1.12.0", scran = "1.30.2",
                      harmony = "1.2.3", lisi = "1.0", RhpcBLASctl = "0.23.42")
actual_versions <- c(R = as.character(getRversion()), vapply(names(expected_versions)[-1], function(p) as.character(utils::packageVersion(p)), character(1)))
version_mismatch <- names(expected_versions)[expected_versions != actual_versions[names(expected_versions)]]
if (length(version_mismatch)) {
  fail("Pinned runtime version mismatch: %s", paste(sprintf("%s=%s (expected %s)", version_mismatch,
    actual_versions[version_mismatch], expected_versions[version_mismatch]), collapse = "; "))
}
if (!grepl("^[[:xdigit:]]{64}$", expected_sha256)) fail("Expected SHA-256 must contain 64 hexadecimal characters")
package_sha256 <- digest::digest(file = package_path, algo = "sha256")
if (!identical(package_sha256, expected_sha256))
  fail("Data package SHA-256 mismatch: observed %s", package_sha256)
# Package extraction is install-free and isolated; do not attach it or update any system library.
tar_listing <- tryCatch(utils::untar(package_path, list = TRUE), error = function(e) fail("Invalid data package archive: %s", conditionMessage(e)))
if (!all(c("pbmcsca.SeuratData/DESCRIPTION", "pbmcsca.SeuratData/data/pbmcsca.rda") %in% tar_listing))
  fail("Archive is not the expected SeuratData pbmcsca package (DESCRIPTION/data entry missing)")
if (any(grepl("(^/|(^|/)\\.\\.(/|$))", tar_listing))) fail("Unsafe path found in data package archive")
extract_dir <- tempfile("pbmcsca-public-")
dir.create(extract_dir)
utils::untar(package_path, files = c("pbmcsca.SeuratData/DESCRIPTION", "pbmcsca.SeuratData/data/pbmcsca.rda"), exdir = extract_dir)
desc <- read.dcf(file.path(extract_dir, "pbmcsca.SeuratData", "DESCRIPTION"))
if (desc[1, "Package"] != "pbmcsca.SeuratData" || desc[1, "Version"] != "3.0.0")
  fail("Expected pbmcsca.SeuratData version 3.0.0; archive declares %s %s", desc[1, "Package"], desc[1, "Version"])
data_env <- new.env(parent = baseenv())
loaded_names <- load(file.path(extract_dir, "pbmcsca.SeuratData", "data", "pbmcsca.rda"), envir = data_env)
if (!"pbmcsca" %in% loaded_names) fail("Expected pbmcsca object was not found in package data")
unlink(extract_dir, recursive = TRUE, force = TRUE)
source_obj <- data_env$pbmcsca
if (!inherits(source_obj, "Seurat")) fail("The packaged pbmcsca object is not a Seurat object")

# Fixed deterministic selection and single-threaded execution.
seed <- 20261023L
RNGkind("L'Ecuyer-CMRG")
set.seed(seed)
if (requireNamespace("future", quietly = TRUE)) future::plan(future::sequential)
BiocParallel::register(BiocParallel::SerialParam())
if (requireNamespace("RhpcBLASctl", quietly = TRUE)) {
  try(RhpcBLASctl::blas_set_num_threads(1), silent = TRUE)
  try(RhpcBLASctl::omp_set_num_threads(1), silent = TRUE)
}

# Resolve exact grouping and supplied cell-type metadata, refusing ambiguous schemas.
meta <- source_obj[[]]
if (!"RNA" %in% SeuratObject::Assays(source_obj)) fail("Public object has no RNA assay")
group_aliases <- c("10x_Chromium_v2_A" = "10x Chromium (v2) A",
                   "10x_Chromium_v2_B" = "10x Chromium (v2) B",
                   "10x_Chromium_v3" = "10x Chromium (v3)")
normalize_group <- function(x) tolower(gsub("[^[:alnum:]]", "", x))
available_groups <- unique(as.character(meta$Method))
for (alias in names(group_aliases)) {
  matches <- available_groups[normalize_group(available_groups) == normalize_group(alias)]
  if (length(matches) != 1L) fail("Could not map requested group %s to one exact public Method value", alias)
  group_aliases[[alias]] <- matches[[1]]
}
all_groups <- unname(group_aliases)
group_candidates <- names(meta)[vapply(meta, function(x) all(all_groups %in% as.character(x)), logical(1))]
if ("Method" %in% group_candidates) group_col <- "Method" else if (length(group_candidates) == 1L) group_col <- group_candidates else
  fail("Could not uniquely identify the metadata column containing all expected groups %s; candidates: %s",
       paste(all_groups, collapse = ", "), paste(group_candidates, collapse = ", "))
label_candidates <- names(meta)[tolower(names(meta)) == "celltype"]
if (length(label_candidates) != 1L) fail("Expected one supplied CellType metadata column; found: %s", paste(label_candidates, collapse = ", "))
label_col <- label_candidates[[1]]
if (!"nFeature_RNA" %in% names(meta)) fail("Expected public nFeature_RNA metadata is absent")
meta$.__group <- as.character(meta[[group_col]])
meta$.__label <- trimws(as.character(meta[[label_col]]))
meta$.__feature_pass <- is.finite(as.numeric(meta$nFeature_RNA)) & as.numeric(meta$nFeature_RNA) > 200
meta$.__label_pass <- !is.na(meta$.__label) & nzchar(meta$.__label) &
  !tolower(meta$.__label) %in% c("unknown", "unassigned")
meta$.__in_scope <- meta$.__group %in% all_groups
if (anyDuplicated(rownames(meta))) fail("Source cell IDs are not unique")

# Retrieve public raw RNA counts only; the new objects below contain no inherited reductions or normalized values.
raw_counts <- SeuratObject::GetAssayData(source_obj, assay = "RNA", layer = "counts")
if (is.null(colnames(raw_counts)) || anyDuplicated(colnames(raw_counts))) fail("Raw RNA count matrix has missing or duplicate cell IDs")
if (!setequal(colnames(raw_counts), rownames(meta))) fail("Raw count matrix and source metadata cell IDs do not match")
if (any(!is.finite(raw_counts@x)) || any(raw_counts@x < 0)) fail("Raw counts contain invalid values")
meta <- meta[colnames(raw_counts), , drop = FALSE]
if (!identical(rownames(meta), colnames(raw_counts))) fail("Could not align source metadata to raw count columns")
detected_genes <- Matrix::colSums(raw_counts > 0)
if (!isTRUE(all.equal(as.numeric(detected_genes), as.numeric(meta$nFeature_RNA), check.attributes = FALSE)))
  fail("Supplied detected-gene metadata disagrees with the public raw RNA counts")

cap <- 80L
selection <- list()
filter_rows <- list()
stratum_labels <- sort(unique(meta$.__label[meta$.__label_pass & meta$.__in_scope]))
for (g in all_groups) {
  idxg <- which(meta$.__group == g)
  for (lab in stratum_labels) {
    ids_all <- rownames(meta)[idxg[meta$.__label[idxg] == lab]]
    feature_ids <- ids_all[meta[ids_all, ".__feature_pass"]]
    eligible <- feature_ids[meta[feature_ids, ".__label_pass"]]
    kept <- character(0)
    if (length(eligible)) {
      eligible <- sort(eligible, method = "radix")
      kept <- if (length(eligible) <= cap) eligible else sort(sample(eligible, cap), method = "radix")
    }
    if (g != all_groups[[2]] && length(kept)) selection[[g]] <- c(selection[[g]], kept)
    if (g == all_groups[[2]] && length(kept)) selection[["reference"]] <- c(selection[["reference"]], kept)
    filter_rows[[length(filter_rows) + 1L]] <- data.frame(
      group = g, supplied_CellType = lab, source_n = length(ids_all),
      nFeature_RNA_gt_200 = length(feature_ids), valid_label_n = sum(meta[ids_all, ".__label_pass"]),
      eligible_n = length(eligible), kept_n = length(kept), omitted_by_cap_n = length(eligible) - length(kept),
      stringsAsFactors = FALSE)
  }
  invalid_ids <- rownames(meta)[idxg[!meta$.__label_pass[idxg]]]
  low_feature_ids <- rownames(meta)[idxg[!meta$.__feature_pass[idxg]]]
  filter_rows[[length(filter_rows) + 1L]] <- data.frame(
    group = g, supplied_CellType = "[all labels / filters]", source_n = length(idxg),
    nFeature_RNA_gt_200 = sum(meta$.__feature_pass[idxg]), valid_label_n = sum(meta$.__label_pass[idxg]),
    eligible_n = sum(meta$.__feature_pass[idxg] & meta$.__label_pass[idxg]),
    kept_n = sum(vapply(filter_rows, function(z) if (identical(z$group[1], g) && z$supplied_CellType[1] != "[all labels / filters]") z$kept_n else 0L, integer(1))),
    omitted_by_cap_n = NA_integer_, stringsAsFactors = FALSE)
  # Explicit omission totals by reasons; labels with no valid observations are not invented.
  attr(filter_rows[[length(filter_rows)]], "invalid_label_n") <- length(invalid_ids)
  attr(filter_rows[[length(filter_rows)]], "low_feature_n") <- length(low_feature_ids)
}
query_ids <- sort(unique(unlist(selection[all_groups[-2]], use.names = FALSE)), method = "radix")
reference_ids <- sort(unique(selection[["reference"]]), method = "radix")
if (!length(query_ids) || !length(reference_ids)) fail("Filtering left no query cells or no reference cells")
if (length(intersect(query_ids, reference_ids))) fail("Reference and query cell IDs overlap")
if (!identical(query_ids, sort(query_ids, method = "radix"))) fail("Query cell IDs are not uniquely sorted")
if (anyDuplicated(query_ids) || anyDuplicated(reference_ids)) fail("Selected cell IDs are duplicated")

# Report group-level as well as per-label filters, including invalid/low-feature omissions.
filter_table <- do.call(rbind, filter_rows)
filter_table$invalid_or_unknown_label_n <- NA_integer_
filter_table$low_feature_n <- NA_integer_
for (i in seq_len(nrow(filter_table))) {
  g <- filter_table$group[i]
  in_group <- which(meta$.__group == g)
  if (filter_table$supplied_CellType[i] == "[all labels / filters]") {
    filter_table$invalid_or_unknown_label_n[i] <- sum(!meta$.__label_pass[in_group])
    filter_table$low_feature_n[i] <- sum(!meta$.__feature_pass[in_group])
  }
}
utils::write.csv(filter_table, file.path(out_path, "filtering_counts.csv"), row.names = FALSE, na = "")

# Use identical ordered gene rows in both fresh classic assays; keep only raw counts at construction.
query_counts <- methods::as(raw_counts[, query_ids, drop = FALSE], "dgCMatrix")
reference_counts <- methods::as(raw_counts[, reference_ids, drop = FALSE], "dgCMatrix")
if (!identical(rownames(query_counts), rownames(reference_counts))) fail("Reference/query gene rows differ")
profile_hashes <- function(counts) vapply(seq_len(ncol(counts)), function(j) {
  column <- counts[, j, drop = FALSE]
  dimnames(column) <- NULL
  digest::digest(column, algo = "sha256")
}, character(1))
query_profile_hashes <- profile_hashes(query_counts)
reference_profile_hashes <- profile_hashes(reference_counts)
if (length(intersect(query_profile_hashes, reference_profile_hashes)))
  fail("An identical RNA profile occurs in both reference and query; the demonstration would leak reference information")
query_meta <- meta[query_ids, , drop = FALSE]
reference_meta <- meta[reference_ids, , drop = FALSE]
query_meta$source_label <- query_meta$.__label
query_meta$batch <- query_meta$.__group
query_meta$method_source_label <- paste(query_meta$batch, query_meta$source_label, sep = " | ")
reference_labels <- reference_meta$.__label
names(reference_labels) <- rownames(reference_meta)
selected_cells <- rbind(
  data.frame(cell_id = query_ids, role = "query", batch = query_meta$.__group,
    source_label = query_meta$.__label, detected_genes = query_meta$nFeature_RNA, counts_sha256 = query_profile_hashes),
  data.frame(cell_id = reference_ids, role = "reference", batch = reference_meta$.__group,
    source_label = reference_meta$.__label, detected_genes = reference_meta$nFeature_RNA, counts_sha256 = reference_profile_hashes))
utils::write.csv(selected_cells, file.path(out_path, "selected_cells.csv"), row.names = FALSE)
query <- SeuratObject::CreateSeuratObject(
  counts = SeuratObject::CreateAssayObject(counts = query_counts),
  meta.data = query_meta, project = "pbmcsca_public_query")
reference <- SeuratObject::CreateSeuratObject(
  counts = SeuratObject::CreateAssayObject(counts = reference_counts),
  meta.data = reference_meta, project = "pbmcsca_public_reference")
if (!identical(rownames(SeuratObject::GetAssayData(query, assay = "RNA", layer = "counts")),
               rownames(SeuratObject::GetAssayData(reference, assay = "RNA", layer = "counts")))) fail("Fresh RNA assay genes are not identical")

# Normalize both fresh objects. Reference PCA supports transfer; query variable features are set explicitly.
query <- Seurat::NormalizeData(query, normalization.method = "LogNormalize", scale.factor = 10000, verbose = FALSE)
query <- Seurat::FindVariableFeatures(query, selection.method = "vst", nfeatures = 2000, verbose = FALSE)
reference <- Seurat::NormalizeData(reference, normalization.method = "LogNormalize", scale.factor = 10000, verbose = FALSE)
reference <- Seurat::FindVariableFeatures(reference, selection.method = "vst", nfeatures = 2000, verbose = FALSE)
reference <- Seurat::ScaleData(reference, features = Seurat::VariableFeatures(reference), verbose = FALSE)
reference <- Seurat::RunPCA(reference, features = Seurat::VariableFeatures(reference), npcs = 20,
                            seed.use = seed, approx = TRUE, verbose = FALSE)

# Two distinct methods share one reference; their estimates are not independent evidence.
anchors <- Seurat::FindTransferAnchors(reference = reference, query = query,
  normalization.method = "LogNormalize", reference.reduction = "pca", dims = 1:20,
  features = Seurat::VariableFeatures(reference), verbose = FALSE)
transfer <- Seurat::TransferData(anchorset = anchors, refdata = reference_labels, dims = 1:20, verbose = FALSE)
if (!setequal(rownames(transfer), query_ids)) fail("Seurat transfer predictions do not match query cell IDs")
transfer <- transfer[query_ids, , drop = FALSE]
if (!all(c("predicted.id", "prediction.score.max") %in% colnames(transfer))) fail("Seurat transfer output lacks expected prediction fields")
query_norm <- SeuratObject::GetAssayData(query, assay = "RNA", layer = "data")
single <- SingleR::SingleR(test = query_norm, ref = SeuratObject::GetAssayData(reference, assay = "RNA", layer = "data"),
                           labels = reference_labels[colnames(SeuratObject::GetAssayData(reference, assay = "RNA", layer = "data"))],
                           de.method = "wilcox", fine.tune = TRUE, prune = TRUE)
if (is.null(rownames(single)) || !setequal(rownames(single), query_ids)) fail("SingleR result cell IDs do not match query IDs")
single <- single[query_ids, , drop = FALSE]
if (!all(c("labels", "pruned.labels", "delta.next") %in% colnames(single))) fail("SingleR output lacks expected label/pruning fields")
ann <- data.frame(cell_id = query_ids,
  group = query_meta[query_ids, ".__group"], source_label = query_meta[query_ids, ".__label"],
  SingleR_raw_label = as.character(single$labels),
  SingleR_pruned_label = ifelse(is.na(single$pruned.labels) | !nzchar(as.character(single$pruned.labels)), "Unassigned", as.character(single$pruned.labels)),
  SingleR_delta_next = as.numeric(single$delta.next),
  Seurat_predicted_label = as.character(transfer$predicted.id),
  Seurat_prediction_score_max = as.numeric(transfer$prediction.score.max), stringsAsFactors = FALSE)
if (anyNA(ann$cell_id) || anyDuplicated(ann$cell_id) || !identical(ann$cell_id, query_ids)) fail("Per-cell annotation row order/IDs failed validation")
utils::write.csv(ann, file.path(out_path, "annotation.csv"), row.names = FALSE, na = "")

# Descriptive disagreements only; supplied labels are not treated as truth or accuracy targets.
ann$SingleR_pruned_label <- as.character(ann$SingleR_pruned_label)
ann$Seurat_predicted_label <- as.character(ann$Seurat_predicted_label)
agr <- stats::aggregate(list(n = rep.int(1L, nrow(ann))),
  by = ann[c("group", "source_label", "SingleR_raw_label", "SingleR_pruned_label", "Seurat_predicted_label")], FUN = sum)
utils::write.csv(agr, file.path(out_path, "annotation_grouped_counts.csv"), row.names = FALSE)
label_counts <- do.call(rbind, lapply(c("source_label", "SingleR_raw_label", "SingleR_pruned_label", "Seurat_predicted_label"), function(field) {
  x <- if (field == "SingleR_pruned_label") as.character(ann[[field]]) else as.character(ann[[field]])
  x[is.na(x) | !nzchar(x)] <- "Unassigned"
  z <- as.data.frame(table(group = ann$group, label = x), stringsAsFactors = FALSE)
  z$label_source <- field
  z[z$Freq > 0, c("label_source", "group", "label", "Freq"), drop = FALSE]
}))
names(label_counts)[names(label_counts) == "Freq"] <- "n"
utils::write.csv(label_counts, file.path(out_path, "annotation_label_counts.csv"), row.names = FALSE)

# Confusion-style display is explicitly a descriptive comparison, not a benchmark.
conf <- as.data.frame(table(SingleR_pruned = ann$SingleR_pruned_label,
                            Seurat = ann$Seurat_predicted_label), stringsAsFactors = FALSE)
conf <- conf[conf$Freq > 0, , drop = FALSE]
p_conf <- ggplot2::ggplot(conf, ggplot2::aes(x = Seurat, y = SingleR_pruned, fill = Freq)) +
  ggplot2::geom_tile(color = "white", linewidth = 0.25) +
  ggplot2::geom_text(ggplot2::aes(label = Freq, color = Freq < 40), size = 3, show.legend = FALSE) +
  ggplot2::scale_color_manual(values = c("TRUE" = "white", "FALSE" = "#111827"), guide = "none") +
  ggplot2::scale_fill_viridis_c(option = "C", trans = "sqrt", name = "Cells") +
  ggplot2::labs(title = "Reference-label method comparison", subtitle = "SingleR pruned vs Seurat transfer; counts, not accuracy",
                x = "Seurat predicted label", y = "SingleR pruned label") +
  ggplot2::theme_minimal(base_size = 12) + ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 40, hjust = 1),
    panel.grid = ggplot2::element_blank(), plot.title = ggplot2::element_text(face = "bold"))
ggplot2::ggsave(file.path(out_path, "annotation_confusion.png"), p_conf,
                width = max(8, 1 + 0.9 * length(unique(conf$Seurat))), height = max(6, 1 + 0.65 * length(unique(conf$SingleR_pruned))),
                dpi = 180, bg = "white", limitsize = FALSE)

# Audit per-cell normalized RNA evidence for conventional lineage marker genes.
marker_candidates <- c("CD3D", "MS4A1", "LYZ", "NKG7", "PPBP")
markers <- intersect(marker_candidates, rownames(query_norm))
if (!length(markers)) fail("None of the requested RNA marker genes were found")
marker_matrix <- as.matrix(query_norm[markers, query_ids, drop = FALSE])
marker_long <- data.frame(cell_id = rep(query_ids, each = length(markers)),
  marker = rep(markers, times = length(query_ids)),
  normalized_log_expression = as.vector(marker_matrix),
  group = rep(query_meta[query_ids, ".__group"], each = length(markers)),
  source_label = rep(query_meta[query_ids, ".__label"], each = length(markers)), stringsAsFactors = FALSE)
utils::write.csv(marker_long, file.path(out_path, "marker_expression_per_cell.csv"), row.names = FALSE)
query$method_source_label <- factor(query_meta[colnames(query), "method_source_label"])
p_dot <- Seurat::DotPlot(query, features = markers, group.by = "method_source_label", assay = "RNA", scale = TRUE) +
  ggplot2::labs(title = "Public PBMC RNA marker evidence",
                subtitle = "Dot size: percent expressing; color: per-gene scaled average expression",
                x = "RNA marker", y = "Method | supplied CellType") +
  ggplot2::theme_minimal(base_size = 11) + ggplot2::theme(axis.text.y = ggplot2::element_text(size = 8),
    axis.text.x = ggplot2::element_text(angle = 35, hjust = 1), plot.title = ggplot2::element_text(face = "bold"),
    plot.title.position = "plot", plot.subtitle = ggplot2::element_text(size = 10))
ggplot2::ggsave(file.path(out_path, "marker_dotplot.png"), p_dot,
                width = 8, height = max(6, 0.34 * length(unique(query$method_source_label)) + 2),
                dpi = 180, bg = "white", limitsize = FALSE)

# Query-only integration comparison: one common normalized object, PCA baseline vs Harmony.
query_counts_before <- SeuratObject::GetAssayData(query, assay = "RNA", layer = "counts")
query <- Seurat::ScaleData(query, features = Seurat::VariableFeatures(query), verbose = FALSE)
query <- Seurat::RunPCA(query, features = Seurat::VariableFeatures(query), npcs = 20,
                        seed.use = seed, approx = TRUE, verbose = FALSE)
query <- harmony::RunHarmony(query, group.by.vars = "batch", reduction.use = "pca", dims.use = 1:20,
  theta = 2, lambda = 1, max_iter = 10, ncores = 1, verbose = TRUE)
if (!identical(colnames(query), query_ids)) fail("Harmony changed query cell order")
query_counts_after <- SeuratObject::GetAssayData(query, assay = "RNA", layer = "counts")
if (!isTRUE(all.equal(query_counts_before, query_counts_after, check.attributes = TRUE))) fail("RNA counts changed during integration")
if (!identical(rownames(query_counts_before), rownames(query_counts_after))) fail("RNA gene order changed during integration")
query <- Seurat::RunUMAP(query, reduction = "pca", dims = 1:20, reduction.name = "umap.pca",
                         reduction.key = "UMAPPCA_", n.neighbors = 30, min.dist = 0.3,
                         metric = "cosine", seed.use = seed, verbose = FALSE)
query <- Seurat::RunUMAP(query, reduction = "harmony", dims = 1:20, reduction.name = "umap.harmony",
                         reduction.key = "UMAPHARM_", n.neighbors = 30, min.dist = 0.3,
                         metric = "cosine", seed.use = seed, verbose = FALSE)

# LISI uses the shared ordered 20-D embeddings, never the 2-D UMAP coordinates.
perplexity <- 30
if (ncol(query) < 3 * perplexity + 1) fail("LISI requires at least %d query cells; observed %d", 3 * perplexity + 1, ncol(query))
lisi_metadata <- data.frame(batch = query_meta[query_ids, ".__group"],
                            source_label = query_meta[query_ids, ".__label"], row.names = query_ids)
if (!identical(rownames(lisi_metadata), query_ids) || anyNA(lisi_metadata)) fail("LISI metadata has missing or misaligned values")
get_lisi <- function(reduction_name, display_name) {
  emb <- SeuratObject::Embeddings(query, reduction = reduction_name)[, 1:20, drop = FALSE]
  if (!identical(rownames(emb), query_ids) || any(!is.finite(emb))) fail("Invalid or misaligned %s embedding", display_name)
  utils::write.csv(data.frame(cell_id = query_ids, emb, check.names = FALSE),
    file.path(out_path, paste0("embeddings_", tolower(display_name), ".csv")), row.names = FALSE)
  result <- lisi::compute_lisi(X = emb, meta_data = lisi_metadata,
    label_colnames = c("batch", "source_label"), perplexity = perplexity)
  result <- as.data.frame(result)
  if (nrow(result) != length(query_ids)) fail("LISI output row count differs from selected query cells")
  if (is.null(rownames(result)) || anyDuplicated(rownames(result)) || !setequal(rownames(result), query_ids))
    fail("LISI cell IDs are missing, duplicated, or do not match selected query cells")
  result <- result[query_ids, , drop = FALSE]
  if (any(!is.finite(as.matrix(result)))) fail("LISI returned missing or non-finite scores")
  batch_col <- grep("batch", names(result), ignore.case = TRUE, value = TRUE)
  source_col <- grep("source_label", names(result), ignore.case = TRUE, value = TRUE)
  if (length(batch_col) != 1L || length(source_col) != 1L) fail("Could not identify batch/source_label LISI score columns: %s", paste(names(result), collapse = ", "))
  data.frame(cell_id = query_ids, reduction = display_name,
    iLISI_batch = as.numeric(result[[batch_col]]), cLISI_source_label = as.numeric(result[[source_col]]),
    batch = lisi_metadata$batch, source_label = lisi_metadata$source_label, stringsAsFactors = FALSE)
}
lisi_pca <- get_lisi("pca", "PCA")
lisi_harmony <- get_lisi("harmony", "Harmony")
lisi_all <- rbind(lisi_pca, lisi_harmony)
utils::write.csv(lisi_all, file.path(out_path, "lisi_per_cell.csv"), row.names = FALSE)
lisi_summary <- do.call(rbind, lapply(c("iLISI_batch", "cLISI_source_label"), function(metric) {
  do.call(rbind, lapply(c("overall", "source_label", "batch"), function(stratum) {
    split_key <- if (stratum == "overall") rep("All query cells", nrow(lisi_all)) else lisi_all[[stratum]]
    groups <- split(seq_len(nrow(lisi_all)), interaction(lisi_all$reduction, split_key, drop = TRUE, lex.order = TRUE))
    do.call(rbind, lapply(groups, function(ii) {
      x <- lisi_all[[metric]][ii]
      data.frame(metric = metric, stratum = stratum, group = as.character(split_key[ii[1]]),
        reduction = as.character(lisi_all$reduction[ii[1]]), n = length(x), median = stats::median(x),
        q25 = unname(stats::quantile(x, .25)), q75 = unname(stats::quantile(x, .75)), stringsAsFactors = FALSE)
    }))
  }))
}))
utils::write.csv(lisi_summary, file.path(out_path, "lisi_summary.csv"), row.names = FALSE)
lisi_by_label <- lisi_summary[lisi_summary$stratum != "overall", , drop = FALSE]
utils::write.csv(lisi_by_label, file.path(out_path, "lisi_by_label.csv"), row.names = FALSE)
wide <- reshape(lisi_all, idvar = c("cell_id", "batch", "source_label"), timevar = "reduction", direction = "wide")
paired <- data.frame(cell_id = wide$cell_id, batch = wide$batch, source_label = wide$source_label,
  delta_iLISI_batch_Harmony_minus_PCA = wide$iLISI_batch.Harmony - wide$iLISI_batch.PCA,
  delta_cLISI_source_label_Harmony_minus_PCA = wide$cLISI_source_label.Harmony - wide$cLISI_source_label.PCA,
  stringsAsFactors = FALSE)
if (anyNA(paired)) fail("Paired PCA/Harmony LISI differences are incomplete")
utils::write.csv(paired, file.path(out_path, "lisi_paired_differences.csv"), row.names = FALSE)

lisi_plot_data <- rbind(data.frame(reduction = lisi_all$reduction, score_type = "Batch mixing (iLISI)", score = lisi_all$iLISI_batch),
                        data.frame(reduction = lisi_all$reduction, score_type = "Source-label diversity (cLISI)", score = lisi_all$cLISI_source_label))
lisi_plot_data$reduction <- factor(lisi_plot_data$reduction, levels = c("PCA", "Harmony"))
p_lisi <- ggplot2::ggplot(lisi_plot_data, ggplot2::aes(x = reduction, y = score, fill = reduction)) +
  ggplot2::geom_boxplot(width = 0.62, outlier.size = 0.35, linewidth = 0.35) +
  ggplot2::facet_wrap(~score_type, scales = "free_y", ncol = 2) +
  ggplot2::scale_fill_manual(values = c(PCA = "#5278A5", Harmony = "#D17A42")) +
  ggplot2::labs(title = "Per-cell LISI distributions", subtitle = "Scores computed in 20-D PCA/Harmony spaces; UMAP is not used for scoring", x = NULL, y = "LISI score") +
  ggplot2::theme_minimal(base_size = 12) + ggplot2::theme(legend.position = "none", panel.grid.minor = ggplot2::element_blank(),
    plot.title = ggplot2::element_text(face = "bold"))
ggplot2::ggsave(file.path(out_path, "lisi_distributions.png"), p_lisi, width = 9, height = 5.5, dpi = 180, bg = "white")

# Same UMAP algorithm/parameters/seeds, shown only as a qualitative 2-D illustration.
umap_frames <- list()
for (red in c("PCA", "Harmony")) {
  reduction_name <- if (red == "PCA") "umap.pca" else "umap.harmony"
  xy <- SeuratObject::Embeddings(query, reduction = reduction_name)
  if (!identical(rownames(xy), query_ids)) fail("UMAP cell IDs do not match query ordering")
  frame <- data.frame(cell_id = query_ids, UMAP_1 = xy[, 1], UMAP_2 = xy[, 2],
    batch = lisi_metadata$batch, source_label = lisi_metadata$source_label, reduction = red,
    stringsAsFactors = FALSE)
  for (color_field in c("batch", "source_label")) {
    part <- frame
    part$facet_row <- if (color_field == "batch") "Batch" else "Supplied source label"
    part$color_value <- part[[color_field]]
    umap_frames[[length(umap_frames) + 1L]] <- part
  }
}
umap_plot_data <- do.call(rbind, umap_frames)
umap_plot_data$reduction <- factor(umap_plot_data$reduction, levels = c("PCA", "Harmony"))
utils::write.csv(unique(umap_plot_data[, c("cell_id", "reduction", "UMAP_1", "UMAP_2", "batch", "source_label")]),
  file.path(out_path, "umap_coordinates.csv"), row.names = FALSE)
p_umap <- ggplot2::ggplot(umap_plot_data, ggplot2::aes(x = UMAP_1, y = UMAP_2, color = color_value)) +
  ggplot2::geom_point(size = 0.65, alpha = 0.9, stroke = 0) +
  ggplot2::facet_grid(facet_row ~ reduction, scales = "free") +
  ggplot2::labs(title = "Query UMAPs before and after Harmony", subtitle = "Same selected cells and UMAP settings; visualization only (LISI uses 20 dimensions)",
                x = "UMAP 1", y = "UMAP 2", color = NULL) +
  ggplot2::theme_minimal(base_size = 12) + ggplot2::theme(panel.grid = ggplot2::element_blank(),
    plot.title = ggplot2::element_text(face = "bold"), strip.text = ggplot2::element_text(face = "bold"),
    legend.position = "bottom", legend.key.height = grid::unit(3, "mm")) +
  ggplot2::guides(color = ggplot2::guide_legend(override.aes = list(size = 2.2, alpha = 1), nrow = 2))
ggplot2::ggsave(file.path(out_path, "umap_before_after.png"), p_umap,
                width = 12, height = 8, dpi = 180, bg = "white", limitsize = FALSE)

# Machine-readable run settings/summaries and software provenance; no private paths are emitted.
package_names <- c("Seurat", "SeuratObject", "ggplot2", "SingleR", "scuttle", "scran", "harmony", "lisi", "Matrix", "jsonlite", "BiocParallel", "RhpcBLASctl", "digest")
package_table <- data.frame(package = package_names,
  version = vapply(package_names, function(p) if (requireNamespace(p, quietly = TRUE)) as.character(utils::packageVersion(p)) else NA_character_, character(1)),
  stringsAsFactors = FALSE)
utils::write.csv(package_table, file.path(out_path, "packages.csv"), row.names = FALSE, na = "")
capture.output(utils::sessionInfo(), file = file.path(out_path, "sessionInfo.txt"))
paired_summary <- lapply(c("delta_iLISI_batch_Harmony_minus_PCA", "delta_cLISI_source_label_Harmony_minus_PCA"), function(nm) {
  x <- paired[[nm]]
  list(metric = nm, median = stats::median(x), q25 = unname(stats::quantile(x, .25)), q75 = unname(stats::quantile(x, .75)))
})
names(paired_summary) <- c("iLISI_batch", "cLISI_source_label")
summary <- list(
  dataset = list(package = desc[1, "Package"], version = desc[1, "Version"], sha256 = package_sha256,
                  expected_sha256 = expected_sha256, checksum_source = checksum_source, public_only = TRUE,
                  script_sha256 = digest::digest(file = source_path, algo = "sha256"),
                  reference_query_cell_ids_disjoint = TRUE, reference_query_count_profiles_disjoint = TRUE,
                  detected_gene_metadata_matches_counts = TRUE, rna_counts_unchanged = TRUE),
  runtime = list(R = as.character(getRversion()), seed = seed, rng_kind = RNGkind(), threads = 1L,
                 elapsed_seconds = unname(proc.time()[["elapsed"]] - run_started),
                 nfeatures = 2000L, pcs = 20L, harmony = list(group_by = "batch", theta = 2, lambda = 1, max_iter = 10L),
                 lisi_perplexity = perplexity, umap = list(n_neighbors = 30L, min_dist = 0.3, metric = "cosine", seed = seed)),
  metadata_columns = list(group = group_col, supplied_label = label_col),
  filter = list(feature_rule = "nFeature_RNA > 200", excluded_label_rule = "missing, empty, Unknown, or Unassigned", per_group_cell_type_cap = cap,
                selected_query_cells = length(query_ids), selected_reference_cells = length(reference_ids),
                query_group_counts = as.list(table(query_meta[query_ids, ".__group"])),
                requested_group_aliases_to_source_values = as.list(group_aliases),
                reference_source_group = unname(group_aliases[["10x_Chromium_v2_B"]]),
                query_groups = unname(group_aliases[c("10x_Chromium_v2_A", "10x_Chromium_v3")]),
                source_group_filter_counts = lapply(all_groups, function(g) {
                  ii <- which(meta$.__group == g)
                  list(group = g, source_n = length(ii), feature_pass_n = sum(meta$.__feature_pass[ii]),
                       label_pass_n = sum(meta$.__label_pass[ii]), eligible_n = sum(meta$.__feature_pass[ii] & meta$.__label_pass[ii]),
                       selected_n = sum((if (g == unname(group_aliases[["10x_Chromium_v2_B"]])) rownames(meta)[ii] %in% reference_ids else rownames(meta)[ii] %in% query_ids)))
                })),
  annotation = list(methods = c("Seurat FindTransferAnchors/TransferData", "SingleR de.method=wilcox"),
                    grouped_disagreement_cells = sum(ann$SingleR_pruned_label != ann$Seurat_predicted_label),
                    pruned_singleR_unassigned_n = sum(ann$SingleR_pruned_label == "Unassigned"),
                    note = "Descriptive agreement/disagreement only; no accuracy or ground-truth claim."),
  lisi = list(n_cells_per_embedding = length(query_ids), summary = lapply(c("PCA", "Harmony"), function(r) {
    x <- lisi_all[lisi_all$reduction == r, ]
    list(reduction = r, iLISI_batch_median = stats::median(x$iLISI_batch),
         iLISI_batch_q25 = unname(stats::quantile(x$iLISI_batch, .25)), iLISI_batch_q75 = unname(stats::quantile(x$iLISI_batch, .75)),
         cLISI_source_label_median = stats::median(x$cLISI_source_label),
         cLISI_source_label_q25 = unname(stats::quantile(x$cLISI_source_label, .25)), cLISI_source_label_q75 = unname(stats::quantile(x$cLISI_source_label, .75)))
  }), paired_difference_summary = paired_summary,
  note = "Descriptive medians, quartiles, and paired differences; no hypothesis tests."),
  markers = list(genes_present = markers, per_cell_evidence_file = "marker_expression_per_cell.csv"),
  caveats = c("Cell caps are deterministic and do not represent natural sample composition.",
              "UMAPs are illustrations only; LISI scores use the 20-dimensional embeddings.",
              "RPCA/CCA and scPred are not executed in this example."))
json <- jsonlite::toJSON(summary, auto_unbox = TRUE, pretty = TRUE, null = "null", na = "null", digits = NA)
writeLines(as.character(json), file.path(out_path, "run_summary.json"), useBytes = TRUE)
message("Completed public pbmcsca worked example. Selected query cells: ", length(query_ids),
        "; reference cells: ", length(reference_ids), "; output: ", out_path)
