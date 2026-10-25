#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)
script_path <- if (length(args) >= 1L) args[[1L]] else "inspect_counts.R"
fixture_path <- if (length(args) >= 2L) args[[2L]] else "counts.tsv"
source(script_path, local = TRUE)

result <- inspect_count_table(fixture_path)
stopifnot(identical(result$data$samples, c("sample_A", "sample_B")))
stopifnot(identical(result$data$genes, c("gene_alpha", "gene_beta", "gene_gamma")))
stopifnot(identical(unname(result$totals), c(16, 12)))
stopifnot(identical(result$grand_total, 28))

tmp <- tempfile("cursor-aider-r-test-")
dir.create(tmp)
invalid <- c(
  negative = "gene_id\tsample_A\tsample_B\ngene_alpha\t-1\t8",
  fractional = "gene_id\tsample_A\tsample_B\ngene_alpha\t1.5\t8",
  nan = "gene_id\tsample_A\tsample_B\ngene_alpha\tNaN\t8",
  ragged = "gene_id\tsample_A\tsample_B\ngene_alpha\t12",
  duplicate_gene = "gene_id\tsample_A\tsample_B\ngene_alpha\t12\t8\ngene_alpha\t0\t1",
  duplicate_sample = "gene_id\tsample_A\tsample_A\ngene_alpha\t12\t8"
)
for (case in names(invalid)) {
  path <- file.path(tmp, paste0(case, ".tsv"))
  writeLines(invalid[[case]], path, useBytes = TRUE)
  error <- tryCatch({ read_count_table(path); NA_character_ }, error = function(e) conditionMessage(e))
  stopifnot(!is.na(error))
}
unlink(tmp, recursive = TRUE)
cat("PASS: synthetic orientation/totals and invalid count-table rejection.\n")
