# Public PBMC annotation and integration: worked example

This bundle makes the cell-type annotation and integration lessons reproducible from a real public count matrix. It compares **SingleR with Seurat reference-label transfer**, then compares **unintegrated PCA with Harmony** on the same query cells. It supplies the code, selected cell IDs, observed CSV results, figures, settings and software records. RPCA, CCA, scPred and silhouette analysis are **not executed**.

## Start here

Use a separate R environment. The tested setup is **Ubuntu 24.04 with R 4.3.3**, Seurat/SeuratObject 5.0.1, SingleR 2.4.1, scuttle 1.12.0, scran 1.30.2, ggplot2 3.4.4, Harmony 1.2.3 and LISI 1.0. RhpcBLASctl 0.23.42 controls numerical-library threads. `scran` is required for the chosen SingleR Wilcoxon marker-selection mode.

On a separate Ubuntu 24.04 installation, run:

```bash
bash setup_ubuntu.sh
python3 prepare_inputs.py --data-dir data
Rscript run_example.R \
  --data-package data/pbmcsca.SeuratData_3.0.0.tar.gz \
  --output reproduced-results
```

`setup_ubuntu.sh` uses `sudo apt-get` to install documented R and compiler prerequisites in that Ubuntu environment. It then installs the three checksum-pinned R source packages in a writable user R library. Read the script before running it; do not apply it blindly to an existing analysis project. The installer checks the tested direct package versions and stops rather than silently substituting another Harmony implementation.

If R and dependencies are already installed, check them without installing anything:

```bash
python3 install_r_sources.py --check-only
```

Other operating systems require a manually prepared environment with the recorded R/package versions; the Ubuntu setup script is not advertised as a cross-platform installer. The version records are **not a complete binary/environment lockfile**. Ubuntu dependency updates, libraries and platform differences can affect numerical results; `observed/sessionInfo.txt` records the saved run's loaded dependencies. The example deliberately pins Harmony 1.2.3 rather than silently updating to Harmony2.

Python uses only its standard library. The public input download is 58,634,290 bytes (about 59 MB decimal); package installation needs additional bandwidth and disk space. Measured run time and memory, excluding installation, are recorded in `observed/reproduction_check.json`. These are observations from one machine, not a performance guarantee or minimum hardware specification.

## Tested environment and figure reproducibility

An independent run of the original, pre-font-pin lab reproduced all 14 CSV files byte-for-byte in a fresh official Ubuntu Base 24.04.4 root filesystem with no pre-existing R or analysis packages. It ran in a chroot on the same underlying host, kernel and hardware—not on a separate physical machine. The only bootstrap steps were configuring DNS and device nodes and installing `sudo` in the minimal root filesystem; the documented setup and analysis were then run unchanged.

In that original audit, all four PNGs regenerated, but none was pixel-identical to its published counterpart. Noto Sans and DejaVu Sans defaults were found in the compared environments. Inspection of the UMAP showed typography and layout differences despite byte-identical UMAP coordinates; this does not establish that fonts account for every changed pixel in all four figures.

The current revision explicitly pins DejaVu Sans regular and bold (checked by SHA-256 using fontconfig), the theme and geom text settings, and the base-R Cairo PNG device. Missing or mismatched fonts fail clearly in the environment checker and analysis. `setup_ubuntu.sh` installs `fontconfig` and `fonts-dejavu-core`; font hashes are listed in `inputs.json`, and the actual font hashes and graphics-library versions are recorded in `observed/run_summary.json` for the saved run. A rerun records them in its own `run_summary.json`.

A follow-up run of this font-pinned script in the original environment and the separately installed Ubuntu filesystem from the audit produced byte-identical copies of all 14 CSVs and all four PNGs, including identical decoded pixels. The 14 CSVs also remain byte-identical to the original published numerical outputs. This follow-up reused the installed environments; it was not another installation-from-zero or a different-hardware test. Details are in `observed/reproduction_check.json`. These measures improve consistency but are not a complete graphics or environment lock, and do not promise universal pixel identity.

Windows, macOS, different hardware or physical machines, and the RPCA/CCA extensions remain untested.

## Public input and attribution

