---
title: "Git and GitHub for Bioinformatics"
category: "Foundations & Prerequisites"
date: "2026-08-15"
image: "images/git-github-bioinformatics.png"
excerpt: "Use Git and GitHub to track code, document analyses, collaborate safely, and make bioinformatics projects reproducible."
author: "Nasir Mahmood Abbasi, PhD"
---

<div class="mb-10 text-xl text-gray-600 leading-relaxed">
  <p>Git records how a project changes over time. GitHub provides a collaborative home for repositories, issues, releases, and documentation. Together they make it possible to identify the exact scripts and configuration used to produce a result. Never commit private patient data or credentials.</p>
</div>

## Learning Objectives & Prerequisites

**By the end of this lesson, you should be able to:**

- Create a repository, make commits, inspect history, and use branches.
- Write a useful README and `.gitignore` for a bioinformatics project.
- Push code without exposing raw data, passwords, tokens, or private identifiers.
- Use issues and pull requests for review.

**Prerequisites:**

- Complete [Computer and Data Fundamentals](computer-data-fundamentals.html).
- Install Git and create a GitHub account if you want to push to a remote repository.

## 1. Start a reproducible repository

A repository should contain scripts, configuration, documentation, and small example data—not an uncontrolled dump of raw sequencing files.

```bash
mkdir omics-demo && cd omics-demo
git init
printf "# Omics demo\n" > README.md
printf "*.fastq.gz\n.env\nresults/\n" > .gitignore
git add README.md .gitignore
git commit -m "Initialize reproducible project"
```

## 2. Record meaningful changes

A commit should represent one understandable change. Use `git diff` before committing and write messages that explain what changed.

```bash
git status
git diff
git log --oneline --decorate -5
git add scripts/
git commit -m "Add read QC summary script"
```

## 3. Connect a remote safely

Use SSH keys or a credential manager. Never put a personal access token in a URL, shell history, notebook, or script.

```bash
git remote add origin https://github.com/USER/REPO.git
git branch -M main
git push -u origin main
```

## 4. Reproducibility checklist

Record software versions, environment files, reference versions, command parameters, and the commit hash associated with a result.

```bash
git rev-parse --short HEAD
python --version
conda env export --from-history > environment.yml
```

## Practical Exercise

Create a small repository containing a README, `.gitignore`, one script, and an environment file. Make two commits and use `git log` to show the history.

**Pass criteria:** The repository history contains two meaningful commits, no credentials or raw human data are tracked, and the README explains how to reproduce the example.

## Troubleshooting

If a push is rejected, pull and inspect the remote history before forcing anything. If a secret was committed, rotate it immediately; deleting the file is not enough because it remains in Git history.

## Knowledge Check & Assessment

### 1. Concept Verification

Write short answers explaining the main concepts, the assumptions behind them, and one way a careless workflow could produce a misleading result.

### 2. Practical Execution

Complete the practical exercise above and save the command, script, table, or figure in the project structure. **Pass Criteria:** The repository history contains two meaningful commits, no credentials or raw human data are tracked, and the README explains how to reproduce the example.

### 3. Troubleshooting

Explain what you would inspect first if the output were empty, malformed, unexpectedly large, or failed because of a missing file, package, permission, memory, or metadata problem.

## Next Steps

Continue with [Reproducible Project Structure](reproducible-project-structure.html) and [Python Fundamentals](python-fundamentals-bioinformatics.html). Record the software versions, dataset or example inputs, and any decisions you made.
