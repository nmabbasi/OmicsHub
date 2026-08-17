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