The input is [`pbmcsca.SeuratData` 3.0.0](https://seurat.nygenome.org/src/contrib/pbmcsca.SeuratData_3.0.0.tar.gz), distributed by [SeuratData / Satija Lab](https://github.com/satijalab/seurat-data). Its `DESCRIPTION` declares **CC BY 4.0**. The original study is [Ding et al. (2020), *Systematic comparison of single-cell and single-nucleus RNA-sequencing methods*](https://doi.org/10.1038/s41587-020-0465-8). The paper links public RNA-seq to GEO **GSE132044** and the Broad Single Cell Portal, including PBMC study **SCP424**.

Attribution: Ding et al. and the original study contributors; packaged for SeuratData by Satija Lab. New teaching subset selection, analysis, summaries and figures by The Omics Hub. The figures here are newly generated from the public input, not copied from the study's figures. Dataset use follows the package-declared [CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/); this statement is not an independent rights assessment of every underlying study file. Upstream software retains its own licenses.

The raw input archive and third-party source packages are **not republished in this bundle**. `inputs.json` records their exact URLs, sizes and SHA-256 hashes. The data preparer refuses a size/hash mismatch and never replaces an existing mismatched archive. To reuse an identical download:

```bash
python3 prepare_inputs.py --data-dir data \
  --from-cache /path/to/pbmcsca.SeuratData_3.0.0.tar.gz
```

## Fixed design

The archive contains 31,021 cells across nine `Method` groups and seven technologies. This example uses literal source metadata values, not the underscored layer names found in some vignettes:

| Role | Literal `Method` values |
|---|---|
| Query, annotation and integration | `10x Chromium (v2) A`; `10x Chromium (v3)` |
| Reference, annotation only | `10x Chromium (v2) B` |

Keep cells with `nFeature_RNA > 200` and nonempty supplied `CellType` labels; exclude missing, `Unknown` and `Unassigned` labels. Before scoring either method, take at most **80 cells per Method × source-label stratum**, using sorted IDs, seed **20261023** and R's `L'Ecuyer-CMRG` random-number generator. Small strata are retained. `filtering_counts.csv` records eligibility, exclusions and capping, including zero-count strata; `selected_cells.csv` records the retained query and reference IDs.

The script verifies detected-gene metadata against the RNA count matrix, disjoint query/reference IDs, and absence of identical count profiles across query and reference. It constructs fresh classic RNA assays from sparse raw counts rather than using inherited reductions or normalized values. Source labels are **expression-derived annotations, not independent ground truth**. This is a within-study teaching design, not a held-out-donor or cross-study validation.

Log normalization uses scale factor 10,000. Query/reference variable-feature selection requests 2,000 genes and PCA uses 20 dimensions. SingleR uses `de.method="wilcox"`, fine tuning and pruning; Seurat uses `FindTransferAnchors()` and categorical `TransferData()` with the same reference cells/labels. Pruned SingleR calls remain `Unassigned`; prediction scores and deltas are retained rather than treated as calibrated probabilities.

Harmony uses the query's PCA, batch field `Method`, theta 2, lambda 1, `max_iter=10` and one core. The script verifies that RNA counts remain unchanged. Separate PCA/Harmony UMAPs use seed 20261023, 30 neighbors, minimum distance 0.3 and cosine distance. They are qualitative visualizations, not shared coordinates or quantitative evidence of success.

LISI is calculated on the same ordered cells in **20-dimensional PCA/Harmony embeddings**, with perplexity 30 and the original assay-group/source-label metadata. It is not calculated on UMAP or on clusters newly derived from the corrected embedding. The workflow asserts matching cell IDs and metadata order before scoring.

## Read the outputs

The `observed/` directory contains a saved successful run. A rerun writes to your chosen output directory without changing the saved observations.

| File | What it lets you inspect |
|---|---|
| `run_summary.json` | Input/script hashes, exact settings, counts, diagnostic summaries and integrity checks |
| `filtering_counts.csv` / `selected_cells.csv` | Full filtering audit and selected reference/query IDs |
| `annotation.csv` | Per-cell source label, SingleR raw/pruned calls and delta, Seurat call and score |
| `annotation_grouped_counts.csv` / `annotation_label_counts.csv` | Descriptive counts by batch/label and method |
| `lisi_per_cell.csv` | Paired PCA/Harmony iLISI and cLISI scores, with IDs and source metadata |
| `lisi_summary.csv` / `lisi_by_label.csv` | Medians and quartiles overall, by source label and by batch; filter `stratum` to choose the grouping |
| `lisi_paired_differences.csv` | Per-cell Harmony-minus-PCA changes; median paired change is not necessarily the difference of pooled medians |
| `embeddings_pca.csv` / `embeddings_harmony.csv` | The ordered 20-dimensional coordinates used for LISI |
| `umap_coordinates.csv` | The two qualitative visualization coordinate sets |
| `marker_expression_per_cell.csv` | Original normalized RNA evidence for CD3D, MS4A1, LYZ, NKG7 and PPBP where present |
| `*.png` | New annotation comparison, RNA marker, paired UMAP and LISI distribution figures |
| `packages.csv` / `sessionInfo.txt` | Direct package versions and loaded R environment |
| `reproduction_check.json` | Independent rerun comparison and observed machine-resource use |

Outputs must go to an empty directory by default. `--force` explicitly permits replacement of known generated output filenames only; unrelated files are retained. Prefer a new directory when experimenting.

## What the results do not prove

Shared reference labels mean the two annotation methods are **not independent corroboration**. Exact source-label agreement is not accuracy; the marker plot is expression-derived and therefore is not orthogonal validation. Novel cell states, clinical diagnosis and cross-study generalization are outside this example.

Label-stratified caps change cell-type proportions. Some rare types lack a counterpart in one batch—particularly plasmacytoid dendritic cells in the chosen v3 query after filtering—so a universal mixing target is inappropriate. Higher batch iLISI can reflect mixing without establishing that only technical effects were removed. Lower source-label cLISI indicates greater purity of those supplied labels, not complete biological preservation.

Keep the baseline, inspect category-specific results and original RNA, and consider independent measurements before accepting an integrated representation. Cells are not independent donor replicates. Corrected coordinates are not corrected count matrices for expression inference, and no hypothesis tests or population-level significance claims are reported.
