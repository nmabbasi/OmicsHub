# Synthetic Seurat visualization example

This small reproducible example is intentionally **synthetic**. It contains no public or biological measurements. The script constructs a toy 36-feature × 48-cell count matrix with three arbitrary labels and four toy sample IDs using seed `20261023`, writes the CSV fixture, reloads it, and runs Seurat normalization, variable-feature selection, scaling, PCA, and UMAP before plotting.

From the repository root, run:

```sh
Rscript files/visualization-example/run_example.R
```

The executed command in this revision was `Rscript files/visualization-example/run_example.R` (output captured in `run-evidence.txt`). Tested core-workflow versions were R 4.3.3, Seurat 5.0.1, SeuratObject 5.0.1, ggplot2 3.4.4, and uwot 0.1.16. `session-info.txt` contains the captured R session; `package-versions.txt` lists the packages used by the core route; `run-checksums.txt` records MD5 hashes for the generated CSV fixture and four PNG figures.

Outputs:

- `synthetic_counts.csv` — integer features-by-cells input
- `synthetic_metadata.csv` — cell labels, condition, and synthetic sample IDs
- `images/tutorial-figures/visualization-synthetic-umap.png` (repository-relative)
- `images/tutorial-figures/visualization-synthetic-feature.png` (repository-relative)
- `images/tutorial-figures/visualization-synthetic-dotplot.png` (repository-relative)
- `images/tutorial-figures/visualization-synthetic-composition.png` (repository-relative)

The balanced label counts and marker-like shifts are generator parameters, not evidence. UMAP coordinates, axes, and distances have no biological meaning here; the composition chart is balanced by construction. The script does not run SCpubr or dittoSeq. Their tutorial sections remain optional, unexecuted templates and are not dependencies of this route. The script intentionally does not commit a serialized Seurat RDS; it reconstructs the small object from the CSV inputs on each run.
