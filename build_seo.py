#!/usr/bin/env python3
"""Build SEO-ready tutorial pages from lesson Markdown and the shared homepage shell."""
from __future__ import annotations

import html
import json
import os
import re
from pathlib import Path

import markdown

from inject_html_cards import tutorials

ROOT = Path(__file__).resolve().parent
LESSONS_DIR = ROOT / "lessons"
SITE_URL = "https://theomicshub.com"
SITE_NAME = "The Omics Hub"
AUTHOR = "Nasir Mahmood Abbasi, PhD"


def replace_meta_tag(head: str, attribute: str, name: str, value: str) -> str:
    """Update a meta tag regardless of whether its attributes were serialized in one order or another."""
    pattern = rf'(<meta\b(?=[^>]*\b{attribute}="{re.escape(name)}")[^>]*\bcontent=")[^"]*("[^>]*>)'
    replacement = rf'\g<1>{html.escape(value, quote=True)}\g<2>'
    updated, count = re.subn(pattern, replacement, head)
    if count:
        return updated
    return head.replace("</head>", f'  <meta {attribute}="{name}" content="{html.escape(value, quote=True)}"/>\n</head>')


def parse_frontmatter(md_content: str, tutorial_id: str) -> tuple[dict[str, str], str]:
    defaults = {"title": tutorial_id.replace("-", " ").title(), "excerpt": "", "author": AUTHOR}
    match = re.search(r"^---\s*\n(.*?)\n---\s*\n", md_content, re.DOTALL)
    if not match:
        return defaults, md_content
    frontmatter = match.group(1)
    for key in ("title", "excerpt", "author"):
        value = re.search(rf'{key}:\s*"([^"]+)"', frontmatter)
        if value:
            defaults[key] = value.group(1).strip()
    return defaults, md_content[match.end():]


def make_nav_card(tutorial: dict[str, str], direction: str, label: str) -> str:
    is_next = direction == "next"
    alignment = "text-right" if is_next else "text-left"
    gradient = "bg-gradient-to-l" if is_next else "bg-gradient-to-r"
    icon_path = "M9 5l7 7-7 7" if is_next else "M15 19l-7-7 7-7"
    inner = f'''
            <div class="absolute inset-0 {gradient} from-blue-50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div class="relative z-10 flex items-center {'justify-end ' if is_next else ''}gap-4">
                {'' if is_next else '<div class="w-12 h-12 flex-shrink-0 rounded-full bg-gray-50 flex items-center justify-center group-hover:bg-blue-600 transition-colors duration-300"><svg class="w-6 h-6 text-gray-400 group-hover:text-white transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="' + icon_path + '"></path></svg></div>'}
                <div class="{alignment}">
                    <span class="block text-xs font-bold tracking-widest text-gray-400 uppercase mb-1">{html.escape(label)}</span>
                    <span class="block text-gray-900 font-bold group-hover:text-blue-700 transition-colors line-clamp-2 leading-snug">{html.escape(tutorial['title'])}</span>
                </div>
                {('<div class="w-12 h-12 flex-shrink-0 rounded-full bg-gray-50 flex items-center justify-center group-hover:bg-blue-600 transition-colors duration-300"><svg class="w-6 h-6 text-gray-400 group-hover:text-white transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="' + icon_path + '"></path></svg></div>') if is_next else ''}
            </div>'''
    return f'''<a href="{html.escape(tutorial['id'])}.html" class="group relative flex flex-col justify-center p-6 bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden {alignment}">
{inner}
        </a>'''


def terminal_nav_card() -> str:
    return '''<a href="start-here.html" class="group relative flex flex-col justify-center p-6 bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden text-right">
            <div class="absolute inset-0 bg-gradient-to-l from-blue-50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div class="relative z-10 flex items-center justify-end gap-4">
                <div class="text-right">
                    <span class="block text-xs font-bold tracking-widest text-gray-400 uppercase mb-1">Explore another lane</span>
                    <span class="block text-gray-900 font-bold group-hover:text-blue-700 transition-colors leading-snug">Return to the Academy Pathway</span>
                </div>
                <div class="w-12 h-12 flex-shrink-0 rounded-full bg-gray-50 flex items-center justify-center group-hover:bg-blue-600 transition-colors duration-300">
                    <svg class="w-6 h-6 text-gray-400 group-hover:text-white transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                </div>
            </div>
        </a>'''


