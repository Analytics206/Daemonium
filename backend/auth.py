"""
Firebase authentication utilities for Daemonium FastAPI backend

- Initializes Firebase Admin SDK during app startup (if enabled)
- Provides a FastAPI dependency to verify Firebase ID tokens
- Enforces that the token's UID matches the request path parameter `user_id`
"""
from __future__ import annotations

import base64
import json
import logging
import asyncio
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status

from .config import get_settings

logger = logging.getLogger(__name__)

# Lazy imports to avoid hard dependency issues when auth disabled
try:
    import firebase_admin
    from firebase_admin import auth as fb_auth
    from firebase_admin import credentials
except Exception:  # pragma: no cover - only when package missing
    firebase_admin = None  # type: ignore
    fb_auth = None  # type: ignore
    credentials = None  # type: ignore


def _build_credentials(settings) -> Optional["credentials.Base"]:
    """Create firebase credentials from file, base64 JSON, or ADC fallback.

    Returns None to signal using Application Default Credentials (ADC).
    """
    if credentials is None:
        return None

    # Prefer explicit credentials when provided
    if settings.firebase_credentials_file:
        try:
            return credentials.Certificate(settings.firebase_credentials_file)
        except Exception as e:
            logger.error(f"Failed to load Firebase credentials from file: {e}")
            raise

    if settings.firebase_credentials_base64:
        try:
            decoded = base64.b64decode(settings.firebase_credentials_base64).decode("utf-8")
            data = json.loads(decoded)
            return credentials.Certificate(data)
        except Exception as e:
            logger.error("Failed to decode/load Firebase base64 credentials JSON")
            logger.debug(f"Credential decode error: {e}")
            raise

    # Use ADC when explicit credentials not provided
    try:
        return credentials.ApplicationDefault()
    except Exception as e:
        logger.warning(f"Application Default Credentials unavailable: {e}")
        return None


def init_firebase_if_enabled(settings=None) -> bool:
    """Initialize Firebase Admin SDK if enabled in settings.

    Returns True if initialized or already initialized; False if skipped/disabled.
    Raises only for credential read errors; other init issues are logged and skipped.
    """
    if settings is None:
        settings = get_settings()

    if not settings.firebase_enabled:
        logger.info("Firebase auth disabled by configuration; skipping initialization")
        return False

    if firebase_admin is None or credentials is None:
        logger.error("firebase-admin package not available but required for auth")
        return False

    # Avoid double-initialization
    try:
        if getattr(firebase_admin, "_apps", None):
            return True
    except Exception:
        # Proceed to initialize
        pass

    cred = _build_credentials(settings)

    opts: Dict[str, Any] = {}
    if settings.firebase_project_id:
        # Optionally help ADC resolve the project
        opts["projectId"] = settings.firebase_project_id

    try:
        if cred is not None:
            firebase_admin.initialize_app(cred, opts or None)
        else:
            # ADC path
            firebase_admin.initialize_app(options=opts or None)  # type: ignore[arg-type]
        logger.info("Firebase Admin SDK initialized")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        return False


async def verify_firebase_id_token(user_id: str, request: Request) -> Dict[str, Any]:
    """FastAPI dependency to validate Authorization: Bearer <ID_TOKEN>.

    - When Firebase auth is disabled, this is a no-op and returns a stub payload.
    - When enabled, verifies the token and enforces UID == path `user_id`.
    Returns a dict with minimal auth info, e.g., {"uid": str, "claims": {...}}.
    """
    settings = get_settings()

    # Bypass when disabled (keeps backward compatibility for local/dev setups)
    if not settings.firebase_enabled:
        return {"uid": user_id, "auth": "disabled"}

    if firebase_admin is None or fb_auth is None:
        logger.error("firebase-admin package not available but required for auth")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Auth service unavailable")

    # Ensure Firebase is initialized (in case startup init failed or ran late)
    try:
        if not getattr(firebase_admin, "_apps", None):
            ok = init_firebase_if_enabled(settings)
            if not ok:
                raise RuntimeError("Firebase not initialized")
    except Exception as e:
        logger.error(f"Auth initialization error: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Auth service unavailable")

    # Extract and validate Authorization header
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Empty bearer token")

    # Verify token in a worker thread to avoid blocking the event loop
    try:
        decoded: Dict[str, Any] = await asyncio.to_thread(
            fb_auth.verify_id_token,
            token,
            clock_skew_seconds=60,  # allow small clock skew
        )
    except Exception as e:
        # Avoid logging token; provide generic auth failure
        logger.info(f"ID token verification failed for user_id={user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    uid = decoded.get("uid") or decoded.get("sub")
    if not uid:
        logger.info("Verified token missing UID/SUB claim")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")

    if uid != user_id:
        logger.warning(f"User ID mismatch: token.uid={uid} != path.user_id={user_id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: user mismatch")

    return {"uid": uid, "claims": decoded}
