#!/usr/bin/env python3
"""
Verification script for MongoDB indexes and sample queries on 'discussion_hook'.

- Loads Mongo settings from config/default.yaml (same as uploader)
- Validates presence and structure of indexes created by uploader v1.0.0
- Ensures only one text index exists, named 'discussion_hooks_text_v2'
- Runs smoke tests: membership on themes/keywords and text search using derived terms

Exit code 0 on success, 1 on any verification failure.
"""
from __future__ import annotations

import sys
import yaml
from pathlib import Path
from urllib.parse import quote_plus
from typing import Any, Dict
from pymongo import MongoClient


def load_config(config_path: Path) -> Dict[str, Any]:
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_client(mongo_cfg: dict) -> MongoClient:
    host = mongo_cfg.get('host', 'localhost')
    port = mongo_cfg.get('port', 27017)
    database = mongo_cfg.get('database', 'daemonium')
    username = mongo_cfg.get('username')
    password = mongo_cfg.get('password')

    if username and password:
        u = quote_plus(username)
        p = quote_plus(password)
        uri = f"mongodb://{u}:{p}@{host}:{port}/{database}?authSource=admin"
    else:
        uri = f"mongodb://{host}:{port}/{database}"
    return MongoClient(uri)


def verify_indexes(db, verbose: bool = True) -> bool:
    ok = True
    coll = db['discussion_hook']
    idx_info = coll.index_information()

    if verbose:
        print("Existing indexes:")
        for name, info in idx_info.items():
            print(f"  - {name}: {info}")

    # Helper to check an index by exact key spec and optional uniqueness
    def has_index(name: str, keys: list, unique: bool | None = None) -> bool:
        info = idx_info.get(name)
        if not info:
            return False
        key_spec = info.get('key') or []
        if key_spec != keys:
            return False
        if unique is not None and bool(info.get('unique')) != unique:
            return False
        return True

    # Expected non-text indexes from uploader
    expected = [
        ("idx_author", [("author", 1)], None),
        ("idx_category", [("category", 1)], None),
        ("idx_filename", [("filename", 1)], None),
        ("idx_themes", [("themes", 1)], None),
        ("idx_keywords", [("keywords", 1)], None),
        ("idx_discussion_hooks_theme", [("discussion_hooks.theme", 1)], None),
        ("idx_discussion_hooks_keywords", [("discussion_hooks.keywords", 1)], None),
    ]

    for name, keys, unique in expected:
        if not has_index(name, keys, unique):
            print(f"[ERROR] Missing or malformed index: {name}")
            ok = False

    # Text index checks
    text_indexes = []
    for name, info in idx_info.items():
        key_spec = info.get('key', [])
        has_text_bucket = any((isinstance(direction, str) and str(direction).lower() == 'text') for _, direction in key_spec)
        has_weights = bool(info.get('weights'))
        if has_text_bucket or has_weights:
            text_indexes.append((name, info))

    if len(text_indexes) != 1:
        details = [(n, i.get('key'), i.get('weights')) for n, i in text_indexes]
        print(f"[ERROR] Expected exactly one text index, found {len(text_indexes)} -> {details}")
        ok = False
    else:
        name, info = text_indexes[0]
        if name != 'discussion_hooks_text_v2':
            print(f"[ERROR] Text index name mismatch: expected 'discussion_hooks_text_v2', got '{name}'")
            ok = False
        expected_text_fields = {"discussion_hooks.theme", "discussion_hooks.hooks", "discussion_hooks.keywords"}
        weights = info.get('weights') or {}
        actual_fields = set(weights.keys())
        if actual_fields != expected_text_fields:
            print(f"[ERROR] Text index fields mismatch.\n  Expected fields: {expected_text_fields}\n  Actual fields:   {actual_fields}")
            ok = False
        if any(w != 1 for w in weights.values()):
            print(f"[ERROR] Unexpected text index weights: {weights}")
            ok = False

    return ok


