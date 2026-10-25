#!/usr/bin/env Rscript
# Bounded local teaching workflow for synthetic or user-supplied count matrices.
# Base R only. This deterministic workflow does not call a model or run generated code.

MAX_BYTES <- 2 * 1024 * 1024
MAX_GENES <- 10000L
MAX_SAMPLES <- 100L
ID_PATTERN <- "^[A-Za-z0-9][A-Za-z0-9_.-]*$"

workflow_error <- function(message) stop(structure(list(message = message), class = c("workflow_error", "error", "condition")))

json_string <- function(x) {
  x <- gsub("\\", "\\\\", as.character(x), fixed = TRUE)
  x <- gsub('"', '\\"', x, fixed = TRUE)
  x <- gsub("\n", "\\n", x, fixed = TRUE)
  paste0('"', x, '"')
}

write_event <- function(path, role, status, message) {
  line <- paste0('{"role":', json_string(role), ',"status":', json_string(status), ',"message":', json_string(message), '}')
  cat(line, "\n", file = path, append = TRUE, sep = "")
}

sha256_or_md5 <- function(path) {
  # Base R ships MD5, which is a content identifier for this lesson, not an integrity/security guarantee.
  unname(tools::md5sum(path))
}

read_csv_chars <- function(path, limit_bytes = MAX_BYTES) {
  if (!file.exists(path) || dir.exists(path)) workflow_error(sprintf("Input must be an existing file: %s", basename(path)))
  size <- file.info(path)$size
  if (is.na(size) || size > limit_bytes) workflow_error(sprintf("Input exceeds %d byte teaching limit: %s", limit_bytes, basename(path)))
  tryCatch(utils::read.csv(path, header = TRUE, check.names = FALSE, stringsAsFactors = FALSE,
                           colClasses = "character", na.strings = character(), strip.white = FALSE,
                           comment.char = "", fill = FALSE, fileEncoding = "UTF-8"),
           error = function(e) workflow_error(sprintf("Could not read valid UTF-8 CSV input: %s", conditionMessage(e))))
}

load_inputs <- function(counts_path, metadata_path) {
  counts <- read_csv_chars(counts_path)
  meta <- read_csv_chars(metadata_path)
  if (ncol(counts) < 3L || names(counts)[[1L]] != "gene_id") {
    workflow_error("Counts header must be gene_id followed by at least two sample IDs")
  }
  samples <- names(counts)[-1L]
  if (length(samples) > MAX_SAMPLES || any(!grepl(ID_PATTERN, samples, perl = TRUE)) || anyDuplicated(samples)) {
    workflow_error("Sample IDs must be unique simple IDs (letters, digits, _, ., -); maximum 100")
  }
  if (nrow(counts) < 1L || nrow(counts) > MAX_GENES) workflow_error("Counts require 1..10000 gene rows")
  genes <- counts[[1L]]
  if (any(!grepl(ID_PATTERN, genes, perl = TRUE)) || anyDuplicated(genes)) {
    workflow_error("Gene IDs must be unique simple IDs (letters, digits, _, ., -)")
  }
  tokens <- as.matrix(counts[-1L])
  if (any(!grepl("^[0-9]{1,12}$", tokens, perl = TRUE))) {
    workflow_error("Counts must be ASCII nonnegative integer values of at most 12 digits")
  }
  values <- matrix(as.numeric(tokens), nrow = nrow(tokens), ncol = ncol(tokens), dimnames = list(genes, samples))
  if (any(!is.finite(values))) workflow_error("Counts must be finite numeric values")

  if (!identical(names(meta), c("sample_id", "group"))) workflow_error("Metadata header must be exactly sample_id,group")
  ids <- meta$sample_id
  groups <- meta$group
  if (any(!grepl(ID_PATTERN, ids, perl = TRUE)) || any(!grepl(ID_PATTERN, groups, perl = TRUE)) || anyDuplicated(ids)) {
    workflow_error("Metadata rows need unique simple sample IDs and simple group labels")
  }
  if (!setequal(ids, samples) || length(ids) != length(samples)) {
    workflow_error("Metadata sample IDs must exactly match counts columns (order may differ)")
  }
  groups <- setNames(groups, ids)[samples]
  list(samples = samples, genes = genes, counts = values, groups = groups)
}

