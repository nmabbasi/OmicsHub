#!/usr/bin/env Rscript
# Sort the Copilot lesson's synthetic gene/count TSV. Base R only.

split_tsv_fields <- function(line) {
  fields <- strsplit(paste0(line, "\t.__END__"), "\t", fixed = TRUE)[[1L]]
  fields[-length(fields)]
}

read_counts <- function(path) {
  if (!file.exists(path) || dir.exists(path)) stop("Input must be an existing file.", call. = FALSE)
  lines <- tryCatch(readLines(path, warn = FALSE, encoding = "UTF-8"),
                    error = function(e) stop("Could not read input as text: ", conditionMessage(e), call. = FALSE))
  if (length(lines) < 2L) stop("Expected a header and at least one data row.", call. = FALSE)
  header <- split_tsv_fields(lines[[1L]])
  if (!identical(header, c("gene", "count"))) stop("Header must be exactly gene<TAB>count.", call. = FALSE)
  rows <- lapply(seq.int(2L, length(lines)), function(i) {
    fields <- split_tsv_fields(lines[[i]])
    if (length(fields) != 2L) stop(sprintf("Line %d must contain exactly two tab-separated fields.", i), call. = FALSE)
    if (!nzchar(fields[[1L]])) stop(sprintf("Line %d has a blank gene name.", i), call. = FALSE)
    if (!grepl("^[0-9]+$", fields[[2L]], perl = TRUE)) {
      stop(sprintf("Line %d count must be a nonnegative whole number.", i), call. = FALSE)
    }
    value <- as.numeric(fields[[2L]])
    if (!is.finite(value) || value > 2^53) stop(sprintf("Line %d count is outside the exact numeric range supported here.", i), call. = FALSE)
    data.frame(gene = fields[[1L]], count = value, original_order = i, stringsAsFactors = FALSE)
  })
  do.call(rbind, rows)
}

sort_counts <- function(input_path) {
  counts <- read_counts(input_path)
  counts <- counts[order(-counts$count, counts$original_order), c("gene", "count"), drop = FALSE]
  counts$count <- format(counts$count, scientific = FALSE, trim = TRUE, digits = 15)
  counts
}

write_sorted_counts <- function(input_path, output_path) {
  input <- normalizePath(input_path, mustWork = TRUE)
  output <- normalizePath(output_path, mustWork = FALSE)
  if (identical(input, output)) stop("Input and output paths must be different.", call. = FALSE)
  if (file.exists(output) || dir.exists(output)) stop("Refusing to overwrite an existing output.", call. = FALSE)
  parent <- dirname(output)
  if (!dir.exists(parent)) stop("Output folder must already exist.", call. = FALSE)
  result <- sort_counts(input)
  lines <- c("gene\tcount", paste(result$gene, result$count, sep = "\t"))
  temporary <- tempfile(pattern = ".sort-counts-", tmpdir = parent)
  on.exit(if (file.exists(temporary)) unlink(temporary), add = TRUE)
  writeLines(lines, temporary, useBytes = TRUE)
  if (!file.rename(temporary, output)) stop("Could not move the completed result into place.", call. = FALSE)
  invisible(output)
}

main <- function(args) {
  if (length(args) != 2L) {
    cat("Usage: Rscript sort_counts.R INPUT.tsv OUTPUT.tsv\n", file = stderr())
    return(2L)
  }
  tryCatch({
    write_sorted_counts(args[[1L]], args[[2L]])
    cat("Wrote validated rows sorted by count descending; ties keep input order.\n")
    0L
  }, error = function(e) {
    cat("REJECT: ", conditionMessage(e), "\n", sep = "", file = stderr())
    1L
  })
}

if (sys.nframe() == 0L && !interactive()) quit(status = main(commandArgs(trailingOnly = TRUE)))
