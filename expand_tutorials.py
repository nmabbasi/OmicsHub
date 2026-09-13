#!/usr/bin/env python3
"""Expand the 10 shortest tutorials with substantial expert-level content."""
import re

LESSONS_DIR = "lessons"

# --- Expansions: keyed by filename, value is additional markdown to INSERT before the Practical Exercise ---

expansions = {}

# 1. reproducible-project-structure.md (530 words → target ~1000)
expansions["reproducible-project-structure.md"] = {
    "insert_before": "## Practical Exercise",
    "content": """
## 5. Naming Conventions

Adopt a systematic naming scheme. Avoid spaces, special characters, and ambiguous abbreviations. Use ISO 8601 dates (`YYYY-MM-DD`) and lowercase with hyphens or underscores.

```text
# Good: descriptive, date-stamped, sortable
data/raw/2026-08-15_rnaseq_sample01_R1.fastq.gz
results/figures/2026-08-15_pca-plot.webp

# Bad: ambiguous, unsortable, undated
data/new data (2)/file.txt
results/final_final_v3.png
```

## 6. Environment and Dependency Management

Record the exact software environment alongside the project. This ensures that another researcher—or your future self—can recreate the same computational conditions.

```bash
# Conda: export a pinned environment
conda env export --no-builds > envs/environment.yml

# Pip: freeze exact versions
pip freeze > envs/requirements.txt

# R: use renv for snapshot isolation
# In R console: renv::snapshot()
```

**Why this matters:** A script that runs under Python 3.10 with pandas 1.5 may silently produce different results under Python 3.12 with pandas 2.1 due to API changes, deprecations, or altered default parameters.

## 7. Version Control Integration

Every project should be a Git repository from day one. Commit early and often, and use `.gitignore` to exclude large data files, temporary outputs, and sensitive credentials.

```bash
# Initialize and make first commit
git init
echo "data/raw/" >> .gitignore
echo "*.pyc" >> .gitignore
echo ".env" >> .gitignore
git add .
git commit -m "Initial project structure with README and configs"
```

Track the relationship between code versions and results by recording the Git commit hash alongside every output:

```bash
echo "Results generated at commit: $(git rev-parse --short HEAD)" >> results/run_log.txt
```

## 8. Data Protection and Backup Strategy

Raw data must be treated as **immutable**. Never modify raw files directly; instead, read them into processing scripts and write derived outputs to `data/processed/` or `results/`.

| Rule | Implementation |
|---|---|
| Raw data is read-only | `chmod 444 data/raw/*` after download |
| Processed data is reproducible | Delete and regenerate from raw + code |
| Results include provenance | Each output records the script, commit, and parameters used |
| Sensitive data stays local | Use `.gitignore` and never commit patient identifiers |

## 9. Documentation Standards

A good README answers five questions:

1. **What** does this project analyze?
2. **How** do I set up the environment?
3. **Where** is the input data, and how was it obtained?
4. **Which** commands reproduce the results?
5. **What** are the known limitations?

```markdown
# RNA-seq Differential Expression Analysis

## Setup
1. Install conda: see envs/environment.yml
2. Place raw FASTQ files in data/raw/
3. Run: bash scripts/run_pipeline.sh

## Outputs
- results/figures/volcano_plot.webp
- results/tables/deg_table.csv

## Limitations
- Tested on Ubuntu 22.04 with 32 GB RAM
- Requires ~50 GB disk space for genome index
```

"""
}

