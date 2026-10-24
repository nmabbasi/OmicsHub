"""Guards for the owner-authorized four-lesson and reader-navigation revision.

These comparisons complement scientific contract tests: they do not claim that
all biological examples were executed or that learner retention was measured.
"""
from pathlib import Path
import re
import subprocess
import unittest

from reviewed_tutorial_baseline import (
    LEARNER_REVISION_ARTICLES,
    normalize_learner_revision,
    normalize_reviewed_content,
)
from reader_typography_baseline import normalize_reader_typography
from beginner_walkthrough_baseline import normalize_beginner_walkthrough_revision
from six_lesson_revision_baseline import normalize_six_lesson_revision
from tidyverse_setup_baseline import normalize_tidyverse_setup_revision
from remaining_validation_baseline import (
    allowed_paths as remaining_validation_paths,
    normalize_remaining_validation_edit,
)

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED_BASELINE = "49cb63d91b508ae3c3e4a6b0a11ac2bb10d48fa1"
ARTICLE = re.compile(r"<article\b[^>]*>.*?</article>", re.S)
SCRIPT = re.compile(r"<script\b[^>]*>.*?</script>", re.S)


class LearnerRevisionScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = {}
        for page in sorted((ROOT / "tutorials").glob("*.html")):
            relative = page.relative_to(ROOT).as_posix()
            result = subprocess.run(
                ["git", "show", PUBLISHED_BASELINE + ":" + relative],
                cwd=ROOT, capture_output=True, text=True,
            )
            if result.returncode:
                raise unittest.SkipTest("published PR 6 baseline unavailable")
            cls.baseline[relative] = result.stdout

    def test_exactly_four_article_bodies_are_authorized(self):
        self.assertEqual(LEARNER_REVISION_ARTICLES, {
            "tutorials/ai-prompt-engineering-seurat.html",
            "tutorials/hpc-submission-part1.html",
            "tutorials/reproducible-workflows-snakemake-nextflow.html",
            "tutorials/wes-variant-calling-pipeline.html",
        })
        self.assertEqual(len(self.baseline), 58)
        checked = 0
        for relative, before in self.baseline.items():
            if relative in LEARNER_REVISION_ARTICLES:
                continue
            with self.subTest(page=relative):
                after = (ROOT / relative).read_text(encoding="utf-8")
                if relative in remaining_validation_paths():
                    after = normalize_remaining_validation_edit(relative, after)
                # One legacy page nests the continuation nav inside its article.
                # For these 54 pages the helper masks navs, never article content.
                before = normalize_tidyverse_setup_revision(relative, before)
                after = normalize_tidyverse_setup_revision(relative, after)
                before = normalize_beginner_walkthrough_revision(relative, before)
                after = normalize_beginner_walkthrough_revision(relative, after)
                before = normalize_six_lesson_revision(relative, before)
                after = normalize_six_lesson_revision(relative, after)
                self.assertEqual(
                    ARTICLE.findall(normalize_learner_revision(
                        relative, normalize_reader_typography(relative, before)
                    )),
                    ARTICLE.findall(normalize_learner_revision(
                        relative, normalize_reader_typography(relative, after)
                    )),
                )
                checked += 1
        self.assertEqual(checked, 54)

    def test_surrounding_page_content_and_all_site_scripts_are_preserved(self):
        for relative, before in self.baseline.items():
            with self.subTest(page=relative):
                after = (ROOT / relative).read_text(encoding="utf-8")
                raw_before, raw_after = before, after
                if relative in remaining_validation_paths():
                    after = normalize_remaining_validation_edit(relative, after)
                before = normalize_tidyverse_setup_revision(relative, before)
                after = normalize_tidyverse_setup_revision(relative, after)
                before = normalize_beginner_walkthrough_revision(relative, before)
                after = normalize_beginner_walkthrough_revision(relative, after)
                before = normalize_six_lesson_revision(relative, before)
                after = normalize_six_lesson_revision(relative, after)
                self.assertEqual(
                    normalize_learner_revision(relative, normalize_reviewed_content(
                        relative, normalize_reader_typography(relative, before)
                    )),
                    normalize_learner_revision(relative, normalize_reviewed_content(
                        relative, normalize_reader_typography(relative, after)
                    )),
                )
                def executable_scripts(text):
                    return [item for item in SCRIPT.findall(text)
                            if 'application/ld+json' not in item.split(">", 1)[0]]
                self.assertEqual(executable_scripts(raw_before), executable_scripts(raw_after))

    def test_scope_normalizer_does_not_hide_unapproved_article_or_header_changes(self):
        relative = "tutorials/command-line-part1.html"
        original = self.baseline[relative]
        mutated = original.replace("<article", "<article data-unapproved=\"true\"", 1)
        self.assertNotEqual(
            normalize_learner_revision(relative, normalize_reader_typography(relative, original)),
            normalize_learner_revision(relative, normalize_reader_typography(relative, mutated)),
        )
        mutated = original.replace("<head>", "<head><!-- unexpected header edit -->", 1)
        self.assertNotEqual(
            normalize_learner_revision(relative, normalize_reader_typography(relative, original)),
            normalize_learner_revision(relative, normalize_reader_typography(relative, mutated)),
        )


if __name__ == "__main__":
    unittest.main()
