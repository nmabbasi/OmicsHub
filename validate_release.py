#!/usr/bin/env python3
"""Release QA for The Omics Hub static build, including non-image readiness standards."""
from __future__ import annotations

import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
ERRORS: list[str] = []
WARNINGS: list[str] = []

STANDALONE = {
    "index.html": ("https://theomicshub.com/", True),
    "start-here.html": ("https://theomicshub.com/start-here.html", True),
    "services.html": ("https://theomicshub.com/services.html", True),
    "about.html": ("https://theomicshub.com/about.html", True),
    "contact.html": ("https://theomicshub.com/contact.html", True),
    "success.html": ("https://theomicshub.com/success.html", False),
    "pages/privacy.html": ("https://theomicshub.com/pages/privacy.html", True),
    "pages/terms.html": ("https://theomicshub.com/pages/terms.html", True),
    "pages/disclaimer.html": ("https://theomicshub.com/pages/disclaimer.html", True),
    "pages/cookie.html": ("https://theomicshub.com/pages/cookie.html", True),
}


def fail(message: str) -> None:
    ERRORS.append(message)


def warn(message: str) -> None:
    WARNINGS.append(message)


def local_target_exists(source: Path, href: str) -> bool:
    if href.startswith(("http://", "https://", "mailto:", "#", "javascript:", "data:")):
        return True
    clean = href.split("#", 1)[0].split("?", 1)[0]
    if not clean:
        return True
    return (source.parent / clean).exists()


def canonical_values(soup: BeautifulSoup) -> list[str]:
    return [tag.get("href", "") for tag in soup.find_all("link", rel="canonical")]


html_files = [path for path in (sorted(ROOT.glob("*.html")) + sorted((ROOT / "pages").glob("*.html"))) if path.name != "404.html"]
tutorial_paths = [path for path in ROOT.glob("*.html") if path.name not in {"index.html", "about.html", "contact.html", "services.html", "start-here.html", "success.html", "404.html"}]

for path in html_files:
    text = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(text, "html.parser")
    relative = path.relative_to(ROOT).as_posix()

    if "Coming Soon" in text or "currently in active development" in text:
        fail(f"{relative}: placeholder remains")
    if "The Omics Hub" not in (soup.title.get_text(" ", strip=True) if soup.title else ""):
        fail(f"{relative}: site brand missing from title")
    if not soup.find("meta", attrs={"name": "description"}):
        fail(f"{relative}: missing meta description")
    if not soup.html or soup.html.get("lang") != "en":
        fail(f"{relative}: html language is not en")

    for tag in soup.find_all(["a", "img", "link", "script"]):
        attr = "href" if tag.name in {"a", "link"} else "src"
        value = tag.get(attr)
        if value and not local_target_exists(path, value):
            fail(f"{relative}: missing local resource {value}")
        if value and value.endswith(".md"):
            fail(f"{relative}: stale markdown link {value}")

    if 'aria-controls="mobile-menu"' not in text or 'aria-expanded="false"' not in text:
        fail(f"{relative}: mobile navigation ARIA contract missing")
    if 'function toggleMobileMenu()' not in text:
        fail(f"{relative}: mobile navigation toggle function missing")
    if 'id="navigation-accessibility"' not in text:
        fail(f"{relative}: Legal menu accessibility script missing")
    if 'id="legal-menu-button"' in text and 'aria-haspopup="true"' not in text:
        fail(f"{relative}: Legal menu accessibility contract missing")

    if relative in STANDALONE:
        expected_canonical, should_index = STANDALONE[relative]
        canonicals = canonical_values(soup)
        if canonicals != [expected_canonical]:
            fail(f"{relative}: canonical mismatch {canonicals}")
        robots = soup.find("meta", attrs={"name": "robots"})
        robots_value = robots.get("content", "") if robots else ""
        if should_index and "index" not in robots_value:
            fail(f"{relative}: expected indexable robots meta")
        if not should_index and "noindex" not in robots_value:
            fail(f"{relative}: success page must be noindex")
        if not soup.find("script", attrs={"type": "application/ld+json"}):
            fail(f"{relative}: missing standalone structured data")

