args <- commandArgs(trailingOnly = TRUE)
workflow_path <- if (length(args)) args[[1L]] else "orchestrator_workflow.R"
source(workflow_path, local = TRUE)

expect_error <- function(expr, pattern) {
  message <- tryCatch({ force(expr); NA_character_ }, error = function(e) conditionMessage(e))
  stopifnot(!is.na(message), grepl(pattern, message, ignore.case = TRUE))
}

tmp <- tempfile("orchestrator-r-test-")
dir.create(tmp)
demo <- file.path(tmp, "demo")
make_demo(demo)
stopifnot(file.exists(file.path(demo, "counts.csv")), file.exists(file.path(demo, "counts_positive.csv")), file.exists(file.path(demo, "metadata.csv")))

# Reordered metadata remains correctly joined by sample_id.
metadata <- readLines(file.path(demo, "metadata.csv"), warn = FALSE)
writeLines(c(metadata[1L], rev(metadata[-1L])), file.path(demo, "metadata_reordered.csv"))
qc_out <- file.path(tmp, "qc")
run_workflow(file.path(demo, "counts.csv"), file.path(demo, "metadata_reordered.csv"), qc_out, "qc", 50, workflow_path)
qc <- read.csv(file.path(qc_out, "sample_qc.csv"), check.names = FALSE, stringsAsFactors = FALSE)
stopifnot(identical(qc$sample_id, c("S1", "S2", "S3")))
stopifnot(identical(qc$group, c("control", "case", "case")))
stopifnot(identical(as.numeric(qc$library_size), c(100, 100, 0)))
stopifnot(identical(as.integer(qc$detected_genes), c(2L, 3L, 0L)))
stopifnot(file.exists(file.path(qc_out, "manifest.json")), file.exists(file.path(qc_out, "plan.json")), file.exists(file.path(qc_out, "events.jsonl")), file.exists(file.path(qc_out, "report.md")))
manifest <- paste(readLines(file.path(qc_out, "manifest.json")), collapse = "\n")
stopifnot(grepl("deterministic_local_not_ai", manifest, fixed = TRUE), grepl("r_version", manifest, fixed = TRUE), grepl("counts_md5", manifest, fixed = TRUE))
events <- readLines(file.path(qc_out, "events.jsonl"), warn = FALSE)
stopifnot(any(grepl("needs_human_review", events, fixed = TRUE)))

cpm_out <- file.path(tmp, "cpm")
run_workflow(file.path(demo, "counts_positive.csv"), file.path(demo, "metadata.csv"), cpm_out, "normalize", 50, workflow_path)
cpm <- read.csv(file.path(cpm_out, "cpm.csv"), check.names = FALSE, stringsAsFactors = FALSE)
stopifnot(identical(names(cpm), c("gene_id", "S1", "S2", "S3")))
stopifnot(max(abs(colSums(cpm[-1L]) - 1e6)) < 0.01)

zero_out <- file.path(tmp, "zero-failure")
expect_error(run_workflow(file.path(demo, "counts.csv"), file.path(demo, "metadata.csv"), zero_out, "normalize", 50, workflow_path), "zero-library")
stopifnot(file.exists(file.path(zero_out, "sample_qc.csv")), !file.exists(file.path(zero_out, "cpm.csv")))
stopifnot(any(grepl('"status":"failed"', readLines(file.path(zero_out, "events.jsonl")), fixed = TRUE)))
expect_error(run_workflow(file.path(demo, "counts.csv"), file.path(demo, "metadata.csv"), qc_out, "qc", 50, workflow_path), "overwrite")

bad_counts <- file.path(tmp, "fractional.csv")
writeLines(c("gene_id,S1,S2", "GENE1,1.5,3"), bad_counts)
expect_error(load_inputs(bad_counts, file.path(demo, "metadata.csv")), "integer")
bad_metadata <- file.path(tmp, "mismatch.csv")
writeLines(c("sample_id,group", "S1,control", "S2,case", "OTHER,case"), bad_metadata)
expect_error(load_inputs(file.path(demo, "counts.csv"), bad_metadata), "exactly match")

unlink(tmp, recursive = TRUE)
cat("PASS: R workflow demo, QC, metadata join, CPM, provenance, and safe failures.\n")
