# The Omics Hub

Source code for [theomicshub.com](https://theomicshub.com), an open-access curriculum and interactive portal designed for life scientists moving from Linux HPC terminal workflows into R-based single-cell transcriptomics.

[![Website: Live](https://img.shields.io/badge/Website-theomicshub.com-0284c7.svg)](https://theomicshub.com)
[![Tests: 585 Passing](https://img.shields.io/badge/Tests-585%20Passed-10b981.svg)]()
[![Stack: Vanilla HTML5 / CSS / JS](https://img.shields.io/badge/Stack-Vanilla%20Web-f59e0b.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What the Platform Covers

- **HPC & Cluster Foundations**: Connecting via SSH / MobaXterm, module environments, Conda environment isolation, and Slurm batch submission.
- **Linux to R Transition**: File handling, count matrix extraction, format conversions, and data hygiene between shell and statistical environments.
- **Single-Cell RNA-seq Workflows**: Quality control metrics, doublet filtering, normalization, dimensional reduction (PCA, UMAP), clustering, and marker gene identification with Seurat.

---

## Architecture & Design Principles

The site is built without heavy client-side frameworks (no React, no bundler overhead, no npm dependency tree) to ensure instant loading times and long-term maintainability:
- **Core Stack**: Semantic HTML5, Vanilla CSS3 with custom design tokens, and modular JavaScript.
- **Styling System**: CSS custom properties for light / dark modes, accessible contrast ratios (WCAG AA compliant), and responsive grid / flexbox layouts.
- **No external render blockers**: Built-in SVG icons and local system font fallbacks to guarantee fast first-contentful paint.

---

## Local Development

Preview the portal locally without installing any web frameworks:

```bash
# Clone the repository
git clone https://github.com/nmabbasi/OmicsHub.git
cd OmicsHub

# Start a local web server (Python 3)
python3 -m http.server 8000
```
Open `http://localhost:8000` in your browser.

---

## Running the Automated Test Suite

The repository includes a regression test suite covering DOM element structure, internal navigation links, and CSS contract enforcement:

```bash
# Run all unit and integration tests
python3 -m unittest discover -s tests -p "test_*.py"
```

---

## Directory Structure

```text
OmicsHub/
├── index.html              # Main landing page
├── start-here.html         # Curriculum roadmap and learner stepper
├── css/                    # Shared stylesheets and theme tokens
├── js/                     # Client-side search, theme toggle, and navigators
├── pages/                  # Markdown / HTML tutorial pages
├── tests/                  # Automated Python regression test suite
└── .github/workflows/      # Automated GitHub Pages deployment pipeline
```

---

## Author & Contact

**Nasir Mahmood Abbasi, PhD**  
Computational Biologist | Université de Bordeaux / CNRS  
- Website: [nmabbasi.github.io](https://nmabbasi.github.io/)  
- Email: [nmabbasi@gmail.com](mailto:nmabbasi@gmail.com)
