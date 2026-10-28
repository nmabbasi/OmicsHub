"""Strict regressions for the approved 2026-10-25 compatibility layer."""
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import unittest

from navigation_performance_baseline import (
    APPROVED_PATHS,
    BASE_COMMIT,
    FIXTURE_PATH,
    FIXTURE_PATHS,
    FIXTURE_SHA256,
    ROOT,
    WORKFLOW_PATH,
    navigation_performance_fixture,
    normalize_navigation_performance,
    restore_navigation_performance_bytes,
)
from latest_review_baseline import (
    latest_review_fixture,
    normalize_latest_review,
    restore_latest_review_asset,
)
from startup_performance_baseline import (
    ASSET_PATHS as STARTUP_ASSET_PATHS,
    TUTORIAL_PATHS as STARTUP_TUTORIAL_PATHS,
    normalize_startup_performance,
    startup_performance_fixture,
)
from startup_generated_asset_baseline import restore_startup_generated_asset
from editorial_review_baseline import PUBLIC_PATHS as EDITORIAL_REVIEW_PATHS
from start_here_desktop_baseline import (
    normalize_start_here_desktop_html,
    restore_start_here_desktop_asset,
)
from home_catalogue_banner_baseline import restore_home_catalogue_banner_asset
from coffee_removal_baseline import (
    coffee_removal_fixture,
    restore_coffee_removal_bytes,
    restore_coffee_removal_text,
)
from optional_report_baseline import (
    OPTIONAL_REPORT_PATHS,
    verify_optional_report_file,
)
from tutorial_58_review_baseline import (
    REVIEW_PATHS as TUTORIAL_58_REVIEW_PATHS,
    normalize_58_review,
    restore_58_review_asset,
)
from tutorial_execution_baseline import (
    new_execution_asset_paths,
    verify_new_execution_asset,
)


TEST_INFRASTRUCTURE_PATHS = {
    'tests/coffee_removal_baseline.py',
    'tests/optional_report_baseline.py',
    'tests/fixtures/coffee-removal-review.json',
    'tests/test_coffee_removal_baseline.py',
    'tests/fixtures/gget-mobile-baseline.json',
    'tests/gget_mobile_baseline.py',
    'tests/test_gget_mobile_baseline.py',
    'tests/browser_navigation_performance.py',
    'tests/browser_start_here_ui.py',
    'tests/browser_startup_performance.py',
    'tests/browser_startup_preservation.py',
    'tests/browser_home_catalogue_ui.py',
    'tests/fixtures/sitewide-top-review-edits.json',
    'tests/sitewide_top_baseline.py',
    'tests/test_sitewide_top_ui.py',
    'tests/browser_tutorial_reader_ui.py',
    'tests/editorial_review_baseline.py',
    'tests/fixtures/editorial-review-edits.json',
    'tests/fixtures/navigation-performance-edits.json',
    'tests/fixtures/startup-performance-edits.json',
    'tests/generate_latest_review_fixture.py',
    'tests/generate_startup_performance_fixture.py',
    'tests/home_catalogue_banner_baseline.py',
    'tests/home_catalogue_baseline.py',
    'tests/latest_review_baseline.py',
    'tests/navigation_guard_baseline.py',
    'tests/test_navigation_guard.py',
    'tests/navigation_performance_baseline.py',
    'tests/fixtures/tutorial-58-review-hashes.json',
    'tests/fixtures/tutorial-execution-exact-delta.json',
    'tests/test_58_tutorial_review_fixes.py',
    'tests/test_code_tabs.py',
    'tests/test_execution_scope_assets.py',
    'tests/test_priority_slurm.py',
    'tests/test_remaining_cite_longread.py',
    'tests/tutorial_58_review_baseline.py',
    'tests/r_first_revision_baseline.py',
    'tests/reader_text_colour_baseline.py',
    'tests/start_here_baseline.py',
    'tests/start_here_desktop_baseline.py',
    'tests/startup_generated_asset_baseline.py',
    'tests/startup_performance_baseline.py',
    'tests/test_code_tabs_digest_memoization.js',
    'tests/test_editorial_review_baseline.py',
    'tests/test_editorial_scope_fixes.py',
    'tests/test_home_catalogue_scope.py',
    'tests/test_home_catalogue_ui.py',
    'tests/test_latest_review_baseline.py',
    'tests/test_learning_promises.py',
    'tests/test_navigation_performance_baseline.py',
    'tests/test_r_first_revision_baseline.py',
    'tests/test_reader_layout_batching.js',
    'tests/test_beginner_walkthrough_scope.py',
    'tests/test_reader_punctuation.py',
    'tests/test_reader_text_colours.py',
    'tests/test_remaining_reference_support.py',
    'tests/test_remaining_validation_scope.py',
    'tests/test_revision_trajectory.py',
    'tests/test_six_lesson_revision_scope.py',
    'tests/test_sitewide_reference_fixes.py',
    'tests/test_start_here_blue_learning.py',
    'tests/test_start_here_desktop_baseline.py',
    'tests/test_start_here_hover.py',
    'tests/test_start_here_ui.py',
    'tests/test_start_here_visual_polish.py',
    'tests/test_startup_performance_baseline.py',
    'tests/test_text_alignment.py',
    'tests/test_tutorial_execution_baseline.py',
    'tests/test_tutorial_reader_ui.py',
    'tests/test_tutorial_startup.py',
    'tests/test_tidyverse_setup_scope.py',
    'tests/test_ubuntu_tidyverse_scope.py',
    'tests/test_verified_analysis_figures.py',
    'tests/tutorial_execution_baseline.py',
}



