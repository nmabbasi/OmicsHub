#!/usr/bin/env python3
"""Read-only checks for responsive assets and nonblocking font delivery."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import hashlib
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class Tags(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

class MobileLoadingTests(unittest.TestCase):
    def test_every_html_page_uses_existing_local_font_resources(self):
        pages = list(ROOT.glob('*.html')) + list(ROOT.glob('pages/*.html')) + list(ROOT.glob('tutorials/*.html'))
        for page in pages:
            text = page.read_text(encoding='utf-8')
            with self.subTest(page=page.relative_to(ROOT).as_posix()):
                self.assertNotIn('https://fonts.googleapis.com', text)
                self.assertNotIn('https://fonts.gstatic.com', text)
                links = [attrs for tag, attrs in Tags(text).tags if tag == 'link']
                css = [a for a in links if a.get('rel') == 'stylesheet' and a.get('href', '').endswith('fonts/fonts.css')]
                self.assertEqual(len(css), 1)
                self.assertTrue((page.parent / css[0]['href']).is_file())
                fonts = [a for a in links if a.get('as') == 'font' and a.get('rel') == 'preload']
                self.assertEqual(len(fonts), 1)
                self.assertEqual(fonts[0].get('crossorigin'), 'anonymous')
                self.assertTrue((page.parent / fonts[0]['href']).is_file())

    def test_font_css_and_licenses_are_local_and_complete(self):
        css = (ROOT / 'fonts/fonts.css').read_text(encoding='utf-8')
        self.assertNotIn('https://', css)
        self.assertIn("font-family: 'Inter'", css)
        self.assertIn("font-family: 'JetBrains Mono'", css)
        self.assertNotIn('font-display: block', css)
        for value in re.findall(r'url\(([^)]+)\)', css):
            path = ROOT / 'fonts' / value
            self.assertTrue(path.is_file(), value)
            self.assertEqual(path.read_bytes()[:4], b'wOF2')
        for name in ['inter-OFL.txt', 'jetbrains-mono-OFL.txt']:
            self.assertIn('SIL OPEN FONT LICENSE', (ROOT / 'fonts' / name).read_text(encoding='utf-8'))

    def test_hero_responsive_preload_matches_picture(self):
        tags = Tags((ROOT / 'index.html').read_text(encoding='utf-8')).tags
        hero = next(a for t, a in tags if t == 'img' and a.get('fetchpriority') == 'high')
        preload = next(a for t, a in tags if t == 'link' and a.get('as') == 'image')
        source = next(a for t, a in tags if t == 'source' and 'hero-image-light-navy-clean' in a.get('srcset', ''))
        fallback = next(a for t, a in tags if t == 'source' and a.get('type') == 'image/webp')
        self.assertEqual(source['srcset'], preload['imagesrcset'])
        self.assertEqual(hero['sizes'], preload['imagesizes'])
        self.assertEqual(hero['srcset'], fallback['srcset'])
        self.assertEqual(hero['sizes'], source['sizes'])
        self.assertEqual(hero['sizes'], fallback['sizes'])
        self.assertEqual(source['type'], 'image/avif')
        self.assertEqual(preload['type'], 'image/avif')
        self.assertEqual((hero['width'], hero['height']), ('1920', '1920'))
        original = ROOT / hero['src']
        self.assertTrue(original.is_file())
        for width in [480, 768, 1200]:
            variant = ROOT / f'images/hero-image-light-navy-clean-{width}.webp'
            self.assertTrue(variant.is_file())
            self.assertLess(variant.stat().st_size, original.stat().st_size)
            self.assertIn(f'{variant.name} {width}w', hero['srcset'])

    def test_landing_pages_do_not_download_unused_code_libraries(self):
        for name in ['index.html', 'tutorials.html']:
            with self.subTest(page=name):
                tags = Tags((ROOT / name).read_text(encoding='utf-8')).tags
                self.assertFalse(any(t == 'pre' for t, a in tags))
                for tag, attrs in tags:
                    value = attrs.get('src', attrs.get('href', ''))
                    self.assertNotIn('cdnjs.cloudflare.com/ajax/libs/prism/', value)
                    self.assertNotIn('cdn.jsdelivr.net/npm/marked/', value)
                shared = next(a for t, a in tags if t == 'script' and a.get('src', '').startswith('script.js'))
                self.assertIn('defer', shared)

    def test_tutorial_code_and_advertising_setup_are_not_removed(self):
        for page in ROOT.glob('tutorials/*.html'):
            text = page.read_text(encoding='utf-8')
            with self.subTest(page=page.name):
                self.assertIn('copy-code.js', text)
                self.assertIn('pagead2.googlesyndication.com/pagead/js/adsbygoogle.js', text)
                self.assertIn('cookie-consent.js', text)
                self.assertIn('google-adsense-account', text)

    def test_local_images_have_positive_intrinsic_dimensions(self):
        pages = list(ROOT.glob('*.html')) + list(ROOT.glob('pages/*.html')) + list(ROOT.glob('tutorials/*.html'))
        for page in pages:
            for tag, attrs in Tags(page.read_text(encoding='utf-8')).tags:
                if tag != 'img' or not attrs.get('src'):
                    continue
                url = urlsplit(attrs['src'])
                if url.scheme or url.netloc:
                    continue
                with self.subTest(page=page.name, image=attrs['src']):
                    self.assertGreater(int(attrs.get('width', '0')), 0)
                    self.assertGreater(int(attrs.get('height', '0')), 0)

    def test_homepage_uses_smaller_css_without_replacing_tutorial_styles(self):
        homepage = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn('href="home-page.min.css?', homepage)
        shared = ROOT / 'style.css'
        subset = ROOT / 'home-page.min.css'
        self.assertLess(subset.stat().st_size, shared.stat().st_size * 0.4)
        css = subset.read_text(encoding='utf-8')
        for selector in ['subscribe-community-button', 'hero-laptop-content', 'footer', 'html']:
            self.assertIn(selector, css)
        for page in ROOT.glob('tutorials/*.html'):
            self.assertIn('../style.css', page.read_text(encoding='utf-8'))

    def test_homepage_css_source_fingerprint_is_current(self):
        digest = hashlib.sha256()
        files = ['style.css', 'index.html', 'script.js', 'subscribe-fab.js',
                 'cookie-consent.js', 'mobile-navigation.js']
        for name in files:
            digest.update((ROOT / name).read_bytes())
        css = (ROOT / 'home-page.min.css').read_text(encoding='utf-8')
        self.assertIn('Source SHA256: ' + digest.hexdigest(), css,
                      'Rebuild with npm run --prefix tools build:home-css before publication')

if __name__ == '__main__':
    unittest.main()
