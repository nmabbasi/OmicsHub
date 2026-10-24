"""Static UI contracts. No scientific execution is claimed by these checks."""
from pathlib import Path
import importlib.util
import json
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRE_UI = '243bc04'
spec = importlib.util.spec_from_file_location('tutorial_ui_generator', ROOT / 'tools/generate_tutorial_ui.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

class TutorialReaderUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata = generator.load_metadata(ROOT)
        cls.pages = sorted((ROOT / 'tutorials').glob('*.html'))

    def test_every_lesson_body_is_byte_identical_outside_generated_navigation(self):
        for page in self.pages:
            relative = page.relative_to(ROOT).as_posix()
            before = subprocess.check_output(['git', 'show', f'{PRE_UI}:{relative}'], cwd=ROOT).decode()
            after = page.read_text()
            # One legacy article contains its continuation nav. Exclude only that
            # named nav, whose complete renderer/targets have separate tests.
            pattern = r'<nav\b(?=[^>]*\bid="reader-course-navigation")[^>]*>.*?</nav>'
            before = re.sub(pattern, '__GENERATED_CONTINUATION_NAV__', before, flags=re.S)
            after = re.sub(pattern, '__GENERATED_CONTINUATION_NAV__', after, flags=re.S)
            with self.subTest(page=page.name):
                self.assertEqual(re.findall(r'<article\b.*?</article>', before, re.S), re.findall(r'<article\b.*?</article>', after, re.S))
                self.assertEqual(re.findall(r'"dateModified"\s*:\s*"[^"]+"', before), re.findall(r'"dateModified"\s*:\s*"[^"]+"', after))

    def test_inventory_is_complete_and_every_code_hash_is_checked(self):
        self.assertEqual(len(self.metadata['tutorials']), 58)
        self.assertEqual(sum(len(s['blocks']) for s in self.metadata['tutorials'].values()), 351)
        self.assertEqual(sum(len(s['groups']) for s in self.metadata['tutorials'].values()), 8)
        self.assertEqual({slug for slug, s in self.metadata['tutorials'].items() if s['groups']}, {
            'scrna-seq-basics', 'statistics-for-bioinformatics', 'experimental-design-batch-effects', 'spatial-transcriptomics-r-python'
        })
        for slug in ['ai-prompt-engineering-seurat', 'scrna-seq-quality-control', 'scrna-seq-trajectory-inference', 'infercnv-copy-number-variation']:
            self.assertFalse(self.metadata['tutorials'][slug]['groups'], slug)

    def test_generation_is_current_and_idempotent(self):
        checked = subprocess.run(['python3', 'tools/generate_tutorial_ui.py', '--check'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        for page in self.pages:
            source = page.read_text()
            self.assertEqual(generator.render_page(source), source, page.name)

    def test_new_assets_are_local_and_static_back_link_works_without_js(self):
        for page in self.pages:
            source = page.read_text()
            with self.subTest(page=page.name):
                self.assertNotIn('cdnjs.cloudflare.com/ajax/libs/prism', source)
                self.assertEqual(source.count('assets/vendor/prism/prism-1.29.0.js'), 1)
                for name in ['tutorial-reader.css', 'tutorial-navigation.css', 'tutorial-code-data.js', 'code-tabs.js']:
                    self.assertEqual(source.count(f'../{name}?v={generator.VERSION}"'), 1)
                self.assertEqual(source.count('id="back-to-top"'), 1)
                self.assertIn('id="back-to-top" href="#tutorial-title"', source)
                self.assertIn('id="tutorial-title"', source)
                self.assertNotIn('data-code-tabs', source, 'Language routes stay visible in source/no-JS mode')

    def test_upgrading_first_draft_versions_never_duplicates_local_assets(self):
        for page in self.pages:
            current = page.read_text()
            previous = current.replace(generator.VERSION, '20261024-reader-ui')
            self.assertEqual(generator.render_page(previous), current, page.name)

    def test_failed_fingerprints_are_rejected_before_publishing_stale_tabs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'tools').mkdir(); (root / 'tutorials').mkdir()
            for name in ['tutorial-code-languages.json', 'tutorial-code-groups.json']:
                (root / 'tools' / name).write_bytes((ROOT / 'tools' / name).read_bytes())
            for page in self.pages: (root / 'tutorials' / page.name).write_bytes(page.read_bytes())
            page = root / 'tutorials/statistics-for-bioinformatics.html'
            page.write_text(page.read_text().replace('import numpy as np', 'import numpy as changed', 1))
            with self.assertRaisesRegex(ValueError, 'fingerprint changed'):
                generator.load_metadata(root)

    def test_tabs_and_clipboard_have_explicit_accessibility_and_fallbacks(self):
        tabs = (ROOT / 'code-tabs.js').read_text()
        copy = (ROOT / 'copy-code.js').read_text()
        css = (ROOT / 'tutorial-reader.css').read_text()
        for value in ["'tablist'", "'tab'", "'tabpanel'", "'aria-selected'", "'aria-controls'", "'aria-labelledby'", "'ArrowRight'", "'ArrowLeft'", "'Home'", "'End'", "'hashchange'", "'SHA-256'"]:
            self.assertIn(value, tabs)
        self.assertNotIn("event.key === 'ArrowDown'", tabs, 'Horizontal tabs preserve vertical scrolling keys')
        self.assertIn("code.textContent", copy)
        self.assertIn('navigator.clipboard', copy)
        self.assertIn('range.selectNodeContents(code || pre)', copy)
        self.assertIn("'aria-live', 'polite'", copy)
        self.assertIn('@media (prefers-reduced-motion: reduce)', css)
        self.assertIn('@media print', css)
        self.assertIn('.code-tab-panel[hidden] { display: block !important; }', css)
        self.assertNotIn('position: fixed', css)
        for text in [tabs, copy, css]: self.assertNotIn('\u2014', text)

    def test_all_external_non_prism_sources_and_inline_scripts_are_preserved(self):
        def external_scripts(source):
            return [url for url in re.findall(r'<script\b[^>]*src="([^"]+)"', source) if url.startswith('http') and '/prism/' not in url]
        def inline_scripts(source):
            return [block for block in re.findall(r'<script\b[^>]*>.*?</script>', source, re.S) if not re.match(r'<script\b[^>]*\bsrc=', block)]
        for page in self.pages:
            before = subprocess.check_output(['git', 'show', f'{PRE_UI}:tutorials/{page.name}'], cwd=ROOT).decode()
            after = page.read_text()
            self.assertEqual(external_scripts(before), external_scripts(after), page.name)
            self.assertEqual(inline_scripts(before), inline_scripts(after), page.name)

if __name__ == '__main__': unittest.main()
