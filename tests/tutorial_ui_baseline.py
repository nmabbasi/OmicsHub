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
from start_here_baseline import normalize_start_here
from home_catalogue_baseline import normalize_home_catalogue
from reader_text_colour_baseline import READER_TEXT_ASSET_SHA256, restore_reader_text_asset
from r_first_revision_baseline import (
    R_FIRST_ASSET_PATHS, normalize_r_first_revision, restore_r_first_asset,
)
from latest_review_baseline import normalize_latest_review, restore_latest_review_asset

ROOT = Path(__file__).resolve().parents[1]
PRE_UI_COMMIT = '243bc04e5edff51b33bef1b9312a48f6b2ae5751'
UI_VERSION = '20261024-reader-ui-v3'
FIXTURE_SHA256 = '073789da159288cd82fa5c67535b5f11d8d117bb1a01bb446138cd3449089a51'
UI_MARKERS = (UI_VERSION, 'reader-path-card__copy', 'reader-sequence-utilities', '<!-- Tutorial top link -->')

TUTORIAL_UI_SHA256 = {
    ".github/workflows/static.yml": "b625c7afe9a00f8e7db14822bd31c5b30b89dc0ca766beb0abe1bab0f8fc73c7",
    ".github/workflows/tutorial-review.yml": "2a03d1c3187a6d9a71d8b5995da1f2f58f110b86f7b4252d542ca74af358cac0",
    "home-page.min.css": "cdb62d189a51a3c5e30734e65ffa9928aeff2662aa8bba42620a8ebff32ada43",
    "assets/vendor/prism/LICENSE": "2b947f0901a7ffcf08a89957da9783c0e9c6e72cb6ce8e959f501ab5409e4d2b",
    "assets/vendor/prism/prism-1.29.0.js": "6c45e1fd96435df297b0afa19685ea4ee6c1ef784b6b8c2c14cfdbcd9331e110",
    "code-tabs.js": "64db902cf23a8dbfca01a5f78cd74b9336cdd0ae3c224235cff9258004bc1341",
    "copy-code.js": "8eeeee419ea4b7da0e9890b6aed65cba32469c2e0a1a88896dbd3f13b8db796a",
    "script.js": "caf24bee4c7cd9b2f116ac7a149fc47b71507ae3deebda5ba18f250367990fa0",
    "subscribe-fab.js": "d8025077985e1d179473f03279cab1b2f7a9dcc8ea8e7ca7f22e5384dd4e2268",
    "tools/generate_learning_paths.py": "18606101c840099f0a191fba5b12524a865b039a317436a0e25caec7fd242834",
    "tools/generate_tutorial_ui.py": "a83562318ffc5e0ed2a61d871d0d72689a68af78448730f0e493ea7ec9c89a92",
    "tools/tutorial-code-groups.json": "71830f470c56a454f50220eac1d33e4c48bcfdbd5c6270886a7225b0df00a150",
    "tools/tutorial-code-languages.json": "070aa1f0bd780087222a969efd15622fc8c675ef6aaf27d38fe6d6d875e73ad3",
    "tutorial-code-data.js": "6d011cb3d2c5a383922625351778dea16e4094b5d5f7bb5d5a71e3cc2bd6144f",
    "tutorial-navigation.css": "f716eefbce9e73c3b797818ad154ebc94a5911d12c1c9971749fe166cc9e1974",
    "tutorial-reader.css": "3964dee44c4e529e74f8bea476e99813695638c2ccf3bc74cddb55b7d342f0cf",
    "back-to-top.css": "835d1ef5330eacdd3452052d181bb1f0f440cfb0b2bf36be973ba03f53427896"
}
TUTORIAL_UI_PATHS = frozenset(TUTORIAL_UI_SHA256) | R_FIRST_ASSET_PATHS

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
    """Reverse only literal page-specific UI chunks, never a regex-selected body.

    The home-catalogue adapter runs first so historic scientific-scope helpers
    can still compose it with the older Start Here and tutorial UI restorations.
    """
    if not isinstance(text, str):
        raise TypeError('tutorial UI normalization requires decoded text')
    text = normalize_latest_review(relative_path, text)
    text = normalize_r_first_revision(relative_path, text)
    text = normalize_home_catalogue(relative_path, text)
    text = normalize_start_here(relative_path, text)
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
    original_data = data
    data = restore_latest_review_asset(relative_path, data)
    if relative_path in R_FIRST_ASSET_PATHS:
        data = restore_r_first_asset(relative_path, data)
        if relative_path not in TUTORIAL_UI_SHA256:
            return original_data
    from home_catalogue_baseline import HOME_CATALOGUE_ASSET_PATHS, verify_home_catalogue_file
    if relative_path in HOME_CATALOGUE_ASSET_PATHS and relative_path in TUTORIAL_UI_PATHS:
        observed = hashlib.sha256(data).hexdigest()
        # Preserve former complete pins for older snapshots; current work is
        # separately pinned as a home-catalogue asset.
        if observed == TUTORIAL_UI_SHA256[relative_path]:
            return original_data
        verify_home_catalogue_file(relative_path, data)
        return original_data
    if relative_path in TUTORIAL_UI_PATHS:
        if (relative_path in READER_TEXT_ASSET_SHA256
                and hashlib.sha256(data).hexdigest() == READER_TEXT_ASSET_SHA256[relative_path]):
            data = restore_reader_text_asset(relative_path, data)
        observed = hashlib.sha256(data).hexdigest()
        if observed != TUTORIAL_UI_SHA256[relative_path]:
            raise AssertionError(f"tutorial UI file fingerprint mismatch for {relative_path}: {observed}")
        return original_data
    verify_home_catalogue_file(relative_path, data)
    return original_data


def pre_ui_bytes(relative_path):
    result = subprocess.run(['git', 'show', f'{PRE_UI_COMMIT}:{relative_path}'], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return result.stdout if result.returncode == 0 else None
