import re
import glob
import os

print("=" * 70)
print("RESPONSIVE DESIGN AUDIT")
print("=" * 70)

# Check all main pages + a sample of tutorials
main_pages = ['index.html', 'tutorials.html', 'about.html', 'services.html', 
              'contact.html', 'start-here.html']
tutorial_pages = ['tutorials/scrna-seq-basics.html', 'tutorials/conda-mamba-part1.html',
                  'tutorials/metatranscriptomics-functional-pathways.html',
                  'tutorials/ai-coding-cursor-aider.html']
policy_pages = ['pages/privacy.html', 'pages/cookie.html', 'pages/terms.html']
all_pages = main_pages + tutorial_pages + policy_pages

issues = []

for page in all_pages:
    if not os.path.exists(page):
        issues.append(f"[MISSING] {page} does not exist")
        continue
    
    with open(page, 'r') as f:
        content = f.read()
    
    basename = os.path.basename(page)
    page_issues = []
    
    # 1. Viewport meta tag
    if 'viewport' not in content:
        page_issues.append("Missing viewport meta tag")
    elif 'width=device-width' not in content:
        page_issues.append("Viewport missing width=device-width")
    
    # 2. Check for hardcoded pixel widths that could break mobile
    # Look for style="width:XXXpx" that aren't on small elements
    hardcoded_widths = re.findall(r'style="[^"]*width:\s*(\d+)px', content)
    large_widths = [w for w in hardcoded_widths if int(w) > 500]
    if large_widths:
        page_issues.append(f"Hardcoded widths > 500px: {large_widths}")
    
    # 3. Check for horizontal overflow risks - elements with fixed widths
    fixed_width_elements = re.findall(r'class="[^"]*w-\[(\d+)px\][^"]*"', content)
    large_fixed = [w for w in fixed_width_elements if int(w) > 400]
    if large_fixed:
        page_issues.append(f"Fixed width classes > 400px: {large_fixed}")
    
    # 4. Mobile navigation
    if '<header' in content:
        has_mobile_menu = 'mobile-menu' in content or 'md:hidden' in content
        if not has_mobile_menu:
            page_issues.append("No mobile menu detected")
    
    # 5. Check responsive grid classes
    has_grid = 'grid' in content
    has_responsive_grid = re.search(r'(md:|lg:|sm:)grid-cols', content)
    if has_grid and not has_responsive_grid:
        # Check if it's a simple grid that might break
        grid_cols = re.findall(r'grid-cols-(\d+)', content)
        if any(int(c) > 2 for c in grid_cols):
            page_issues.append(f"Grid with {max(grid_cols)} cols but no responsive breakpoints")
    
    # 6. Check for overflow-x hidden on body/main (prevents horizontal scroll)
    # This is actually set via CSS usually
    
    # 7. Check text sizes - any text that's too large on mobile
    huge_text = re.findall(r'text-(6xl|7xl|8xl|9xl)', content)
    if huge_text:
        # Check if they have responsive variants
        for size in set(huge_text):
            pattern = f'(sm:|md:|lg:)text-{size}'
            if re.search(pattern, content):
                pass  # Good, it's responsive
            else:
                # Check if the class is preceded by a responsive smaller size
                context_matches = re.findall(r'class="[^"]*text-' + size + r'[^"]*"', content)
                for cm in context_matches:
                    if 'md:text-' in cm or 'lg:text-' in cm:
                        pass  # It's used as a responsive variant itself
                    elif 'text-4xl' in cm or 'text-3xl' in cm or 'text-2xl' in cm:
                        pass  # Has a smaller base
                    else:
                        page_issues.append(f"Very large text ({size}) without responsive sizing")
    
    # 8. Check images have responsive classes
    imgs = re.findall(r'<img[^>]+>', content)
    for img in imgs:
        if 'w-full' not in img and 'max-w-' not in img:
            src = re.search(r'src="([^"]+)"', img)
            src_val = src.group(1) if src else 'unknown'
            # Skip tiny icons/logos
            if 'w-6' not in img and 'w-7' not in img and 'w-10' not in img and 'w-4' not in img and 'w-12' not in img and 'w-8' not in img:
                page_issues.append(f"Image without w-full: {src_val[:50]}")
    
    # 9. Check tables for overflow handling
    tables = content.count('<table')
    if tables > 0:
        if 'overflow-x' not in content and 'overflow-auto' not in content:
            page_issues.append(f"{tables} table(s) without overflow scroll wrapper")
    
    # 10. Check for max-width container
    if 'container' not in content and 'max-w-' not in content:
        page_issues.append("No max-width container - content may stretch too wide on large monitors")
    
    if page_issues:
        print(f"\n⚠ {page}:")
        for pi in page_issues:
            print(f"  - {pi}")
    else:
        print(f"✅ {page}")

# Additional checks
print("\n### ADDITIONAL RESPONSIVE CHECKS ###")

# Check style.css for responsive rules
if os.path.exists('style.css'):
    with open('style.css', 'r') as f:
        css = f.read()
    
    media_queries = re.findall(r'@media[^{]+', css)
    print(f"\nstyle.css media queries: {len(media_queries)}")
    for mq in media_queries[:10]:
        print(f"  {mq.strip()}")
    
    # Check for overflow-x hidden
    if 'overflow-x' in css:
        print("  ✅ Has overflow-x control")
    else:
        print("  ⚠ No overflow-x: hidden found in CSS")

# Check tailwind for responsive utilities
print("\n### RESPONSIVE GRID PATTERNS USED ###")
for page in main_pages:
    if os.path.exists(page):
        with open(page, 'r') as f:
            content = f.read()
        grids = re.findall(r'class="[^"]*grid[^"]*"', content)
        responsive_grids = [g for g in grids if 'md:' in g or 'lg:' in g]
        if responsive_grids:
            print(f"\n{page} responsive grids:")
            for rg in responsive_grids[:5]:
                # Extract just the grid classes
                grid_cls = re.findall(r'(?:grid-cols-\d+|md:grid-cols-\d+|lg:grid-cols-\d+|gap-\d+)', rg)
                if grid_cls:
                    print(f"  {' '.join(grid_cls)}")

# Check footer responsive layout
print("\n### FOOTER LAYOUT ###")
with open('index.html', 'r') as f:
    content = f.read()
footer_match = re.search(r'<footer[^>]*>(.*?)</footer>', content, re.DOTALL)
if footer_match:
    footer = footer_match.group(1)
    if 'footer-grid' in footer:
        print("  Uses .footer-grid class (check style.css for responsive rules)")
    if 'grid' in footer and ('md:' in footer or 'lg:' in footer):
        print("  ✅ Footer has responsive grid")
    elif 'flex' in footer:
        print("  Footer uses flex layout")

# Check newsletter form responsiveness
print("\n### NEWSLETTER FORM LAYOUT ###")
if 'newsletter-form' in content:
    print("  Uses .newsletter-form class (check style.css for responsive rules)")

print("\n" + "=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)
