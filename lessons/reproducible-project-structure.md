---
title: "Reproducible Project Structure"
category: "Foundations & Prerequisites"
date: "2026-08-15"
image: "images/reproducible-project-structure.jpg"
excerpt: "Organize data, scripts, results, logs, environments, and metadata into a reproducible bioinformatics project."
author: "Nasir Mahmood Abbasi, PhD"
---

<div class="mb-10 text-xl text-gray-600 leading-relaxed">
  <p>A reproducible analysis is easier to inspect, rerun, share, and repair. A consistent project structure prevents raw files from being overwritten and makes the path from input to figure visible to collaborators.</p>
</div>

## Learning Objectives & Prerequisites

**By the end of this lesson, you should be able to:**

- Create a safe directory structure for data, code, results, logs, and configuration.
- Separate immutable raw data from derived files.
- Record commands, software versions, references, and random seeds.
- Write a README that lets another learner reproduce a result.

**Prerequisites:**

- Complete [Git and GitHub for Bioinformatics](git-github-bioinformatics.html).
- Know basic shell commands and one scripting language.


### Expected Output

By the end of this lesson, you should have: **A project directory with separated raw data, derived data, code, results, documentation, and an environment or dependency record.**

## 1. A practical layout

Use names that communicate role rather than personal computer paths.

```text
project/
├── README.md
├── config/
├── data/raw/
├── data/processed/
├── envs/
├── scripts/
├── results/figures/
├── results/tables/
└── logs/
```

## 2. Provenance files

Record input checksums, software versions, reference builds, commands, parameters, and the Git commit. Keep large or sensitive data outside public repositories.

```bash
find data/raw -type f -maxdepth 1 -print0 | xargs -0 sha256sum > config/raw_checksums.sha256
python --version > config/versions.txt
git rev-parse HEAD >> config/versions.txt
```

## 3. Configuration over hard-coding

Put sample names, paths, thresholds, and resource settings in a configuration file. This lets the same script run on a second dataset without editing logic.

```yaml
threads: 4
min_genes: 200
reference: GRCh38
input: data/raw/counts.tsv
```

## 4. README and results

Explain setup, expected inputs, commands, outputs, and limitations. Name results by meaning and preserve logs beside them.

```text
1. Create environment
2. Place validated input in data/raw
3. Run scripts/run_qc.sh
4. Inspect results/figures/qc.png
```

## Practical Exercise

Create this structure for a small project, add a README with four reproducible steps, and record one version file and one checksum file.

**Pass criteria:** A second learner can find the input, command, environment, output, log, and limitation without asking where files live.

## Troubleshooting

If a script depends on a personal path, replace it with a command-line argument or configuration value.

## Knowledge Check & Assessment

### 1. Concept Verification

Write short answers explaining the main concepts, the assumptions behind them, and one way a careless workflow could produce a misleading result.

### 2. Practical Execution

Complete the practical exercise above and save the command, script, table, or figure in the project structure. **Pass Criteria:** A second learner can find the input, command, environment, output, log, and limitation without asking where files live.

### 3. Troubleshooting

Explain what you would inspect first if the output were empty, malformed, unexpectedly large, or failed because of a missing file, package, permission, memory, or metadata problem.

## Next Steps

Continue with [Snakemake & Nextflow](reproducible-workflows-snakemake-nextflow.html) and [Research Reporting](research-reporting-interpretation.html). Record the software versions, dataset or example inputs, and any decisions you made.
