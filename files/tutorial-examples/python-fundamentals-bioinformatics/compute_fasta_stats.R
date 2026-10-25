#!/usr/bin/env Rscript
# Read FASTA records, validate A/C/G/T/N after normalization, and write CSV.
# Usage: Rscript compute_fasta_stats.R INPUT.fasta OUTPUT.csv
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) {
  stop("Usage: Rscript compute_fasta_stats.R INPUT.fasta OUTPUT.csv", call. = FALSE)
}
input_path <- normalizePath(args[[1]], mustWork = TRUE)
output_path <- normalizePath(args[[2]], mustWork = FALSE)
if (identical(input_path, output_path)) {
  stop("Input and output paths must be different", call. = FALSE)
}

fasta_records <- function(path) {
  lines <- readLines(path, warn = FALSE, encoding = "UTF-8")
  records <- list()
  current_id <- NULL
  sequence_parts <- character()

  save_record <- function() {
    if (!is.null(current_id)) {
      records[[length(records) + 1L]] <<- list(
        id = current_id,
        sequence = paste(sequence_parts, collapse = "")
      )
    }
  }

  for (raw_line in lines) {
    line <- trimws(raw_line)
    if (!nzchar(line)) next
    if (startsWith(line, ">")) {
      save_record()
      current_id <- trimws(substring(line, 2L))
      if (!nzchar(current_id)) stop("FASTA header is empty", call. = FALSE)
      sequence_parts <- character()
    } else {
      if (is.null(current_id)) {
        stop("Sequence text found before the first FASTA header", call. = FALSE)
      }
      sequence_parts <- c(sequence_parts, line)
    }
  }
  save_record()
  records
}

normalize_sequence <- function(sequence) {
  toupper(gsub("[[:space:]]+", "", sequence, perl = TRUE))
}
valid_bases <- c("A", "C", "G", "T", "N")
records <- fasta_records(input_path)
rows <- lapply(records, function(record) {
  sequence <- normalize_sequence(record$sequence)
  valid <- nzchar(sequence) && all(strsplit(sequence, "", fixed = TRUE)[[1L]] %in% valid_bases)
  gc_text <- ""
  if (valid) {
    bases <- strsplit(sequence, "", fixed = TRUE)[[1L]]
    gc_text <- sprintf("%.5f", sum(bases %in% c("G", "C")) / length(bases))
  }
  data.frame(
    id = record$id,
    length = nchar(sequence, type = "chars"),
    gc_fraction = gc_text,
    valid = if (valid) "yes" else "no",
    stringsAsFactors = FALSE,
    check.names = FALSE
  )
})
result <- if (length(rows)) {
  do.call(rbind, rows)
} else {
  data.frame(id = character(), length = integer(), gc_fraction = character(),
             valid = character(), stringsAsFactors = FALSE)
}
output_dir <- dirname(output_path)
if (!dir.exists(output_dir) && !dir.create(output_dir, recursive = TRUE)) {
  stop("Could not create output directory: ", output_dir, call. = FALSE)
}
write.csv(result, output_path, row.names = FALSE, na = "", fileEncoding = "UTF-8")