# 2. reference-genomes-annotation.md (550 words → target ~1000)
expansions["reference-genomes-annotation.md"] = {
    "insert_before": "## Practical Exercise",
    "content": """
## 5. Common Reference Sources

Different communities maintain different reference resources. Choosing the correct source depends on your organism, analysis type, and downstream tools.

| Source | Organism Focus | Best For | URL |
|---|---|---|---|
| GENCODE | Human, Mouse | RNA-seq, gene-level analysis | gencodegenes.org |
| Ensembl | Multi-species | Comparative genomics, variant annotation | ensembl.org |
| NCBI RefSeq | Multi-species | Clinical genomics, standardized gene models | ncbi.nlm.nih.gov |
| UCSC Genome Browser | Multi-species | Visualization, track hubs | genome.ucsc.edu |
| Phytozome | Plants | Plant genomics | phytozome-next.jgi.doe.gov |

## 6. Chromosome Naming Conflicts

One of the most common silent errors in bioinformatics is a chromosome naming mismatch between your reference genome and annotation file. Different sources use different conventions:

```text
# UCSC style          # Ensembl/NCBI style
chr1                  1
chrM                  MT
chrX                  X
```

**Detection:** Compare the first column of the FASTA index (`.fai`) with the first column of the GTF/GFF:

```bash
# Extract chromosome names from FASTA index
cut -f1 genome.fa.fai | sort > chrom_fasta.txt

# Extract chromosome names from GTF
awk '$3=="gene" {print $1}' annotation.gtf | sort -u > chrom_gtf.txt

# Compare — any differences indicate a naming mismatch
diff chrom_fasta.txt chrom_gtf.txt
```

**Resolution:** Use a mapping file or sed to convert between conventions. Never manually edit a reference FASTA—always script the conversion and document it.

## 7. Annotation File Formats Explained

| Format | Extension | Key Features |
|---|---|---|
| GTF | `.gtf` | Tab-separated, 9 columns, gene/transcript/exon hierarchy |
| GFF3 | `.gff3` | Hierarchical parent-child relationships, more flexible than GTF |
| BED | `.bed` | Simple coordinate format, 0-based start positions |

**Critical difference:** GTF uses 1-based, fully closed coordinates (`start=1, end=100` means positions 1 through 100). BED uses 0-based, half-open coordinates (`start=0, end=100` means positions 1 through 100). Mixing these silently shifts all your coordinates by one base.

## 8. Version Pinning and Reproducibility

Always record the exact version of your reference files. A GENCODE release number alone is not sufficient—record the full download URL, file checksum, and download date.

```bash
# Create a reproducible reference manifest
cat > config/reference_manifest.yml << 'EOF'
reference:
  assembly: GRCh38.p14
  annotation: GENCODE v46
  fasta_url: "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_46/GRCh38.p14.genome.fa.gz"
  gtf_url: "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_46/gencode.v46.annotation.gtf.gz"
  download_date: "2026-08-15"
  fasta_md5: "abc123def456..."
  gtf_md5: "789ghi012jkl..."
  chromosome_naming: "chr-prefixed"
EOF
```

## 9. When to Update References

Updating your reference genome mid-project can invalidate all previous results. Follow these guidelines:

- **Start of project:** Choose the latest stable release and lock it.
- **During analysis:** Never change references unless you discover a critical error.
- **Between projects:** Evaluate whether a newer release fixes known issues relevant to your analysis.
- **Publication:** Report the exact assembly, annotation release, and download source in your Methods section.

"""
}

# 3. r-tidyverse-fundamentals.md (563 words → target ~1000)
expansions["r-tidyverse-fundamentals.md"] = {
    "insert_before": "## Practical Exercise",
    "content": """
## 5. Reading and Writing Data

In bioinformatics, you will frequently import CSV, TSV, and Excel files. Use the `readr` package (part of tidyverse) for consistent parsing and explicit column type detection.

```r
# Read a tab-separated gene expression matrix
expr <- read_tsv("data/raw/gene_counts.tsv", show_col_types = TRUE)

# Inspect dimensions and first rows
dim(expr)
head(expr)

# Write results with consistent formatting
write_csv(expr, "data/processed/filtered_counts.csv")
```

**Common pitfall:** Excel silently converts gene names like `MARCH1` and `SEPT2` to dates. Always use plain-text formats (CSV/TSV) for bioinformatics data and verify gene name integrity after import.

## 6. Reshaping Data: Wide vs. Long Format

Many bioinformatics datasets arrive in wide format (one column per sample), but most R analysis and plotting functions expect long (tidy) format.

```r
# Wide format: each sample is a column
wide_data <- data.frame(
  gene = c("TP53", "BRCA1", "MYC"),
  sample_A = c(150, 320, 890),
  sample_B = c(175, 280, 920)
)

# Pivot to long format for ggplot and statistical testing
long_data <- wide_data |>
  pivot_longer(
    cols = starts_with("sample_"),
    names_to = "sample",
    values_to = "expression"
  )

# Now each row is one gene-sample measurement
print(long_data)
# Output:
# gene   sample    expression
# TP53   sample_A  150
# TP53   sample_B  175
# BRCA1  sample_A  320
# ...
```

## 7. Factors and Categorical Variables

Factors are essential for controlling group order in plots and statistical models. Always set factor levels explicitly rather than relying on alphabetical order.

```r
# Without explicit levels, R uses alphabetical order
samples$condition <- factor(samples$condition, levels = c("control", "treated"))

# This ensures "control" appears first in plots and is the reference level in models
levels(samples$condition)
# [1] "control" "treated"
```

**Why this matters:** In differential expression analysis, the reference level of a factor determines the direction of fold-change calculations. If "treated" is accidentally set as the reference, all log2FC values will be inverted.

## 8. Error Handling and Defensive Programming

Before running an analysis pipeline, validate your inputs programmatically:

```r
# Check that required columns exist
stopifnot(
  "sample_id" %in% colnames(samples),
  "condition" %in% colnames(samples),
  nrow(samples) > 0
)

# Check for unexpected NA values in critical columns
na_counts <- samples |> summarise(across(everything(), ~sum(is.na(.x))))
print(na_counts)

# Assert no duplicate sample IDs
if (anyDuplicated(samples$sample_id)) {
  stop("Duplicate sample IDs detected — check your metadata file.")
}
```

## 9. Reproducible R Sessions

Always record your R session information at the end of every analysis script. This captures the exact R version, loaded packages, and operating system.

```r
# At the end of your script
sink("logs/session_info.txt")
sessionInfo()
sink()

# Expected output includes:
# R version 4.4.1 (2024-06-14)
# Platform: x86_64-pc-linux-gnu
# attached packages: tidyverse 2.0.0, ggplot2 3.5.1, dplyr 1.1.4 ...
```

| Troubleshooting Issue | Likely Cause | Solution |
|---|---|---|
| `Error: package 'X' is not available` | R version too old for the package | Update R or use BiocManager for Bioconductor packages |
| Plot appears blank | Factor levels don't match data values | Check `levels()` and ensure data contains matching values |
| `Joining, by = ...` warning | Implicit join columns | Specify `by = "column_name"` explicitly |
| Gene names converted to dates | Excel auto-formatting | Re-import from original TSV; never open bioinformatics files in Excel |

"""
}

