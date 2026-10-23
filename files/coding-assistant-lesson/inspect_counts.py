#!/usr/bin/env python3
"""Check the shape and integer syntax of the lesson's invented count table.

This does not establish provenance, count-generation methods, biological
validity, sample independence, or whether the values are appropriate for an
analysis. It is a format and arithmetic exercise only.
"""
import csv
from pathlib import Path
import re
import sys

INTEGER = re.compile(r"^[0-9]+$")


def read_count_table(path: Path) -> tuple[list[str], list[str], list[list[int]]]:
    """Return sample names, gene names, and integer rows for genes by samples."""
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle, delimiter="\t"))
    if len(rows) < 2 or len(rows[0]) < 2:
        raise ValueError("Expected a header and at least one gene and one sample.")

    header = rows[0]
    if header[0] != "gene_id":
        raise ValueError("The first column must be named gene_id.")
    samples = header[1:]
    if any(not name for name in samples) or len(set(samples)) != len(samples):
        raise ValueError("Sample column names must be nonempty and unique.")

    genes = []
    matrix = []
    for line_number, row in enumerate(rows[1:], start=2):
        if len(row) != len(header):
            raise ValueError(f"Line {line_number} has {len(row)} fields; expected {len(header)}.")
        gene = row[0]
        if not gene or gene in genes:
            raise ValueError(f"Line {line_number} has an empty or duplicate gene_id.")
        genes.append(gene)
        values = []
        for column_number, text in enumerate(row[1:], start=2):
            if not INTEGER.fullmatch(text):
                raise ValueError(
                    f"Line {line_number}, column {column_number} is not a nonnegative integer count: {text!r}."
                )
            values.append(int(text))
        matrix.append(values)
    if not genes:
        raise ValueError("The table must contain at least one gene row.")
    return samples, genes, matrix


def sample_totals(samples: list[str], matrix: list[list[int]]) -> dict[str, int]:
    """Sum each sample column, because each input row represents a gene."""
    return {sample: sum(row[index] for row in matrix) for index, sample in enumerate(samples)}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python3 inspect_counts.py counts.tsv", file=sys.stderr)
        return 2
    try:
        samples, genes, matrix = read_count_table(Path(argv[1]))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"REJECT: {exc}", file=sys.stderr)
        return 1
    totals = sample_totals(samples, matrix)
    print(f"Orientation: rows=genes ({len(genes)}); columns=samples ({len(samples)}).")
    for sample, total in totals.items():
        print(f"{sample} column sum: {total}")
    print(f"All-cell arithmetic sum: {sum(totals.values())}")
    print("These format and sum checks do not verify provenance, raw-count status, sample independence, or biological validity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
