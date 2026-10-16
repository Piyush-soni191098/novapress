from __future__ import annotations

from typing import Optional

from app import config

_supabase_client = None
_supabase_admin_client = None


def get_supabase():
    """Return the user-scoped Supabase client (uses anon key)."""
    global _supabase_client
    if _supabase_client is None and config.supabase_configured():
        try:
            from supabase import create_client
            _supabase_client = create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
        except ImportError:
            pass
    return _supabase_client


def get_supabase_admin():
    """Return the service-role Supabase client (backend-only, never exposed to browser)."""
    global _supabase_admin_client
    if _supabase_admin_client is None and config.supabase_admin_configured():
        try:
            from supabase import create_client
            _supabase_admin_client = create_client(
                config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY
            )
        except ImportError:
            pass
    return _supabase_admin_client