# 4. python-fundamentals-bioinformatics.md (564 words → target ~1000)
expansions["python-fundamentals-bioinformatics.md"] = {
    "insert_before": "## Practical Exercise",
    "content": """
## 5. Environment Setup and Virtual Environments

Never install packages into the system Python. Always use a virtual environment or conda to isolate dependencies per project.

```bash
# Create a virtual environment
python3 -m venv envs/bioinfo
source envs/bioinfo/bin/activate

# Install core bioinformatics libraries
pip install biopython pandas matplotlib numpy

# Verify installation
python -c "import Bio; print(Bio.__version__)"
# Expected: 1.83 (or your installed version)

# Freeze exact versions for reproducibility
pip freeze > envs/requirements.txt
```

## 6. Parsing Biological Files with Biopython

The most common Python task in bioinformatics is reading and writing sequence files. Biopython's `SeqIO` module handles FASTA, FASTQ, GenBank, and many other formats.

```python
from Bio import SeqIO

# Parse a FASTA file and extract basic statistics
records = list(SeqIO.parse("data/raw/sequences.fasta", "fasta"))
print(f"Total sequences: {len(records)}")

for record in records[:3]:
    print(f"  {record.id}: {len(record.seq)} bp, GC={gc_fraction(record.seq):.2%}")

def gc_fraction(seq):
    \"\"\"Calculate GC content of a DNA sequence.\"\"\"
    seq = seq.upper()
    gc = sum(1 for base in seq if base in "GC")
    return gc / len(seq) if len(seq) > 0 else 0.0

# Expected output:
# Total sequences: 1542
#   seq_001: 2341 bp, GC=42.15%
#   seq_002: 1876 bp, GC=38.90%
#   seq_003: 3102 bp, GC=45.22%
```

## 7. Working with Tabular Data Using Pandas

Most bioinformatics workflows produce tabular data (count matrices, variant tables, metadata). Pandas is the standard tool for manipulating these in Python.

```python
import pandas as pd

# Read a gene expression count matrix
counts = pd.read_csv("data/raw/gene_counts.tsv", sep="\\t", index_col=0)
print(f"Shape: {counts.shape}")  # (genes, samples)
print(counts.head())

# Filter genes with low total counts
min_total = 10
filtered = counts[counts.sum(axis=1) >= min_total]
print(f"Genes before filtering: {counts.shape[0]}")
print(f"Genes after filtering: {filtered.shape[0]}")

# Calculate basic statistics per sample
sample_stats = pd.DataFrame({
    "total_reads": counts.sum(),
    "detected_genes": (counts > 0).sum(),
    "median_count": counts.median()
})
print(sample_stats)
```

## 8. Writing Functions and Modular Code

As your analyses grow, organize reusable logic into functions with type hints, docstrings, and input validation.

```python
from pathlib import Path

def load_count_matrix(filepath: str, min_total: int = 10) -> pd.DataFrame:
    \"\"\"Load and filter a gene count matrix.
    
    Args:
        filepath: Path to tab-separated count matrix.
        min_total: Minimum total counts across all samples.
    
    Returns:
        Filtered DataFrame with genes as rows, samples as columns.
    
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the matrix is empty after filtering.
    \"\"\"
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Count matrix not found: {path}")
    
    df = pd.read_csv(path, sep="\\t", index_col=0)
    filtered = df[df.sum(axis=1) >= min_total]
    
    if filtered.empty:
        raise ValueError(f"No genes passed the min_total={min_total} filter")
    
    return filtered
```

## 9. Testing and Validation

Always validate your outputs before proceeding to the next analysis step:

```python
# Assertions catch silent errors early
assert counts.shape[0] > 0, "Count matrix is empty"
assert not counts.isnull().any().any(), "NaN values detected in count matrix"
assert (counts >= 0).all().all(), "Negative counts detected"

# Check for duplicate gene names
duplicates = counts.index[counts.index.duplicated()]
if len(duplicates) > 0:
    print(f"WARNING: {len(duplicates)} duplicate gene IDs found")
```

| Problem | Likely Cause | Solution |
|---|---|---|
| `ModuleNotFoundError` | Package not installed in active environment | Activate your venv and `pip install` the package |
| `FileNotFoundError` | Wrong working directory or relative path | Use `Path(__file__).parent` or absolute paths |
| `UnicodeDecodeError` | Binary file opened as text | Use `"rb"` mode or check file format |
| Pandas silently drops rows | Duplicate index values | Use `reset_index()` or deduplicate explicitly |

"""
}

