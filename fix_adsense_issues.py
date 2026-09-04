#!/usr/bin/env python3
"""Fix all 3 AdSense blocking issues across The Omics Hub."""

import os
import glob
import re

# ============================================================
# ISSUE 1: Cookie Consent Banner
# ============================================================

COOKIE_BANNER_HTML = '''<!-- Cookie Consent Banner -->
<div id="cookie-consent-banner" class="fixed bottom-0 inset-x-0 z-[9999] transition-transform duration-500" style="font-family:'Inter',system-ui,sans-serif;">
  <div class="mx-auto max-w-4xl px-4 pb-4 sm:px-6">
    <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-2xl sm:flex sm:items-start sm:gap-6">
      <div class="flex-1 min-w-0">
        <p class="text-sm font-semibold text-gray-900 mb-1">Cookie preferences</p>
        <p class="text-sm text-gray-600 leading-relaxed">
          This site uses cookies for analytics and to serve relevant content. Essential cookies are always active. You may accept or decline optional cookies. See our
          <a href="COOKIE_POLICY_HREF" class="text-blue-600 hover:underline font-medium">Cookie Policy</a> for details.
        </p>
      </div>
      <div class="mt-4 flex flex-wrap items-center gap-2 sm:mt-0 sm:flex-shrink-0">
        <button data-cookie-choice="declined" class="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500">Decline</button>
        <button data-cookie-choice="accepted" class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500">Accept all</button>
      </div>
    </div>
  </div>
</div>
<script src="COOKIE_CONSENT_JS_HREF" defer></script>
<!-- /Cookie Consent Banner -->
'''

