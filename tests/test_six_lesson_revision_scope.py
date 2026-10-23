"""Strict PR8 scope guard for the six approved tutorial revisions."""
from pathlib import Path
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET

from beginner_walkthrough_baseline import (
    BEGINNER_WALKTHROUGH_ARTICLES,
    PUBLISHED_PR9,
    normalize_beginner_walkthrough_revision,
)
from six_lesson_revision_baseline import (
    PUBLISHED_PR8,
    ROOT,
    SIX_LESSON_ARTICLES,
    SIX_LESSON_CURRENT_EXECUTION_NOTES,
    SIX_LESSON_DISCLOSURE_PAGES,
    normalize_six_lesson_revision,
)
from tidyverse_setup_baseline import (
    PUBLISHED_PR10,
    TIDYVERSE_SETUP_ARTICLE,
    normalize_tidyverse_setup_revision,
)

ALLOWED_FIXTURE_PREFIXES = (
    "files/text-processing-lesson/",
    "files/micromamba-lesson/",
    "files/slurm-basics-lesson/",
    "files/trajectory-contract-lesson/",
    "files/annotation-preflight-lesson/",
    "files/coding-assistant-lesson/",
)
DISCLOSURE = re.compile(
    r'<p\s+class="text-sm text-gray-600 mb-2"[^>]*>.*?</p>', re.S | re.I
)
DATE_MODIFIED = re.compile(r'"dateModified"\s*:\s*"([^"]+)"')
SCRIPT = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.S | re.I)
JSONLD = re.compile(r"\btype\s*=\s*([\"'])application/ld\+json\1", re.I)


