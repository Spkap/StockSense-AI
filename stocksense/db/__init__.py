"""
StockSense Database Package

Supabase-based storage for analysis cache and user data.
"""
from .database import (
    init_db,
    save_analysis,
    get_latest_analysis,
    delete_cached_analysis,
    get_all_cached_tickers,
    get_all_cached_tickers_with_timestamps,
)

from .supabase_client import (
    get_supabase_client,
    SupabaseAuthError,
    verify_user_token,
    get_user_profile,
    get_user_positions,
    create_position,
    delete_position,
    get_user_theses,
    create_thesis,
    update_thesis,
    get_thesis_history,
)

__all__ = [
    # Database operations
    "init_db",
    "save_analysis",
    "get_latest_analysis",
    "delete_cached_analysis",
    "get_all_cached_tickers",
    "get_all_cached_tickers_with_timestamps",
    # Supabase client
    "get_supabase_client",
    "SupabaseAuthError",
    "verify_user_token",
    "get_user_profile",
    "get_user_positions",
    "create_position",
    "delete_position",
    "get_user_theses",
    "create_thesis",
    "update_thesis",
    "get_thesis_history",
]