# 5. research-reporting-interpretation.md (571 words → target ~1000)
expansions["research-reporting-interpretation.md"] = {
    "insert_before": "## Practical Exercise",
    "content": """
## 5. Reporting Standards in Bioinformatics

Different analysis types have community-agreed reporting standards. Following these ensures your work is reviewable and reproducible.

| Analysis Type | Reporting Guideline | Key Requirements |
|---|---|---|
| RNA-seq differential expression | MINSEQE / ENCODE | Raw data in GEO/SRA, normalization method, statistical test, FDR threshold |
| Variant calling | GA4GH / ACMG | Reference genome, caller + version, filter criteria, pathogenicity evidence |
| Metagenomics | MIMARKS / MIxS | Sample metadata, sequencing platform, database version, classification method |
| Single-cell RNA-seq | scRNA-tools reporting | Cell count, QC thresholds, clustering resolution, marker genes |
| Machine learning | TRIPOD / PROBAST | Training/test split, performance metrics, cross-validation strategy |

## 6. Writing a Methods Section

A complete Methods section should allow another researcher to reproduce your analysis from raw data to final figures. Include:

```markdown
## Methods

### Data acquisition
RNA-seq reads for 12 tumor/normal pairs were obtained from GEO (GSE123456).
Raw FASTQ files were validated with FastQC v0.12.1 and trimmed with
Trim Galore v0.6.10 (--quality 20 --length 36).

### Alignment and quantification
Reads were aligned to GRCh38 (GENCODE v46) using STAR v2.7.11b
(--outSAMtype BAM SortedByCoordinate). Gene-level counts were obtained
with featureCounts v2.0.6 (-t exon -g gene_id -s 2).

### Differential expression
DESeq2 v1.42.0 was used with default shrinkage (apeglm). Genes with
adjusted p-value < 0.05 and |log2FC| > 1 were considered significant.

### Software environment
All analyses were run on Ubuntu 22.04 with R 4.4.1 and Python 3.11.
A complete conda environment specification is available in the repository.
```

## 7. Figure and Table Best Practices

Figures and tables are often the first (and sometimes only) elements reviewers examine. Follow these principles:

- **Self-contained:** Every figure should be interpretable without reading the full text.
- **Labeled axes:** Include units, sample sizes, and statistical annotations.
- **Color-blind friendly:** Use colorblind-safe palettes (e.g., viridis, ColorBrewer).
- **Resolution:** Minimum 300 DPI for publication; vector formats (PDF, SVG) preferred.

```r
# Example: a publication-quality volcano plot
library(ggplot2)
ggplot(deg_results, aes(x = log2FoldChange, y = -log10(padj))) +
  geom_point(aes(color = significant), size = 1, alpha = 0.6) +
  scale_color_manual(values = c("grey70", "#E41A1C")) +
  labs(
    x = expression(log[2]~"Fold Change"),
    y = expression(-log[10]~"Adjusted p-value"),
    title = "Differential Expression: Tumor vs. Normal",
    subtitle = paste(sum(deg_results$significant), "significant genes (FDR < 0.05, |log2FC| > 1)")
  ) +
  theme_minimal(base_size = 14) +
  geom_hline(yintercept = -log10(0.05), linetype = "dashed", color = "blue")
```

## 8. Common Reporting Errors to Avoid

| Error | Why It's Problematic | Correction |
|---|---|---|
| Reporting p-values without multiple testing correction | Inflates false positive rate | Always report adjusted p-values (FDR, Bonferroni) |
| Showing bar plots for continuous distributions | Hides data distribution and outliers | Use box plots, violin plots, or dot plots |
| Omitting sample sizes | Readers cannot assess statistical power | State n per group in every figure legend |
| Cherry-picking genes for validation | Confirmation bias | Report all tested genes with effect sizes and confidence intervals |
| Using "significant" without defining the threshold | Ambiguous and non-reproducible | State the exact threshold: "FDR < 0.05 and |log2FC| > 1" |

## 9. Interpretation vs. Over-interpretation

The most common scientific writing error is stating conclusions that exceed the evidence. Follow this hierarchy:

1. **Observation:** "Gene X shows a 3.2-fold increase in expression (FDR = 0.001) in tumor samples."
2. **Interpretation:** "This is consistent with the known role of Gene X in cell proliferation pathways."
3. **Over-interpretation (avoid):** "Gene X causes tumor growth." ← Requires functional validation, not just differential expression.

"""
}

