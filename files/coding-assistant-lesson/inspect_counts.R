#!/usr/bin/env Rscript
# Inspect the lesson's synthetic gene-by-sample count TSV. Base R only.

split_tsv_fields <- function(line) {
  fields <- strsplit(paste0(line, "\t.__END__"), "\t", fixed = TRUE)[[1L]]
  fields[-length(fields)]
}

read_count_table <- function(path) {
  if (!file.exists(path) || dir.exists(path)) stop("Input must be an existing file.", call. = FALSE)
  lines <- tryCatch(readLines(path, warn = FALSE, encoding = "UTF-8"),
                    error = function(e) stop("Could not read input as text: ", conditionMessage(e), call. = FALSE))
  if (length(lines) < 2L) stop("Expected a header and at least one gene row.", call. = FALSE)
  header <- split_tsv_fields(lines[[1L]])
  if (length(header) < 3L || header[[1L]] != "gene_id") {
    stop("Header must start with gene_id and contain at least one sample column.", call. = FALSE)
  }
  samples <- header[-1L]
  if (any(!nzchar(samples)) || anyDuplicated(samples)) stop("Sample names must be nonblank and unique.", call. = FALSE)
  genes <- character()
  values <- vector("list", length(lines) - 1L)
  for (i in seq.int(2L, length(lines))) {
    row <- split_tsv_fields(lines[[i]])
    if (length(row) != length(header)) stop(sprintf("Line %d has the wrong number of fields.", i), call. = FALSE)
    gene <- row[[1L]]
    if (!nzchar(gene) || gene %in% genes) stop(sprintf("Line %d has a blank or duplicate gene_id.", i), call. = FALSE)
    genes <- c(genes, gene)
    tokens <- row[-1L]
    if (any(!grepl("^[0-9]+$", tokens, perl = TRUE))) {
      stop(sprintf("Line %d contains a value that is not a nonnegative integer count.", i), call. = FALSE)
    }
    numbers <- as.numeric(tokens)
    if (any(!is.finite(numbers)) || any(numbers > 2^53)) {
      stop(sprintf("Line %d contains a count outside the exact numeric range supported here.", i), call. = FALSE)
    }
    values[[i - 1L]] <- numbers
  }
  matrix <- do.call(rbind, values)
  colnames(matrix) <- samples
  rownames(matrix) <- genes
  list(samples = samples, genes = genes, counts = matrix)
}

inspect_count_table <- function(path) {
  data <- read_count_table(path)
  totals <- colSums(data$counts)
  list(data = data, totals = totals, grand_total = sum(totals))
}

main <- function(args) {
  if (length(args) != 1L) {
    cat("Usage: Rscript inspect_counts.R counts.tsv\n", file = stderr())
    return(2L)
  }
  tryCatch({
    result <- inspect_count_table(args[[1L]])
    cat(sprintf("Orientation: rows=genes (%d); columns=samples (%d).\n", length(result$data$genes), length(result$data$samples)))
    for (sample in result$data$samples) cat(sprintf("%s column sum: %.0f\n", sample, result$totals[[sample]]))
    cat(sprintf("All-cell arithmetic sum: %.0f\n", result$grand_total))
    cat("These format and sum checks do not verify provenance, raw-count status, sample independence, or biological validity.\n")
    0L
  }, error = function(e) {
    cat("REJECT: ", conditionMessage(e), "\n", sep = "", file = stderr())
    1L
  })
}

if (sys.nframe() == 0L && !interactive()) quit(status = main(commandArgs(trailingOnly = TRUE)))
