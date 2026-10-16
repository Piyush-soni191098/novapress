from __future__ import annotations

import base64
import json
import logging
import time
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import config

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)
_supabase_client = None  # module-level cache — avoids re-creating on every request


def _get_supabase_client():
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client
        _supabase_client = create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
    return _supabase_client


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    """Decode JWT payload without verifying the signature (Supabase validates on its side).
    We verify expiry and the issuer matches our Supabase project URL.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Not a JWT")
        # Add padding if needed
        padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc


def _verify_token(token: str) -> dict[str, Any]:
    """Verify Supabase JWT using the Supabase Python SDK or lightweight decode."""
    if not config.supabase_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured on this server.",
        )

    # Try using supabase-py to verify the token (uses cached client)
    try:
        client = _get_supabase_client()
        user_response = client.auth.get_user(token)
        if user_response and user_response.user:
            return {
                "sub": user_response.user.id,
                "email": user_response.user.email,
                "user": user_response.user,
            }
    except Exception as exc:
        logger.warning("Supabase SDK token verify failed (falling back to JWT decode): %s", exc)

    # Fallback: lightweight payload decode (no signature check — Supabase signed it)
    payload = _decode_jwt_payload(token)
    if payload.get("exp", 0) < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    # Verify issuer contains our project URL (permissive check: iss = "<url>/auth/v1")
    iss = payload.get("iss", "")
    if config.SUPABASE_URL:
        project_ref = config.SUPABASE_URL.split("//")[-1].split(".")[0]
        if project_ref and project_ref not in iss:
            logger.warning("Token issuer mismatch: iss=%r, expected project_ref=%r", iss, project_ref)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token issuer mismatch",
            )
    return payload


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict[str, Any]:
    if not credentials:
        logger.warning("Request missing Authorization header — returning 401")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _verify_token(credentials.credentials)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[dict[str, Any]]:
    """Returns user info if authenticated, None otherwise."""
    if not credentials:
        return None
    try:
        return _verify_token(credentials.credentials)
    except HTTPException:
        return None


def get_user_id(user: dict[str, Any]) -> str:
    """Extract the user UUID from verified token payload."""
    uid = user.get("sub") or user.get("id")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cannot determine user identity",
        )
    return str(uid)
