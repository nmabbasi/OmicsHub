"""PR11 scope guard for the authorized Ubuntu Tidyverse lesson revision."""
from pathlib import Path
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET

from ubuntu_tidyverse_baseline import (
    CURRENT_DATE,
    PUBLISHED_PR11,
    ROOT,
    TIDYVERSE_SETUP_ARTICLE,
    normalize_ubuntu_tidyverse_revision,
    published_pr11_tidyverse_page,
)
from remaining_validation_baseline import (
    allowed_paths as remaining_validation_paths,
    load_manifest,
    normalize_remaining_validation_edit,
    normalize_remaining_validation_sitemap,
)

SITE = "https://theomicshub.com/"
SCRIPT = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.S | re.I)
JSONLD_TYPE = re.compile(r"\btype\s*=\s*([\"'])application/ld\+json\1", re.I)
WORKFLOW = re.compile(
    r"<pre\b(?=[^>]*\bid=[\"']tidyverse-workflow[\"'])[^>]*>.*?</pre\s*>",
    re.S | re.I,
)
ARTICLE = re.compile(
    r"(?P<open><article\b[^>]*>)(?P<body>.*?)(?P<close></article\s*>)",
    re.S | re.I,
)
DATE_MODIFIED = re.compile(r'("dateModified"\s*:\s*")([^\"]+)(")')
UPDATED = re.compile(r"Updated (2026-10-\d{2})")


