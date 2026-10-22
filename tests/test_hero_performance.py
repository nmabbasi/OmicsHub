#!/usr/bin/env python3
"""Homepage-only performance proposal guards, using Python stdlib."""
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'e7037f1b9a9eea8f4338e7b6696f791d8172f844'

class Tags(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

class HeroPerformanceTests(unittest.TestCase):
    def test_viewport_and_hero_discovered_before_font_requests(self):
        tags = Tags((ROOT / 'index.html').read_text()).tags
        viewport = next(i for i, (t, a) in enumerate(tags) if t == 'meta' and a.get('name') == 'viewport')
        preload = next(i for i, (t, a) in enumerate(tags) if t == 'link' and a.get('as') == 'image')
        fonts = next(i for i, (t, a) in enumerate(tags) if t == 'link' and a.get('as') == 'font')
        self.assertLess(viewport, preload)
        self.assertLess(preload, fonts)
        self.assertEqual(tags[preload][1]['fetchpriority'], 'high')

    def test_avif_preload_exactly_matches_first_picture_source(self):
        tags = Tags((ROOT / 'index.html').read_text()).tags
        preloads = [a for t, a in tags if t == 'link' and a.get('as') == 'image']
        self.assertEqual(len(preloads), 1, 'Do not preload both AVIF and WebP')
        sources = [a for t, a in tags if t == 'source' and 'hero-image-light-navy-clean' in a.get('srcset', '')]
        self.assertEqual([a['type'] for a in sources], ['image/avif', 'image/webp'])
        self.assertEqual(preloads[0]['type'], sources[0]['type'])
        self.assertEqual(preloads[0]['imagesrcset'], sources[0]['srcset'])
        self.assertEqual(preloads[0]['imagesizes'], sources[0]['sizes'])
        self.assertIn('(min-width:640px) calc(100vw - 128px)', sources[0]['sizes'])
        self.assertEqual(sources[0]['sizes'], sources[1]['sizes'])
        for width in [480, 640, 768, 1200, 1920]:
            p = ROOT / f'images/hero-image-light-navy-clean-{width}.avif'
            self.assertTrue(p.is_file())
            self.assertIn(b'ftypavif', p.read_bytes()[:40])
            self.assertIn(f'{p.name} {width}w', sources[0]['srcset'])
        mobile = ROOT / 'images/hero-image-light-navy-clean-640.avif'
        published = ROOT / 'images/hero-image-light-navy-clean-768.webp'
        self.assertLess(mobile.stat().st_size, published.stat().st_size * .6)

    def test_fallback_and_layout_are_preserved(self):
        html = (ROOT / 'index.html').read_text()
        hero = next(a for t, a in Tags(html).tags if t == 'img' and a.get('fetchpriority') == 'high')
        self.assertEqual(hero['src'], 'images/hero-image-light-navy-clean.webp')
        self.assertEqual((hero['width'], hero['height']), ('1920', '1920'))
        self.assertNotEqual(hero.get('loading'), 'lazy')
        self.assertIn('hero-image-light-navy-clean-768.webp 768w', hero['srcset'])

    def test_homepage_analytics_is_deferred_and_ads_remain_async(self):
        html = (ROOT / 'index.html').read_text()
        tags = Tags(html).tags
        analytics = [a for t, a in tags if t == 'script' and a.get('src') == 'analytics.js']
        self.assertEqual(len(analytics), 1)
        self.assertIn('defer', analytics[0])
        ads = [a for t, a in tags if t == 'script' and 'adsbygoogle.js' in a.get('src', '')]
        self.assertEqual(len(ads), 1)
        self.assertIn('async', ads[0])
        self.assertEqual(ads[0]['crossorigin'], 'anonymous')
        self.assertEqual(ads[0]['src'], 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2910340533244599')
        for field in ['ad_storage', 'ad_user_data', 'ad_personalization', 'analytics_storage']:
            self.assertIn("'" + field + "': 'denied'", html)

    def test_approved_content_ads_and_original_assets_unchanged(self):
        def old(name):
            result = subprocess.run(['git', 'show', BASELINE + ':' + name], cwd=ROOT,
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            return result.stdout if result.returncode == 0 else None
        baseline = old('index.html')
        if baseline is None:
            self.skipTest('Historical baseline unavailable in shallow checkout')
        original = baseline.decode()
        current = (ROOT / 'index.html').read_text()
        # Undo only the new source and responsive-size attributes; the whole body must match.
        old_sizes = re.search(r'<img[^>]+fetchpriority="high"[^>]+sizes="([^"]+)"', original).group(1)
        body = current[current.index('<body'):]
        body = re.sub(r'<source[^>]+type="image/avif"/>\n', '', body)
        body = re.sub(r'sizes="[^"]+"', 'sizes="' + old_sizes + '"', body)
        self.assertEqual(body, original[original.index('<body'):])
        old_ads = re.search(r'<script[^>]+adsbygoogle\.js[^>]+></script>', original).group()
        self.assertIn(old_ads, current, 'Keep the provider script exactly unchanged')
        for name in ['analytics.js', 'cookie-consent.js', 'style.css', 'subscribe-fab.js',
                     'images/hero-image-light-navy-clean.webp',
                     'images/hero-image-light-navy-clean-480.webp',
                     'images/hero-image-light-navy-clean-768.webp',
                     'images/hero-image-light-navy-clean-1200.webp']:
            self.assertEqual(old(name), (ROOT / name).read_bytes(), name)
        for p in (ROOT / 'tutorials').glob('*.html'):
            self.assertEqual(old('tutorials/' + p.name), p.read_bytes(), p.name)

if __name__ == '__main__':
    unittest.main()
