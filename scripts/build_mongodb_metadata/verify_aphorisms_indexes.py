#!/usr/bin/env python3
"""
Verification script for MongoDB indexes and nested structure on 'aphorisms'.

- Loads Mongo settings from config/default.yaml (same as uploader)
- Validates presence and structure of indexes created by uploader v2.0.0
- Ensures only one text index exists, named 'aphorisms_text_index'
- Verifies documents preserve nested 'subject' array with theme/keywords/aphorisms
- Runs smoke tests: nested keyword membership and text search

Exit code 0 on success, 1 on any verification failure.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict
from urllib.parse import quote_plus

import yaml
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
    coll = db['aphorisms']
    idx_info = coll.index_information()

    if verbose:
        print("Existing indexes:")
        for name, info in idx_info.items():
            print(f"  - {name}: {info}")

    # Helpers
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
        ("idx_filename", [("filename", 1)], None),
        ("idx_category", [("category", 1)], None),
        ("idx_subject_theme", [("subject.theme", 1)], None),
        ("idx_subject_keywords", [("subject.keywords", 1)], None),
        ("idx_subject_aphorisms", [("subject.aphorisms", 1)], None),
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
        if name != 'aphorisms_text_index':
            print(f"[ERROR] Text index name mismatch: expected 'aphorisms_text_index', got '{name}'")
            ok = False
        expected_text_fields = {"author", "category", "subject.theme", "subject.keywords", "subject.aphorisms"}
        weights = info.get('weights') or {}
        actual_fields = set(weights.keys())
        if actual_fields != expected_text_fields:
            print(f"[ERROR] Text index fields mismatch.\n  Expected fields: {expected_text_fields}\n  Actual fields:   {actual_fields}")
            ok = False
        if any(w != 1 for w in weights.values()):
            print(f"[ERROR] Unexpected text index weights: {weights}")
            ok = False

    return ok


def verify_nested_structure(db) -> bool:
    ok = True
    coll = db['aphorisms']

    sample = coll.find_one({}, {"author": 1, "subject": 1, "keywords": 1, "aphorisms": 1})
    if not sample:
        print("[WARN] No documents found in 'aphorisms' to verify structure")
        return False

    # Ensure no flattened top-level fields
    if 'keywords' in sample:
        print("[ERROR] Found unexpected top-level 'keywords' field (should be nested under subject[].keywords)")
        ok = False
    if 'aphorisms' in sample:
        print("[ERROR] Found unexpected top-level 'aphorisms' field (should be nested under subject[].aphorisms)")
        ok = False

    subj = sample.get('subject')
    if not isinstance(subj, list) or not subj:
        print("[ERROR] 'subject' must be a non-empty list of objects")
        return False

    if not all(isinstance(s, dict) for s in subj):
        print("[ERROR] 'subject' must be a list of objects with theme/keywords/aphorisms fields")
        ok = False

    # Check that at least one subject has normalized arrays
    found_normalized = False
    for s in subj:
        kws = s.get('keywords')
        aphs = s.get('aphorisms')
        if isinstance(kws, list) and isinstance(aphs, list):
            found_normalized = True
            break
    if not found_normalized:
        print("[ERROR] No subject entry contains normalized arrays for 'keywords' and 'aphorisms'")
        ok = False

    return ok


def run_smoke_tests(db) -> bool:
    ok = True
    coll = db['aphorisms']

    sample = coll.find_one({"subject": {"$exists": True, "$type": "array", "$ne": []}}, {"subject": 1})
    if not sample:
        print("[WARN] No documents with non-empty 'subject' to run smoke tests")
        return False

    # Derive a keyword from the first subject that has keywords
    keyword = None
    text_term = None
    for s in sample.get('subject', []):
        if isinstance(s.get('keywords'), list) and s['keywords']:
            keyword = s['keywords'][0]
        if isinstance(s.get('aphorisms'), list) and s['aphorisms']:
            # use first word of first aphorism as text term
            first_aph = s['aphorisms'][0]
            if isinstance(first_aph, str) and first_aph.strip():
                text_term = first_aph.strip().split()[0]
        if keyword and text_term:
            break

    if keyword:
        count_kw = coll.count_documents({"subject.keywords": keyword})
        print(f"[SMOKE] subject.keywords contains '{keyword}': count={count_kw}")
        if count_kw < 1:
            print("[ERROR] Expected at least 1 document matching nested keyword membership")
            ok = False
    else:
        print("[WARN] Could not derive a sample nested keyword; skipping membership test")

    if text_term:
        count_text = coll.count_documents({"$text": {"$search": text_term}})
        print(f"[SMOKE] text search for '{text_term}': count={count_text}")
        if count_text < 1:
            print("[ERROR] Expected at least 1 document from text search")
            ok = False
    else:
        print("[WARN] Could not derive text term from first aphorism; skipping text search test")

    return ok


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    cfg = load_config(root / "config" / "default.yaml")
    client = get_client(cfg["mongodb"])  # type: ignore[index]
    db = client[cfg["mongodb"].get("database", "daemonium")]  # type: ignore[index]

    all_ok = True
    print("--- Verifying indexes on 'aphorisms' ---")
    if not verify_indexes(db):
        all_ok = False

    print("--- Verifying nested 'subject' structure ---")
    if not verify_nested_structure(db):
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
