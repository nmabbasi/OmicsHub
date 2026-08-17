---
title: "Statistics for Bioinformatics"
category: "Foundations & Prerequisites"
date: "2026-08-15"
image: "images/statistics-bioinformatics-workstation.webp"
excerpt: "Learn distributions, replicates, effect sizes, multiple testing, and statistical power for biological data analysis."
author: "Nasir Mahmood Abbasi, PhD"
---

<div class="mb-10 text-xl text-gray-600 leading-relaxed">
  <p>Statistics helps distinguish repeatable evidence from noise. In bioinformatics, the number of measurements can be enormous while the number of biological replicates remains small, so study design and effect size matter as much as a p-value.</p>
</div>

## Learning Objectives & Prerequisites

**By the end of this lesson, you should be able to:**

- Distinguish biological from technical replicates.
- Explain effect size, uncertainty, p-values, and false discovery rate.
- Choose a simple comparison without violating independence assumptions.
- Interpret a result with limitations and not just a significance threshold.

**Prerequisites:**

- Basic algebra and a data frame in R or Python.
- Complete [Quality Control Fundamentals](quality-control-fundamentals.html).

## 1. Replicates and distributions

Biological replicates represent independent experimental units; technical replicates measure the same unit repeatedly. Plot the data before selecting a test.

```r
set.seed(7)
x <- rnorm(12, mean=10, sd=2)
summary(x)
hist(x, main="Example distribution", xlab="Measurement")
```

## 2. Effect size and uncertainty

A difference of 0.2 may be statistically significant in a huge dataset but scientifically unimportant. Report a difference or fold change with uncertainty and the scale used.

```r
mean_treated - mean_control
log2(mean_treated / mean_control)
```

## 3. Multiple testing

Testing thousands of genes creates many false positives. Control the false discovery rate with an appropriate correction and pre-specify the threshold.

```r
p.adjust(p_values, method = "BH")
```

### Matched Python and R example

Use the same biological-replicate vectors in either language. The code illustrates a simple independent-sample comparison and a Benjamini–Hochberg adjustment; it does not replace checking the design, assumptions, or effect size.

```python
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests

control = np.array([8.9, 9.8, 10.4, 9.5])
treated = np.array([11.2, 10.7, 12.1, 11.4])
result = stats.ttest_ind(treated, control, equal_var=False)
print({"mean_difference": treated.mean() - control.mean(), "p_value": result.pvalue})

adjusted_p = multipletests(p_values, method="fdr_bh")[1]
```
```r
control <- c(8.9, 9.8, 10.4, 9.5)
treated <- c(11.2, 10.7, 12.1, 11.4)
result <- t.test(treated, control, var.equal = FALSE)
print(list(mean_difference = mean(treated) - mean(control), p_value = result$p.value))

adjusted_p <- p.adjust(p_values, method = "BH")
```

## 4. Power and limitations

Power depends on effect size, variability, sample size, and the decision threshold. A non-significant result is not proof of no effect; report the uncertainty and observed effect.

```text
Report: effect size, confidence interval, sample size, test, adjusted p-value, and biological limitation.
```

## Practical Exercise

Take a small table with two conditions. Plot each group, report the mean difference, and explain why biological replicate count matters more than simply adding cells or reads.

**Pass criteria:** The report includes replicate definitions, effect size, uncertainty, multiple-testing handling, and a limitation statement.

## Troubleshooting

If assumptions fail, do not automatically switch tests. Inspect distributions, dependence, batch, outliers, and the design before consulting a statistician.

## Knowledge Check & Assessment

### 1. Concept Verification

Write short answers explaining the main concepts, the assumptions behind them, and one way a careless workflow could produce a misleading result.

### 2. Practical Execution

Complete the practical exercise above and save the command, script, table, or figure in the project structure. **Pass Criteria:** The report includes replicate definitions, effect size, uncertainty, multiple-testing handling, and a limitation statement.

### 3. Troubleshooting

Explain what you would inspect first if the output were empty, malformed, unexpectedly large, or failed because of a missing file, package, permission, memory, or metadata problem.

## Next Steps

Continue with [Experimental Design and Batch Effects](experimental-design-batch-effects.html) and [Pseudobulk DE Analysis](transcriptomics-differential-expression.html). Record the software versions, dataset or example inputs, and any decisions you made.
