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
    # Stage 4: Analysis-Thesis Linkage
    origin_analysis_id: Optional[int] = Field(None, description="SQLite cache ID of the analysis that informed this thesis")
    origin_analysis_snapshot: Optional[dict] = Field(None, description="Snapshot of key analysis metrics at thesis creation")


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
    origin_analysis_id: Optional[int] = None
    origin_analysis_snapshot: Optional[dict] = None
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


@router.get("/theses/{thesis_id}/compare")
async def compare_thesis_with_current(thesis_id: str, user = Depends(get_current_user)):
    """
    Compare thesis origin analysis with current analysis for the same ticker.
    
    Returns diff showing what has changed since thesis was created.
    Stage 4: Analysis-Thesis Linkage
    """
    from .supabase_client import get_supabase_client
    from .database import get_latest_analysis
    
    try:
        client = get_supabase_client()
        client.postgrest.auth(user["access_token"])
        
        # Get the thesis with its origin snapshot
        response = client.table("theses").select("*").eq("id", thesis_id).eq("user_id", user["id"]).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Thesis not found")
        
        thesis = response.data
        ticker = thesis["ticker"]
        origin_snapshot = thesis.get("origin_analysis_snapshot")
        
        if not origin_snapshot:
            return {
                "has_comparison": False,
                "message": "No origin analysis linked to this thesis",
                "thesis_id": thesis_id,
                "ticker": ticker
            }
        
        # Get current analysis
        current_analysis = get_latest_analysis(ticker)
        
        if not current_analysis:
            return {
                "has_comparison": False,
                "message": f"No current analysis available for {ticker}",
                "thesis_id": thesis_id,
                "ticker": ticker,
                "origin_snapshot": origin_snapshot
            }
        
        # Compute diff
        diff = {
            "has_comparison": True,
            "thesis_id": thesis_id,
            "ticker": ticker,
            "thesis_created_at": thesis["created_at"],
            "origin": origin_snapshot,
            "current": {
                "sentiment": current_analysis.get("overall_sentiment", current_analysis.get("sentiment_report", "")[:50]),
                "confidence": current_analysis.get("overall_confidence", 0),
                "timestamp": current_analysis.get("timestamp"),
            },
            "changes": []
        }
        
        # Compare sentiment
        origin_sentiment = origin_snapshot.get("sentiment", "")
        current_sentiment = diff["current"]["sentiment"]
        if origin_sentiment != current_sentiment:
            diff["changes"].append({
                "field": "sentiment",
                "from": origin_sentiment,
                "to": current_sentiment,
                "direction": "changed"
            })
        
        # Compare confidence
        origin_confidence = origin_snapshot.get("confidence", 0)
        current_confidence = diff["current"]["confidence"]
        if abs(origin_confidence - current_confidence) > 0.1:
            direction = "increased" if current_confidence > origin_confidence else "decreased"
            diff["changes"].append({
                "field": "confidence",
                "from": origin_confidence,
                "to": current_confidence,
                "delta": round(current_confidence - origin_confidence, 2),
                "direction": direction
            })
        
        # Compare skeptic verdict if available
        origin_skeptic = origin_snapshot.get("skeptic_verdict", "")
        # Try to get skeptic from current analysis - may be in different formats
        
        diff["change_summary"] = f"{len(diff['changes'])} significant changes since thesis creation"
        
        return diff
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {e}")


# ============================================
# Kill Alerts Routes (Stage 4)
# ============================================

class AlertStatusUpdate(BaseModel):
    status: str  # pending, dismissed, acknowledged, acted
    user_action: Optional[str] = None


class KillAlertResponse(BaseModel):
    id: str
    thesis_id: str
    ticker: str
    triggered_criteria: str
    triggering_signal: str
    match_confidence: float
    analysis_sentiment: Optional[str] = None
    analysis_confidence: Optional[float] = None
    status: str
    created_at: str


@router.get("/kill-alerts")
async def list_kill_alerts(
    ticker: Optional[str] = None,
    status: str = "pending",
    user = Depends(get_current_user)
):
    """Get kill alerts for the current user."""
    from .kill_criteria_monitor import get_pending_alerts
    
    # For now, get_pending_alerts only gets pending; we could extend this
    alerts = get_pending_alerts(user["id"], user["access_token"], ticker)
    
    # Filter by status if not pending
    if status != "pending":
        # Need to fetch all and filter (or extend the query function)
        pass
    
    return {"alerts": alerts, "count": len(alerts)}


@router.get("/kill-alerts/{alert_id}")
async def get_kill_alert(alert_id: str, user = Depends(get_current_user)):
    """Get a specific kill alert."""
    from .supabase_client import get_supabase_client
    
    try:
        client = get_supabase_client()
        client.postgrest.auth(user["access_token"])
        
        response = client.table("kill_alerts").select("*").eq("id", alert_id).eq("user_id", user["id"]).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return response.data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Alert not found: {e}")


@router.patch("/kill-alerts/{alert_id}")
async def update_kill_alert(
    alert_id: str,
    update: AlertStatusUpdate,
    user = Depends(get_current_user)
):
    """Update a kill alert status (dismiss, acknowledge, or mark as acted upon)."""
    from .kill_criteria_monitor import update_alert_status
    
    valid_statuses = ["pending", "dismissed", "acknowledged", "acted"]
    if update.status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    success = update_alert_status(
        user["id"],
        user["access_token"],
        alert_id,
        update.status,
        update.user_action
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found or update failed")
    
    return {"message": "Alert updated successfully", "status": update.status}


@router.delete("/kill-alerts/{alert_id}")
async def delete_kill_alert(alert_id: str, user = Depends(get_current_user)):
    """Delete a kill alert."""
    from .supabase_client import get_supabase_client
    
    try:
        client = get_supabase_client()
        client.postgrest.auth(user["access_token"])
        
        client.table("kill_alerts").delete().eq("id", alert_id).eq("user_id", user["id"]).execute()
        return {"message": "Alert deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete alert: {e}")

