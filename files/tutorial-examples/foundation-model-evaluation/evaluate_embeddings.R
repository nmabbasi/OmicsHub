#!/usr/bin/env Rscript
# Evaluate supplied embeddings only. This script does not generate model embeddings.
MAX_CSV_BYTES <- 10 * 1024 * 1024
MAX_DISTANCE_TERMS <- 10000000

fail <- function(message) stop(message, call. = FALSE)

read_csv_strict <- function(path) {
  if (!file.exists(path)) fail(sprintf("Input does not exist: %s", path))
  size <- file.info(path)$size
  if (is.na(size) || size > MAX_CSV_BYTES) fail(sprintf("%s exceeds the 10 MiB teaching-example limit", path))
  tryCatch(
    read.csv(path, check.names = FALSE, stringsAsFactors = FALSE,
             colClasses = "character", na.strings = character(),
             fill = FALSE, comment.char = "", strip.white = FALSE,
             fileEncoding = "UTF-8"),
    error = function(e) fail(sprintf("%s is not a valid rectangular UTF-8 CSV: %s", path, conditionMessage(e)))
  )
}

load_embedding_inputs <- function(embeddings_path, metadata_path) {
  emb <- read_csv_strict(embeddings_path)
  meta <- read_csv_strict(metadata_path)
  if (anyDuplicated(names(emb)) || any(!nzchar(trimws(names(emb))))) fail("Embedding CSV headers must be unique and nonblank")
  if (anyDuplicated(names(meta)) || any(!nzchar(trimws(names(meta))))) fail("Metadata CSV headers must be unique and nonblank")
  if (!identical(names(meta), c("cell_id", "donor_id", "label", "split"))) {
    fail("Metadata columns must be exactly cell_id, donor_id, label, split")
  }
  if (!"cell_id" %in% names(emb)) fail("Embedding CSV requires exactly one cell_id column")
  dimensions <- setdiff(names(emb), "cell_id")
  if (!length(dimensions) || any(!grepl("^embedding_", dimensions))) {
    fail("Embeddings require one or more embedding_* dimension columns")
  }
  ids <- trimws(emb$cell_id)
  mids <- trimws(meta$cell_id)
  if (anyNA(ids) || any(!nzchar(ids)) || anyDuplicated(ids)) fail("Embeddings contain blank or duplicate cell_id values")
  if (anyNA(mids) || any(!nzchar(mids)) || anyDuplicated(mids)) fail("Metadata contain blank or duplicate cell_id values")
  if (!setequal(ids, mids)) {
    missing <- head(setdiff(mids, ids), 5)
    extra <- head(setdiff(ids, mids), 5)
    fail(sprintf("Cell ID mismatch: missing embeddings for [%s]; missing metadata for [%s]",
                 paste(missing, collapse = ","), paste(extra, collapse = ",")))
  }
  if (anyNA(meta$donor_id) || any(!nzchar(trimws(meta$donor_id))) ||
      anyNA(meta$label) || any(!nzchar(trimws(meta$label)))) {
    fail("donor_id and label must be nonblank for every cell")
  }
  meta$cell_id <- mids
  meta$donor_id <- trimws(meta$donor_id)
  meta$label <- trimws(meta$label)
  meta$split <- tolower(trimws(meta$split))
  if (anyNA(meta$split) || any(!meta$split %in% c("train", "test"))) fail("split must be train or test")
  coords <- as.matrix(data.frame(lapply(emb[dimensions], function(x) suppressWarnings(as.numeric(x))),
                                 check.names = FALSE))
  if (any(!is.finite(coords))) fail("Embedding values must be numeric and finite (no NaN or infinity)")
  rownames(coords) <- ids
  rownames(meta) <- meta$cell_id
  meta <- meta[ids, , drop = FALSE]
  train <- which(meta$split == "train")
  test <- which(meta$split == "test")
  if (!length(train) || !length(test)) fail("Need at least one reference train cell and one held-out test cell")
  overlap <- intersect(unique(meta$donor_id[train]), unique(meta$donor_id[test]))
  if (length(overlap)) fail(sprintf("Donor leakage: donor occurs in both train and test: %s", paste(sort(overlap), collapse = ", ")))
  list(coords = coords, meta = meta, train = train, test = test, dimensions = dimensions)
}

