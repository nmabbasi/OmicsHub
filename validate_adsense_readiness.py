from pathlib import Path
from bs4 import BeautifulSoup

root = Path(__file__).resolve().parent
files = sorted(root.glob('*.html')) + sorted((root / 'pages').glob('*.html'))
errors = []
for path in files:
    html = path.read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    if len(soup.find_all('h1')) != 1:
        errors.append(f'{path}: H1={len(soup.find_all("h1"))}')
    if len(soup.find_all('link', rel='canonical')) != 1:
        errors.append(f'{path}: canonical={len(soup.find_all("link", rel="canonical"))}')
    if html.count('id="cookie-consent-banner"') != 1:
        errors.append(f'{path}: consent banner count={html.count("id=\\\"cookie-consent-banner\\\"")}')
    if 'adsense-consent.js' not in html:
        errors.append(f'{path}: consent bootstrap missing')
    if 'google-adsense-account' not in html:
        errors.append(f'{path}: publisher meta missing')
    consent_pos = html.find('adsense-consent.js')
    ads_pos = html.find('adsbygoogle.js')
    if consent_pos < 0 or ads_pos < 0 or consent_pos > ads_pos:
        errors.append(f'{path}: consent script not before ads')

for name in ['ads.txt', 'robots.txt', 'cookie-consent.js', 'adsense-consent.js']:
    if not (root / name).exists():
        errors.append(f'missing {name}')
if 'google.com, pub-2910340533244599, DIRECT, f08c47fec0942fa0' not in (root / 'ads.txt').read_text(encoding='utf-8'):
    errors.append('ads.txt publisher line missing')

print(f'targeted_checked={len(files)} targeted_errors={len(errors)}')
for error in errors[:50]:
    print(error)
raise SystemExit(1 if errors else 0)
