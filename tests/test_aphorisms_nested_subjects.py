import pytest
from fastapi.testclient import TestClient

import backend.main as main
from backend.routers import aphorisms as aph_router


SAMPLE_APHORISMS = [
    {
        "_id": "hume_morality",
        "author": "David Hume",
        "category": "Morality and Ethics",
        "text": "Custom is the great guide of human life.",
        "subject": [
            {
                "theme": "Ethics",
                "keywords": ["virtue", "custom"],
                "aphorisms": ["Custom is the great guide of human life."],
            },
            {
                "theme": "Epistemology",
                "keywords": ["skepticism"],
                "aphorisms": ["All knowledge degenerates into probability."],
            },
        ],
        "context": "Treatise",
        "themes": ["ethics", "skepticism"],
    },
    {
        "_id": "plato_politics",
        "author": "Plato",
        "category": "Politics and Society",
        "text": "Justice in the state mirrors justice in the soul.",
        "subject": [
            {
                "theme": "Politics",
                "keywords": ["justice", "state"],
                "aphorisms": [
                    "Justice in the state mirrors justice in the soul."
                ],
            },
            {
                "theme": "Metaphysics",
                "keywords": ["forms"],
                "aphorisms": ["The form of the good..."],
            },
        ],
        "context": "Republic",
        "themes": ["politics", "justice"],
    },
]


class FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)
        self._skip = 0
        self._limit = None

    def skip(self, n):
        self._skip = int(n)
        return self

    def limit(self, n):
        self._limit = int(n)
        return self

    async def to_list(self, length=None):
        docs = self._docs
        if self._skip:
            docs = docs[self._skip :]
        if self._limit is not None:
            docs = docs[: self._limit]
        elif length is not None:
            docs = docs[:length]
        return list(docs)


class FakeCollection:
    def __init__(self, docs):
        self.docs = list(docs)
        self.last_filter = None

    def find(self, search_filter):
        # Capture the filter so tests can assert it includes nested subject fields
        self.last_filter = search_filter
        return FakeCursor(self.docs)


class MockDBManager:
    def __init__(self, docs):
        self.docs = list(docs)
        self.last_get_aphorisms_kwargs = None
        self.collection = None  # Optional FakeCollection set by tests

    async def get_aphorisms(
        self,
        skip: int = 0,
        limit: int = 100,
        philosopher: str | None = None,
        subject_theme: str | None = None,
        subject_keyword: str | None = None,
        subject_aphorism: str | None = None,
    ):
        # Record passthrough args for assertions
        self.last_get_aphorisms_kwargs = {
            "skip": skip,
            "limit": limit,
            "philosopher": philosopher,
            "subject_theme": subject_theme,
            "subject_keyword": subject_keyword,
            "subject_aphorism": subject_aphorism,
        }

        def has_subject_theme(d):
            if not subject_theme:
                return True
            st = subject_theme.lower()
            for s in (d.get("subject") or []):
                t = (s or {}).get("theme")
                if t and st in str(t).lower():
                    return True
            return False

        def has_subject_keyword(d):
            if not subject_keyword:
                return True
            sk = subject_keyword.lower()
            for s in (d.get("subject") or []):
                kws = (s or {}).get("keywords") or []
                for kw in kws:
                    if sk in str(kw).lower():
                        return True
            return False

        def has_subject_aphorism(d):
            if not subject_aphorism:
                return True
            sa = subject_aphorism.lower()
            for s in (d.get("subject") or []):
                aphs = (s or {}).get("aphorisms") or []
                for a in aphs:
                    if sa in str(a).lower():
                        return True
            return False

        def has_philosopher(d):
            if not philosopher:
                return True
            p = philosopher.lower()
            return p in str(d.get("author", "")).lower() or p in str(
                d.get("philosopher", "")
            ).lower()

        filtered = [
            d
            for d in self.docs
            if has_philosopher(d)
            and has_subject_theme(d)
            and has_subject_keyword(d)
            and has_subject_aphorism(d)
        ]
        return filtered[skip : skip + limit]

    def get_collection(self, name: str):
        # Return the FakeCollection when tests set it
        if name == "aphorisms" and self.collection is not None:
            return self.collection
        # Fallback minimal collection to avoid crashes when not explicitly set
        return FakeCollection(self.docs)


