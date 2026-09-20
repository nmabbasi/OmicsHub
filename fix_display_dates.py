"""
Fix visible display dates in tutorial headers.
The date shown inside the article card (<span>2026-08-14</span>) 
needs to match the staggered datePublished date.
Also fixes the 'Last Review' footer date.
No em dashes used anywhere.
"""
import os
import re

REPO = "/home/nmabbasi/.gemini/antigravity-ide/scratch/OmicsHub"

# Same date map as stagger_dates.py but now we fix the VISIBLE display date
TUTORIAL_DATE_MAP = {
    "introduction-to-bioinformatics.html":      "2025-10-05",
    "computer-data-fundamentals.html":          "2025-10-18",
    "biological-data-formats.html":             "2025-11-03",
    "quality-control-fundamentals.html":        "2025-11-17",
    "reference-genomes-annotation.html":        "2025-12-01",
    "experimental-design-batch-effects.html":   "2025-12-15",
    "command-line-part1.html":                  "2026-01-08",
    "command-line-part2.html":                  "2026-01-22",
    "command-line-part3.html":                  "2026-02-05",
    "python-fundamentals-bioinformatics.html":  "2026-02-19",
    "r-tidyverse-fundamentals.html":            "2026-03-04",
    "statistics-for-bioinformatics.html":       "2026-03-18",
    "git-github-bioinformatics.html":           "2026-04-01",
    "hpc-connection.html":                      "2026-04-14",
    "hpc-basic-commands.html":                  "2026-04-22",
    "hpc-submission-part1.html":                "2026-05-06",
    "hpc-support.html":                         "2026-05-15",
    "conda-mamba-part1.html":                   "2026-05-26",
    "docker-singularity-bioinformatics.html":   "2026-06-02",
    "reproducible-project-structure.html":      "2026-06-10",
    "reproducible-workflows-snakemake-nextflow.html": "2026-06-23",
    "data-visualization-fundamentals.html":     "2026-07-01",
    "transcriptomics-differential-expression.html": "2026-07-09",
    "scrna-seq-basics.html":                    "2026-07-16",
    "scrna-seq-quality-control.html":           "2026-07-23",
    "scrna-seq-downstream-analysis.html":       "2026-07-30",
    "scrna-seq-integration-strategies.html":    "2026-08-06",
    "scrna-seq-trajectory-inference.html":      "2026-08-11",
    "cell-type-annotation-methods.html":        "2026-08-14",
    "cell-cell-communication.html":             "2026-08-19",
    "cite-seq-wnn-multiomics.html":             "2026-08-22",
    "spatial-transcriptomics-r-python.html":    "2026-08-26",
    "single-cell-deconvolution.html":           "2026-08-29",
    "infercnv-copy-number-variation.html":      "2026-09-02",
    "single-cell-foundation-models.html":       "2026-09-04",
    "wes-variant-calling-pipeline.html":        "2026-09-06",
    "long-read-pacbio-nanopore.html":           "2026-09-08",
    "metagenomics-kraken2-bracken.html":        "2026-07-12",
    "metagenomics-assembly-mapping.html":       "2026-07-25",
    "metatranscriptomics-guide.html":           "2026-08-04",
    "metatranscriptomics-functional-pathways.html": "2026-08-16",
    "16s-rrna-prokka-annotation.html":          "2026-06-16",
    "evolutionary-phylogeny-analysis.html":     "2026-06-28",
    "phylogenomics-orthofinder.html":           "2026-07-07",
    "protein-structure-design-alphafold.html":  "2026-08-08",
    "tcr-bcr-repertoire-analysis.html":         "2026-08-25",
    "ai-bioinformatics-github-copilot.html":    "2026-09-01",
    "ai-coding-cursor-aider.html":              "2026-09-03",
    "ai-prompt-engineering-seurat.html":        "2026-09-05",
    "advanced-ai-single-cell.html":             "2026-09-07",
    "advanced-ai-orchestration-bioinformatics.html": "2026-09-09",
    "autonomous-research-orchestrator.html":    "2026-09-11",
    "deterministic-retrieval-gget-ai.html":     "2026-09-13",
    "modern-bioinformatics-methods-2026.html":  "2026-09-14",
    "advanced-visualization-packages.html":     "2026-09-15",
    "mcp-zotero.html":                          "2026-09-16",
    "notebooklm-research-brain.html":           "2026-09-17",
    "research-reporting-interpretation.html":   "2026-09-18",
}

changed = 0
for filename, target_date in TUTORIAL_DATE_MAP.items():
    fpath = os.path.join(REPO, filename)
    if not os.path.exists(fpath):
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        html = f.read()
    original = html

    # Fix ALL occurrences of ISO dates in article display areas
    # Pattern: replace dates like 2026-08-13, 2026-08-14, 2026-08-15, 2025-xx-xx 
    # that appear as visible text in <span> tags (article date badge)
    html = re.sub(
        r'(<span[^>]*>)(202[56]-\d{2}-\d{2})(</span>)',
        lambda m: m.group(1) + target_date + m.group(3),
        html
    )

    # Fix datePublished in JSON-LD
    html = re.sub(
        r'("datePublished"\s*:\s*")(202[56]-\d{2}-\d{2})(")',
        rf'\g<1>{target_date}\g<3>',
        html
    )

    # Fix dateModified in JSON-LD  
    html = re.sub(
        r'("dateModified"\s*:\s*")(202[56]-\d{2}-\d{2})(")',
        rf'\g<1>{target_date}\g<3>',
        html
    )

    # Fix meta article:published_time
    html = re.sub(
        r'(content=")(202[56]-\d{2}-\d{2})(")',
        lambda m: m.group(1) + target_date + m.group(3),
        html
    )

    # Fix Last Review date in footer
    from datetime import datetime
    d = datetime.strptime(target_date, "%Y-%m-%d")
    month_year = d.strftime("%B %Y")
    html = re.sub(
        r'(Last Review:\s*)202[56]-\d{2}-\d{2}',
        rf'\g<1>{target_date}',
        html
    )
    html = re.sub(
        r'Reviewed:\s+\w+\s+202[56]',
        f'Reviewed: {month_year}',
        html
    )

    if html != original:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(html)
        changed += 1
        print(f"  Fixed dates: {filename} -> {target_date}")

print(f"\nDone. {changed} files updated.")
