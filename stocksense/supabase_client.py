"""
Supabase client and authentication utilities.

Stage 3: User Belief System
"""

import os
from functools import lru_cache
from typing import Optional, Dict, Any

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class SupabaseAuthError(Exception):
    """Custom exception for Supabase auth errors."""
    pass


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Get a cached Supabase client instance.
    
    Uses the anon/publishable key for client-safe operations.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise SupabaseAuthError(
            "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_ANON_KEY in .env"
        )
    
    return create_client(url, key)


def get_supabase_admin_client() -> Client:
    """
    Get a Supabase client with service role (admin) privileges.
    
    Use only for server-side operations that need to bypass RLS.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        raise SupabaseAuthError(
            "Missing Supabase admin credentials. Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env"
        )
    
    return create_client(url, key)


def verify_user_token(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a user's JWT access token and return user info.
    
    Args:
        access_token: The JWT from the Authorization header
        
    Returns:
        User data dict if valid, None if invalid
    """
    try:
        client = get_supabase_client()
        # Get user from token
        user_response = client.auth.get_user(access_token)
        
        if user_response and user_response.user:
            return {
                "id": str(user_response.user.id),
                "email": user_response.user.email,
                "created_at": str(user_response.user.created_at) if user_response.user.created_at else None,
            }
        return None
    except Exception as e:
        print(f"Token verification error: {e}")
        return None


def get_user_profile(user_id: str, access_token: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile from profiles table.
    
    Args:
        user_id: The user's UUID
        access_token: User's JWT for RLS
        
    Returns:
        Profile data or None
    """
    try:
        client = get_supabase_client()
        # Set auth header for RLS
        client.postgrest.auth(access_token)
        
        response = client.table("profiles").select("*").eq("id", user_id).single().execute()
        return response.data
    except Exception as e:
        print(f"Profile fetch error: {e}")
        return None


# ============================================
# Position Operations
# ============================================

def get_user_positions(user_id: str, access_token: str) -> list:
    """Get all positions for a user."""
    try:
        client = get_supabase_client()
        client.postgrest.auth(access_token)
        
        response = client.table("positions").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Positions fetch error: {e}")
        return []


def create_position(user_id: str, access_token: str, position_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new position for a user."""
    try:
        client = get_supabase_client()
        client.postgrest.auth(access_token)
        
        data = {
            "user_id": user_id,
            "ticker": position_data["ticker"].upper(),
            "position_type": position_data.get("position_type", "watching"),
            "entry_date": position_data.get("entry_date"),
            "entry_price": position_data.get("entry_price"),
            "current_shares": position_data.get("current_shares"),
            "notes": position_data.get("notes"),
        }
        
        response = client.table("positions").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Position create error: {e}")
        return None


def delete_position(user_id: str, access_token: str, position_id: str) -> bool:
    """Delete a position."""
    try:
        client = get_supabase_client()
        client.postgrest.auth(access_token)
        
        client.table("positions").delete().eq("id", position_id).eq("user_id", user_id).execute()
        return True
    except Exception as e:
        print(f"Position delete error: {e}")
        return False


# ============================================
# Thesis Operations
# ============================================

def get_user_theses(user_id: str, access_token: str, ticker: Optional[str] = None) -> list:
    """Get theses for a user, optionally filtered by ticker."""
    try:
        client = get_supabase_client()
        client.postgrest.auth(access_token)
        
        query = client.table("theses").select("*").eq("user_id", user_id)
        if ticker:
            query = query.eq("ticker", ticker.upper())
        
        response = query.order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Theses fetch error: {e}")
        return []


def create_thesis(user_id: str, access_token: str, thesis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new thesis with kill criteria."""
    try:
        client = get_supabase_client()
        client.postgrest.auth(access_token)
        
        data = {
            "user_id": user_id,
            "ticker": thesis_data["ticker"].upper(),
            "position_id": thesis_data.get("position_id"),
            "thesis_summary": thesis_data["thesis_summary"],
            "conviction_level": thesis_data.get("conviction_level", "medium"),
            "kill_criteria": thesis_data.get("kill_criteria", []),
            "time_horizon": thesis_data.get("time_horizon", "medium"),
            "thesis_type": thesis_data.get("thesis_type", "growth"),
            "status": "active",
        }
        
        response = client.table("theses").insert(data).execute()
        thesis = response.data[0] if response.data else None
        
        # Create history entry
        if thesis:
            _create_thesis_history(user_id, access_token, thesis["id"], thesis, "created")
        
        return thesis
    except Exception as e:
        print(f"Thesis create error: {e}")
        return None


def update_thesis(user_id: str, access_token: str, thesis_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a thesis and log history."""
    try:
        client = get_supabase_client()
        client.postgrest.auth(access_token)
        
        # Get current thesis for history
        current = client.table("theses").select("*").eq("id", thesis_id).single().execute()
        
        # Determine change type
        change_type = "updated"
        if "conviction_level" in updates and updates["conviction_level"] != current.data.get("conviction_level"):
            change_type = "conviction_changed"
        if updates.get("status") == "invalidated":
            change_type = "invalidated"
        if updates.get("status") == "exited":
            change_type = "exited"
        
        # Update thesis
        response = client.table("theses").update(updates).eq("id", thesis_id).eq("user_id", user_id).execute()
        thesis = response.data[0] if response.data else None
        
        # Create history entry
        if thesis:
            _create_thesis_history(
                user_id, access_token, thesis_id, thesis, 
                change_type, updates.get("change_reason")
            )
        
        return thesis
    except Exception as e:
        print(f"Thesis update error: {e}")
        return None


def _create_thesis_history(
    user_id: str, 
    access_token: str, 
    thesis_id: str, 
    thesis: Dict[str, Any],
    change_type: str,
    change_reason: Optional[str] = None
) -> None:
    """Create a thesis history entry."""
    try:
        client = get_supabase_client()
        client.postgrest.auth(access_token)
        
        data = {
            "thesis_id": thesis_id,
            "user_id": user_id,
            "thesis_summary": thesis["thesis_summary"],
            "conviction_level": thesis.get("conviction_level"),
            "kill_criteria": thesis.get("kill_criteria"),
            "change_type": change_type,
            "change_reason": change_reason,
        }
        
        client.table("thesis_history").insert(data).execute()
    except Exception as e:
        print(f"Thesis history error: {e}")


def get_thesis_history(user_id: str, access_token: str, thesis_id: str) -> list:
    """Get history for a specific thesis."""
    try:
        client = get_supabase_client()
        client.postgrest.auth(access_token)
        
        response = client.table("thesis_history").select("*").eq("thesis_id", thesis_id).eq("user_id", user_id).order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Thesis history fetch error: {e}")
        return []