# 6. experimental-design-batch-effects.md (575 words)
expansions["experimental-design-batch-effects.md"] = {
    "insert_before": "## Practical Exercise",
    "content": """
## 5. Experimental Design Principles

Good experimental design prevents confounding before data generation. The key principles are:

| Principle | Definition | Example |
|---|---|---|
| **Randomization** | Assign samples to groups randomly | Randomly assign mice to treatment cages |
| **Replication** | Include biological replicates (not technical) | ≥3 biological replicates per condition |
| **Blocking** | Group known sources of variation | Process all conditions on the same sequencing lane |
| **Balancing** | Equal sample sizes across groups | Same number of samples per condition per batch |

```text
# GOOD: Balanced design — each batch processes both conditions
Batch 1: Control_1, Control_2, Treated_1, Treated_2
Batch 2: Control_3, Control_4, Treated_3, Treated_4

# BAD: Confounded design — batch = condition
Batch 1: Control_1, Control_2, Control_3, Control_4
Batch 2: Treated_1, Treated_2, Treated_3, Treated_4
```

**Why the bad design fails:** Any difference between groups could be caused by the biological condition OR by batch-specific technical variation (different reagent lots, different operators, different sequencing lanes). These effects are mathematically inseparable.

## 6. Identifying Batch Effects

Before correction, you must first detect whether batch effects exist. Use dimensionality reduction (PCA) to visualize sample clustering:

```r
library(DESeq2)

# Perform variance-stabilizing transformation
vsd <- vst(dds, blind = TRUE)

# PCA plot colored by condition, shaped by batch
plotPCA(vsd, intgroup = c("condition", "batch")) +
  labs(title = "PCA: Check for Batch Effects") +
  theme_minimal()
```

**Interpretation guide:**
- If samples cluster primarily by **condition** → minimal batch effect, proceed.
- If samples cluster primarily by **batch** → strong batch effect, correction needed.
- If batch and condition are **confounded** → correction is impossible; redesign the experiment.

## 7. Batch Correction Methods

| Method | Package | When to Use | Limitation |
|---|---|---|---|
| **Include batch as covariate** | DESeq2, limma | Batch is known, not confounded with condition | Requires balanced design |
| **ComBat** | sva | Remove batch effects from normalized data | Can over-correct if groups are unbalanced |
| **Harmony** | harmony | Single-cell integration across batches | May merge genuine biological differences |
| **limma::removeBatchEffect** | limma | Visualization only (corrected values for PCA/heatmaps) | Do NOT use corrected values for DE testing |

```r
# Correct approach: include batch in the DESeq2 model
design(dds) <- ~ batch + condition

# The condition effect is estimated AFTER accounting for batch
dds <- DESeq(dds)
results <- results(dds, contrast = c("condition", "treated", "control"))
```

**Critical warning:** Never use batch-corrected expression values as input for differential expression testing. Instead, include batch as a covariate in the statistical model. Using corrected values can deflate variance estimates and inflate false positive rates.

## 8. Sample Size and Power Considerations

Underpowered experiments waste resources and produce unreliable results. Use power analysis before designing your experiment:

```r
# RNA-seq power analysis (rough estimate)
library(RNASeqPower)
rnapower(
  depth = 20,        # millions of reads per sample
  cv = 0.4,          # biological coefficient of variation
  effect = 1.5,      # minimum fold change to detect
  alpha = 0.05,      # significance level
  power = 0.8        # desired power
)
# Output: n = 5 samples per group needed
```

| Biological CV | Typical System | Recommended Replicates |
|---|---|---|
| 0.1 – 0.2 | Cell lines | 3 per group |
| 0.3 – 0.4 | Inbred mice | 4–6 per group |
| 0.5 – 1.0 | Human clinical | 8–15+ per group |

"""
}