class ExecutableInlineScriptParser(HTMLParser):
    TYPES = {"", "application/ecmascript", "application/javascript", "module", "text/ecmascript", "text/javascript"}

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.scripts = []
        self.current = None
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.current = {"attrs": dict(attrs), "body": []}

    def handle_data(self, data):
        if self.current is not None:
            self.current["body"].append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.current is not None:
            attrs = self.current["attrs"]
            if "src" not in attrs and attrs.get("type", "").strip().lower() in self.TYPES:
                self.scripts.append((attrs, "".join(self.current["body"])))
            self.current = None


class NavigationPerformanceBaselineTests(unittest.TestCase):
    def test_fixture_is_closed_hash_pinned_and_proves_each_exact_edit(self):
        raw = FIXTURE_PATH.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), FIXTURE_SHA256)
        fixture = navigation_performance_fixture()
        self.assertEqual(set(fixture), FIXTURE_PATHS)
        self.assertEqual(len(APPROVED_PATHS), 51)
        self.assertEqual(FIXTURE_PATHS, APPROVED_PATHS | {WORKFLOW_PATH})

        for path in sorted(APPROVED_PATHS):
            with self.subTest(path=path):
                entry = fixture[path]
                current = normalize_startup_performance(
                    path, normalize_58_review(
                        path, (ROOT / path).read_text(encoding="utf-8")
                    )
                ).encode("utf-8")
                self.assertEqual(current, entry["after_bytes"])
                self.assertEqual(
                    hashlib.sha256(current).hexdigest(), entry["after_sha256"]
                )
                self.assertEqual(
                    entry["before_bytes"].replace(
                        entry["removed_block"].encode("utf-8"), b"", 1
                    ),
                    current,
                )
                self.assertEqual(
                    normalize_navigation_performance(path, current.decode("utf-8")).encode("utf-8"),
                    entry["before_bytes"],
                )
                before = entry["before_bytes"].decode("utf-8")
                after = current.decode("utf-8")
                for tag in ("pre", "code"):
                    pattern = rf"<{tag}\b[^>]*>.*?</{tag}\s*>"
                    self.assertEqual(
                        re.findall(pattern, after, re.S | re.I),
                        re.findall(pattern, before, re.S | re.I),
                    )
                self.assertEqual(
                    ExecutableInlineScriptParser(after).scripts,
                    ExecutableInlineScriptParser(before).scripts,
                )

    def test_workflow_restoration_is_exact_and_available_through_asset_api(self):
        entry = navigation_performance_fixture()[WORKFLOW_PATH]
        current = (ROOT / WORKFLOW_PATH).read_bytes()
        self.assertEqual(current, entry["after_bytes"])
        self.assertEqual(
            restore_navigation_performance_bytes(WORKFLOW_PATH, current),
            entry["before_bytes"],
        )
        self.assertEqual(
            restore_latest_review_asset(WORKFLOW_PATH, current),
            latest_review_fixture()[WORKFLOW_PATH]["base_bytes"],
        )

    def test_unknown_text_code_attribute_and_workflow_mutations_are_not_concealed(self):
        tutorial = "tutorials/scrna-seq-basics.html"
        current = (ROOT / tutorial).read_text(encoding="utf-8")
        # The new closed adapter rejects raw unknown mutations separately;
        # this test keeps exercising the original navigation-layer contract.
        current = normalize_58_review(tutorial, current)
        current = restore_coffee_removal_text(tutorial, current)
        mutations = {
            "text": current + "<!-- UNREVIEWED_TEXT_MUTATION -->\n",
            "code": current + "<script>window.__UNREVIEWED_CODE_MUTATION__ = true;</script>\n",
            "attribute": current.replace("<html", '<html data-unreviewed="true"', 1),
        }
        frozen_base = startup_performance_fixture()[tutorial]["base_bytes"].decode("utf-8")
        expected = {
            "text": frozen_base + "<!-- UNREVIEWED_TEXT_MUTATION -->\n",
            "code": frozen_base + "<script>window.__UNREVIEWED_CODE_MUTATION__ = true;</script>\n",
            "attribute": frozen_base.replace("<html", '<html data-unreviewed="true"', 1),
        }
        for label, changed in mutations.items():
            with self.subTest(mutation=label):
                self.assertNotEqual(changed, current)
                self.assertEqual(normalize_navigation_performance(tutorial, changed), expected[label])
                self.assertIn("UNREVIEWED_" if label != "attribute" else "data-unreviewed", normalize_latest_review(tutorial, changed))

        workflow = (ROOT / WORKFLOW_PATH).read_bytes()
        changed_workflow = workflow.replace(b"navigation-performance.json", b"unreviewed-performance.json", 1)
        self.assertEqual(
            restore_navigation_performance_bytes(WORKFLOW_PATH, changed_workflow),
            changed_workflow,
        )
        self.assertEqual(
            restore_latest_review_asset(WORKFLOW_PATH, changed_workflow),
            changed_workflow,
        )

    def test_public_diff_is_exactly_the_51_approved_tutorial_files_and_reports(self):
        changed = set(subprocess.check_output(
            ["git", "diff", "--name-only", BASE_COMMIT, "--"], cwd=ROOT, text=True
        ).splitlines())
        changed -= EDITORIAL_REVIEW_PATHS - STARTUP_TUTORIAL_PATHS
        self.assertIn(WORKFLOW_PATH, changed)
        # Exclude only new coffee-only paths after whole-file digest validation.
        coffee = coffee_removal_fixture()
        for path, entry in coffee.items():
            self.assertEqual(
                restore_coffee_removal_bytes(
                    path,
                    restore_58_review_asset(path, (ROOT / path).read_bytes()),
                ),
                entry['base_bytes'],
            )
        changed -= set(coffee) - (
            STARTUP_TUTORIAL_PATHS | STARTUP_ASSET_PATHS
            | {'home-page.min.css', 'start-here.css', 'start-here.html'}
        )
        # Verify the two explicitly authorized Start Here edits before including
        # them in the exact public-path set; unrelated CSS/HTML remains rejected.
        self.assertEqual(
            restore_start_here_desktop_asset(
                "start-here.css", (ROOT / "start-here.css").read_bytes()
            ),
            subprocess.check_output(
                ["git", "show", "e846ce3fb6053ed611dc87fc62748865499913d0:start-here.css"],
                cwd=ROOT,
            ),
        )
        desktop_html = (ROOT / "start-here.html").read_text(encoding="utf-8")
        self.assertEqual(
            normalize_start_here_desktop_html("start-here.html", desktop_html),
            subprocess.check_output(
                ["git", "show", "e846ce3fb6053ed611dc87fc62748865499913d0:start-here.html"],
                cwd=ROOT, text=True,
            ),
        )
        for path in sorted(changed & OPTIONAL_REPORT_PATHS):
            verify_optional_report_file(path, (ROOT / path).read_bytes())
        review_only_paths = TUTORIAL_58_REVIEW_PATHS - (
            STARTUP_TUTORIAL_PATHS | STARTUP_ASSET_PATHS
            | {"home-page.min.css", "start-here.css", "start-here.html"}
        )
        self.assertEqual(review_only_paths, {
            "files/tutorial-examples/research-reporting-interpretation/research-reporting-workflow.Rmd",
            "tools/catalogue-learning.json",
            "tools/tutorial-code-groups.json",
            "tools/tutorial-code-languages.json",
            "tutorial-code-data.js",
        })
        for path in sorted(changed & review_only_paths):
            current = (ROOT / path).read_bytes()
            restored = (
                normalize_58_review(path, current.decode("utf-8")).encode("utf-8")
                if path.endswith(".Rmd")
                else restore_58_review_asset(path, current)
            )
            self.assertNotEqual(restored, current, path)
        changed -= review_only_paths
        execution_review_paths = {
            "files/tutorial-examples/16s-dada2-taxonomy/dada2-taxonomy-workflow.Rmd",
            "files/tutorial-examples/execution-evidence/2026-10-28-reporting.json",
        }
        self.assertEqual(
            new_execution_asset_paths() & execution_review_paths,
            execution_review_paths,
        )
        for path in sorted(changed & execution_review_paths):
            self.assertEqual(
                verify_new_execution_asset(path, (ROOT / path).read_bytes()),
                (ROOT / path).read_bytes(),
            )
        changed -= execution_review_paths
        self.assertEqual(
            changed - TEST_INFRASTRUCTURE_PATHS - {WORKFLOW_PATH},
            STARTUP_TUTORIAL_PATHS | STARTUP_ASSET_PATHS
            | {"home-page.min.css", "start-here.css", "start-here.html", "tutorial-library.css", "home-catalogue.css"}
            | OPTIONAL_REPORT_PATHS,
        )

    def test_all_other_tracked_source_assets_and_site_surfaces_are_byte_preserved(self):
        tracked = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", BASE_COMMIT], cwd=ROOT, text=True
        ).splitlines()
        allowed = STARTUP_TUTORIAL_PATHS | STARTUP_ASSET_PATHS | {WORKFLOW_PATH}
        for path in tracked:
            if path in OPTIONAL_REPORT_PATHS:
                verify_optional_report_file(path, (ROOT / path).read_bytes())
                continue
            if path.startswith("tests/") or path in allowed:
                continue
            if path.startswith(".github/") and path != WORKFLOW_PATH:
                # Workflow/test configuration is not a public site surface.
                continue
            with self.subTest(path=path):
                expected = subprocess.check_output(
                    ["git", "show", f"{BASE_COMMIT}:{path}"], cwd=ROOT
                )
                current = restore_58_review_asset(path, (ROOT / path).read_bytes())
                if path == "start-here.css":
                    current = restore_start_here_desktop_asset(path, current)
                elif path == "home-catalogue.css":
                    current = restore_home_catalogue_banner_asset(path, current)
                elif path == "start-here.html":
                    current = normalize_start_here_desktop_html(
                        path, current.decode("utf-8")
                    ).encode("utf-8")
                current = restore_startup_generated_asset(path, current, "main")
                self.assertEqual(current, expected)


if __name__ == "__main__":
    unittest.main()
