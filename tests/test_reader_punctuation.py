"""Protect the owner-requested reader-copy cleanup without masking scientific changes."""
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import unittest

from beginner_walkthrough_baseline import normalize_beginner_walkthrough_revision
from six_lesson_revision_baseline import normalize_six_lesson_revision
from tidyverse_setup_baseline import normalize_tidyverse_setup_revision
from remaining_validation_baseline import (
    allowed_paths as remaining_validation_paths,
    normalize_remaining_validation_edit,
)
from advanced_validation_baseline import (
    allowed_asset_paths as advanced_asset_paths,
    normalize_advanced_validation_asset,
    normalize_advanced_validation_if_allowed,
    published_bytes as advanced_published_bytes,
)
from resource_content_baseline import normalize_resource_content
from tutorial_ui_baseline import (
    TUTORIAL_UI_PATHS,
    normalize_tutorial_ui,
    verify_tutorial_ui_file,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = 'c030bc62bf6e4a4ad21f9ff64cb630c152157692'
FIXTURE = ROOT / 'tests/fixtures/reader-copy-edits.json'
NAVIGATION = ['index.html', 'start-here.html', 'tutorials.html', 'about.html',
              'contact.html', 'services.html', 'success.html', '404.html']


def baseline(relative):
    return subprocess.check_output(['git', 'show', f'{BASE}:{relative}'], cwd=ROOT).decode()


def current_before_resource_content_edits(relative):
    return normalize_resource_content(relative, (ROOT / relative).read_bytes()).decode('utf-8')


class LinkAndIdParser(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag == 'a':
            self.links.append((attrs.get('href'), attrs.get('target'), attrs.get('rel')))


class ReaderPunctuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(FIXTURE.read_text())
        cls.pages = NAVIGATION + sorted(str(p.relative_to(ROOT)) for p in (ROOT/'pages').glob('*.html'))
        cls.pages += sorted(str(p.relative_to(ROOT)) for p in (ROOT/'tutorials').glob('*.html'))
        cls.old = {path: baseline(path) for path in cls.pages}

    def test_all_70_public_reading_pages_have_no_literal_or_encoded_em_dashes(self):
        self.assertEqual(len(self.pages), 70)
        for relative in self.pages:
            with self.subTest(page=relative):
                text = (ROOT/relative).read_text()
                self.assertNotIn('\u2014', unescape(text))
                self.assertNotRegex(text, r'(?i)\\u2014')

    def test_edit_fixture_lists_only_public_pages_and_the_navigation_copy_source(self):
        self.assertEqual(self.manifest['schema_version'], 1)
        self.assertEqual(set(self.manifest['files']), set(self.pages) | {'tools/learning-paths.json'})
        for relative, changes in self.manifest['files'].items():
            for pair in changes['replacements']:
                with self.subTest(path=relative, before=pair['before'][:60]):
                    self.assertIn('\u2014', pair['before'])
                    self.assertNotIn('\u2014', pair['after'])
                    self.assertNotEqual(pair['before'], pair['after'])

    def test_every_source_change_matches_the_exact_recorded_copy_and_cache_edits(self):
        for relative, changes in self.manifest['files'].items():
            with self.subTest(path=relative):
                expected = self.old.get(relative) or baseline(relative)
                for pair in changes['replacements']:
                    self.assertIn(pair['before'], expected)
                    expected = expected.replace(pair['before'], pair['after'])
                for pair in self.manifest['stylesheet_versions']:
                    expected = expected.replace(pair['before'], pair['after'])
                expected = normalize_beginner_walkthrough_revision(relative, expected)
                current = normalize_beginner_walkthrough_revision(
                    relative, normalize_advanced_validation_if_allowed(
                        relative, current_before_resource_content_edits(relative)
                    )
                )
                expected = normalize_six_lesson_revision(relative, expected)
                current = normalize_six_lesson_revision(relative, current)
                expected = normalize_tidyverse_setup_revision(relative, expected)
                current = normalize_tidyverse_setup_revision(relative, current)
                if relative in remaining_validation_paths():
                    current = normalize_remaining_validation_edit(relative, current)
                self.assertEqual(current, expected)

    def test_all_pre_inline_code_and_executable_script_blocks_remain_byte_identical(self):
        patterns = [r'<pre\b[^>]*>.*?</pre>', r'<code\b[^>]*>.*?</code>']
        for relative, before in self.old.items():
            before = normalize_beginner_walkthrough_revision(relative, before)
            after = normalize_beginner_walkthrough_revision(
                relative, normalize_advanced_validation_if_allowed(
                    relative, current_before_resource_content_edits(relative)
                )
            )
            before = normalize_six_lesson_revision(relative, before)
            after = normalize_six_lesson_revision(relative, after)
            before = normalize_tidyverse_setup_revision(relative, before)
            after = normalize_tidyverse_setup_revision(relative, after)
            if relative in remaining_validation_paths():
                after = normalize_remaining_validation_edit(
                    relative, (ROOT / relative).read_text()
                )
            for pattern in patterns:
                with self.subTest(path=relative, pattern=pattern):
                    old_blocks, new_blocks = re.findall(pattern, before, re.S), re.findall(pattern, after, re.S)
                    self.assertEqual(old_blocks, new_blocks)
            # Executable JavaScript is checked on the raw pages. Do not restore
            # target articles first, or a script placed inside one could hide.
            raw_after = normalize_tutorial_ui(relative, (ROOT/relative).read_text())
            old_scripts = [block for block in re.findall(
                r'<script\b[^>]*>.*?</script>', self.old[relative], re.S
            ) if 'type="application/ld+json"' not in block]
            new_scripts = [block for block in re.findall(
                r'<script\b[^>]*>.*?</script>', raw_after, re.S
            ) if 'type="application/ld+json"' not in block]
            with self.subTest(path=relative, pattern='raw executable scripts'):
                self.assertEqual(old_scripts, new_scripts)

    def test_links_anchor_ids_and_modification_metadata_are_unchanged(self):
        for relative, before in self.old.items():
            with self.subTest(page=relative):
                before = normalize_beginner_walkthrough_revision(relative, before)
                after = normalize_beginner_walkthrough_revision(
                    relative, normalize_advanced_validation_if_allowed(
                        relative, current_before_resource_content_edits(relative)
                    )
                )
                before = normalize_six_lesson_revision(relative, before)
                after = normalize_six_lesson_revision(relative, after)
                before = normalize_tidyverse_setup_revision(relative, before)
                after = normalize_tidyverse_setup_revision(relative, after)
                if relative in remaining_validation_paths():
                    after = normalize_remaining_validation_edit(
                        relative, (ROOT / relative).read_text()
                    )
                old, new = LinkAndIdParser(before), LinkAndIdParser(after)
                self.assertEqual(old.links, new.links)
                self.assertEqual(old.ids, new.ids)
                pattern = r'"dateModified"\s*:\s*"[^\"]+"'
                self.assertEqual(re.findall(pattern, before), re.findall(pattern, after))

    def test_analysis_downloads_research_examples_images_and_site_scripts_are_unchanged(self):
        # The newer six-lesson scope suite checks the exact six sitemap dates
        # and every other XML field against PR8; typography assets stay strict.
        changed = subprocess.check_output(
            ['git', 'diff', '--name-only', BASE, '--', 'files/', 'images/',
             'tutorials/examples/', '*.js'], cwd=ROOT, text=True).splitlines()
        baseline_files = set(subprocess.check_output(
            ['git', 'ls-tree', '-r', '--name-only', BASE, '--', 'files/'], cwd=ROOT, text=True
        ).splitlines())
        allowed_prefixes = (
            'files/text-processing-lesson/', 'files/micromamba-lesson/',
            'files/slurm-basics-lesson/', 'files/trajectory-contract-lesson/',
            'files/annotation-preflight-lesson/', 'files/coding-assistant-lesson/',
        )
        fixture_changes = [path for path in changed if path.startswith('files/')]
        approved_assets = advanced_asset_paths()
        for relative in fixture_changes:
            if relative in approved_assets:
                self.assertEqual(
                    normalize_advanced_validation_asset(
                        relative, (ROOT / relative).read_bytes()
                    ),
                    advanced_published_bytes(relative),
                    'the exact approved asset path must retain its manifest-pinned full bytes',
                )
        # This consent repair authorizes one production script and its exact runtime fixture.
        reviewed_scripts = {'analytics.js', 'tests/test_analytics_load_order.js'}
        verified_ui_paths = set(changed) & TUTORIAL_UI_PATHS
        for relative in sorted(verified_ui_paths):
            verify_tutorial_ui_file(relative, (ROOT / relative).read_bytes())
        forbidden = [path for path in changed
                     if path not in reviewed_scripts
                     and path not in verified_ui_paths
                     and not path.startswith('files/')]
        invalid_fixtures = [
            path for path in fixture_changes
            if (path in baseline_files and path not in approved_assets)
            or (not path.startswith(allowed_prefixes) and path not in approved_assets)
        ]
        self.assertEqual(forbidden, [], 'Reader-copy edits must not modify images, research examples or site scripts')
        self.assertEqual(invalid_fixtures, [], 'Only new files in the six approved teaching-fixture folders are permitted')

    def test_generated_navigation_copy_cannot_reintroduce_em_dashes(self):
        for relative in ['tools/learning-paths.json', 'tools/generate_learning_paths.py', 'script.js']:
            with self.subTest(path=relative):
                text = (ROOT/relative).read_text()
                self.assertNotIn('\u2014', unescape(text))
                self.assertNotRegex(text, r'(?i)\\u2014')

    def test_all_reading_pages_use_the_new_shared_stylesheet_version(self):
        for relative in self.pages:
            with self.subTest(path=relative):
                stylesheet = 'home-page.min.css' if relative == 'index.html' else 'style.css'
                self.assertIn(stylesheet+'?v=20261023-reader-typography', (ROOT/relative).read_text())
        self.assertIn('home-page.min.css?v=20261023-reader-typography', (ROOT/'index.html').read_text())
        self.assertIn('start-here.css?v=20261023-reader-typography', (ROOT/'start-here.html').read_text())


if __name__ == '__main__':
    unittest.main()
