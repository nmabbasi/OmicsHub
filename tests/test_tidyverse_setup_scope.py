"""PR10 scope guard for the authorized tidyverse setup lesson revision."""
from pathlib import Path
import re
import subprocess
import unittest

from tidyverse_setup_baseline import (
    PUBLISHED_PR10,
    ROOT,
    TIDYVERSE_SETUP_ARTICLE,
    normalize_tidyverse_setup_revision,
    published_tidyverse_page,
)

SITE = "https://theomicshub.com/"
SCRIPT = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.S | re.I)
JSONLD_TYPE = re.compile(r"\btype\s*=\s*([\"'])application/ld\+json\1", re.I)
ARTICLE = re.compile(
    r"(?P<open><article\b[^>]*>)(?P<body>.*?)(?P<close></article\s*>)",
    re.S | re.I,
)
DATE_MODIFIED = re.compile(r'("dateModified"\s*:\s*")([^\"]+)(")')
UPDATED = re.compile(r"Updated (2026-10-\d{2})")


def git_bytes(relative_path):
    result = subprocess.run(
        ["git", "show", f"{PUBLISHED_PR10}:{relative_path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def changed_paths():
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only", "--no-renames", PUBLISHED_PR10, "--"],
        cwd=ROOT, text=True,
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True,
    ).splitlines()
    return sorted(set(tracked) | set(untracked))


def scripts(text, executable_only=False):
    blocks = SCRIPT.findall(text)
    if executable_only:
        return [block for block in blocks if not JSONLD_TYPE.search(block.split(">", 1)[0] + ">")]
    return [block for block in blocks if JSONLD_TYPE.search(block.split(">", 1)[0] + ">")]


def normalize_jsonld_date(block):
    matches = list(DATE_MODIFIED.finditer(block))
    if len(matches) != 1 or matches[0].group(2) not in {"2026-10-21", "2026-10-23"}:
        raise AssertionError("expected one approved JSON-LD dateModified value")
    match = matches[0]
    return block[:match.start(2)] + "__DATE_MODIFIED__" + block[match.end(2):]


class TidyverseSetupScopeTests(unittest.TestCase):
    def test_pr10_baseline_target_and_only_its_two_date_labels_are_authorized(self):
        original = published_tidyverse_page()
        current = (ROOT / TIDYVERSE_SETUP_ARTICLE).read_text(encoding="utf-8")
        old_articles, new_articles = list(ARTICLE.finditer(original)), list(ARTICLE.finditer(current))
        self.assertEqual(len(old_articles), 1)
        self.assertEqual(len(new_articles), 1)
        self.assertEqual(new_articles[0].group("open"), old_articles[0].group("open"))
        self.assertEqual(new_articles[0].group("close"), old_articles[0].group("close"))
        self.assertEqual(
            normalize_tidyverse_setup_revision(TIDYVERSE_SETUP_ARTICLE, current), original,
            "only the target inner article body and its two date labels may change",
        )
        self.assertEqual(DATE_MODIFIED.findall(original)[0][1], "2026-10-21")
        self.assertEqual(DATE_MODIFIED.findall(current)[0][1], "2026-10-23")
        self.assertEqual(UPDATED.findall(original), ["2026-10-21"])
        self.assertEqual(UPDATED.findall(current), ["2026-10-23"])

    def test_restorer_does_not_mask_wrappers_navigation_or_other_metadata(self):
        original = published_tidyverse_page()
        normalized = normalize_tidyverse_setup_revision(TIDYVERSE_SETUP_ARTICLE, original)
        self.assertEqual(normalized, original)
        body_change = original.replace(
            "</article>", "<p>authorized article-body change</p></article>", 1
        )
        self.assertEqual(
            normalize_tidyverse_setup_revision(TIDYVERSE_SETUP_ARTICLE, body_change), original
        )
        outside_changes = (
            original.replace('aria-labelledby="tutorial-title"',
                             'aria-labelledby="unexpected-title"', 1),
            original.replace('aria-label="Learning path navigation"',
                             'aria-label="Unexpected navigation"', 1),
            original.replace('"datePublished": "2026-09-05"',
                             '"datePublished": "2026-09-06"', 1),
        )
        for changed in outside_changes:
            with self.subTest(change=changed[:80]):
                self.assertNotEqual(
                    normalize_tidyverse_setup_revision(TIDYVERSE_SETUP_ARTICLE, changed),
                    original,
                )

    def test_raw_executable_scripts_and_jsonld_except_date_are_unchanged(self):
        pages = sorted((ROOT / "tutorials").glob("*.html"))
        self.assertEqual(len(pages), 58)
        for page in pages:
            relative = page.relative_to(ROOT).as_posix()
            old_bytes = git_bytes(relative)
            self.assertIsNotNone(old_bytes, relative)
            old = old_bytes.decode("utf-8")
            current = page.read_text(encoding="utf-8")
            with self.subTest(page=relative):
                self.assertEqual(scripts(current, executable_only=True),
                                 scripts(old, executable_only=True))
                old_jsonld, current_jsonld = scripts(old), scripts(current)
                if relative == TIDYVERSE_SETUP_ARTICLE:
                    self.assertEqual(len(old_jsonld), 1)
                    self.assertEqual(len(current_jsonld), 1)
                    old_jsonld = [normalize_jsonld_date(block) for block in old_jsonld]
                    current_jsonld = [normalize_jsonld_date(block) for block in current_jsonld]
                self.assertEqual(current_jsonld, old_jsonld,
                                 "JSON-LD fields other than the approved date must remain exact")

    def test_all_other_tutorials_public_pages_assets_and_site_scripts_are_byte_identical(self):
        tutorial_paths = sorted((ROOT / "tutorials").glob("*.html"))
        self.assertEqual(len(tutorial_paths), 58)
        self.assertTrue((ROOT / TIDYVERSE_SETUP_ARTICLE).is_file())
        for page in tutorial_paths:
            relative = page.relative_to(ROOT).as_posix()
            if relative == TIDYVERSE_SETUP_ARTICLE:
                continue
            old = git_bytes(relative)
            self.assertIsNotNone(old, relative)
            with self.subTest(tutorial=relative):
                self.assertEqual(page.read_bytes(), old)

        for relative in changed_paths():
            if relative.startswith("tests/") or relative in {TIDYVERSE_SETUP_ARTICLE, "sitemap.xml"}:
                continue
            old = git_bytes(relative)
            path = ROOT / relative
            with self.subTest(path=relative):
                self.assertIsNotNone(old, "new public files and assets are forbidden")
                self.assertTrue(path.is_file(), "deleting published files is forbidden")
                self.assertEqual(path.read_bytes(), old,
                                 "all other public pages, assets, styles, and site scripts are immutable")

    def test_sitemap_diff_is_exactly_the_target_lastmod_replacement(self):
        original = git_bytes("sitemap.xml")
        self.assertIsNotNone(original)
        current = (ROOT / "sitemap.xml").read_bytes()
        target_url = (SITE + TIDYVERSE_SETUP_ARTICLE).encode("ascii")
        escaped_url = re.escape(target_url)
        row_pattern = re.compile(rb"<url>\s*<loc>" + escaped_url + rb"</loc>.*?</url>", re.S)
        rows = list(row_pattern.finditer(original))
        self.assertEqual(len(rows), 1)
        row = rows[0].group(0)
        self.assertEqual(row.count(b"<lastmod>2026-10-21</lastmod>"), 1)
        updated_row = row.replace(b"<lastmod>2026-10-21</lastmod>",
                                  b"<lastmod>2026-10-23</lastmod>", 1)
        expected = original[:rows[0].start()] + updated_row + original[rows[0].end():]
        self.assertEqual(current, expected,
                         "the complete sitemap must match PR10 except this one lastmod")


if __name__ == "__main__":
    unittest.main()
