#!/usr/bin/env python3
"""
Verification script for MongoDB indexes and sample queries on 'philosophy_schools'.

- Loads Mongo settings from config/default.yaml (same as uploader)
- Validates presence and structure of indexes created by uploader v2.0.0
- Ensures only one text index exists, named 'philosophy_schools_text_v2'
- Runs smoke tests: keywords array contains 'logos', text search for 'absurd'

Exit code 0 on success, 1 on any verification failure.
"""
import sys
import yaml
from pathlib import Path
from urllib.parse import quote_plus
from pymongo import MongoClient


def load_config(config_path: Path):
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


def verify_indexes(db, verbose=True) -> bool:
    ok = True
    coll = db['philosophy_schools']
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
        # key_spec is list of tuples: [(field, direction|"text"), ...]
        if key_spec != keys:
            return False
        if unique is not None and bool(info.get('unique')) != unique:
            return False
        return True

    # Expected indexes
    expected = [
        ("idx_school_id_unique", [("school_id", 1)], True),
        ("idx_school", [("school", 1)], None),
        ("idx_category", [("category", 1)], None),
        ("idx_school_category", [("school", 1), ("category", 1)], None),
        ("idx_keywords", [("keywords", 1)], None),
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
        if name != 'philosophy_schools_text_v2':
            print(f"[ERROR] Text index name mismatch: expected 'philosophy_schools_text_v2', got '{name}'")
            ok = False
        expected_text_fields = {"school", "summary", "core_principles", "keywords"}
        weights = info.get('weights') or {}
        actual_fields = set(weights.keys())
        if actual_fields != expected_text_fields:
            print(f"[ERROR] Text index fields mismatch.\n  Expected fields: {expected_text_fields}\n  Actual fields:   {actual_fields}")
            ok = False
        # Optionally verify weights are 1 for all fields
        if any(w != 1 for w in weights.values()):
            print(f"[ERROR] Unexpected text index weights: {weights}")
            ok = False

    return ok


essential_smoke_queries = [
    {
        "desc": "keywords contains 'logos'",
        "filter": {"keywords": "logos"},
        "min_count": 1,
    },
    {
        "desc": "text search for 'absurd'",
        "filter": {"$text": {"$search": "absurd"}},
        "min_count": 1,
    },
]


def run_smoke_tests(db) -> bool:
    ok = True
    coll = db['philosophy_schools']
    for test in essential_smoke_queries:
        count = coll.count_documents(test["filter"])  # efficient count for filter
        print(f"[SMOKE] {test['desc']}: count={count}")
        if count < test["min_count"]:
            print(f"[ERROR] Smoke test failed: {test['desc']} expected >= {test['min_count']} results")
            ok = False
    return ok


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    cfg = load_config(root / "config" / "default.yaml")
    client = get_client(cfg["mongodb"])  # type: ignore[index]
    db = client[cfg["mongodb"].get("database", "daemonium")]  # type: ignore[index]

    all_ok = True
    print("--- Verifying indexes on 'philosophy_schools' ---")
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
