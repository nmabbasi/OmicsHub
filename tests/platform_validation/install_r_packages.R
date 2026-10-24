# Install public packages as platform binaries only; fail rather than compile source.
required <- c("tidyverse", "here", "Seurat", "patchwork")
os <- Sys.info()[["sysname"]]
architecture <- R.version[["arch"]]
r_version <- as.character(getRversion())

if (identical(os, "Linux")) {
  release_lines <- readLines("/etc/os-release", warn = FALSE)
  read_os_value <- function(key) {
    line <- grep(paste0("^", key, "="), release_lines, value = TRUE)
    if (length(line) != 1L) return("")
    sub(paste0("^", key, "=\"?([^\"]*)\"?$"), "\\1", line)
  }
  distribution <- read_os_value("ID")
  codename <- read_os_value("VERSION_CODENAME")
  if (!identical(distribution, "ubuntu") || !codename %in% c("noble", "resolute")) {
    stop(sprintf("No configured public R binary distribution for %s/%s", distribution, codename))
  }
  repository <- sprintf("https://packagemanager.posit.co/cran/__linux__/%s/latest", codename)
  options(HTTPUserAgent = sprintf(
    "R/%s R (%s)", getRversion(),
    paste(getRversion(), R.version[["platform"]], R.version[["arch"]], R.version[["os"]])
  ))
  # The Linux repository chooses the native binary from the R user-agent header.
  # Posit may fall back to source if a binary is absent; never compile that source.
  options(install.packages.compile.from.source = "never")
  cat(sprintf(
    "PLATFORM_R_PACKAGE_INSTALL_JSON {\"status\":\"starting\",\"os\":\"%s\",\"architecture\":\"%s\",\"r\":\"%s\",\"repository\":\"%s\",\"source_compilation\":\"disabled\"}\n",
    os, architecture, r_version, repository
  ))
  tryCatch({
    install.packages(required, repos = c(CRAN = repository), Ncpus = 2)
  }, error = function(e) {
    cat("PLATFORM_R_PACKAGE_INSTALL_FAILURE: ", conditionMessage(e), "\n", sep = "", file = stderr())
    stop(e)
  })
} else if (os %in% c("Windows", "Darwin")) {
  repository <- "https://packagemanager.posit.co/cran/latest"
  options(install.packages.compile.from.source = "never")
  cat(sprintf(
    "PLATFORM_R_PACKAGE_INSTALL_JSON {\"status\":\"starting\",\"os\":\"%s\",\"architecture\":\"%s\",\"r\":\"%s\",\"repository\":\"%s\",\"package_type\":\"binary\",\"source_compilation\":\"disabled\"}\n",
    os, architecture, r_version, repository
  ))
  tryCatch({
    install.packages(required, repos = c(CRAN = repository), type = "binary", Ncpus = 2)
  }, error = function(e) {
    cat("PLATFORM_R_PACKAGE_INSTALL_FAILURE: ", conditionMessage(e), "\n", sep = "", file = stderr())
    stop(e)
  })
} else {
  stop(sprintf("Unsupported native runner OS for public binary install: %s", os))
}

missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) {
  stop(sprintf("Required native R binaries remain unavailable: %s", paste(missing, collapse = ", ")))
}
versions <- vapply(required, function(package) as.character(packageVersion(package)), character(1))
package_json <- paste(sprintf("\"%s\":\"%s\"", names(versions), versions), collapse = ",")
cat(sprintf(
  "PLATFORM_R_PACKAGE_INSTALL_JSON {\"status\":\"ok\",\"os\":\"%s\",\"architecture\":\"%s\",\"r\":\"%s\",\"packages\":{%s}}\n",
  os, architecture, r_version, package_json
))