# 7. data-visualization-fundamentals.md (590 words)
expansions["data-visualization-fundamentals.md"] = {
    "insert_before": "## Practical Exercise",
    "content": """
## 5. Choosing the Right Plot Type

The most common mistake in data visualization is choosing a plot type that obscures the data's structure. Use this decision guide:

| Question You're Answering | Recommended Plot | Avoid |
|---|---|---|
| How is a single variable distributed? | Histogram, density plot, violin plot | Pie chart |
| How do two continuous variables relate? | Scatter plot, hexbin plot | 3D surface plot |
| How do groups compare? | Box plot, violin plot, dot plot | Bar plot with error bars |
| How does a measurement change over time? | Line plot | Scatter plot without connection |
| What is the composition of categories? | Stacked bar chart, alluvial plot | Pie chart for >5 categories |
| What are the relationships in high-dimensional data? | PCA, UMAP, heatmap | >3 dimensions on cartesian axes |

## 6. A Complete Plotting Example in Python

```python
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Create example QC data
np.random.seed(42)
qc_data = pd.DataFrame({
    "sample": [f"S{i:02d}" for i in range(1, 13)],
    "total_reads_M": np.random.normal(25, 5, 12),
    "mapping_rate": np.random.uniform(0.85, 0.98, 12),
    "condition": ["control"]*6 + ["treated"]*6
})

# Create a publication-quality figure
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Panel A: Read depth per sample
colors = ["#4C72B0" if c == "control" else "#DD8452" for c in qc_data["condition"]]
axes[0].bar(qc_data["sample"], qc_data["total_reads_M"], color=colors)
axes[0].set_xlabel("Sample")
axes[0].set_ylabel("Total Reads (millions)")
axes[0].set_title("A. Sequencing Depth")
axes[0].tick_params(axis="x", rotation=45)
axes[0].axhline(y=20, color="red", linestyle="--", alpha=0.5, label="QC threshold")
axes[0].legend()

# Panel B: Mapping rate distribution by group
for cond, color in [("control", "#4C72B0"), ("treated", "#DD8452")]:
    subset = qc_data[qc_data["condition"] == cond]
    axes[1].hist(subset["mapping_rate"], bins=6, alpha=0.6, color=color, label=cond)
axes[1].set_xlabel("Mapping Rate")
axes[1].set_ylabel("Frequency")
axes[1].set_title("B. Alignment Quality")
axes[1].legend()

plt.tight_layout()
plt.savefig("results/figures/qc_summary.webp", dpi=300, bbox_inches="tight")
plt.show()
```

## 7. Color and Accessibility

Approximately 8% of males and 0.5% of females have some form of color vision deficiency. Use colorblind-safe palettes:

```python
# Colorblind-safe palettes
import matplotlib.pyplot as plt

# Option 1: Use built-in colorblind-safe colormap
plt.set_cmap("viridis")

# Option 2: Seaborn colorblind palette
import seaborn as sns
sns.set_palette("colorblind")

# Option 3: Manually specify accessible colors
accessible_colors = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "vermilion": "#D55E00",
    "sky_blue": "#56B4E9"
}
```

## 8. Figure Quality Standards

| Requirement | Standard | How to Check |
|---|---|---|
| Resolution | ≥300 DPI for print, ≥150 DPI for web | `fig.savefig(..., dpi=300)` |
| Format | Vector (SVG/PDF) for figures, WebP/PNG for web | Save both formats |
| Font size | ≥8pt for axis labels, ≥10pt for titles | Set `fontsize` parameters |
| Axis labels | Include units in parentheses | "Expression (TPM)", "Length (bp)" |
| Legend | Inside or adjacent to the plot area | Never overlapping data points |
| White space | Minimal margins, no excessive padding | `bbox_inches="tight"` |

"""
}

# 8. git-github-bioinformatics.md (604 words)
expansions["git-github-bioinformatics.md"] = {
    "insert_before": "## Practical Exercise",
    "content": """
## 5. Setting Up a Bioinformatics Repository

```bash
# Initialize a new project
mkdir rnaseq-analysis && cd rnaseq-analysis
git init

# Configure your identity (required once per machine)
git config user.name "Your Name"
git config user.email "your.email@institution.edu"

# Create the standard bioinformatics .gitignore
cat > .gitignore << 'EOF'
# Large data files — track with DVC or external storage
data/raw/
*.fastq.gz
*.bam
*.bai

# Temporary and generated files
*.pyc
__pycache__/
.ipynb_checkpoints/

# Environment files
envs/
.venv/

# OS files
.DS_Store
Thumbs.db

# Sensitive credentials
.env
*.key
EOF

git add .
git commit -m "Initial project structure"
```

## 6. Branching and Feature Development

Branches let you experiment without risking your stable analysis. Use descriptive branch names:

```bash
# Create a branch for a new analysis
git checkout -b feature/add-deseq2-analysis

# Make changes, commit incrementally
git add scripts/run_deseq2.R
git commit -m "Add DESeq2 differential expression script"

git add results/figures/volcano_plot.webp
git commit -m "Add volcano plot from DESeq2 results"

# When the analysis is complete and verified, merge back
git checkout main
git merge feature/add-deseq2-analysis
git branch -d feature/add-deseq2-analysis
```

## 7. Commit Discipline

Good commit messages are essential for understanding the history of an analysis. Follow the conventional commit format:

```text
# Good commits — each captures one logical change
git commit -m "Add QC filtering step: remove genes with < 10 total counts"
git commit -m "Fix chromosome naming mismatch between FASTA and GTF"
git commit -m "Update DESeq2 from v1.40 to v1.42 for apeglm shrinkage"

# Bad commits — vague, bundled, or meaningless
git commit -m "updates"
git commit -m "fixed stuff"
git commit -m "final version v3"
```

## 8. Handling Large Files with Git LFS or DVC

Raw sequencing data (FASTQ, BAM) should never be committed directly to Git. Use Git LFS or DVC for large file tracking:

```bash
# Option 1: Git LFS for moderately large files
git lfs install
git lfs track "*.bam"
git lfs track "*.fastq.gz"
git add .gitattributes
git commit -m "Configure Git LFS for sequencing files"

# Option 2: DVC for very large datasets
pip install dvc
dvc init
dvc add data/raw/sample_R1.fastq.gz
git add data/raw/sample_R1.fastq.gz.dvc .gitignore
git commit -m "Track raw FASTQ with DVC"
```

## 9. Conflict Resolution

When two collaborators edit the same file, Git reports a merge conflict. Resolve it systematically:

```bash
# Attempt to merge
git merge collaborator/branch-name

# If conflict occurs, Git marks the file:
# <<<<<<< HEAD
# your version of the code
# =======
# their version of the code
# >>>>>>> collaborator/branch-name

# Steps to resolve:
# 1. Open the conflicting file
# 2. Choose the correct version (or combine both)
# 3. Remove the conflict markers
# 4. Test that the code still works
# 5. Stage and commit

git add scripts/run_analysis.R
git commit -m "Resolve merge conflict in run_analysis.R: keep updated filter threshold"
```

| Problem | Cause | Solution |
|---|---|---|
| `fatal: not a git repository` | Not in a Git-initialized directory | Run `git init` or `cd` to the correct directory |
| Accidentally committed large files | Forgot `.gitignore` | Use `git rm --cached file` and update `.gitignore` |
| Lost work after `git reset --hard` | Destructive reset | Use `git reflog` to find and recover the lost commit |
| Push rejected | Remote has newer commits | Run `git pull --rebase` before pushing |

"""
}