def lesson_navigation(current_idx: int, tutorial: dict[str, str]) -> str:
    prev_html = ""
    next_html = ""
    if current_idx > 0:
        previous = tutorials[current_idx - 1]
        label = "Previous Stage" if previous["category"] != tutorial["category"] else "Previous Lesson"
        prev_html = make_nav_card(previous, "previous", label)
    if current_idx < len(tutorials) - 1:
        following = tutorials[current_idx + 1]
        label = "Next Stage" if following["category"] != tutorial["category"] else "Next Lesson"
        next_html = make_nav_card(following, "next", label)
    else:
        next_html = terminal_nav_card()
    if not prev_html:
        prev_html = '''<a href="start-here.html" class="group relative flex flex-col justify-center p-6 bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden text-left">
            <div class="relative z-10 flex items-center gap-4"><div class="w-12 h-12 flex-shrink-0 rounded-full bg-gray-50 flex items-center justify-center"><svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg></div><div><span class="block text-xs font-bold tracking-widest text-gray-400 uppercase mb-1">Academy orientation</span><span class="block text-gray-900 font-bold group-hover:text-blue-700 transition-colors leading-snug">Start with the Academy Pathway</span></div></div>
        </a>'''
    return f'''
    <section class="mt-16 pt-10 border-t border-gray-100" aria-label="Course sequence">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
            <h2 class="text-2xl font-black text-gray-900 tracking-tight">Continue Learning</h2>
            <span class="inline-block bg-blue-50 text-blue-700 text-xs font-bold px-3 py-1.5 rounded-full uppercase tracking-wider">Course Sequence</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {prev_html}
            {next_html}
        </div>
    </section>'''


def tutorial_head(base_head: str, tutorial: dict[str, str], metadata: dict[str, str]) -> str:
    title = metadata["title"]
    excerpt = metadata["excerpt"] or f"Step-by-step bioinformatics tutorial: {title}."
    canonical = f"{SITE_URL}/{tutorial['id']}.html"
    image_url = f"{SITE_URL}/{tutorial['image']}" if tutorial.get("image") else f"{SITE_URL}/images/favicon.svg"
    doc_title = f"{title} | {SITE_NAME}"

    head = re.sub(r'\s*<script type="application/ld\+json">.*?</script>\s*', '\n', base_head, flags=re.DOTALL)
    head = re.sub(r"<title>.*?</title>", f"<title>{html.escape(doc_title)}</title>", head, count=1, flags=re.DOTALL)
    head = replace_meta_tag(head, "name", "description", excerpt)
    head = replace_meta_tag(head, "property", "og:title", doc_title)
    head = replace_meta_tag(head, "property", "og:description", excerpt)
    head = replace_meta_tag(head, "property", "og:url", canonical)
    head = replace_meta_tag(head, "property", "og:image", image_url)
    head = replace_meta_tag(head, "name", "twitter:title", doc_title)
    head = replace_meta_tag(head, "name", "twitter:description", excerpt)
    head = replace_meta_tag(head, "name", "twitter:image", image_url)
    head = re.sub(r"\s*<link rel=\"canonical\"[^>]*>\s*", "\n", head)

    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": excerpt,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "image": image_url,
        "author": {"@type": "Person", "name": metadata.get("author") or AUTHOR, "url": f"{SITE_URL}/about.html"},
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL, "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/images/favicon.svg"}},
        "datePublished": tutorial["date"],
        "dateModified": tutorial["date"],
    }
    injection = f'  <link rel="canonical" href="{canonical}"/>\n  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>\n'
    return head.replace("</head>", injection + "</head>")


def sitemap_entry(url: str, priority: str, changefreq: str = "monthly") -> str:
    return f"  <url>\n    <loc>{url}</loc>\n    <changefreq>{changefreq}</changefreq>\n    <priority>{priority}</priority>\n  </url>\n"