score_embeddings <- function(inputs, k = 3L) {
  if (length(k) != 1L || is.na(k) || !is.finite(k) || k < 1 || k != as.integer(k)) fail("k must be a positive integer")
  if (k > length(inputs$train)) fail(sprintf("k=%d exceeds reference size (%d)", k, length(inputs$train)))
  terms <- as.double(length(inputs$train)) * length(inputs$test) * ncol(inputs$coords)
  if (terms > MAX_DISTANCE_TERMS) fail("Training/evaluation limit exceeded: train cells x test cells x dimensions must be at most 10 million distance terms")
  predictions <- lapply(inputs$test, function(q) {
    delta <- sweep(inputs$coords[inputs$train, , drop = FALSE], 2, inputs$coords[q, ], "-")
    d2 <- rowSums(delta * delta)
    if (any(!is.finite(d2))) fail("Distance calculation overflowed; review/scale embedding values before evaluating")
    order_ix <- order(d2, rownames(inputs$coords)[inputs$train], method = "radix")
    nearest <- order_ix[seq_len(k)]
    neighbor_labels <- inputs$meta$label[inputs$train[nearest]]
    votes <- table(neighbor_labels)
    top <- sort(names(votes)[votes == max(votes)])
    data.frame(
      cell_id = rownames(inputs$coords)[q],
      donor_id = inputs$meta$donor_id[q],
      truth = inputs$meta$label[q],
      prediction = top[[1]],
      confidence_top_vote_fraction = max(votes) / k,
      tied_top_labels = paste(top, collapse = ";"),
      neighbor_ids = paste(rownames(inputs$coords)[inputs$train[nearest]], collapse = ";"),
      neighbor_distances_squared = paste(format(d2[nearest], digits = 17, scientific = TRUE), collapse = ";"),
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, predictions)
}

summarize_predictions <- function(predictions) {
  labels <- sort(unique(c(predictions$truth, predictions$prediction)))
  per_class <- lapply(labels, function(label) {
    tp <- sum(predictions$truth == label & predictions$prediction == label)
    support <- sum(predictions$truth == label)
    predicted <- sum(predictions$prediction == label)
    precision <- if (predicted) tp / predicted else 0
    recall <- if (support) tp / support else 0
    f1 <- if (precision + recall) 2 * precision * recall / (precision + recall) else 0
    data.frame(metric = "per_class_f1", group = label, n = support, value = f1)
  })
  accuracy <- mean(predictions$truth == predictions$prediction)
  macro_f1 <- mean(vapply(per_class, function(x) x$value, numeric(1)))
  overall <- data.frame(metric = c("accuracy", "macro_f1"), group = "all",
                        n = nrow(predictions), value = c(accuracy, macro_f1))
  donor <- do.call(rbind, lapply(sort(unique(predictions$donor_id)), function(d) {
    rows <- predictions$donor_id == d
    data.frame(metric = "donor_accuracy", group = d, n = sum(rows),
               value = mean(predictions$truth[rows] == predictions$prediction[rows]))
  }))
  do.call(rbind, c(list(overall), per_class, list(donor)))
}

run_evaluation <- function(embeddings_path, metadata_path, output_prefix, k = 3L) {
  inputs <- load_embedding_inputs(embeddings_path, metadata_path)
  predictions <- score_embeddings(inputs, k)
  metrics <- summarize_predictions(predictions)
  pred_path <- paste0(output_prefix, "_predictions.csv")
  metrics_path <- paste0(output_prefix, "_metrics.csv")
  if (file.exists(pred_path) || file.exists(metrics_path)) fail("Refusing to overwrite an existing prediction or metrics output")
  parent <- dirname(pred_path)
  if (!dir.exists(parent) && !dir.create(parent, recursive = TRUE)) fail(sprintf("Cannot create output directory: %s", parent))
  write.csv(predictions, pred_path, row.names = FALSE, na = "")
  write.csv(metrics, metrics_path, row.names = FALSE, na = "")
  invisible(list(predictions = predictions, metrics = metrics,
                 prediction_file = pred_path, metrics_file = metrics_path,
                 inference_performed = FALSE))
}

main <- function(args) {
  if (length(args) < 3 || length(args) > 4) {
    fail("Usage: Rscript evaluate_embeddings.R embeddings.csv metadata.csv output_prefix [k]")
  }
  k <- if (length(args) == 4) suppressWarnings(as.integer(args[[4]])) else 3L
  result <- run_evaluation(args[[1]], args[[2]], args[[3]], k)
  cat(sprintf("Wrote %s and %s (%d held-out cells; inference_performed=false)\n",
              result$prediction_file, result$metrics_file, nrow(result$predictions)))
}

if (sys.nframe() == 0L) {
  tryCatch(main(commandArgs(trailingOnly = TRUE)), error = function(e) {
    message("ERROR: ", conditionMessage(e))
    quit(status = 2L)
  })
}
