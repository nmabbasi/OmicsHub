#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)
script_path <- if (length(args)) args[[1L]] else "sort_counts.R"
source(script_path, local = TRUE)

expect_error <- function(expr, pattern) {
  message <- tryCatch({ force(expr); NA_character_ }, error = function(e) conditionMessage(e))
  stopifnot(!is.na(message), grepl(pattern, message, ignore.case = TRUE))
}

tmp <- tempfile("copilot-r-test-")
dir.create(tmp)
on.exit(unlink(tmp, recursive = TRUE))
input <- file.path(tmp, "counts.tsv")
output <- file.path(tmp, "sorted.tsv")
writeLines(c("gene\tcount", "TP53\t12", "BRCA1\t8"), input, useBytes = TRUE)
original <- readBin(input, "raw", n = file.info(input)$size)
write_sorted_counts(input, output)
expected <- c("gene\tcount", "TP53\t12", "BRCA1\t8")
stopifnot(identical(readLines(output, warn = FALSE), expected))
stopifnot(identical(readBin(input, "raw", n = file.info(input)$size), original))

# A tie is stable: original input order is retained.
tie_input <- file.path(tmp, "ties.tsv")
tie_output <- file.path(tmp, "ties-sorted.tsv")
writeLines(c("gene\tcount", "first\t4", "second\t4", "lower\t2"), tie_input)
write_sorted_counts(tie_input, tie_output)
stopifnot(identical(readLines(tie_output, warn = FALSE)[-1L], c("first\t4", "second\t4", "lower\t2")))

invalid_cases <- list(
  blank_gene = c("gene\tcount", "\t2"),
  missing_count = c("gene\tcount", "TP53\t"),
  negative = c("gene\tcount", "TP53\t-1"),
  fractional = c("gene\tcount", "TP53\t1.5"),
  wrong_header = c("symbol\tcount", "TP53\t12"),
  ragged = c("gene\tcount", "TP53\t12\textra")
)
for (case in names(invalid_cases)) {
  bad <- file.path(tmp, paste0(case, ".tsv"))
  rejected_output <- file.path(tmp, paste0(case, "-out.tsv"))
  writeLines(invalid_cases[[case]], bad, useBytes = TRUE)
  before <- readBin(bad, "raw", n = file.info(bad)$size)
  expect_error(write_sorted_counts(bad, rejected_output), ".+")
  stopifnot(!file.exists(rejected_output))
  stopifnot(identical(readBin(bad, "raw", n = file.info(bad)$size), before))
}
expect_error(write_sorted_counts(input, input), "different")
cat("PASS: R sort, stable ties, validation, no invalid output, and input preservation.\n")
