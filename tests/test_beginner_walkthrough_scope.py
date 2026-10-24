"""Strict PR9 scope guard for the six approved beginner walkthrough revisions."""
from pathlib import Path
import re
import subprocess
import unittest

from beginner_walkthrough_baseline import (
    BEGINNER_WALKTHROUGH_ARTICLES,
    PUBLISHED_PR9,
    normalize_beginner_walkthrough_revision,
)
from tidyverse_setup_baseline import (
    PUBLISHED_PR10,
    TIDYVERSE_SETUP_ARTICLE,
    normalize_tidyverse_setup_revision,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.S | re.I)
JSONLD = re.compile(r"\btype\s*=\s*([\"'])application/ld\+json\1", re.I)


def git_bytes(path):
    result = subprocess.run(
        ["git", "show", f"{PUBLISHED_PR9}:{path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def changed_paths():
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only", "--no-renames", PUBLISHED_PR9, "--"],
        cwd=ROOT, text=True,
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True,
    ).splitlines()
    return sorted(set(tracked) | set(untracked))


def executable_scripts(text):
    return [
        block for block in SCRIPT.findall(text)
        if not JSONLD.search(block.split(">", 1)[0] + ">")
    ]


def jsonld_scripts(text):
    return [
        block for block in SCRIPT.findall(text)
        if JSONLD.search(block.split(">", 1)[0] + ">")
    ]


def normalize_jsonld_date(block):
    return re.sub(
        r'("dateModified"\s*:\s*")[^"]+(\")',
        r"\1__DATE_MODIFIED__\2", block,
    )


class BeginnerWalkthroughScopeTests(unittest.TestCase):
    def test_exact_six_page_allowlist_and_pr9_sources_exist(self):
        self.assertEqual(BEGINNER_WALKTHROUGH_ARTICLES, {
            "tutorials/computer-data-fundamentals.html",
            "tutorials/statistics-for-bioinformatics.html",
            "tutorials/experimental-design-batch-effects.html",
            "tutorials/command-line-part2.html",
            "tutorials/command-line-part3.html",
            "tutorials/conda-mamba-part1.html",
        })
        for relative in sorted(BEGINNER_WALKTHROUGH_ARTICLES):
            with self.subTest(page=relative):
                self.assertIsNotNone(git_bytes(relative))
                self.assertTrue((ROOT / relative).is_file())

    def test_only_article_inner_content_and_permitted_dates_differ(self):
        for relative in sorted(BEGINNER_WALKTHROUGH_ARTICLES):
            original_bytes = git_bytes(relative)
            self.assertIsNotNone(original_bytes, relative)
            current = (ROOT / relative).read_text(encoding="utf-8")
            original = original_bytes.decode("utf-8")
            with self.subTest(page=relative):
                self.assertEqual(
                    normalize_beginner_walkthrough_revision(relative, current), original,
                    "only the approved article body and allowed dateModified may change",
                )
                old_date = re.findall(r'"dateModified"\s*:\s*"([^"]+)"', original)
                new_date = re.findall(r'"dateModified"\s*:\s*"([^"]+)"', current)
                self.assertEqual(len(old_date), 1)
                self.assertEqual(len(new_date), 1)
                expected_old = "2026-10-21" if relative in {
                    "tutorials/computer-data-fundamentals.html",
                    "tutorials/statistics-for-bioinformatics.html",
                    "tutorials/experimental-design-batch-effects.html",
                } else "2026-10-23"
                self.assertEqual(old_date, [expected_old])
                if expected_old == "2026-10-23":
                    self.assertEqual(new_date, [expected_old], "existing CLI/Micromamba dates must stay unchanged")
                else:
                    self.assertIn(new_date[0], {"2026-10-21", "2026-10-23"})

    def test_all_tutorial_executable_scripts_remain_raw_byte_identical(self):
        pages = sorted((ROOT / "tutorials").glob("*.html"))
        self.assertEqual(len(pages), 58)
        for page in pages:
            relative = page.relative_to(ROOT).as_posix()
            old_bytes = git_bytes(relative)
            self.assertIsNotNone(old_bytes, relative)
            with self.subTest(page=relative):
                # Compare scripts before any article restoration; scripts added
                # within an authorized article must not be hidden by its body allowance.
                self.assertEqual(
                    executable_scripts(page.read_text(encoding="utf-8")),
                    executable_scripts(old_bytes.decode("utf-8")),
                )
                current_jsonld = jsonld_scripts(page.read_text(encoding="utf-8"))
                old_jsonld = jsonld_scripts(old_bytes.decode("utf-8"))
                if relative in BEGINNER_WALKTHROUGH_ARTICLES or relative == TIDYVERSE_SETUP_ARTICLE:
                    current_jsonld = [normalize_jsonld_date(block) for block in current_jsonld]
                    old_jsonld = [normalize_jsonld_date(block) for block in old_jsonld]
                self.assertEqual(current_jsonld, old_jsonld)

    def test_changed_paths_are_limited_to_target_articles_tests_and_sitemap(self):
        for relative in changed_paths():
            if relative.startswith("tests/") or relative == "sitemap.xml":
                continue
            current_path = ROOT / relative
            old_bytes = git_bytes(relative)
            with self.subTest(path=relative):
                self.assertIsNotNone(old_bytes, "new source/assets outside tests are forbidden")
                self.assertTrue(current_path.is_file(), "deleting published files is forbidden")
                if relative in BEGINNER_WALKTHROUGH_ARTICLES:
                    self.assertEqual(
                        normalize_beginner_walkthrough_revision(
                            relative, current_path.read_text(encoding="utf-8")
                        ),
                        old_bytes.decode("utf-8"),
                        "target page changes must be confined to its article body/date",
                    )
                elif relative == TIDYVERSE_SETUP_ARTICLE:
                    published = subprocess.run(
                        ["git", "show", f"{PUBLISHED_PR10}:{relative}"], cwd=ROOT,
                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
                    )
                    self.assertEqual(published.returncode, 0, relative)
                    self.assertEqual(
                        normalize_tidyverse_setup_revision(
                            relative, current_path.read_text(encoding="utf-8")
                        ),
                        published.stdout.decode("utf-8"),
                        "the separate PR10 authorization permits only the tidyverse body and dates",
                    )
                elif relative == "analytics.js":
                    self.assertIsNotNone(old_bytes, "analytics.js must already exist in the published source")
                    self.assertTrue(current_path.is_file(), "deleting analytics.js is forbidden")
                    # Exact authorized source is pinned by test_analytics_source_scope.py.
                else:
                    self.assertEqual(
                        current_path.read_bytes(), old_bytes,
                        "non-target pages, old assets, CSS, navigation, and site scripts are immutable",
                    )

    def test_restorer_leaves_article_wrappers_and_surroundings_visible(self):
        relative = "tutorials/computer-data-fundamentals.html"
        original = git_bytes(relative).decode("utf-8")
        normalized = normalize_beginner_walkthrough_revision(relative, original)
        body_mutation = original.replace(
            "</article>", "<p>authorized body delta</p></article>", 1
        )
        self.assertEqual(
            normalize_beginner_walkthrough_revision(relative, body_mutation), normalized
        )
        for mutated in (
            original.replace("<article", '<article data-unapproved="1"', 1),
            original.replace("<head>", "<head><!-- unauthorized -->", 1),
            original.replace("</footer>", "<!-- unauthorized --></footer>", 1),
        ):
            with self.subTest(mutation=mutated[:60]):
                self.assertNotEqual(
                    normalize_beginner_walkthrough_revision(relative, mutated), normalized
                )

    def test_restorer_supports_article_only_fragments(self):
        relative = "tutorials/computer-data-fundamentals.html"
        original = git_bytes(relative).decode("utf-8")
        article = re.search(r"<article\b[^>]*>.*?</article>", original, re.S | re.I).group(0)
        changed = article.replace("</article>", "<p>revised walkthrough</p></article>")
        self.assertEqual(
            normalize_beginner_walkthrough_revision(relative, changed),
            normalize_beginner_walkthrough_revision(relative, article),
        )


if __name__ == "__main__":
    unittest.main()