for path in tutorial_paths:
    text = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(text, "html.parser")
    expected_canonical = f"https://theomicshub.com/{path.stem}.html"
    canonicals = canonical_values(soup)
    if canonicals != [expected_canonical]:
        fail(f"{path.name}: canonical mismatch {canonicals}")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if title == "The Omics Hub" or not title.endswith("| The Omics Hub"):
        fail(f"{path.name}: generic or malformed document title {title!r}")
    if len(soup.find_all("h1")) != 1:
        fail(f"{path.name}: expected exactly one H1, found {len(soup.find_all('h1'))}")
    if text.count('application/ld+json') != 1:
        fail(f"{path.name}: expected exactly one JSON-LD block")
    if '"@type": "Article"' not in text or '"Nasir Mahmood Abbasi, PhD"' not in text:
        fail(f"{path.name}: incomplete Article schema")
    visible_text = soup.get_text(" ", strip=True)
    if "Learning Objectives" not in visible_text or "Prerequisites" not in visible_text:
        fail(f"{path.name}: missing learner objectives or prerequisites")
    if "Knowledge Check & Assessment" not in visible_text or "Concept Verification" not in visible_text or "Troubleshooting" not in visible_text:
        fail(f"{path.name}: incomplete knowledge check")
    if "Practical Execution" not in visible_text and "Practical Exercise" not in visible_text:
        fail(f"{path.name}: missing practical assessment")
    for generic in ["Master the core concepts and practical commands of this topic.", "A reproducible workflow and a clear understanding of the methodology."]:
        if generic in text:
            fail(f"{path.name}: generic learning scaffold remains")
    nav_line = next((line for line in text.splitlines() if 'id="nav-desktop-tutorials"' in line), "")
    if 'aria-current="page"' not in nav_line:
        fail(f"{path.name}: Tutorials desktop tab not active")
        
    home_line = next((line for line in text.splitlines() if 'id="nav-desktop-home"' in line), "")
    if 'aria-current="page"' in home_line:
        fail(f"{path.name}: Home incorrectly active")

# Sitemap should index strategic pages and tutorials, but never the transactional success page.
sitemap_root = ET.fromstring((ROOT / "sitemap.xml").read_text(encoding="utf-8"))
sitemap_urls = {node.text for node in sitemap_root.findall("{*}url/{*}loc") if node.text}
for relative, (url, should_index) in STANDALONE.items():
    if should_index and url not in sitemap_urls:
        fail(f"sitemap: missing indexable page {relative}")
    if not should_index and url in sitemap_urls:
        fail(f"sitemap: non-indexable page included {relative}")
for path in tutorial_paths:
    expected = f"https://theomicshub.com/{path.name}"
    if expected not in sitemap_urls:
        fail(f"sitemap: missing tutorial {path.name}")

# Form and trust controls.
services = (ROOT / "services.html").read_text(encoding="utf-8")
contact = (ROOT / "contact.html").read_text(encoding="utf-8")
privacy = (ROOT / "pages" / "privacy.html").read_text(encoding="utf-8")
about = (ROOT / "about.html").read_text(encoding="utf-8")
success = (ROOT / "success.html").read_text(encoding="utf-8")
if 'name="newsletter_consent" required' not in services or 'name="_honey"' not in services:
    fail("services: newsletter consent or honeypot missing")
if 'name="_honey"' not in contact or 'name="consent" required' not in contact:
    fail("contact: privacy or anti-spam controls missing")
if "Information You Submit" not in privacy or "FormSubmit" not in privacy:
    fail("privacy: submitted-form processing disclosure missing")
if "Editorial Standards &amp; Updates" not in about or "Professional Transparency" not in about:
    fail("about: trust and editorial sections missing")
if 'name="robots" content="noindex, follow"' not in success:
    fail("success: noindex directive missing")
if not (ROOT / "files" / "scRNA_seq_Marker_Cheat_Sheet.pdf").exists():
    fail("lead magnet PDF missing")

# Source lessons should remain clean and structured.
for lesson in (ROOT / "lessons").glob("*.md"):
    source = lesson.read_text(encoding="utf-8", errors="ignore")
    if "Coming Soon" in source or ".md)" in source:
        fail(f"{lesson.name}: source placeholder or stale link")
    # Code-tab panels use HTML <pre><code> blocks, whose language comments can begin
    # with '# '. Remove those blocks before testing actual Markdown headings.
    source_without_html_code = re.sub(r"<pre\b[^>]*>.*?</pre>", "", source, flags=re.IGNORECASE | re.DOTALL)
    in_fence = False
    for line in source_without_html_code.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if not in_fence and re.match(r"^#\s+", line):
            fail(f"{lesson.name}: body Markdown H1 remains")
            break

print(json.dumps({
    "html_pages": len(html_files),
    "tutorial_pages": len(tutorial_paths),
    "sitemap_urls": len(sitemap_urls),
    "errors": ERRORS,
    "warnings": WARNINGS,
}, indent=2))
raise SystemExit(1 if ERRORS else 0)
