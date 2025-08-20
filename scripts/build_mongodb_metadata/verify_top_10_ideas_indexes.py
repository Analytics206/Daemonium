#!/usr/bin/env python3
"""
Verification script for MongoDB indexes and sample queries on 'top_10_ideas'.

- Loads Mongo settings from config/default.yaml (same as uploader)
- Validates presence and structure of indexes created by uploader v2.0.0
- Ensures only one text index exists, named 'top_10_ideas_text_v2'
- Runs smoke tests derived from existing data: checks keywords array and text search

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
    coll = db['top_10_ideas']
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
        ("idx_category", [("category", 1)], None),
        ("idx_filename", [("filename", 1)], None),
        ("idx_keywords", [("top_ideas.keywords", 1)], None),
        ("idx_top_ideas_idea", [("top_ideas.idea", 1)], None),
        ("idx_top_ideas_key_books", [("top_ideas.key_books", 1)], None),
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
        if name != 'top_10_ideas_text_v2':
            print(f"[ERROR] Text index name mismatch: expected 'top_10_ideas_text_v2', got '{name}'")
            ok = False
        expected_text_fields = {"author", "category", "top_ideas.idea", "top_ideas.description", "top_ideas.key_books", "top_ideas.keywords"}
        weights = info.get('weights') or {}
        actual_fields = set(weights.keys())
        if actual_fields != expected_text_fields:
            print(f"[ERROR] Text index fields mismatch.\n  Expected fields: {expected_text_fields}\n  Actual fields:   {actual_fields}")
            ok = False
        if any(w != 1 for w in weights.values()):
            print(f"[ERROR] Unexpected text index weights: {weights}")
            ok = False

    return ok


def run_smoke_tests(db) -> bool:
    ok = True
    coll = db['top_10_ideas']

    # Attempt to derive a realistic keyword and idea string from existing data
    sample = coll.find_one({}, {"top_ideas": 1})
    if not sample or not isinstance(sample.get("top_ideas"), list) or len(sample["top_ideas"]) == 0:
        print("[WARN] No sample top_ideas found to derive smoke test terms")
        # Still run a generic existence test
        count_any_keywords = coll.count_documents({"top_ideas.keywords": {"$exists": True}})
        print(f"[SMOKE] documents with top_ideas.keywords exists: count={count_any_keywords}")
        return count_any_keywords >= 1

    first_idea = next((i for i in sample["top_ideas"] if isinstance(i, dict)), {})
    first_keyword = None
    if isinstance(first_idea.get("keywords"), list) and first_idea["keywords"]:
        first_keyword = first_idea["keywords"][0]

    # Smoke 1: keyword array membership
    if first_keyword:
        count_kw = coll.count_documents({"top_ideas.keywords": first_keyword})
        print(f"[SMOKE] top_ideas.keywords contains '{first_keyword}': count={count_kw}")
        if count_kw < 1:
            print("[ERROR] Expected at least 1 document matching keyword membership")
            ok = False
    else:
        print("[WARN] No keyword available in sample; skipping membership test")

    # Smoke 2: text search using either a keyword or idea string
    text_term = None
    if first_keyword and isinstance(first_keyword, str) and first_keyword.strip():
        text_term = first_keyword.strip().split()[0]
    idea_text = first_idea.get("idea")
    if not text_term and isinstance(idea_text, str) and idea_text.strip():
        text_term = idea_text.strip().split()[0]

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
    print("--- Verifying indexes on 'top_10_ideas' ---")
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