essential_fields_proj = {
    "themes": 1,
    "keywords": 1,
    "discussion_hooks.theme": 1,
    "discussion_hooks.keywords": 1,
    "discussion_hooks.hooks": 1,
}


def run_smoke_tests(db) -> bool:
    ok = True
    coll = db['discussion_hook']

    sample = coll.find_one({}, essential_fields_proj)
    if not sample:
        print("[WARN] No documents found in 'discussion_hook' to run smoke tests")
        return False

    # Smoke 1: theme membership in top-level themes array (or derive from nested)
    first_theme = None
    themes = sample.get("themes")
    if isinstance(themes, list) and themes:
        first_theme = themes[0]
    elif isinstance(sample.get("discussion_hooks"), list) and sample["discussion_hooks"]:
        nested_theme = sample["discussion_hooks"][0].get("theme")
        if isinstance(nested_theme, str) and nested_theme.strip():
            first_theme = nested_theme

    if isinstance(first_theme, str) and first_theme.strip():
        count_theme = coll.count_documents({"themes": first_theme})
        print(f"[SMOKE] themes contains '{first_theme}': count={count_theme}")
        if count_theme < 1:
            print("[ERROR] Expected at least 1 document matching theme membership")
            ok = False
    else:
        print("[WARN] Could not derive a theme; skipping theme membership test")

    # Smoke 2: keyword membership
    first_kw = None
    kws = sample.get("keywords")
    if isinstance(kws, list) and kws:
        first_kw = kws[0]
    elif isinstance(sample.get("discussion_hooks"), list) and sample["discussion_hooks"]:
        nested_kws = sample["discussion_hooks"][0].get("keywords")
        if isinstance(nested_kws, list) and nested_kws:
            first_kw = nested_kws[0]

    if isinstance(first_kw, str) and first_kw.strip():
        count_kw = coll.count_documents({"keywords": first_kw})
        print(f"[SMOKE] keywords contains '{first_kw}': count={count_kw}")
        if count_kw < 1:
            print("[ERROR] Expected at least 1 document matching keyword membership")
            ok = False
    else:
        print("[WARN] Could not derive a keyword; skipping keyword membership test")

    # Smoke 3: text search using theme or keyword or hook term
    text_term = None
    if isinstance(first_theme, str) and first_theme.strip():
        text_term = first_theme.strip().split()[0]
    if not text_term and isinstance(first_kw, str) and first_kw.strip():
        text_term = first_kw.strip().split()[0]
    if not text_term and isinstance(sample.get("discussion_hooks"), list) and sample["discussion_hooks"]:
        hooks_list = sample["discussion_hooks"][0].get("hooks")
        if isinstance(hooks_list, list) and hooks_list:
            first_hook = hooks_list[0]
            if isinstance(first_hook, str) and first_hook.strip():
                text_term = first_hook.strip().split()[0]

    if text_term:
        count_text = coll.count_documents({"$text": {"$search": text_term}})
        print(f"[SMOKE] text search for '{text_term}': count={count_text}")
        if count_text < 1:
            print("[ERROR] Expected at least 1 document from text search")
            ok = False
    else:
        print("[WARN] Could not derive text term; skipping text search test")

    return ok


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    cfg = load_config(root / "config" / "default.yaml")
    client = get_client(cfg["mongodb"])  # type: ignore[index]
    db = client[cfg["mongodb"].get("database", "daemonium")]  # type: ignore[index]

    all_ok = True
    print("--- Verifying indexes on 'discussion_hook' ---")
    if not verify_indexes(db):
        all_ok = False

    print("--- Running smoke queries ---")
    if not run_smoke_tests(db):
        all_ok = False

    client.close()
    if all_ok:
        print("[OK] Verification passed.")
        sys.exit(0)
    else:
        print("[FAIL] Verification failed.")
        sys.exit(1)
