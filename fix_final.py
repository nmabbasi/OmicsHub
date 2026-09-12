import re

# --- FIX INJECT HTML CARDS ---
with open('inject_html_cards.py', 'r', encoding='utf-8') as f:
    inject_script = f.read()

# Fix total count
inject_script = inject_script.replace('{len(tutorials)}', '{len(tutorials) + 10}')

# Append AI category to the loops
ai_cat_code = """
# Manually inject AI category
cat_html += '<button class="sidebar-category w-full text-left px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-colors" data-category="AI-Driven Research & Agentic Bioinformatics" data-category-tone="ai-driven" onclick="filterTutorials(\\\'AI-Driven Research & Agentic Bioinformatics\\\')">AI-Driven Research & Agentic Bioinformatics<span class="category-count" aria-label="10 tutorials">10</span></button>\\n'
filter_buttons_html += '<button class="category-btn px-4 py-2 rounded-full text-sm font-medium transition-colors bg-gray-200 text-gray-700 hover:bg-gray-300" data-category="AI-Driven Research & Agentic Bioinformatics" data-category-tone="ai-driven" onclick="filterTutorialsOnly(\\\'AI-Driven Research & Agentic Bioinformatics\\\')">AI-Driven Research & Agentic Bioinformatics<span class="category-count" aria-label="10 tutorials">10</span></button>\\n'

# Recent posts
"""
inject_script = inject_script.replace('# Recent posts', ai_cat_code)

with open('inject_html_cards.py', 'w', encoding='utf-8') as f:
    f.write(inject_script)


# --- FIX BUILD SEO ---
with open('build_seo.py', 'r', encoding='utf-8') as f:
    seo_script = f.read()

new_sitemap_logic = """
    import glob
    html_files = glob.glob("*.html")
    excluded = ["404.html", "success.html", "index.html", "start-here.html", "services.html", "about.html", "contact.html"]
    tutorial_files = [f for f in html_files if f not in excluded and not f.startswith("pages/")]
    sitemap.extend(sitemap_entry(SITE_URL + "/" + tut, "0.8") for tut in tutorial_files)
"""

seo_script = re.sub(
    r'sitemap\.extend\(sitemap_entry\(url, "0\.8"\) for url in tutorial_urls\)',
    new_sitemap_logic.strip(),
    seo_script
)

with open('build_seo.py', 'w', encoding='utf-8') as f:
    f.write(seo_script)

print("Fixed inject_html_cards.py and build_seo.py")
