#!/usr/bin/env python3
"""Regression checks for three tutorial fixes prepared for owner review."""
from html import unescape
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CODE_BLOCK = re.compile(r'<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>', re.S)


def page_text(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def code_blocks(relative_path):
    return [unescape(code) for code in CODE_BLOCK.findall(page_text(relative_path))]


class KrakenSyntheticHierarchyTests(unittest.TestCase):
    def test_genus_clade_and_percent_reconcile_with_children(self):
        report = next(
            block for block in code_blocks("tutorials/metagenomics-kraken2-bracken.html")
            if "Examplegenus" in block
        )
        rows = [line.split(maxsplit=5) for line in report.splitlines() if line.strip()]
        root = next(row for row in rows if row[5] == "root")
        genus = next(row for row in rows if row[5] == "Examplegenus")
        children = [row for row in rows if row[5] in {"Example species", "Another species"}]
        root_clade = int(root[1])
        genus_clade = int(genus[1])
        genus_direct = int(genus[2])
        child_clades = sum(int(row[1]) for row in children)

        self.assertEqual(root_clade, 1000)
        self.assertEqual(genus_direct, 20)
        self.assertEqual(child_clades, 600)
        self.assertEqual(genus_clade, genus_direct + child_clades)
        self.assertEqual(float(genus[0]), round(100 * genus_clade / root_clade, 2))

    def test_bracken_practice_calculations_remain_explicit(self):
        text = page_text("tutorials/metagenomics-kraken2-bracken.html")
        self.assertIn("80 + 20 = 100 estimated reads, fraction 0.100", text)
        self.assertIn("50 + 10 = 60 estimated reads, fraction 0.060", text)
        self.assertIn("The unclassified fraction is 10%", text)


class GitHubCollaborationExampleTests(unittest.TestCase):
    def test_clone_update_and_review_are_cautious_and_complete(self):
        text = page_text("tutorials/git-github-bioinformatics.html")
        start = text.index("<h2>Clone, update, and contribute through review</h2>")
        end = text.index("<h2>Read the repository state</h2>", start)
        section = text[start:end]
        for required in (
            "git clone https://github.com/OWNER/REPOSITORY.git",
            "git status --short",
            "git pull --ff-only origin main",
            "git switch -c docs/input-notes",
            "git diff --check",
            "git diff --cached",
            "git push -u origin docs/input-notes",
            "pull request",
            "reviewer",
            "fork the repository",
            "force push or hard reset",
        ):
            with self.subTest(required=required):
                self.assertIn(required, section)
        self.assertNotIn("git reset --hard", section)
        self.assertNotIn("git push --force", section)


class SyntheticBcrExampleTests(unittest.TestCase):
    def test_reproducible_fixture_pair_check_and_expected_heavy_chain_counts(self):
        text = page_text("tutorials/tcr-bcr-repertoire-analysis.html")
        match = re.search(
            r'<pre id="bcr-synthetic-workflow"><code\b[^>]*>(.*?)</code></pre>',
            text,
            re.S,
        )
        self.assertIsNotNone(match)
        code = unescape(match.group(1))
        for required in (
            "sample_id = rep(\"toy_A\", 8)",
            "cell_barcode",
            "productive = c(TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, FALSE, TRUE)",
            "productive_bcr <- subset(bcr, productive)",
            '"IGH" %in% chains && any(chains %in% c("IGK", "IGL"))',
            "stopifnot(sum(has_paired_chains) == 3L, sum(!has_paired_chains) == 1L)",
            'subset(productive_bcr, chain == "IGH")',
            "length(unique(x))",
            "stopifnot(identical(as.integer(bcr_clones$cells), c(2L, 1L)))",
            'write.table(bcr_clones, row.names = FALSE, quote = FALSE, sep = "\\t")',
        ):
            with self.subTest(required=required):
                self.assertIn(required, code)

        for expected in (
            "cells_with_IGH_and_light=3; without_productive_pair=1",
            "toy_A\tIGHV1-2\tIGHJ4\tCARGGYYGMDV\t2",
            "toy_A\tIGHV3-7\tIGHJ6\tCARRDYGMDV\t1",
            "This key is not a scRepertoire clone call",
            "not a validated BCR pipeline",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
