#!/usr/bin/env Rscript
# Retrieve a precomputed AlphaFold DB entry or inspect a local PDB file. No prediction/design.
MAX_PDB_BYTES <- 10 * 1024 * 1024
ACCESSION_PATTERN <- "^[A-Z0-9]{6,10}$"
API_ROOT <- "https://alphafold.ebi.ac.uk/api/prediction/"

fail <- function(message) stop(message, call. = FALSE)

parse_ca_records <- function(lines) {
  model_count <- sum(grepl("^MODEL ", lines))
  if (model_count > 1L) fail("multiple MODEL records are unsupported; this reader accepts one model")
  ca <- lines[grepl("^ATOM  ", lines) & nchar(lines) >= 16L & substr(lines, 13L, 16L) |> trimws() == "CA"]
  if (!length(ca)) fail("no alpha-carbon ATOM records found")
  selected <- list()
  seen <- character()
  for (i in seq_along(lines)) {
    line <- lines[[i]]
    if (!grepl("^ATOM  ", line) || nchar(line) < 16L || trimws(substr(line, 13L, 16L)) != "CA") next
    if (nchar(line) < 66L) fail(sprintf("line %d: CA ATOM record is too short", i))
    alt <- substr(line, 17L, 17L)
    chain <- trimws(substr(line, 22L, 22L)); if (!nzchar(chain)) chain <- "_"
    residue <- trimws(substr(line, 23L, 26L))
    icode <- trimws(substr(line, 27L, 27L))
    if (!grepl("^[+-]?[0-9]+$", residue)) fail(sprintf("line %d: CA residue number must be an integer", i))
    key <- paste(chain, residue, icode, sep = "|")
    alt_key <- paste(key, alt, sep = "|")
    if (alt_key %in% seen) fail(sprintf("line %d: duplicate CA record for chain/residue/insertion/altloc", i))
    seen <- c(seen, alt_key)
    if (!alt %in% c(" ", "A")) next
    raw_b <- trimws(substr(line, 61L, 66L))
    b <- suppressWarnings(as.numeric(raw_b))
    if (is.na(b) || !is.finite(b) || b < 0 || b > 100) fail(sprintf("line %d: CA B-factor must be finite and in [0,100]", i))
    priority <- if (alt == " ") 0L else 1L
    if (is.null(selected[[key]]) || priority < selected[[key]]$priority) {
      selected[[key]] <- list(priority = priority, row = data.frame(chain = chain,
        residue_id = residue, insertion_code = icode, bfactor = b, stringsAsFactors = FALSE))
    }
  }
  if (!length(selected)) fail("no alpha-carbon ATOM records with usable B-factors found")
  rows <- do.call(rbind, lapply(selected, `[[`, "row"))
  rows <- rows[order(rows$chain, as.integer(rows$residue_id), rows$insertion_code), , drop = FALSE]
  rownames(rows) <- NULL
  rows
}

inspect_pdb <- function(pdb_path, output_prefix, accession = "", model_id = "", model_version = "", source_url = "", verified_alphafold = FALSE) {
  if (!file.exists(pdb_path)) fail(sprintf("PDB file does not exist: %s", pdb_path))
  size <- file.info(pdb_path)$size
  if (is.na(size) || size > MAX_PDB_BYTES) fail("PDB input exceeds the 10 MiB teaching-example limit")
  lines <- tryCatch(readLines(pdb_path, warn = FALSE, encoding = "ASCII"), error = function(e) fail(sprintf("Cannot read ASCII PDB: %s", conditionMessage(e))))
  residues <- parse_ca_records(lines)
  residue_path <- paste0(output_prefix, "_residues.csv")
  summary_path <- paste0(output_prefix, "_summary.csv")
  if (file.exists(residue_path) || file.exists(summary_path)) fail("Refusing to overwrite an existing residue or summary output")
  parent <- dirname(residue_path)
  if (!dir.exists(parent) && !dir.create(parent, recursive = TRUE)) fail(sprintf("Cannot create output directory: %s", parent))
  summary <- data.frame(
    field = c("accession", "model_id", "model_version", "source_url", "input_file",
              "input_bytes", "ca_residue_count", "chains", "mean_ca_bfactor",
              "min_ca_bfactor", "max_ca_bfactor", "interpretation"),
    value = c(accession, model_id, model_version, source_url, basename(pdb_path),
              as.character(size), as.character(nrow(residues)), paste(sort(unique(residues$chain)), collapse = ";"),
              format(mean(residues$bfactor), digits = 10), as.character(min(residues$bfactor)),
              as.character(max(residues$bfactor)),
              if (verified_alphafold) "For this API-selected AlphaFold DB file, B-factor is pLDDT (local model confidence); this is not evidence of function, binding, stability, or experimental accuracy."
              else "B-factors are reported as provided; provenance was not verified, and experimental B-factors are not pLDDT. This is not evidence of function, binding, stability, or experimental accuracy."),
    stringsAsFactors = FALSE
  )
  write.csv(residues, residue_path, row.names = FALSE, na = "")
  write.csv(summary, summary_path, row.names = FALSE, na = "")
  invisible(list(residues = residues, summary = summary, residue_file = residue_path, summary_file = summary_path))
}