def git_bytes(path):
    result = subprocess.run(
        ["git", "show", f"{PUBLISHED_PR8}:{path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def changed_paths():
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only", "--no-renames", PUBLISHED_PR8, "--"],
        cwd=ROOT, text=True,
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True
    ).splitlines()
    return sorted(set(tracked) | set(untracked))


class SixLessonRevisionScopeTests(unittest.TestCase):
    def test_exact_six_page_allowlist_and_pr8_sources_exist(self):
        self.assertEqual(SIX_LESSON_ARTICLES, {
            "tutorials/command-line-part2.html",
            "tutorials/conda-mamba-part1.html",
            "tutorials/hpc-basic-commands.html",
            "tutorials/scrna-seq-trajectory-inference.html",
            "tutorials/advanced-ai-single-cell.html",
            "tutorials/ai-coding-cursor-aider.html",
        })
        for relative in sorted(SIX_LESSON_ARTICLES):
            with self.subTest(page=relative):
                self.assertIsNotNone(git_bytes(relative))
                self.assertTrue((ROOT / relative).is_file())

    def test_only_article_inner_content_date_and_exact_disclosure_can_change(self):
        for relative in sorted(SIX_LESSON_ARTICLES):
            old_bytes = git_bytes(relative)
            self.assertIsNotNone(old_bytes, relative)
            old = old_bytes.decode("utf-8")
            current = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(page=relative):
                self.assertEqual(DATE_MODIFIED.findall(old), ["2026-10-21"])
                self.assertIn(DATE_MODIFIED.findall(current),
                              [["2026-10-21"], ["2026-10-23"]])
                if relative in SIX_LESSON_DISCLOSURE_PAGES:
                    current_notes = DISCLOSURE.findall(current)
                    old_notes = DISCLOSURE.findall(old)
                    self.assertEqual(len(old_notes), 1)
                    self.assertEqual(len(current_notes), 1)
                    expected_note = SIX_LESSON_CURRENT_EXECUTION_NOTES.get(relative, old_notes[0])
                    self.assertEqual(
                        current_notes[0], expected_note,
                        "register only the exact approved current disclosure paragraph in "
                        "SIX_LESSON_CURRENT_EXECUTION_NOTES",
                    )
                else:
                    self.assertEqual(DISCLOSURE.findall(current), DISCLOSURE.findall(old))
                self.assertEqual(
                    normalize_six_lesson_revision(
                        relative, normalize_beginner_walkthrough_revision(relative, current)
                    ),
                    normalize_six_lesson_revision(
                        relative, normalize_beginner_walkthrough_revision(relative, old)
                    ),
                    "content outside the approved article body/date/exact disclosure changed",
                )

    def test_executable_scripts_remain_byte_identical_on_all_tutorial_pages(self):
        pages = sorted((ROOT / "tutorials").glob("*.html"))
        self.assertEqual(len(pages), 58)
        for page in pages:
            relative = page.relative_to(ROOT).as_posix()
            old_bytes = git_bytes(relative)
            self.assertIsNotNone(old_bytes, relative)
            old = old_bytes.decode("utf-8")
            current = page.read_text(encoding="utf-8")
            def executable(text):
                return [
                    block for block in SCRIPT.findall(text)
                    if not JSONLD.search(block.split(">", 1)[0] + ">")
                ]
            with self.subTest(page=relative):
                self.assertEqual(executable(current), executable(old))

    def test_global_source_diff_and_fixture_folders_stay_within_allowlist(self):
        for relative in changed_paths():
            # Test infrastructure is this task's explicit area; sitemap dates
            # are parent-owned and receive their own precise metadata test.
            if relative.startswith("tests/") or relative == "sitemap.xml":
                continue
            current_path = ROOT / relative
            old_bytes = git_bytes(relative)
            with self.subTest(path=relative):
                if relative in SIX_LESSON_ARTICLES:
                    self.assertIsNotNone(old_bytes)
                    self.assertTrue(current_path.is_file())
                    self.assertEqual(
                        normalize_six_lesson_revision(
                            relative,
                            normalize_beginner_walkthrough_revision(
                                relative, current_path.read_text(encoding="utf-8")
                            ),
                        ),
                        normalize_six_lesson_revision(
                            relative,
                            normalize_beginner_walkthrough_revision(
                                relative, old_bytes.decode("utf-8")
                            ),
                        ),
                    )
                elif relative in BEGINNER_WALKTHROUGH_ARTICLES:
                    published = subprocess.run(
                        ["git", "show", f"{PUBLISHED_PR9}:{relative}"], cwd=ROOT,
                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
                    )
                    self.assertEqual(published.returncode, 0, relative)
                    self.assertEqual(
                        normalize_beginner_walkthrough_revision(
                            relative, current_path.read_text(encoding="utf-8")
                        ),
                        published.stdout.decode("utf-8"),
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
                    )
                elif relative.startswith("files/"):
                    self.assertTrue(relative.startswith(ALLOWED_FIXTURE_PREFIXES),
                                    "new fixtures must be in an approved lesson folder")
                    if old_bytes is not None:
                        self.assertEqual(current_path.read_bytes(), old_bytes,
                                         "pre-existing datasets/output artifacts are immutable")
                else:
                    self.assertIsNotNone(old_bytes,
                                         "new source files outside approved fixture folders are forbidden")
                    self.assertTrue(current_path.is_file(), "deleting published files is forbidden")
                    self.assertEqual(current_path.read_bytes(), old_bytes,
                                     "non-target source, CSS, navigation and site scripts are immutable")

    def test_normalizer_preserves_article_wrapper_and_unapproved_surrounding_text(self):
        relative = "tutorials/command-line-part2.html"
        original = git_bytes(relative).decode("utf-8")
        normalized = normalize_six_lesson_revision(relative, original)
        body_mutation = original.replace("<article", '<article data-unapproved="1"', 1)
        self.assertNotEqual(normalize_six_lesson_revision(relative, body_mutation), normalized)
        head_mutation = original.replace("<head>", "<head><!-- unauthorized -->", 1)
        self.assertNotEqual(normalize_six_lesson_revision(relative, head_mutation), normalized)
        footer_mutation = original.replace("</footer>", "<!-- unauthorized --></footer>", 1)
        self.assertNotEqual(normalize_six_lesson_revision(relative, footer_mutation), normalized)

    def test_normalizer_supports_article_only_fragments(self):
        relative = "tutorials/command-line-part2.html"
        original = git_bytes(relative).decode("utf-8")
        article = re.search(r"<article\b[^>]*>.*?</article>", original, re.S | re.I).group(0)
        changed = article.replace("</article>", "<p>revised lesson copy</p></article>")
        self.assertEqual(
            normalize_six_lesson_revision(relative, changed),
            normalize_six_lesson_revision(relative, article),
        )

    def test_sitemap_changes_only_approved_lesson_dates_including_tidyverse(self):
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        def dates(data):
            root = ET.fromstring(data)
            return {
                row.findtext("s:loc", namespaces=namespace): row.findtext("s:lastmod", namespaces=namespace)
                for row in root.findall("s:url", namespace)
            }
        before = dates(git_bytes("sitemap.xml"))
        after = dates((ROOT / "sitemap.xml").read_bytes())
        self.assertEqual(set(before), set(after))
        beginner_date_paths = {
            "tutorials/computer-data-fundamentals.html",
            "tutorials/statistics-for-bioinformatics.html",
            "tutorials/experimental-design-batch-effects.html",
        }
        tidyverse_date_paths = {TIDYVERSE_SETUP_ARTICLE}
        allowed = {
            "https://theomicshub.com/" + path
            for path in SIX_LESSON_ARTICLES | beginner_date_paths | tidyverse_date_paths
        }
        self.assertEqual({url for url in before if before[url] != after[url]}, allowed)
        for url in allowed:
            expected_date = "2026-10-24" if url.endswith(TIDYVERSE_SETUP_ARTICLE) else "2026-10-23"
            self.assertEqual(after[url], expected_date)
        restored = ET.fromstring((ROOT / "sitemap.xml").read_bytes())
        for row in restored.findall("s:url", namespace):
            url = row.findtext("s:loc", namespaces=namespace)
            if url in allowed:
                row.find("s:lastmod", namespace).text = before[url]
        self.assertEqual(
            ET.tostring(restored), ET.tostring(ET.fromstring(git_bytes("sitemap.xml"))),
            "all sitemap fields and ordering other than the ten approved dates must remain unchanged",
        )


if __name__ == "__main__":
    unittest.main()
