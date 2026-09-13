---
title: "Python Fundamentals for Bioinformatics"
category: "Foundations & Prerequisites"
date: "2026-08-15"
image: "images/python-bioinformatics-workstation.webp"
excerpt: "Learn Python variables, collections, functions, files, and simple sequence processing for bioinformatics."
author: "Nasir Mahmood Abbasi, PhD"
---

<div class="mb-10 text-xl text-gray-600 leading-relaxed">
  <p>Python becomes useful in bioinformatics when it turns repeated manual inspection into a testable program. This lesson teaches a small, practical subset of Python and applies it to sequence records and tabular data.</p>
</div>

## Learning Objectives & Prerequisites

**By the end of this lesson, you should be able to:**

- Use variables, lists, dictionaries, loops, functions, and conditions.
- Read text files safely and count simple sequence statistics.
- Use a virtual environment and record package versions.
- Write a small script with a clear input and output.

**Prerequisites:**

- Complete [Basic Navigation](command-line-part1.html).
- Python 3.10 or newer and a text editor.


### Expected Output

By the end of this lesson, you should have: **A small reproducible Python script or notebook that reads a biological table, performs one transparent transformation, and writes a named output file.**

## 1. Values and collections

Use strings for sequences, lists for ordered records, and dictionaries for keyed metadata.

```python
sequence = "ACGTACGT"
length = len(sequence)
gc = (sequence.count("G") + sequence.count("C")) / length
print(f"length={length}, gc={gc:.2%}")
```

## 2. Functions and validation

Functions make repeated operations testable. Validate input before calculating a result.

```python
def gc_fraction(sequence):
    seq = sequence.strip().upper()
    if not seq or any(base not in "ACGTN" for base in seq):
        raise ValueError("Expected a DNA sequence")
    return (seq.count("G") + seq.count("C")) / len(seq)
```

## 3. Read a small FASTA file

For production work use a tested parser such as Biopython, but a simple parser is useful for understanding the format.

```python
def fasta_records(path):
    name, seq = None, []
    with open(path) as handle:
        for line in handle:
            line=line.strip()
            if line.startswith(">"):
                if name is not None: yield name, "".join(seq)
                name, seq = line[1:], []
            else: seq.append(line)
        if name is not None: yield name, "".join(seq)
```

## 4. Environments and tests

Keep project dependencies isolated and test a function with a known sequence.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install biopython
python -c "import Bio; print(Bio.__version__)"
```


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
    """Calculate GC content of a DNA sequence."""
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
counts = pd.read_csv("data/raw/gene_counts.tsv", sep="\t", index_col=0)
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
    """Load and filter a gene count matrix.
    
    Args:
        filepath: Path to tab-separated count matrix.
        min_total: Minimum total counts across all samples.
    
    Returns:
        Filtered DataFrame with genes as rows, samples as columns.
    
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the matrix is empty after filtering.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Count matrix not found: {path}")
    
    df = pd.read_csv(path, sep="\t", index_col=0)
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


## Practical Exercise

Write `fasta_gc.py` that prints each FASTA identifier, sequence length, and GC percentage. Test it on two records, including one containing `N`.

**Pass criteria:** The script validates input, prints deterministic output for both records, and exits with a useful error for invalid characters.

## Troubleshooting

If imports fail, confirm the virtual environment is active. If a file is not found, print the current directory and use an explicit relative or absolute path.

## Knowledge Check & Assessment

### 1. Concept Verification

Write short answers explaining the main concepts, the assumptions behind them, and one way a careless workflow could produce a misleading result.

### 2. Practical Execution

Complete the practical exercise above and save the command, script, table, or figure in the project structure. **Pass Criteria:** The script validates input, prints deterministic output for both records, and exits with a useful error for invalid characters.

### 3. Troubleshooting

Explain what you would inspect first if the output were empty, malformed, unexpectedly large, or failed because of a missing file, package, permission, memory, or metadata problem.

## Next Steps

Continue with [R and Tidyverse Fundamentals](r-tidyverse-fundamentals.html) and [Biological Data Formats](biological-data-formats.html). Record the software versions, dataset or example inputs, and any decisions you made.
