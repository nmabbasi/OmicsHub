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
UI_VERSION = '20261024-reader-ui'
FIXTURE_SHA256 = 'd5012158246cec4d80d834bcc10dd4c07b7fd7192787951602fa31eb79116672'
UI_MARKERS = (UI_VERSION, 'reader-path-card__copy', 'reader-sequence-utilities', '<!-- Tutorial top link -->')

TUTORIAL_UI_SHA256 = {
    ".github/workflows/static.yml": "b625c7afe9a00f8e7db14822bd31c5b30b89dc0ca766beb0abe1bab0f8fc73c7",
    ".github/workflows/tutorial-review.yml": "d738f96dd776b82d070c5bbb66d8a225c6fd3cb6a2d90b14dd89fdb4f58ee67a",
    "home-page.min.css": "0f4e17dc8a6c0c62c3b050bca3c6134a9996706ae5fffe870fbb0a8e711a80ae",
    "assets/vendor/prism/LICENSE": "2b947f0901a7ffcf08a89957da9783c0e9c6e72cb6ce8e959f501ab5409e4d2b",
    "assets/vendor/prism/prism-1.29.0.js": "6c45e1fd96435df297b0afa19685ea4ee6c1ef784b6b8c2c14cfdbcd9331e110",
    "code-tabs.js": "64db902cf23a8dbfca01a5f78cd74b9336cdd0ae3c224235cff9258004bc1341",
    "copy-code.js": "8eeeee419ea4b7da0e9890b6aed65cba32469c2e0a1a88896dbd3f13b8db796a",
    "script.js": "caf24bee4c7cd9b2f116ac7a149fc47b71507ae3deebda5ba18f250367990fa0",
    "subscribe-fab.js": "207701b304ae1f1a5476b5d281c0d2a3ecf34688c638d0f37c370e1e60e680a7",
    "tools/generate_learning_paths.py": "8ffc1bc901137e01acd9209b3c11a386f52cd1ed74baebde6330d04d98727fe3",
    "tools/generate_tutorial_ui.py": "f4e3b40fd002eb0f626b2abb89dd1e6983ee1bc33890403a69c361f8e2bdd05b",
    "tools/tutorial-code-groups.json": "71830f470c56a454f50220eac1d33e4c48bcfdbd5c6270886a7225b0df00a150",
    "tools/tutorial-code-languages.json": "070aa1f0bd780087222a969efd15622fc8c675ef6aaf27d38fe6d6d875e73ad3",
    "tutorial-code-data.js": "6d011cb3d2c5a383922625351778dea16e4094b5d5f7bb5d5a71e3cc2bd6144f",
    "tutorial-navigation.css": "057cba0308e74359fe1824b1c92d9b12957e5d5e85df4968c55f0ed32052c835",
    "tutorial-reader.css": "01d2fa90e62e3ca81f4551d8e81c492fed4f7e1ea533cd45f996ebf9b75c3b7e"
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