# 9. biological-data-formats.md (638 words)
expansions["biological-data-formats.md"] = {
    "insert_before": "## Practical Exercise",
    "content": """
## 5. Format Specifications and Validation

Every file format has a formal specification. Understanding the column structure prevents silent parsing errors.

### FASTA Format
```text
>sequence_id optional description
ATCGATCGATCGATCGATCG
ATCGATCGATCGATCG
```
- Header lines start with `>`
- Sequence can span multiple lines
- No quality scores (use FASTQ for raw reads)

### FASTQ Format
```text
@read_id instrument:run:flowcell:lane:tile:x:y
ATCGATCGATCGATCGATCG
+
IIIIIIIIIIIIIIIIIIIII
```
- Four lines per record: header, sequence, separator, quality
- Quality scores are Phred+33 encoded ASCII characters
- `I` = Q40 (1 in 10,000 error rate), `!` = Q0

### SAM/BAM Format
```text
@HD  VN:1.6  SO:coordinate
@SQ  SN:chr1  LN:248956422
read001  0  chr1  1000  60  150M  *  0  0  ATCG...  IIII...  NM:i:0
```
- Header lines start with `@`
- 11 mandatory columns: QNAME, FLAG, RNAME, POS, MAPQ, CIGAR, RNEXT, PNEXT, TLEN, SEQ, QUAL
- BAM is the compressed binary version of SAM

## 6. Validation Commands

Always validate file integrity before analysis. Corrupted files produce silent errors that propagate through entire pipelines.

```bash
# Validate FASTQ integrity
# Count records (should be divisible by 4)
wc -l reads.fastq  # Must be multiple of 4

# Validate BAM file
samtools quickcheck aligned.bam && echo "OK" || echo "CORRUPTED"

# Validate VCF file
bcftools stats variants.vcf | head -20

# Check FASTA index consistency
samtools faidx reference.fa
# Creates reference.fa.fai — verify chromosome count
wc -l reference.fa.fai

# Verify file checksums after transfer
md5sum -c checksums.md5
```

## 7. Format Conversion

Converting between formats is a routine bioinformatics task. Use established tools rather than custom scripts to avoid edge cases.

| From | To | Tool | Command |
|---|---|---|---|
| SAM | BAM | samtools | `samtools view -bS input.sam > output.bam` |
| BAM | SAM | samtools | `samtools view -h input.bam > output.sam` |
| BAM | FASTQ | samtools | `samtools fastq input.bam > output.fastq` |
| FASTQ | FASTA | seqtk | `seqtk seq -a input.fastq > output.fasta` |
| GFF3 | GTF | gffread | `gffread input.gff3 -T -o output.gtf` |
| VCF | BED | bedtools | `bedtools vcf2bed < input.vcf > output.bed` |

**Warning:** Coordinate system differences between BED (0-based, half-open) and GTF/VCF (1-based, closed) are the single most common source of off-by-one errors in bioinformatics. Always verify coordinates after conversion.

## 8. Compression and Storage

Raw bioinformatics files are typically very large. Use appropriate compression to save storage and transfer time.

```bash
# BGZF compression (block-gzipped, allows random access)
bgzip -c variants.vcf > variants.vcf.gz
tabix -p vcf variants.vcf.gz

# Standard gzip (no random access)
gzip reads.fastq

# Check compressed file integrity
gzip -t reads.fastq.gz && echo "OK" || echo "CORRUPTED"
```

| File Type | Typical Size (human WGS) | Compressed Size | Compression Ratio |
|---|---|---|---|
| FASTQ (paired) | ~200 GB | ~60 GB (gzip) | 3:1 |
| BAM (aligned) | ~80 GB | N/A (already binary) | — |
| VCF (variants) | ~5 GB | ~500 MB (bgzip) | 10:1 |
| BED (regions) | ~10 MB | ~2 MB (gzip) | 5:1 |

"""
}