def inject_cookie_banner(filepath):
    """Inject cookie consent banner into an HTML file just before </body>."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip if already has the banner
    if 'cookie-consent-banner' in content:
        return False

    # Determine path prefix based on file location
    if filepath.startswith('pages/'):
        cookie_policy_href = 'cookie.html'
        consent_js_href = '../cookie-consent.js'
    else:
        cookie_policy_href = 'pages/cookie.html'
        consent_js_href = 'cookie-consent.js'

    banner = COOKIE_BANNER_HTML.replace('COOKIE_POLICY_HREF', cookie_policy_href)
    banner = banner.replace('COOKIE_CONSENT_JS_HREF', consent_js_href)

    # Insert before </body>
    if '</body>' in content:
        content = content.replace('</body>', banner + '\n</body>')
    else:
        return False

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return True


def fix_cookie_consent():
    """Inject cookie consent banner into all HTML pages."""
    count = 0
    # Root-level HTML files
    for f in sorted(glob.glob('*.html')):
        if inject_cookie_banner(f):
            count += 1
            print(f'  + Cookie banner: {f}')
    # Pages subdirectory
    for f in sorted(glob.glob('pages/*.html')):
        if inject_cookie_banner(f):
            count += 1
            print(f'  + Cookie banner: {f}')
    print(f'  Total files updated with cookie banner: {count}')
    return count


# ============================================================
# ISSUE 2: Custom 404 Page
# ============================================================

PAGE_404 = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<meta name="robots" content="noindex, nofollow"/>
<title>Page Not Found | The Omics Hub</title>
<link href="images/favicon.svg" rel="icon" type="image/svg+xml"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=block" rel="stylesheet"/>
<link href="tailwind.min.css" rel="stylesheet">
<link href="style.css?v=20260818-header-brand-32" rel="stylesheet"/>
<style>
  .error-container { min-height: calc(100vh - 200px); display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 2rem; }
  .error-code { font-size: 8rem; font-weight: 800; line-height: 1; background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #06b6d4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  .error-icon { width: 80px; height: 80px; margin-bottom: 1.5rem; }
  @media (max-width: 640px) { .error-code { font-size: 5rem; } }
</style>
</head>
<body class="bg-white text-gray-900">
<script>
function toggleMobileMenu() {
  const menu = document.getElementById("mobile-menu");
  const trigger = document.querySelector('[aria-controls="mobile-menu"]');
  if (!menu) return;
  const opening = menu.classList.contains("hidden");
  menu.classList.toggle("hidden", !opening);
  if (trigger) {
    trigger.setAttribute("aria-expanded", String(opening));
    trigger.setAttribute("aria-label", opening ? "Close navigation menu" : "Open navigation menu");
  }
}
</script>
<!-- Header -->
<header class="bg-white border-b border-gray-200 sticky top-0 z-50">
<nav class="container mx-auto px-6 py-4">
<div class="flex items-center justify-between">
<div class="flex items-center gap-6">
  <a href="index.html" class="flex items-center space-x-3">
    <div class="w-10 h-10 rounded-lg flex items-center justify-center shadow shadow-blue-900/30" style="width:40px;height:40px;background-color:#123B5D;flex:0 0 40px">
      <svg class="w-7 h-7" viewBox="0 0 32 32" role="img" aria-hidden="true">
        <path d="M6 10 L15 16 L25 7 M15 16 L25 25 M15 16 L7 25" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="6" cy="10" r="3.2" fill="#22D3EE" stroke="#ffffff" stroke-width="1.2"/>
        <circle cx="25" cy="7" r="3.2" fill="#A78BFA" stroke="#ffffff" stroke-width="1.2"/>
        <circle cx="15" cy="16" r="3.7" fill="#ffffff" stroke="#123B5D" stroke-width="1.2"/>
        <circle cx="25" cy="25" r="3.2" fill="#FBBF24" stroke="#ffffff" stroke-width="1.2"/>
        <circle cx="7" cy="25" r="3.2" fill="#34D399" stroke="#ffffff" stroke-width="1.2"/>
      </svg>
    </div>
    <span class="text-xl font-bold text-gray-900 tracking-tight">The Omics Hub</span>
  </a>
</div>
<div class="hidden md:flex items-center space-x-1">
<a href="index.html" class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 rounded-md hover:bg-gray-50 transition-all">Home</a>
<a href="index.html#all-tutorials" class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 rounded-md hover:bg-gray-50 transition-all">Tutorials</a>
<a href="about.html" class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 rounded-md hover:bg-gray-50 transition-all">About</a>
<a href="contact.html" class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 rounded-md hover:bg-gray-50 transition-all">Contact</a>
</div>
<button aria-label="Open navigation menu" aria-controls="mobile-menu" aria-expanded="false" class="md:hidden p-2 rounded-md text-gray-600 hover:bg-gray-100" onclick="toggleMobileMenu()">
<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
</button>
</div>
<div id="mobile-menu" class="md:hidden hidden mt-4 pb-2 border-t border-gray-100">
<div class="flex flex-col pt-3 space-y-1">
<a href="index.html" class="px-4 py-2 text-sm text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-lg transition-colors">Home</a>
<a href="index.html#all-tutorials" class="px-4 py-2 text-sm text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-lg transition-colors">Tutorials</a>
<a href="about.html" class="px-4 py-2 text-sm text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-lg transition-colors">About</a>
<a href="contact.html" class="px-4 py-2 text-sm text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-lg transition-colors">Contact</a>
</div>
</div>
</nav>
</header>

<!-- 404 Content -->
<main>
<div class="error-container">
  <svg class="error-icon" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="40" cy="40" r="36" stroke="#3b82f6" stroke-width="3" fill="#eff6ff"/>
    <path d="M28 32 L36 40 L28 48" stroke="#1e40af" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    <line x1="38" y1="48" x2="52" y2="48" stroke="#1e40af" stroke-width="3" stroke-linecap="round"/>
  </svg>
  <p class="error-code">404</p>
  <h1 class="text-2xl sm:text-3xl font-bold text-gray-900 mt-4 mb-3">Page not found</h1>
  <p class="text-gray-600 max-w-md mb-8 leading-relaxed">The page you are looking for may have been moved, renamed, or does not exist. You can explore our tutorials or return to the homepage.</p>
  <div class="flex flex-wrap items-center justify-center gap-4">
    <a href="index.html" class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-500/30 hover:bg-blue-700 transition-colors">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
      Back to Home
    </a>
    <a href="index.html#all-tutorials" class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-6 py-3 text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-50 transition-colors">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
      Browse Tutorials
    </a>
    <a href="contact.html" class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-6 py-3 text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-50 transition-colors">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
      Contact Us
    </a>
  </div>
</div>
</main>

<!-- Footer -->
<footer class="bg-gray-900 text-white mt-auto">
<div class="container mx-auto px-6 py-10">
  <div class="flex flex-col md:flex-row justify-between gap-8">
    <div>
      <a href="index.html" class="flex items-center space-x-3 mb-3">
        <div class="w-8 h-8 rounded-lg flex items-center justify-center" style="background-color:#123B5D">
          <svg class="w-5 h-5" viewBox="0 0 32 32"><path d="M6 10 L15 16 L25 7 M15 16 L25 25 M15 16 L7 25" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="6" cy="10" r="3.2" fill="#22D3EE" stroke="#fff" stroke-width="1.2"/><circle cx="25" cy="7" r="3.2" fill="#A78BFA" stroke="#fff" stroke-width="1.2"/><circle cx="15" cy="16" r="3.7" fill="#fff" stroke="#123B5D" stroke-width="1.2"/><circle cx="25" cy="25" r="3.2" fill="#FBBF24" stroke="#fff" stroke-width="1.2"/><circle cx="7" cy="25" r="3.2" fill="#34D399" stroke="#fff" stroke-width="1.2"/></svg>
        </div>
        <span class="text-lg font-bold">The Omics Hub</span>
      </a>
      <p class="text-sm text-gray-400 max-w-xs">Practical, hands-on tutorials for bioinformatics, HPC, and single-cell RNA-seq analysis.</p>
    </div>
    <div class="flex gap-16">
      <div>
        <h4 class="text-xs font-semibold text-gray-300 uppercase tracking-wide mb-3">Explore</h4>
        <ul class="space-y-2 text-sm text-gray-400"><li><a href="index.html" class="hover:text-white transition-colors">Home</a></li><li><a href="index.html#all-tutorials" class="hover:text-white transition-colors">Tutorials</a></li><li><a href="about.html" class="hover:text-white transition-colors">About</a></li><li><a href="contact.html" class="hover:text-white transition-colors">Contact</a></li></ul>
      </div>
      <div>
        <h4 class="text-xs font-semibold text-gray-300 uppercase tracking-wide mb-3">Policies</h4>
        <ul class="space-y-2 text-sm text-gray-400"><li><a href="pages/privacy.html" class="hover:text-white transition-colors">Privacy Policy</a></li><li><a href="pages/terms.html" class="hover:text-white transition-colors">Terms of Service</a></li><li><a href="pages/disclaimer.html" class="hover:text-white transition-colors">Disclaimer</a></li><li><a href="pages/cookie.html" class="hover:text-white transition-colors">Cookie Policy</a></li></ul>
      </div>
    </div>
  </div>
  <div class="border-t border-gray-800 mt-8 pt-6 text-center text-sm text-gray-500">&copy; 2026 The Omics Hub. All rights reserved.</div>
</div>
</footer>
</body>
</html>
'''

def create_404_page():
    """Create a branded 404.html page."""
    with open('404.html', 'w', encoding='utf-8') as f:
        f.write(PAGE_404)
    print('  + Created 404.html')


# ============================================================
# ISSUE 3: Expand About Page
# ============================================================

def expand_about_page():
    """Expand the About page with richer content."""
    with open('about.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the "Our Purpose" paragraph and replace with expanded content
    old_purpose = '''Our Purpose\n      </p>\n      <p class="text-gray-700 leading-relaxed">\n      Learning computational biology often requires bridging a significant gap between reading methodology papers and applying those methods to real sequencing data.'''

    new_purpose = '''Our Purpose\n      </p>\n      <p class="text-gray-700 leading-relaxed">\n      The Omics Hub was founded on a simple observation: most bioinformatics learners are biologists first and programmers second. The transition from the wet laboratory bench to the computational command line is one of the most challenging steps in a modern research career. University curricula often separate computational training from biological context, leaving graduate students and postdoctoral researchers to bridge the gap on their own. This platform exists to close that gap with structured, practical guidance that respects both the biology and the computation.\n      </p>\n      <p class="text-gray-700 leading-relaxed mt-3">\n      Learning computational biology often requires bridging a significant gap between reading methodology papers and applying those methods to real sequencing data.'''

    if old_purpose in content:
        content = content.replace(old_purpose, new_purpose)
        print('  + Expanded "Our Purpose" section')

    # Find the author paragraph and expand it
    old_author = '''About the Author\n      </p>\n      <p class="text-gray-700 leading-relaxed">\n      The Omics Hub is created and maintained by Nasir Mahmood Abbasi, PhD, a Bioinformatician w'''

    # We need to see what follows - let me use a more flexible approach
    # Find and expand after "With a deep technical background" paragraph
    old_bg = '''With a deep technical background in analyzing complex biological datasets'''
    new_bg_prefix = '''Nasir completed his doctoral research at the Bordeaux Institute of Oncology (BRIC, INSERM U1312) in Bordeaux, France, where he specialized in the single-cell transcriptomic landscape of Sezary syndrome, a rare and aggressive cutaneous T-cell lymphoma. His work combined high-dimensional flow cytometry, 10x Genomics Chromium scRNA-seq, and TCR repertoire analysis to dissect the cellular heterogeneity of the tumour microenvironment. This research culminated in peer-reviewed publications and a comprehensive bioinformatics pipeline that has been adopted by his laboratory for ongoing clinical studies.\n      </p>\n      <p class="text-gray-700 leading-relaxed mt-3">\n      Beyond his doctoral work, Nasir has contributed to multiple collaborative projects spanning metagenomics, bulk RNA-seq differential expression, and whole-exome sequencing variant calling. His teaching philosophy is rooted in the belief that every analytical choice must be explained and justified, not simply prescribed as a recipe. Each tutorial on The Omics Hub reflects this approach, presenting not only the code but the reasoning behind parameter selections, quality thresholds, and algorithmic trade-offs.\n      </p>\n      <p class="text-gray-700 leading-relaxed mt-3">\n      With a deep technical background in analyzing complex biological datasets'''

    if old_bg in content:
        content = content.replace(old_bg, new_bg_prefix, 1)
        print('  + Expanded author biography section')

    # Add a "Teaching Philosophy" section before "Editorial Standards"
    old_editorial = '''Editorial Standards &amp; Updates'''
    new_editorial = '''Teaching Philosophy\n      </p>\n      <p class="text-gray-700 leading-relaxed">\n      Every tutorial on this platform follows a deliberate pedagogical structure. Each begins with clearly stated learning objectives and prerequisites, ensuring that learners can self-assess their readiness. The core content presents concepts in a logical progression, moving from foundational principles to practical application. Code blocks are always preceded by explanatory prose that contextualizes what the code does and why each parameter was chosen. Finally, each tutorial closes with a knowledge check section that reinforces retention and encourages independent problem-solving.\n      </p>\n      <p class="text-gray-700 leading-relaxed mt-3">\n      This structure was designed specifically for researchers who are simultaneously managing experiments, writing manuscripts, and learning computational methods. The goal is to minimize cognitive overhead and maximize the transfer of knowledge to the learner's own data and research questions.\n      </p>\n    </div>\n    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 mb-8">\n      <p class="text-xl font-semibold text-gray-900 mb-4">\n      Editorial Standards &amp; Updates'''

    if old_editorial in content:
        content = content.replace(old_editorial, new_editorial, 1)
        print('  + Added "Teaching Philosophy" section')

    with open('about.html', 'w', encoding='utf-8') as f:
        f.write(content)

    # Verify new word count
    prose = ' '.join(re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL))
    prose = re.sub(r'<[^>]+>', ' ', prose)
    words = len(prose.split())
    print(f'  About page prose words: {words}')


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print('=' * 60)
    print('FIX 1: Injecting cookie consent banner into all pages')
    print('=' * 60)
    fix_cookie_consent()

    print()
    print('=' * 60)
    print('FIX 2: Creating custom 404 page')
    print('=' * 60)
    create_404_page()

    print()
    print('=' * 60)
    print('FIX 3: Expanding About page')
    print('=' * 60)
    expand_about_page()

    print()
    print('All 3 issues fixed!')
