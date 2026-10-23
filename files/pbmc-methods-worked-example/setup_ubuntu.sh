#!/usr/bin/env bash
# Intended for a separate Ubuntu 24.04 R environment, not an existing analysis project.
set -euo pipefail
. /etc/os-release
if [[ "$ID" != ubuntu || "$VERSION_ID" != 24.04 ]]; then
  printf 'This setup recipe targets Ubuntu 24.04. See README.md for the tested R versions.\n' >&2
  exit 2
fi
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
printf 'Installing documented R and compiler prerequisites in this Ubuntu environment.\n'
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  python3 ca-certificates r-base-core r-base-dev \
  gfortran libblas-dev liblapack-dev \
  r-cran-seurat r-bioc-singler r-bioc-scuttle r-bioc-scran \
  r-cran-ggplot2 r-cran-jsonlite r-cran-digest \
  r-cran-rcpparmadillo r-cran-rcppprogress r-cran-rann
python3 install_r_sources.py