@pytest.fixture
def mock_db_manager():
    return MockDBManager(SAMPLE_APHORISMS)


@pytest.fixture
def client(monkeypatch, mock_db_manager):
    # Prevent real DB connections during app lifespan
    class NoopDB:
        def __init__(self, settings):
            pass

        async def connect(self):
            pass

        async def disconnect(self):
            pass

        async def health_check(self):
            return True

    monkeypatch.setattr(main, "DatabaseManager", NoopDB)

    async def override_db():
        return mock_db_manager

    # Override both router-level and app-level DB dependencies to ensure complete isolation
    main.app.dependency_overrides[main.get_db_manager] = override_db
    main.app.dependency_overrides[aph_router.get_db_manager] = override_db
    with TestClient(main.app) as c:
        yield c
    main.app.dependency_overrides.clear()


# --- Main endpoint tests (nested subject query params) ---

def test_subject_theme_filter(client, mock_db_manager):
    resp = client.get(
        "/api/v1/aphorisms/",
        params={"subject_theme": "Ethics", "limit": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_count"] == 1
    assert body["data"][0]["author"] == "David Hume"

    # Verify passthrough to db_manager.get_aphorisms
    assert mock_db_manager.last_get_aphorisms_kwargs["subject_theme"] == "Ethics"


def test_subject_keyword_filter(client, mock_db_manager):
    resp = client.get(
        "/api/v1/aphorisms/",
        params={"subject_keyword": "virtue", "limit": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_count"] == 1
    assert body["data"][0]["author"] == "David Hume"
    assert (
        mock_db_manager.last_get_aphorisms_kwargs["subject_keyword"] == "virtue"
    )


def test_subject_aphorism_filter(client, mock_db_manager):
    resp = client.get(
        "/api/v1/aphorisms/",
        params={"subject_aphorism": "Custom is the great guide", "limit": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_count"] == 1
    assert body["data"][0]["author"] == "David Hume"
    assert (
        mock_db_manager.last_get_aphorisms_kwargs["subject_aphorism"]
        == "Custom is the great guide"
    )


def test_combined_filters_with_philosopher(client, mock_db_manager):
    resp = client.get(
        "/api/v1/aphorisms/",
        params={
            "subject_theme": "Ethics",
            "subject_keyword": "custom",
            "philosopher": "Hume",
            "limit": 10,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_count"] == 1
    assert body["data"][0]["author"] == "David Hume"

    kw = mock_db_manager.last_get_aphorisms_kwargs
    assert kw["subject_theme"] == "Ethics"
    assert kw["subject_keyword"] == "custom"
    assert kw["philosopher"] == "Hume"


def test_no_results_returns_empty_list(client, mock_db_manager):
    resp = client.get(
        "/api/v1/aphorisms/",
        params={"subject_theme": "NoSuchTheme", "limit": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_count"] == 0
    assert body["data"] == []


# --- Keyword and theme routes should include nested subject fields in filters ---

def test_keyword_route_includes_nested_subject_fields_in_or_filter(client, mock_db_manager):
    # Prepare a fake collection with one doc so route returns 200
    fake = FakeCollection([SAMPLE_APHORISMS[0]])
    mock_db_manager.collection = fake

    resp = client.get("/api/v1/aphorisms/virtue", params={"limit": 5})
    assert resp.status_code == 200

    # Ensure the search filter used includes nested subject fields
    filt = fake.last_filter
    assert isinstance(filt, dict) and "$or" in filt
    keys = set().union(*[set(d.keys()) for d in filt["$or"] if isinstance(d, dict)])
    assert "subject.theme" in keys
    assert "subject.keywords" in keys
    assert "subject.aphorisms" in keys


def test_by_theme_route_uses_subject_theme_in_filter(client, mock_db_manager):
    # Prepare a fake collection with one doc so route returns 200
    fake = FakeCollection([SAMPLE_APHORISMS[0]])
    mock_db_manager.collection = fake

    resp = client.get("/api/v1/aphorisms/by-theme/Ethics", params={"limit": 2})
    assert resp.status_code == 200

    filt = fake.last_filter
    assert isinstance(filt, dict) and "$or" in filt
    keys = set().union(*[set(d.keys()) for d in filt["$or"] if isinstance(d, dict)])
    assert "subject.theme" in keys
