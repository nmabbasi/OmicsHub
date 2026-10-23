"""Regression tests for the prerequisite-aware learning-path generator.
Run: python3 -m unittest tests/test_learning_paths.py (or unittest discover).
"""
from __future__ import annotations

import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
import generate_learning_paths as generator  # noqa: E402


class LinkParser(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, dict[str, str | None]]] = []
        self._anchor: dict[str, str | None] | None = None
        self.feed(source)

    def handle_starttag(self, tag: str, attrs):
        if tag == "a":
            self._anchor = dict(attrs)
            self.links.append((self._anchor.get("href") or "", self._anchor))


class LearningPathManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.facts = generator.load_site(ROOT)

    def test_manifest_covers_exactly_58_pages_and_links_resolve(self):
        self.assertEqual(len(self.facts), 58)
        self.assertEqual(set(self.manifest["tutorials"]), set(self.facts))
        for key, item in self.manifest["tutorials"].items():
            for target in ([item.get("previous")] + [e["target"] for e in item["next"]]):
                if target is None:
                    continue
                with self.subTest(page=key, target=target):
                    self.assertNotEqual(target, key, "self-loop")
                    if target.startswith("@"):
                        self.assertIn(target[1:], self.manifest["start_targets"])
                    else:
                        self.assertIn(target, self.facts)
            for edge in item["next"]:
                self.assertTrue(edge.get("reason", "").strip())

    def test_foundation_sequence_and_language_choice(self):
        nodes = self.manifest["tutorials"]
        self.assertEqual(nodes["introduction-to-bioinformatics"]["next"][0]["target"], "computer-data-fundamentals")
        self.assertEqual(nodes["computer-data-fundamentals"]["previous"], "introduction-to-bioinformatics")
        self.assertEqual(nodes["computer-data-fundamentals"]["next"][0]["target"], "command-line-part1")
        self.assertTrue(any(e["target"] == "biological-data-formats" for e in nodes["computer-data-fundamentals"]["next"]))
        self.assertEqual(nodes["command-line-part1"]["next"][0]["target"], "command-line-part2")
        self.assertEqual(nodes["command-line-part2"]["next"][0]["target"], "command-line-part3")
        self.assertEqual(nodes["command-line-part3"]["next"][0]["target"], "conda-mamba-part1")
        conda_choices = {edge["target"] for edge in nodes["conda-mamba-part1"]["next"]}
        self.assertTrue({"r-tidyverse-fundamentals", "python-fundamentals-bioinformatics"}.issubset(conda_choices))
        self.assertIn("@sh-hpc", conda_choices)
        self.assertEqual(nodes["r-tidyverse-fundamentals"]["next"][0]["target"], "statistics-for-bioinformatics")
        self.assertEqual(nodes["python-fundamentals-bioinformatics"]["next"][0]["target"], "statistics-for-bioinformatics")
        self.assertIn("either", nodes["r-tidyverse-fundamentals"]["next"][0]["reason"].lower())
        self.assertEqual(nodes["hpc-connection"]["previous"], "@sh-hpc")

    def test_single_cell_order_and_question_dependent_options(self):
        nodes = self.manifest["tutorials"]
        self.assertEqual(nodes["scrna-seq-basics"]["next"][0]["target"], "quality-control-fundamentals")
        self.assertEqual(nodes["quality-control-fundamentals"]["next"][0]["target"], "cell-type-annotation-methods")
        annotation_targets = {edge["target"] for edge in nodes["cell-type-annotation-methods"]["next"]}
        self.assertIn("scrna-seq-integration-strategies", annotation_targets)
        self.assertIn("cell-cell-communication", annotation_targets)
        integration = nodes["scrna-seq-integration-strategies"]["next"][0]
        self.assertEqual(integration["target"], "scrna-seq-quality-control")
        metrics = nodes["scrna-seq-quality-control"]
        self.assertEqual(metrics["next"][0]["target"], "scrna-seq-downstream-analysis")
        self.assertIn("not basic cell-level QC", metrics["next"][0]["reason"])
        self.assertIn("continuous-process", nodes["scrna-seq-trajectory-inference"]["next"][0]["reason"])
        self.assertEqual(nodes["scrna-seq-trajectory-inference"]["previous"], "cell-type-annotation-methods")
        self.assertEqual(nodes["cell-cell-communication"]["previous"], "cell-type-annotation-methods")
        self.assertNotIn("scrna-seq-basics", [edge["target"] for edge in nodes["wes-variant-calling-pipeline"]["next"]])
        self.assertEqual(nodes["wes-variant-calling-pipeline"]["previous"], "reference-genomes-annotation")

    def test_cross_modality_branches_and_optional_methods_are_not_false_prerequisites(self):
        nodes = self.manifest["tutorials"]
        self.assertEqual(nodes["wes-variant-calling-pipeline"]["next"][0]["target"], "@sh-genomics")
        self.assertNotIn("infercnv-copy-number-variation", [
            edge["target"] for edge in nodes["wes-variant-calling-pipeline"]["next"]
        ])
        self.assertEqual(nodes["infercnv-copy-number-variation"]["previous"], "cell-type-annotation-methods")
        self.assertEqual(nodes["tcr-bcr-repertoire-analysis"]["next"][0]["target"], "@sh-single-cell")
        self.assertEqual(nodes["scrna-seq-downstream-analysis"]["previous"], "cell-type-annotation-methods")
        self.assertNotEqual(nodes["ai-prompt-engineering-seurat"]["previous"], "single-cell-foundation-models")

    def test_compact_toolbar_keeps_three_slots_and_branches_to_explained_choices(self):
        for key, item in self.manifest["tutorials"].items():
            toolbar = generator.render_toolbar(key, item, self.manifest, self.facts)
            links = LinkParser(toolbar).links
            with self.subTest(page=key):
                self.assertEqual(len(links), 3)
                if len(item["next"]) > 1:
                    self.assertEqual(links[-1][0], "#reader-course-navigation")

    def test_generated_navigation_has_named_routes_no_catalogue_loss_or_linear_counter(self):
        for key, item in self.manifest["tutorials"].items():
            generated = generator.render_page(key, (ROOT / "tutorials" / f"{key}.html").read_text(encoding="utf-8"), self.manifest, self.facts)
            self.assertNotRegex(generated, r"Tutorial\s+\d+\s+of\s+58")
            for pattern in generator.NAV_PATTERNS.values():
                match = pattern.search(generated)
                self.assertIsNotNone(match)
                self.assertIn('data-catalogue-return="" href="../tutorials.html"', match.group(0))
            toolbar = generator.NAV_PATTERNS["toolbar"].search(generated).group(0)
            self.assertIn("Learning path navigation", toolbar)
            bottom = generator.NAV_PATTERNS["continuation"].search(generated).group(0)
            self.assertIn(html.escape(item["route"]), bottom)
            self.assertIn("not a completion tracker", bottom)

    def test_title_labels_are_escaped(self):
        with tempfile.TemporaryDirectory() as temp:
            site = self._copy_fixture(Path(temp))
            page = site / "tutorials" / "introduction-to-bioinformatics.html"
            text = page.read_text(encoding="utf-8")
            text = re.sub(r"(<h1\b[^>]*>).*?(</h1>)", r"\1Try &lt;img src=x onerror=alert(1)&gt;\2", text, count=1, flags=re.S)
            page.write_text(text, encoding="utf-8")
            result = self._run(site)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            output = page.read_text(encoding="utf-8")
            linked_page = site / "tutorials" / "computer-data-fundamentals.html"
            output = linked_page.read_text(encoding="utf-8")
            toolbar = generator.NAV_PATTERNS["toolbar"].search(output).group(0)
            self.assertIn("Try &lt;img src=x onerror=alert(1)&gt;", toolbar)
            self.assertNotIn("<img src=x", toolbar)

    def _copy_fixture(self, site: Path) -> Path:
        shutil.copytree(ROOT / "tutorials", site / "tutorials")
        shutil.copy2(ROOT / "start-here.html", site / "start-here.html")
        shutil.copy2(ROOT / "tutorials.html", site / "tutorials.html")
        (site / "tools").mkdir()
        shutil.copy2(TOOLS / "learning-paths.json", site / "tools" / "learning-paths.json")
        shutil.copy2(TOOLS / "generate_learning_paths.py", site / "tools" / "generate_learning_paths.py")
        return site

    def _run(self, site: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(site / "tools" / "generate_learning_paths.py"), "--root", str(site), *args],
            text=True, capture_output=True, check=False,
        )

    def test_temporary_copy_changes_only_nav_blocks_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            site = self._copy_fixture(Path(temp))
            for page in (site / "tutorials").glob("*.html"):
                text = page.read_text(encoding="utf-8")
                text = text.replace('aria-label="Learning path navigation"',
                                    'aria-label="Tutorial navigation"', 1)
                page.write_text(text, encoding="utf-8")
            original = {p.name: p.read_bytes() for p in (site / "tutorials").glob("*.html")}
            first = self._run(site)
            self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
            self.assertIn("58 tutorial pages", first.stdout)

            for name, before_bytes in original.items():
                after_bytes = (site / "tutorials" / name).read_bytes()
                before, after = before_bytes.decode("utf-8"), after_bytes.decode("utf-8")
                # Replacing just these two existing nav elements must leave every other byte intact.
                for pattern in generator.NAV_PATTERNS.values():
                    before = pattern.sub("<nav>ORIGINAL-NAV</nav>", before, count=1)
                    after = pattern.sub("<nav>ORIGINAL-NAV</nav>", after, count=1)
                with self.subTest(page=name):
                    self.assertEqual(before, after)
                    self.assertEqual(before_bytes.count(b"<article"), after_bytes.count(b"<article"))

            second = self._run(site)
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
            self.assertIn("in 0 tutorial pages", second.stdout)
            check = self._run(site, "--check")
            self.assertEqual(check.returncode, 0, check.stderr + check.stdout)

            stale_page = site / "tutorials" / "introduction-to-bioinformatics.html"
            stale_before = stale_page.read_text(encoding="utf-8")
            stale_page.write_text(stale_before.replace("Learning path navigation", "Tutorial navigation", 1), encoding="utf-8")
            stale_state = stale_page.read_bytes()
            stale_check = self._run(site, "--check")
            self.assertEqual(stale_check.returncode, 1)
            self.assertIn("stale in 1 tutorial pages", stale_check.stdout)
            self.assertEqual(stale_page.read_bytes(), stale_state, "--check must never write")


if __name__ == "__main__":
    unittest.main()