fetch_alphafold <- function(accession, outdir) {
  if (!grepl(ACCESSION_PATTERN, accession)) fail("accession must be 6-10 uppercase alphanumeric characters")
  if (!requireNamespace("jsonlite", quietly = TRUE)) fail("The explicit API fetch requires the jsonlite R package; local PDB analysis does not")
  if (dir.exists(outdir) && length(list.files(outdir, all.files = TRUE, no.. = TRUE))) fail("Refusing to write into a non-empty output directory")
  dir.create(outdir, recursive = TRUE, showWarnings = FALSE)
  api_url <- paste0(API_ROOT, utils::URLencode(accession, reserved = TRUE))
  response <- tempfile(fileext = ".json")
  on.exit(unlink(response), add = TRUE)
  utils::download.file(api_url, response, mode = "wb", quiet = TRUE)
  if (file.info(response)$size > MAX_PDB_BYTES) fail("AlphaFold DB API response exceeds the teaching-example size limit")
  payload <- jsonlite::fromJSON(response, simplifyDataFrame = TRUE)
  if (!is.data.frame(payload) || !nrow(payload)) fail(sprintf("AlphaFold DB returned no model for %s", accession))
  required <- c("uniprotAccession", "pdbUrl")
  if (!all(required %in% names(payload))) fail("AlphaFold DB response is missing accession or pdbUrl fields")
  matches <- which(payload$uniprotAccession == accession & !is.na(payload$pdbUrl) & nzchar(payload$pdbUrl))
  if (length(matches) != 1L) fail("Expected exactly one matching API entry with an advertised PDB URL; inspect the official API response and select a specific entry")
  model <- payload[matches, , drop = FALSE]
  pdb_url <- as.character(model$pdbUrl[[1]])
  if (!grepl("^https://(www\\.)?alphafold\\.ebi\\.ac\\.uk/", pdb_url)) fail("Refusing a PDB URL outside the official HTTPS AlphaFold DB host")
  model_id <- if ("entryId" %in% names(model)) as.character(model$entryId[[1]]) else ""
  model_version <- if ("latestVersion" %in% names(model)) as.character(model$latestVersion[[1]]) else ""
  pdb_path <- file.path(outdir, paste0(accession, "_alphafold.pdb"))
  api_path <- file.path(outdir, paste0(accession, "_alphafold_api.json"))
  if (file.exists(pdb_path) || file.exists(api_path)) fail("Refusing to overwrite existing API or PDB output")
  utils::download.file(pdb_url, pdb_path, mode = "wb", quiet = TRUE)
  if (file.info(pdb_path)$size > MAX_PDB_BYTES) { unlink(pdb_path); fail("Downloaded PDB exceeds the 10 MiB teaching-example limit") }
  writeLines(jsonlite::toJSON(payload, auto_unbox = TRUE, pretty = TRUE), api_path, useBytes = TRUE)
  result <- inspect_pdb(pdb_path, file.path(outdir, paste0(accession, "_alphafold")),
                        accession = accession, model_id = model_id, model_version = model_version,
                        source_url = pdb_url, verified_alphafold = TRUE)
  cat(sprintf("Saved API record, PDB, residue table, and summary in %s\n", outdir))
  invisible(result)
}

main <- function(args) {
  if (length(args) == 3L && identical(args[[1]], "analyze")) {
    inspect_pdb(args[[2]], args[[3]])
    cat(sprintf("Wrote %s_residues.csv and %s_summary.csv (offline; source provenance unverified)\n", args[[3]], args[[3]]))
  } else if (length(args) == 3L && identical(args[[1]], "fetch")) {
    fetch_alphafold(args[[2]], args[[3]])
  } else {
    fail("Usage: Rscript inspect_alphafold.R analyze local.pdb output_prefix | fetch UNIPROT_ACCESSION output_directory")
  }
}

if (sys.nframe() == 0L) {
  tryCatch(main(commandArgs(trailingOnly = TRUE)), error = function(e) {
    message("ERROR: ", conditionMessage(e))
    quit(status = 2L)
  })
}
