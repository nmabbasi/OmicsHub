"""Exact UI-only restoration for historical scientific-scope regression checks.

The 58 page patches are literal, reversible chunks against the last published
revision. They include only local UI asset wiring, generated navigation and the
native top link. Unknown edits are never stripped or hidden. Older snapshots
without this UI revision remain byte-identical.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PRE_UI_COMMIT = '243bc04e5edff51b33bef1b9312a48f6b2ae5751'
UI_VERSION = '20261024-reader-ui-v2'
FIXTURE_SHA256 = '59c6b4c8e47cf26fa7b4deb67e62f1c48aedd1077a41166b28f22c1631e25d35'
UI_MARKERS = (UI_VERSION, 'reader-path-card__copy', 'reader-sequence-utilities', '<!-- Tutorial top link -->')

TUTORIAL_UI_SHA256 = {
    ".github/workflows/static.yml": "b625c7afe9a00f8e7db14822bd31c5b30b89dc0ca766beb0abe1bab0f8fc73c7",
    ".github/workflows/tutorial-review.yml": "d738f96dd776b82d070c5bbb66d8a225c6fd3cb6a2d90b14dd89fdb4f58ee67a",
    "home-page.min.css": "09fc823df93e6aa7e1f233f964b30b195a25333228eeb97268e117e8e9e58ce3",
    "assets/vendor/prism/LICENSE": "2b947f0901a7ffcf08a89957da9783c0e9c6e72cb6ce8e959f501ab5409e4d2b",
    "assets/vendor/prism/prism-1.29.0.js": "6c45e1fd96435df297b0afa19685ea4ee6c1ef784b6b8c2c14cfdbcd9331e110",
    "code-tabs.js": "64db902cf23a8dbfca01a5f78cd74b9336cdd0ae3c224235cff9258004bc1341",
    "copy-code.js": "8eeeee419ea4b7da0e9890b6aed65cba32469c2e0a1a88896dbd3f13b8db796a",
    "script.js": "caf24bee4c7cd9b2f116ac7a149fc47b71507ae3deebda5ba18f250367990fa0",
    "subscribe-fab.js": "a0e69b7d10e937bfb1cecccc8303adc433ea6c604f5fc727779053ece67f2c27",
    "tools/generate_learning_paths.py": "18606101c840099f0a191fba5b12524a865b039a317436a0e25caec7fd242834",
    "tools/generate_tutorial_ui.py": "b4784e65f29f177b1c8355296d756a69d74ee6590299a266c09a359a6de3c117",
    "tools/tutorial-code-groups.json": "71830f470c56a454f50220eac1d33e4c48bcfdbd5c6270886a7225b0df00a150",
    "tools/tutorial-code-languages.json": "070aa1f0bd780087222a969efd15622fc8c675ef6aaf27d38fe6d6d875e73ad3",
    "tutorial-code-data.js": "6d011cb3d2c5a383922625351778dea16e4094b5d5f7bb5d5a71e3cc2bd6144f",
    "tutorial-navigation.css": "f716eefbce9e73c3b797818ad154ebc94a5911d12c1c9971749fe166cc9e1974",
    "tutorial-reader.css": "efdf5bf513f051523da5790191750d52c05e0e577ad92192ee44e5f999b1812f"
}
TUTORIAL_UI_PATHS = frozenset(TUTORIAL_UI_SHA256)

@lru_cache(maxsize=1)
def page_patches():
    path = ROOT / 'tests/fixtures/tutorial-ui-page-edits.json'
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise AssertionError('Exact UI page-patch fixture fingerprint changed')
    fixture = json.loads(raw)
    if fixture['schema'] != 1 or fixture['pre_ui_commit'] != PRE_UI_COMMIT or len(fixture['files']) != 58:
        raise AssertionError('Invalid exact UI page-patch fixture')
    return fixture['files']


def normalize_tutorial_ui(relative_path, text):
    """Reverse only literal current UI chunks, never a regex-selected HTML body.

    This is idempotent and supports fragments. It has no effect on pre-UI history.
    Missing/altered patch chunks stay visible to the existing strict comparisons.
    """
    if not isinstance(text, str):
        raise TypeError('tutorial UI normalization requires decoded text')
    if not (relative_path.startswith('tutorials/') and relative_path.endswith('.html')):
        return text
    if not any(marker in text for marker in UI_MARKERS):
        return text
    for patch in page_patches().get(relative_path, []):
        count = text.count(patch['after'])
        if count > 1:
            raise AssertionError(f'duplicate exact UI patch in {relative_path}')
        if count:
            text = text.replace(patch['after'], patch['before'], 1)
    return text


def verify_tutorial_ui_file(relative_path, data):
    """Pin every explicitly authorized new/modified UI file, never whole folders."""
    if relative_path not in TUTORIAL_UI_PATHS:
        raise AssertionError(f'not an authorized tutorial UI file: {relative_path}')
    observed = hashlib.sha256(data).hexdigest()
    if observed != TUTORIAL_UI_SHA256[relative_path]:
        raise AssertionError(f'tutorial UI file fingerprint mismatch for {relative_path}: {observed}')
    return data


def pre_ui_bytes(relative_path):
    result = subprocess.run(['git', 'show', f'{PRE_UI_COMMIT}:{relative_path}'], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return result.stdout if result.returncode == 0 else None