make_demo <- function(directory) {
  if (file.exists(directory)) workflow_error("Demo directory already exists; refusing to overwrite")
  if (!dir.create(directory, recursive = FALSE)) workflow_error("Could not create demo directory")
  writeLines(c("gene_id,S1,S2,S3", "GENE1,10,20,0", "GENE2,0,5,0", "GENE3,90,75,0", "GENE4,0,0,0"), file.path(directory, "counts.csv"), useBytes = TRUE)
  writeLines(c("gene_id,S1,S2,S3", "GENE1,10,20,5", "GENE2,0,5,0", "GENE3,90,75,45", "GENE4,0,0,0"), file.path(directory, "counts_positive.csv"), useBytes = TRUE)
  writeLines(c("sample_id,group", "S1,control", "S2,case", "S3,case"), file.path(directory, "metadata.csv"), useBytes = TRUE)
  invisible(directory)
}

write_qc <- function(path, input, totals, detected, min_library_size) {
  qc <- data.frame(sample_id = input$samples, group = unname(input$groups),
                   library_size = format(totals, scientific = FALSE, trim = TRUE, digits = 15),
                   detected_genes = as.integer(detected),
                   low_library_warning = ifelse(totals < min_library_size, "yes", "no"),
                   stringsAsFactors = FALSE, check.names = FALSE)
  utils::write.csv(qc, path, row.names = FALSE, quote = FALSE, na = "")
  qc
}

run_workflow <- function(counts_path, metadata_path, output_dir, task = "qc", min_library_size = 50,
                         script_path = NULL) {
  if (!task %in% c("qc", "normalize")) workflow_error("Task must be qc or normalize")
  if (length(min_library_size) != 1L || !is.finite(min_library_size) || min_library_size < 0) workflow_error("Minimum library size must be one nonnegative number")
  counts_path <- normalizePath(counts_path, mustWork = TRUE)
  metadata_path <- normalizePath(metadata_path, mustWork = TRUE)
  output_dir <- normalizePath(output_dir, mustWork = FALSE)
  if (file.exists(output_dir)) workflow_error("Output directory already exists; refusing overwrite")
  if (!dir.exists(dirname(output_dir))) workflow_error("Output parent directory must already exist")
  input <- load_inputs(counts_path, metadata_path)

  steps <- if (task == "qc") "qc" else c("qc", "cpm")
  if (!dir.create(output_dir)) workflow_error("Could not create output directory")
  log <- file.path(output_dir, "events.jsonl")
  write_event(log, "validator", "ok", "Inputs validated; metadata joined by sample_id")
  tryCatch({
    plan <- paste0('{"steps":[', paste(vapply(steps, json_string, character(1)), collapse = ","), ']}')
    writeLines(plan, file.path(output_dir, "plan.json"), useBytes = TRUE)
    write_event(log, "planner", "ok", "Deterministic local plan; no AI or provider call")
    if (is.null(script_path)) {
      file_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
      script_path <- if (length(file_arg)) sub("^--file=", "", file_arg[[1L]]) else "orchestrator_workflow.R"
    }
    script_path <- normalizePath(script_path, mustWork = TRUE)
    manifest <- paste0("{\n",
      '  "counts_md5": ', json_string(sha256_or_md5(counts_path)), ",\n",
      '  "metadata_md5": ', json_string(sha256_or_md5(metadata_path)), ",\n",
      '  "script_md5": ', json_string(sha256_or_md5(script_path)), ",\n",
      '  "r_version": ', json_string(R.version.string), ",\n",
      '  "task": ', json_string(task), ",\n",
      '  "min_library_size": ', format(min_library_size, scientific = FALSE, trim = TRUE), ",\n",
      '  "planner_mode": "deterministic_local_not_ai"\n}\n')
    writeLines(manifest, file.path(output_dir, "manifest.json"), useBytes = TRUE)
    totals <- colSums(input$counts)
    detected <- colSums(input$counts > 0)
    qc <- write_qc(file.path(output_dir, "sample_qc.csv"), input, totals, detected, min_library_size)
    # Recompute totals independently from the written table before marking QC complete.
    qc_check <- utils::read.csv(file.path(output_dir, "sample_qc.csv"), check.names = FALSE, stringsAsFactors = FALSE)
    if (!identical(as.character(qc_check$sample_id), input$samples) ||
        !identical(as.numeric(qc_check$library_size), as.numeric(colSums(input$counts))) ||
        !identical(as.integer(qc_check$detected_genes), as.integer(colSums(input$counts > 0)))) {
      workflow_error("QC review failed: written values differ from validated input")
    }
    write_event(log, "executor", "ok", "Descriptive QC completed; no samples removed")
    cpm_status <- "not requested"
    if (task == "normalize") {
      if (any(totals <= 0)) workflow_error("CPM is undefined for a zero-library sample; inspect the QC output and input")
      cpm <- sweep(input$counts, 2L, totals, "/") * 1e6
      if (any(!is.finite(cpm)) || any(cpm < 0) || any(abs(colSums(cpm) - 1e6) > 0.01)) {
        workflow_error("CPM review failed: values must be finite, nonnegative, and sum to approximately one million per column")
      }
      cpm_frame <- data.frame(gene_id = input$genes, as.data.frame(cpm, check.names = FALSE), check.names = FALSE)
      names(cpm_frame) <- c("gene_id", input$samples)
      utils::write.csv(cpm_frame, file.path(output_dir, "cpm.csv"), row.names = FALSE, quote = FALSE)
      cpm_status <- "passed (finite, nonnegative; each column sums to approximately 1,000,000)"
      write_event(log, "executor", "ok", "Descriptive CPM completed")
    }
    warning_samples <- input$samples[totals < min_library_size]
    warning_text <- if (length(warning_samples)) paste(warning_samples, collapse = ", ") else "None"
    table_lines <- c("| Sample | Group | Count-column total | Detected genes | Low-library warning |", "|---|---|---:|---:|---:|")
    for (i in seq_along(input$samples)) table_lines <- c(table_lines, sprintf("| %s | %s | %.0f | %d | %s |", input$samples[[i]], input$groups[[i]], totals[[i]], detected[[i]], qc$low_library_warning[[i]]))
    report <- c("# Educational count workflow", "", "Status: **NEEDS_HUMAN_REVIEW**", "", table_lines,
      "", sprintf("Warnings (threshold: %s counts): %s. Warnings flag observations for investigation; samples are not removed.", min_library_size, warning_text), "",
      paste0("CPM review: ", cpm_status, "."), "",
      "This workflow reports the supplied count matrix. Included demo fixtures are synthetic; arbitrary user inputs are not presumed synthetic. This is descriptive QC/CPM only: no differential expression or biological validation is performed. A human must verify identities, units, data suitability, and conclusions.", "")
    writeLines(report, file.path(output_dir, "report.md"), useBytes = TRUE)
    write_event(log, "reviewer", "needs_human_review", "Numerical output checks passed; human review still required")
    invisible(output_dir)
  }, error = function(e) {
    write_event(log, "workflow", "failed", conditionMessage(e))
    stop(e)
  })
}

