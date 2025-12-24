"""
Authentication and user data API routes.

Stage 3: User Belief System
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field

from .supabase_client import (
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

router = APIRouter(prefix="/api", tags=["User"])


# ============================================
# Request/Response Models
# ============================================

class UserResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class PositionCreate(BaseModel):
    ticker: str
    position_type: str = "watching"  # long, short, watching
    entry_date: Optional[str] = None
    entry_price: Optional[float] = None
    current_shares: Optional[float] = None
    notes: Optional[str] = None


class PositionResponse(BaseModel):
    id: str
    ticker: str
    position_type: str
    entry_date: Optional[str] = None
    entry_price: Optional[float] = None
    current_shares: Optional[float] = None
    notes: Optional[str] = None
    created_at: str


class ThesisCreate(BaseModel):
    ticker: str
    thesis_summary: str = Field(..., min_length=10, description="Why you own/want to own this")
    conviction_level: str = "medium"  # high, medium, low
    kill_criteria: List[str] = Field(default_factory=list, description="Conditions that would trigger exit")
    time_horizon: str = "medium"  # short, medium, long
    thesis_type: str = "growth"  # growth, value, income, turnaround, special_situation
    position_id: Optional[str] = None


class ThesisUpdate(BaseModel):
    thesis_summary: Optional[str] = None
    conviction_level: Optional[str] = None
    kill_criteria: Optional[List[str]] = None
    status: Optional[str] = None  # active, validated, invalidated, exited
    invalidation_reason: Optional[str] = None
    change_reason: Optional[str] = None


class ThesisResponse(BaseModel):
    id: str
    ticker: str
    thesis_summary: str
    conviction_level: str
    kill_criteria: List[str]
    time_horizon: str
    thesis_type: str
    status: str
    created_at: str
    updated_at: str


# ============================================
# Auth Dependency
# ============================================

async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Extract and verify user from Authorization header.
    
    Expected format: "Bearer <access_token>"
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format. Use: Bearer <token>")
    
    access_token = parts[1]
    user = verify_user_token(access_token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Attach token for downstream RLS operations
    user["access_token"] = access_token
    return user


# ============================================
# User Routes
# ============================================

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user = Depends(get_current_user)):
    """Get the current user's profile."""
    profile = get_user_profile(user["id"], user["access_token"])
    
    if not profile:
        # Profile might not exist yet, return basic info
        return UserResponse(
            id=user["id"],
            email=user["email"],
            display_name=user["email"].split("@")[0] if user["email"] else None,
        )
    
    return UserResponse(
        id=profile["id"],
        email=profile.get("email") or user["email"],
        display_name=profile.get("display_name"),
        avatar_url=profile.get("avatar_url"),
    )


# ============================================
# Position Routes
# ============================================

@router.get("/positions")
async def list_positions(user = Depends(get_current_user)):
    """Get all positions for the current user."""
    positions = get_user_positions(user["id"], user["access_token"])
    return {"positions": positions, "count": len(positions)}


@router.post("/positions", response_model=PositionResponse)
async def add_position(position: PositionCreate, user = Depends(get_current_user)):
    """Add a new position to track."""
    result = create_position(user["id"], user["access_token"], position.model_dump())
    
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create position. Ticker may already exist.")
    
    return result


@router.delete("/positions/{position_id}")
async def remove_position(position_id: str, user = Depends(get_current_user)):
    """Remove a position."""
    success = delete_position(user["id"], user["access_token"], position_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Position not found or already deleted")
    
    return {"message": "Position deleted successfully"}


# ============================================
# Thesis Routes
# ============================================

@router.get("/theses")
async def list_theses(ticker: Optional[str] = None, user = Depends(get_current_user)):
    """Get all theses, optionally filtered by ticker."""
    theses = get_user_theses(user["id"], user["access_token"], ticker)
    return {"theses": theses, "count": len(theses)}


@router.post("/theses", response_model=ThesisResponse)
async def add_thesis(thesis: ThesisCreate, user = Depends(get_current_user)):
    """Create a new investment thesis with kill criteria."""
    result = create_thesis(user["id"], user["access_token"], thesis.model_dump())
    
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create thesis")
    
    return result


@router.patch("/theses/{thesis_id}", response_model=ThesisResponse)
async def modify_thesis(thesis_id: str, updates: ThesisUpdate, user = Depends(get_current_user)):
    """Update a thesis. Changes are tracked in history."""
    # Filter out None values
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    result = update_thesis(user["id"], user["access_token"], thesis_id, update_data)
    
    if not result:
        raise HTTPException(status_code=404, detail="Thesis not found")
    
    return result


@router.get("/theses/{thesis_id}/history")
async def get_thesis_evolution(thesis_id: str, user = Depends(get_current_user)):
    """Get the history of changes for a thesis (belief evolution)."""
    history = get_thesis_history(user["id"], user["access_token"], thesis_id)
    return {"history": history, "count": len(history)}
