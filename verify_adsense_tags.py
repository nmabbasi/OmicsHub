import glob
import os

META_TAG = '<meta name="google-adsense-account" content="ca-pub-2910340533244599"/>'
SCRIPT_TAG = '<script async="" crossorigin="anonymous" src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2910340533244599"></script>'

def ensure_adsense(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False

    # Check for SCRIPT_TAG
    if 'adsbygoogle.js?client=ca-pub-2910340533244599' not in content:
        if '</head>' in content:
            content = content.replace('</head>', f'{SCRIPT_TAG}\n</head>')
            changed = True

    # Check for META_TAG
    if 'google-adsense-account' not in content:
        if '</head>' in content:
            content = content.replace('</head>', f'{META_TAG}\n</head>')
            changed = True

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

if __name__ == '__main__':
    html_files = glob.glob('**/*.html', recursive=True)
    updated = 0
    for file in html_files:
        if ensure_adsense(file):
            print(f'Updated {file}')
            updated += 1
    print(f'Total files updated: {updated}')
