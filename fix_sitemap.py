import glob

SITE_URL = "https://theomicshub.com"

standalone = {
    "/": ("1.0", "weekly"),
    "/start-here.html": ("0.9", "weekly"),
    "/services.html": ("0.7", "monthly"),
    "/about.html": ("0.6", "monthly"),
    "/contact.html": ("0.6", "monthly"),
    "/pages/privacy.html": ("0.3", "yearly"),
    "/pages/terms.html": ("0.3", "yearly"),
    "/pages/disclaimer.html": ("0.3", "yearly"),
    "/pages/cookie.html": ("0.3", "yearly"),
}

html_files = glob.glob("*.html")
excluded = ["404.html", "success.html", "index.html", "start-here.html", "services.html", "about.html", "contact.html"]

tutorial_files = [f for f in html_files if f not in excluded]

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    
    for url, (priority, frequency) in standalone.items():
        f.write('  <url>\n')
        f.write(f'    <loc>{SITE_URL}{url}</loc>\n')
        f.write(f'    <changefreq>{frequency}</changefreq>\n')
        f.write(f'    <priority>{priority}</priority>\n')
        f.write('  </url>\n')
        
    for tut in tutorial_files:
        f.write('  <url>\n')
        f.write(f'    <loc>{SITE_URL}/{tut}</loc>\n')
        f.write('    <changefreq>monthly</changefreq>\n')
        f.write('    <priority>0.8</priority>\n')
        f.write('  </url>\n')
        
    f.write('</urlset>\n')

print(f"Generated sitemap.xml with {len(standalone) + len(tutorial_files)} URLs")