def main() -> None:
    base_html = (ROOT / "index.html").read_text(encoding="utf-8")
    # Analytics is loaded only through analytics.js after consent. Keeping a second
    # inline GA4 configuration would duplicate pageviews on generated tutorial pages.
    base_html, inline_ga4_blocks = re.subn(
        r'\s*<!-- Google Analytics -->\s*<script async src="https://www\.googletagmanager\.com/gtag/js\?id=G-MTD30PYWWH"></script>\s*<script>\s*window\.dataLayer = window\.dataLayer \|\| \[\];\s*function gtag\(\)\{dataLayer\.push\(arguments\);\}\s*gtag\("js", new Date\(\)\);\s*gtag\("config", "G-MTD30PYWWH"\);\s*</script>',
        "\n",
        base_html,
        flags=re.DOTALL,
    )
    if inline_ga4_blocks > 1:
        raise RuntimeError("Expected at most one inline GA4 block in index.html")
    (ROOT / "index.html").write_text(base_html, encoding="utf-8")
    header_split = base_html.split('<main class="min-h-screen">', 1)
    if len(header_split) != 2:
        raise RuntimeError("Could not locate shared main wrapper in index.html")
    footer_split = header_split[1].split("</main>", 1)
    if len(footer_split) != 2:
        raise RuntimeError("Could not locate shared footer boundary in index.html")
    base_head = header_split[0]
    footer_html = "\n</main>" + footer_split[1]
    tutorial_footer_html = re.sub(
        r'\s*<div id="homepage-visitor-counter"[^>]*>.*?</div>\s*',
        '\n',
        footer_html,
        flags=re.DOTALL,
    )

    # Generated tutorials must activate Tutorials, not Home.
    base_head = base_head.replace(
        'id="nav-desktop-home" aria-current="page" class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 rounded-md hover:bg-gray-50 transition-all"',
        'id="nav-desktop-home" class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 rounded-md hover:bg-gray-50 transition-all"',
    )
    base_head = base_head.replace(
        'id="nav-mobile-home" aria-current="page" class="px-4 py-2 text-sm text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-lg transition-colors"',
        'id="nav-mobile-home" class="px-4 py-2 text-sm text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-lg transition-colors"',
    )
    base_head = base_head.replace(
        'id="nav-desktop-tutorials" class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 rounded-md hover:bg-gray-50 transition-all cursor-pointer"',
        'id="nav-desktop-tutorials" aria-current="page" class="px-4 py-2 text-sm font-semibold bg-blue-600 text-white rounded-md shadow-sm transition-all cursor-pointer"',
    )
    base_head = base_head.replace(
        'id="nav-mobile-tutorials" class="px-4 py-2 text-sm text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-lg transition-colors cursor-pointer"',
        'id="nav-mobile-tutorials" aria-current="page" class="px-4 py-2 text-sm font-semibold text-blue-600 bg-blue-50 rounded-lg transition-colors cursor-pointer"',
    )

    tutorial_urls: list[str] = []
    for current_idx, tutorial in enumerate(tutorials):
        lesson_path = LESSONS_DIR / f"{tutorial['id']}.md"
        if not lesson_path.exists():
            continue
        md_content = lesson_path.read_text(encoding="utf-8")
        metadata, body_md = parse_frontmatter(md_content, tutorial["id"])
        title = metadata["title"]
        rendered_html = markdown.markdown(body_md, extensions=["fenced_code", "tables"])
        author = metadata.get("author") or AUTHOR
        initials = "".join(part[0] for part in author.split() if part and part[0].isalpha()).upper()[:2] or "OH"
        image = tutorial.get("image", "")
        image_html = f'''<div class="mb-12 rounded-2xl overflow-hidden shadow-lg border border-gray-100">\n<img src="{html.escape(image)}" alt="{html.escape(title)}" class="w-full h-auto object-cover aspect-video">\n</div>''' if image else ""
        static_content = f'''
            <section class="mb-12">
                <div class="flex items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>{html.escape(tutorial['category'])}</span><span>•</span><span>{html.escape(tutorial['date'])}</span></div>
                <h1 class="text-4xl md:text-5xl font-black text-gray-900 mb-6 leading-tight">{html.escape(title)}</h1>
                <div class="flex items-center gap-4"><div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold text-lg">{html.escape(initials)}</div><div><p class="font-bold text-gray-900">{html.escape(author)}</p><p class="text-sm text-gray-500">Bioinformatics Educator</p></div></div>
            </section>
            {image_html}
            <article class="prose prose-blue prose-lg max-w-none" aria-labelledby="tutorial-title">{rendered_html}</article>
            {lesson_navigation(current_idx, tutorial)}
        '''
        page_content = f'''
    <div class="page-content" id="tutorial-page">
        <div class="container mx-auto px-4 py-8"><div class="max-w-4xl mx-auto"><div id="tutorial-content">{static_content}</div></div></div>
    </div>
    <script>window.STATIC_RENDERED = true; window.PRELOADED_TUTORIAL_ID = "{html.escape(tutorial['id'])}";</script>
        '''
        final_html = tutorial_head(base_head, tutorial, metadata) + '<main class="min-h-screen">' + page_content + tutorial_footer_html
        (ROOT / f"{tutorial['id']}.html").write_text(final_html, encoding="utf-8")
        tutorial_urls.append(f"{SITE_URL}/{tutorial['id']}.html")
        print(f"Generated {tutorial['id']}.html")

    # The visitor counter is a homepage-only social-proof element. It must not appear
    # in shared footers, where it can distract learners and count secondary page loads.
    visitor_counter_pattern = r'\s*<div id="homepage-visitor-counter"[^>]*>.*?</div>\s*'
    for page_path in ROOT.rglob("*.html"):
        if page_path == ROOT / "index.html":
            continue
        page_html = page_path.read_text(encoding="utf-8")
        without_counter = re.sub(visitor_counter_pattern, "\n", page_html, flags=re.DOTALL)
        if page_html != without_counter:
            page_path.write_text(without_counter, encoding="utf-8")

    standalone = [
        (SITE_URL + "/", "1.0", "weekly"),
        (SITE_URL + "/start-here.html", "0.9", "weekly"),
        (SITE_URL + "/services.html", "0.7", "monthly"),
        (SITE_URL + "/about.html", "0.6", "monthly"),
        (SITE_URL + "/contact.html", "0.6", "monthly"),
        (SITE_URL + "/pages/privacy.html", "0.3", "yearly"),
        (SITE_URL + "/pages/terms.html", "0.3", "yearly"),
        (SITE_URL + "/pages/disclaimer.html", "0.3", "yearly"),
        (SITE_URL + "/pages/cookie.html", "0.3", "yearly"),
    ]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n']
    sitemap.extend(sitemap_entry(url, priority, frequency) for url, priority, frequency in standalone)
    sitemap.extend(sitemap_entry(url, "0.8") for url in tutorial_urls)
    sitemap.append("</urlset>\n")
    (ROOT / "sitemap.xml").write_text("".join(sitemap), encoding="utf-8")
    print(f"Generated sitemap.xml with {len(standalone) + len(tutorial_urls)} URLs")


if __name__ == "__main__":
    main()
