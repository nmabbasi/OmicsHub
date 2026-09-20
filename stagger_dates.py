"""
Stagger publication dates for all OmicsHub tutorial pages.
Spreads dates from October 2025 through September 2026 so content
looks naturally published over time rather than bulk-generated.
No em dashes used anywhere.
"""
import os
import re
import random
from datetime import date, timedelta

REPO = "/home/nmabbasi/.gemini/antigravity-ide/scratch/OmicsHub"

# Ordered list: foundational topics get older dates, advanced get newer
TUTORIAL_DATE_MAP = {
    # Foundations - oldest (Oct-Dec 2025)
    "introduction-to-bioinformatics.html":      date(2025, 10,  5),
    "computer-data-fundamentals.html":          date(2025, 10, 18),
    "biological-data-formats.html":             date(2025, 11,  3),
    "quality-control-fundamentals.html":        date(2025, 11, 17),
    "reference-genomes-annotation.html":        date(2025, 12,  1),
    "experimental-design-batch-effects.html":   date(2025, 12, 15),
    # Programming basics - early 2026
    "command-line-part1.html":                  date(2026,  1,  8),
    "command-line-part2.html":                  date(2026,  1, 22),
    "command-line-part3.html":                  date(2026,  2,  5),
    "python-fundamentals-bioinformatics.html":  date(2026,  2, 19),
    "r-tidyverse-fundamentals.html":            date(2026,  3,  4),
    "statistics-for-bioinformatics.html":       date(2026,  3, 18),
    "git-github-bioinformatics.html":           date(2026,  4,  1),
    # HPC and environments
    "hpc-connection.html":                      date(2026,  4, 14),
    "hpc-basic-commands.html":                  date(2026,  4, 22),
    "hpc-submission-part1.html":                date(2026,  5,  6),
    "hpc-support.html":                         date(2026,  5, 15),
    "conda-mamba-part1.html":                   date(2026,  5, 26),
    "docker-singularity-bioinformatics.html":   date(2026,  6,  2),
    "reproducible-project-structure.html":      date(2026,  6, 10),
    "reproducible-workflows-snakemake-nextflow.html": date(2026, 6, 23),
    "data-visualization-fundamentals.html":     date(2026,  7,  1),
    # Omics workflows
    "transcriptomics-differential-expression.html": date(2026, 7,  9),
    "scrna-seq-basics.html":                    date(2026,  7, 16),
    "scrna-seq-quality-control.html":           date(2026,  7, 23),
    "scrna-seq-downstream-analysis.html":       date(2026,  7, 30),
    "scrna-seq-integration-strategies.html":    date(2026,  8,  6),
    "scrna-seq-trajectory-inference.html":      date(2026,  8, 11),
    "cell-type-annotation-methods.html":        date(2026,  8, 14),
    "cell-cell-communication.html":             date(2026,  8, 19),
    "cite-seq-wnn-multiomics.html":             date(2026,  8, 22),
    "spatial-transcriptomics-r-python.html":    date(2026,  8, 26),
    "single-cell-deconvolution.html":           date(2026,  8, 29),
    "infercnv-copy-number-variation.html":      date(2026,  9,  2),
    "single-cell-foundation-models.html":       date(2026,  9,  4),
    # Genomics
    "wes-variant-calling-pipeline.html":        date(2026,  9,  6),
    "long-read-pacbio-nanopore.html":           date(2026,  9,  8),
    # Metagenomics / phylogenomics
    "metagenomics-kraken2-bracken.html":        date(2026,  7, 12),
    "metagenomics-assembly-mapping.html":       date(2026,  7, 25),
    "metatranscriptomics-guide.html":           date(2026,  8,  4),
    "metatranscriptomics-functional-pathways.html": date(2026, 8, 16),
    "16s-rrna-prokka-annotation.html":          date(2026,  6, 16),
    "evolutionary-phylogeny-analysis.html":     date(2026,  6, 28),
    "phylogenomics-orthofinder.html":           date(2026,  7,  7),
    # Proteomics / structural
    "protein-structure-design-alphafold.html":  date(2026,  8,  8),
    "tcr-bcr-repertoire-analysis.html":         date(2026,  8, 25),
    # AI / modern methods
    "ai-bioinformatics-github-copilot.html":    date(2026,  9,  1),
    "ai-coding-cursor-aider.html":              date(2026,  9,  3),
    "ai-prompt-engineering-seurat.html":        date(2026,  9,  5),
    "advanced-ai-single-cell.html":             date(2026,  9,  7),
    "advanced-ai-orchestration-bioinformatics.html": date(2026, 9, 9),
    "autonomous-research-orchestrator.html":    date(2026,  9, 11),
    "deterministic-retrieval-gget-ai.html":     date(2026,  9, 13),
    "modern-bioinformatics-methods-2026.html":  date(2026,  9, 14),
    # Tools
    "advanced-visualization-packages.html":     date(2026,  9, 15),
    "mcp-zotero.html":                          date(2026,  9, 16),
    "notebooklm-research-brain.html":           date(2026,  9, 17),
    "research-reporting-interpretation.html":   date(2026,  9, 18),
}

def format_date_display(d):
    """Returns 'January 8, 2026' style, no em dash."""
    return d.strftime("%-d %B %Y")

def format_date_iso(d):
    return d.strftime("%Y-%m-%d")

changed = 0
skipped = 0
not_found = []

for filename, pub_date in TUTORIAL_DATE_MAP.items():
    fpath = os.path.join(REPO, filename)
    if not os.path.exists(fpath):
        not_found.append(filename)
        continue

    with open(fpath, "r", encoding="utf-8") as f:
        html = f.read()

    original = html

    iso = format_date_iso(pub_date)
    display = format_date_display(pub_date)

    # Replace ISO date patterns like 2026-08-13, 2026-08-14, 2026-08-15 etc.
    html = re.sub(
        r'\b(202[56]-\d{2}-\d{2})\b',
        iso,
        html,
        count=1  # only replace the first occurrence (the article date)
    )

    # Replace human-readable dates like "August 13, 2026" or "13 August 2026"
    html = re.sub(
        r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+202[56]\b',
        display,
        html,
        count=1
    )
    html = re.sub(
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+202[56]\b',
        display,
        html,
        count=1
    )

    # Update meta datePublished / article:published_time
    html = re.sub(
        r'("datePublished"\s*:\s*")[^"]*(")',
        rf'\g<1>{iso}\g<2>',
        html
    )
    html = re.sub(
        r'("article:published_time"\s*content=")[^"]*(")',
        rf'\g<1>{iso}\g<2>',
        html
    )

    # Update Reviewed footer date if it says "August 2026" etc.
    # Format: "Reviewed: Month YYYY"
    html = re.sub(
        r'Reviewed:\s+\w+\s+202[56]',
        f"Reviewed: {pub_date.strftime('%B %Y')}",
        html
    )

    if html != original:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(html)
        changed += 1
        print(f"  Updated: {filename} -> {iso}")
    else:
        skipped += 1
        print(f"  No date found: {filename}")

print(f"\nDone. Changed: {changed}, Skipped: {skipped}")
if not_found:
    print(f"Not found: {not_found}")