# 10. statistics-for-bioinformatics.md (644 words)
expansions["statistics-for-bioinformatics.md"] = {
    "insert_before": "## Practical Exercise",
    "content": """
## 5. Hypothesis Testing Framework

Every statistical test in bioinformatics follows the same logical framework:

1. **State the null hypothesis (H₀):** "There is no difference in gene expression between treated and control groups."
2. **Choose a test:** Based on data distribution, sample size, and experimental design.
3. **Calculate the test statistic and p-value.**
4. **Apply multiple testing correction** (critical in genomics — you're testing thousands of genes).
5. **Interpret the result** in biological context, not just statistical significance.

## 6. A Worked Statistical Test

```r
# Example: Test whether a gene is differentially expressed
# between control and treated groups

control <- c(5.2, 4.8, 5.5, 4.9, 5.1)
treated <- c(8.3, 7.9, 8.7, 8.1, 8.5)

# Step 1: Check normality assumption
shapiro.test(control)  # p = 0.92 (normal)
shapiro.test(treated)  # p = 0.88 (normal)

# Step 2: Check equal variance
var.test(control, treated)  # p = 0.85 (variances equal)

# Step 3: Perform two-sample t-test
result <- t.test(control, treated, var.equal = TRUE)
print(result)

# Output:
# t = -14.2, df = 8, p-value = 1.2e-06
# 95% CI: [-3.73, -2.67]
# mean of control = 5.10, mean of treated = 8.30

# Step 4: Calculate effect size (Cohen's d)
cohens_d <- (mean(treated) - mean(control)) / sqrt(
  ((length(control)-1)*var(control) + (length(treated)-1)*var(treated)) /
  (length(control) + length(treated) - 2)
)
print(paste("Cohen's d:", round(cohens_d, 2)))
# Cohen's d: 12.73 (very large effect)
```

## 7. Multiple Testing Correction

When testing thousands of genes simultaneously, the probability of false positives increases dramatically. A p-value threshold of 0.05 across 20,000 genes would produce ~1,000 false positives by chance.

```r
# Simulate: 20,000 genes, no real differential expression
set.seed(42)
p_values <- runif(20000)  # Uniform p-values (null hypothesis true for all)

# Without correction: how many "significant" at p < 0.05?
sum(p_values < 0.05)  # ~1,000 false positives!

# Bonferroni correction (very conservative)
p_bonferroni <- p.adjust(p_values, method = "bonferroni")
sum(p_bonferroni < 0.05)  # ~0 (correctly rejects none)

# Benjamini-Hochberg (FDR) correction (recommended for genomics)
p_fdr <- p.adjust(p_values, method = "BH")
sum(p_fdr < 0.05)  # ~0 (correctly rejects none)
```

| Method | Controls | Stringency | Best For |
|---|---|---|---|
| Bonferroni | Family-wise error rate (FWER) | Very strict | Clinical/diagnostic applications |
| Benjamini-Hochberg (BH) | False discovery rate (FDR) | Moderate | Exploratory genomics, RNA-seq |
| Storey's q-value | Positive FDR | Least strict | Large-scale screening |

## 8. Common Statistical Pitfalls in Bioinformatics

| Pitfall | Example | Consequence | Prevention |
|---|---|---|---|
| Pseudoreplication | Treating technical replicates as biological | Inflated sample size, false significance | Aggregate technical replicates before testing |
| Data dredging | Testing every gene pair for correlation | Massive multiple testing burden | Pre-register hypotheses or correct for all tests |
| P-hacking | Trying different tests until p < 0.05 | Unreliable results | Choose the test before seeing data |
| Ignoring effect size | Reporting p = 0.001 for a 1.05-fold change | Statistically significant but biologically meaningless | Always report fold change AND p-value |
| Circular analysis | Using all data to select genes, then testing the same genes | 100% false discovery rate | Use independent training/test splits |

## 9. Choosing the Right Statistical Test

| Data Type | Groups | Distribution | Recommended Test |
|---|---|---|---|
| Continuous | 2 groups | Normal | Student's t-test or Welch's t-test |
| Continuous | 2 groups | Non-normal | Wilcoxon rank-sum (Mann-Whitney U) |
| Continuous | ≥3 groups | Normal | One-way ANOVA + post-hoc |
| Continuous | ≥3 groups | Non-normal | Kruskal-Wallis + Dunn's test |
| Count data | 2+ groups | Negative binomial | DESeq2, edgeR |
| Categorical | 2 categories | N/A | Fisher's exact test or Chi-squared |
| Survival | Time-to-event | N/A | Log-rank test, Cox regression |

"""
}


# Now apply expansions
for filename, spec in expansions.items():
    filepath = f"{LESSONS_DIR}/{filename}"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    marker = spec["insert_before"]
    if marker in content:
        content = content.replace(marker, spec["content"] + "\n" + marker)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        words = len(content.split())
        print(f"✅ Expanded {filename} → {words} words")
    else:
        print(f"❌ Could not find marker '{marker}' in {filename}")

print("\nDone! All 10 shortest tutorials expanded.")
