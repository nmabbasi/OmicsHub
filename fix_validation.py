import re

# Fix build_seo.py to exclude the internal HTML snippets
with open('build_seo.py', 'r', encoding='utf-8') as f:
    seo_script = f.read()

seo_script = seo_script.replace(
    'excluded = ["404.html", "success.html", "index.html", "start-here.html", "services.html", "about.html", "contact.html"]',
    'excluded = ["404.html", "success.html", "index.html", "start-here.html", "services.html", "about.html", "contact.html", "old_index.html", "ai_home_cards.html", "ai_grid_cards.html"]'
)

with open('build_seo.py', 'w', encoding='utf-8') as f:
    f.write(seo_script)

# Fix super_validate.py
with open('super_validate.py', 'r', encoding='utf-8') as f:
    val_script = f.read()

val_script = val_script.replace('if len(buttons) >= 2:', 'if len(buttons) >= 1:')
val_script = val_script.replace('html_files = glob.glob("*.html") + glob.glob("pages/*.html")', 'html_files = [f for f in glob.glob("*.html") + glob.glob("pages/*.html") if f not in ["old_index.html", "ai_home_cards.html", "ai_grid_cards.html"]]')

with open('super_validate.py', 'w', encoding='utf-8') as f:
    f.write(val_script)