def git_bytes(relative_path):
    result = subprocess.run(
        ["git", "show", f"{PUBLISHED_PR11}:{relative_path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def changed_paths():
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only", "--no-renames", PUBLISHED_PR11, "--"],
        cwd=ROOT, text=True,
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True,
    ).splitlines()
    return sorted(set(tracked) | set(untracked))


def scripts(text, jsonld=False):
    blocks = SCRIPT.findall(text)
    selected = []
    for block in blocks:
        opening = block.split(">", 1)[0] + ">"
        if bool(JSONLD_TYPE.search(opening)) == jsonld:
            selected.append(block)
    return selected


def expected_sitemap_after_target_date_change(original):
    target_url = (SITE + TIDYVERSE_SETUP_ARTICLE).encode("ascii")
    row_pattern = re.compile(rb"<url>\s*<loc>" + re.escape(target_url) + rb"</loc>.*?</url>", re.S)
    rows = list(row_pattern.finditer(original))
    if len(rows) != 1:
        raise AssertionError("PR11 sitemap must contain exactly one target URL row")
    row = rows[0].group(0)
    old_date = b"<lastmod>2026-10-23</lastmod>"
    new_date = f"<lastmod>{CURRENT_DATE}</lastmod>".encode("ascii")
    if row.count(old_date) != 1:
        raise AssertionError("PR11 target sitemap row must have exactly one Oct 23 lastmod")
    updated = row.replace(old_date, new_date, 1)
    return original[:rows[0].start()] + updated + original[rows[0].end():]


class UbuntuTidyverseScopeTests(unittest.TestCase):
    def test_only_target_article_body_and_exact_two_date_values_change(self):
        original = published_pr11_tidyverse_page()
        current = (ROOT / TIDYVERSE_SETUP_ARTICLE).read_text(encoding="utf-8")
        old_articles, new_articles = list(ARTICLE.finditer(original)), list(ARTICLE.finditer(current))
        self.assertEqual(len(old_articles), 1)
        self.assertEqual(len(new_articles), 1)
        self.assertEqual(new_articles[0].group("open"), old_articles[0].group("open"))
        self.assertEqual(new_articles[0].group("close"), old_articles[0].group("close"))
        self.assertEqual(
            normalize_ubuntu_tidyverse_revision(TIDYVERSE_SETUP_ARTICLE, current), original,
            "only the inner article body and its exact approved date values may change",
        )
        self.assertEqual(DATE_MODIFIED.findall(original)[0][1], "2026-10-23")
        self.assertEqual(DATE_MODIFIED.findall(current), [("\"dateModified\": \"", CURRENT_DATE, "\"")])
        self.assertEqual(UPDATED.findall(original), ["2026-10-23"])
        self.assertEqual(UPDATED.findall(current), [CURRENT_DATE])

    def test_new_restorer_rejects_unapproved_dates_and_wrappers(self):
        original = published_pr11_tidyverse_page()
        self.assertEqual(normalize_ubuntu_tidyverse_revision(TIDYVERSE_SETUP_ARTICLE, original), original)
        mutations = (
            original.replace('"dateModified": "2026-10-23"', '"dateModified": "2026-10-25"', 1),
            original.replace('Updated 2026-10-23', 'Updated 2026-10-25', 1),
            original.replace('aria-labelledby="tutorial-title"', 'aria-labelledby="wrong-title"', 1),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation[:80]):
                with self.assertRaises(AssertionError):
                    normalize_ubuntu_tidyverse_revision(TIDYVERSE_SETUP_ARTICLE, mutation)
        navigation_change = original.replace('aria-label="Learning path navigation"',
                                             'aria-label="Unapproved navigation"', 1)
        self.assertNotEqual(normalize_ubuntu_tidyverse_revision(TIDYVERSE_SETUP_ARTICLE, navigation_change), original)

    def test_scientific_workflow_code_is_byte_exactly_pr11(self):
        original = published_pr11_tidyverse_page()
        current = (ROOT / TIDYVERSE_SETUP_ARTICLE).read_text(encoding="utf-8")
        old_workflows, new_workflows = WORKFLOW.findall(original), WORKFLOW.findall(current)
        self.assertEqual(len(old_workflows), 1)
        self.assertEqual(len(new_workflows), 1)
        self.assertEqual(new_workflows, old_workflows)
        self.assertIn("here::i_am(\"scripts/01-tidy-qc.R\")", new_workflows[0])
        self.assertIn('bg = "white"', new_workflows[0])

    def test_executable_scripts_and_jsonld_other_than_target_date_are_unchanged(self):
        pages = sorted((ROOT / "tutorials").glob("*.html"))
        self.assertEqual(len(pages), 58)
        for page in pages:
            relative = page.relative_to(ROOT).as_posix()
            original_bytes = git_bytes(relative)
            self.assertIsNotNone(original_bytes, relative)
            original = original_bytes.decode("utf-8")
            current = page.read_text(encoding="utf-8")
            with self.subTest(page=relative):
                self.assertEqual(scripts(current), scripts(original), "executable script blocks are immutable")
                old_jsonld, new_jsonld = scripts(original, jsonld=True), scripts(current, jsonld=True)
                if relative == TIDYVERSE_SETUP_ARTICLE or relative in remaining_validation_paths():
                    self.assertEqual(len(old_jsonld), 1)
                    self.assertEqual(len(new_jsonld), 1)
                    self.assertEqual(
                        re.sub(r'("dateModified"\s*:\s*")[^\"]+(")', r"\1__DATE__\2", new_jsonld[0]),
                        re.sub(r'("dateModified"\s*:\s*")[^\"]+(")', r"\1__DATE__\2", old_jsonld[0]),
                        "only JSON-LD dateModified may differ",
                    )
                    if relative == TIDYVERSE_SETUP_ARTICLE:
                        self.assertEqual(DATE_MODIFIED.findall(new_jsonld[0])[0][1], CURRENT_DATE)
                    else:
                        approved = load_manifest()["files"][relative]["date_modified_approved"]
                        self.assertEqual(DATE_MODIFIED.findall(new_jsonld[0])[0][1], approved)
                else:
                    self.assertEqual(new_jsonld, old_jsonld)

    def test_other_public_files_and_tutorials_remain_raw_byte_identical(self):
        tutorial_paths = sorted((ROOT / "tutorials").glob("*.html"))
        for page in tutorial_paths:
            relative = page.relative_to(ROOT).as_posix()
            if relative == TIDYVERSE_SETUP_ARTICLE:
                continue
            old = git_bytes(relative)
            self.assertIsNotNone(old, relative)
            with self.subTest(tutorial=relative):
                current = page.read_bytes()
                if relative in remaining_validation_paths():
                    current = normalize_remaining_validation_edit(
                        relative, current.decode("utf-8")
                    ).encode("utf-8")
                self.assertEqual(current, old)

        for relative in changed_paths():
            if relative.startswith("tests/") or relative in {TIDYVERSE_SETUP_ARTICLE, "sitemap.xml"}:
                continue
            old = git_bytes(relative)
            path = ROOT / relative
            with self.subTest(path=relative):
                if relative == "analytics.js":
                    self.assertIsNotNone(old, "analytics.js must already exist in the published source")
                    self.assertTrue(path.is_file(), "deleting analytics.js is forbidden")
                    # Exact authorized source is pinned by test_analytics_source_scope.py.
                    continue
                if relative in remaining_validation_paths():
                    self.assertIsNotNone(old, "allowlisted page must exist in published source")
                    self.assertTrue(path.is_file(), "deleting published files is forbidden")
                    self.assertEqual(
                        normalize_remaining_validation_edit(
                            relative, path.read_text(encoding="utf-8")
                        ).encode("utf-8"),
                        old,
                        "only exact manifest-approved inner article and date deltas are allowed",
                    )
                    continue
                self.assertIsNotNone(old, "new public files and assets are forbidden")
                self.assertTrue(path.is_file(), "deleting published files is forbidden")
                self.assertEqual(path.read_bytes(), old, "all non-target public files must remain byte-identical")

    def test_sitemap_is_pr11_xml_with_only_target_lastmod_changed(self):
        original = git_bytes("sitemap.xml")
        self.assertIsNotNone(original)
        current = normalize_remaining_validation_sitemap((ROOT / "sitemap.xml").read_bytes())
        expected = expected_sitemap_after_target_date_change(original)
        self.assertEqual(current, expected, "only the target URL's one lastmod may change")
        root = ET.fromstring(current)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        target = SITE + TIDYVERSE_SETUP_ARTICLE
        rows = [entry for entry in root.findall("s:url", ns)
                if entry.findtext("s:loc", namespaces=ns) == target]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].findtext("s:lastmod", namespaces=ns), CURRENT_DATE)


if __name__ == "__main__":
    unittest.main()