parse_args <- function(args) {
  options <- list(task = "qc", min_library_size = 50)
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key == "--help" || key == "-h") return("help")
    if (key == "--make-demo") {
      i <- i + 1L
      if (i > length(args)) workflow_error("--make-demo requires a directory")
      options$make_demo <- args[[i]]
    } else if (key %in% c("--counts", "--metadata", "--out", "--task", "--min-library-size")) {
      i <- i + 1L
      if (i > length(args)) workflow_error(sprintf("%s requires a value", key))
      value <- args[[i]]
      name <- switch(key, "--counts" = "counts", "--metadata" = "metadata", "--out" = "out", "--task" = "task", "--min-library-size" = "min_library_size")
      options[[name]] <- if (key == "--min-library-size") suppressWarnings(as.numeric(value)) else value
    } else workflow_error(sprintf("Unknown option: %s", key))
    i <- i + 1L
  }
  options
}

main <- function(args) {
  tryCatch({
    options <- parse_args(args)
    if (identical(options, "help")) {
      cat("Usage: Rscript orchestrator_workflow.R --make-demo DIR\n",
          "   or: Rscript orchestrator_workflow.R --counts FILE --metadata FILE --out DIR [--task qc|normalize] [--min-library-size N]\n",
          "Base R only. No AI planner, network call, package install, or generated-code execution.\n", sep = "")
      return(invisible(0L))
    }
    if (!is.null(options$make_demo)) {
      make_demo(options$make_demo)
      cat("Wrote synthetic teaching fixtures.\n")
      return(invisible(0L))
    }
    required <- c("counts", "metadata", "out")
    if (!all(required %in% names(options))) workflow_error("Provide --counts, --metadata, and --out (or use --make-demo DIR)")
    run_workflow(options$counts, options$metadata, options$out, options$task, options$min_library_size)
    cat("Completed descriptive workflow; outputs require human review.\n")
    invisible(0L)
  }, error = function(e) {
    cat("ERROR: ", conditionMessage(e), "\n", sep = "", file = stderr())
    invisible(1L)
  }) -> status
  if (is.numeric(status)) as.integer(status) else 0L
}

if (sys.nframe() == 0L && !interactive()) quit(status = main(commandArgs(trailingOnly = TRUE)))
