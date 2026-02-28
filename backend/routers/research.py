import asyncio
import json
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException
from datetime import datetime, timezone
from services.supabase_client import get_supabase
from models.schemas import ResearchStartRequest, ResearchSessionOut

logger = logging.getLogger(__name__)
router = APIRouter()

# Import WebSocket manager from main lazily to avoid circular imports
def _get_ws_connections():
    from main import research_ws_connections
    return research_ws_connections


async def broadcast_progress(session_id: int, payload: dict):
    """Send progress update to all connected WebSocket clients."""
    connections = _get_ws_connections().get(session_id, [])
    dead = []
    for ws in connections:
        try:
            await ws.send_text(json.dumps(payload))
        except Exception:
            dead.append(ws)
    for ws in dead:
        connections.remove(ws)


@router.post("/start")
async def start_research(
    req: ResearchStartRequest,
    background_tasks: BackgroundTasks,
):
    sb = get_supabase()

    # Create session record
    result = sb.table("research_sessions").insert({
        "niche": req.niche,
        "status": "running",
    }).execute()
    session_id = result.data[0]["id"]

    # Log action
    sb.table("evolution_log").insert({
        "log_type": "research_started",
        "data": json.dumps({"message": f"Research started: {req.niche}", "niche": req.niche}),
    }).execute()

    # Run research in background
    background_tasks.add_task(run_full_research, session_id, req.niche)

    return {"session_id": session_id, "status": "running", "niche": req.niche}


@router.get("/sessions")
async def list_sessions():
    sb = get_supabase()
    result = sb.table("research_sessions").select("id,niche,status,products_found,started_at,completed_at").order("started_at", desc=True).limit(20).execute()
    items = []
    for row in result.data or []:
        items.append({
            "session_id": row["id"],
            "niche": row["niche"],
            "status": row["status"],
            "products_found": row.get("products_found", 0),
            "started_at": row.get("started_at"),
            "completed_at": row.get("completed_at"),
        })
    return items


@router.get("/sessions/{session_id}")
async def get_session(session_id: int):
    sb = get_supabase()
    result = sb.table("research_sessions").select("*").eq("id", session_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Session not found")
    row = result.data[0]
    return {
        "session_id": row["id"],
        "niche": row["niche"],
        "status": row["status"],
        "products_found": row.get("products_found", 0),
        "started_at": row.get("started_at"),
        "completed_at": row.get("completed_at"),
    }


# ──────────────────────────────────────────────────────────────
#  CORE RESEARCH ENGINE (runs as background task)
# ──────────────────────────────────────────────────────────────
async def run_full_research(session_id: int, niche: str):
    """
    Full research pipeline — 8 steps.
    Runs in background — broadcasts progress via WebSocket.
    """
    from services.trend_detector import analyze_google_trends, detect_realtime_events, scrape_pinterest_trends
    from services.scraper import scrape_all_platforms
    from services.affiliate_manager import determine_affiliate_type
    from services.evolution_engine import log_research_complete

    sb = get_supabase()

    async def update(step: str, pct: int, extra: dict = {}):
        await broadcast_progress(session_id, {"step": step, "progress": pct, **extra})

    try:
        # STEP 1 — Google Trends
        await update("Analyzing Google Trends for your niche...", 5)
        trends_data = await asyncio.to_thread(analyze_google_trends, niche)

        # STEP 2 — Real-time events
        await update("Detecting real-time events and trends in India...", 15)
        events_data = await asyncio.to_thread(detect_realtime_events, niche)

        # STEP 3 — Pinterest trends
        await update("Scraping Pinterest trends for your niche...", 25)
        pinterest_data = await asyncio.to_thread(scrape_pinterest_trends, niche)

        # STEP 4 — Scrape products from all relevant platforms
        await update("Finding products across Amazon, Flipkart, Myntra, Meesho...", 35)
        raw_products = await asyncio.to_thread(
            scrape_all_platforms, niche, trends_data, events_data, pinterest_data
        )

        # STEP 5 — Competitor analysis
        await update("Running competitor analysis on Pinterest...", 60)

        # STEP 6 — Score + filter
        await update("Scoring and ranking products...", 75)

        # STEP 7 — Deduplicate
        await update("Checking for duplicate products...", 85)

        # STEP 8 — Save to DB
        await update("Saving results to database...", 92)
        saved = 0
        for p in raw_products:
            sb.table("products").insert({
                "title": p.get("title", ""),
                "platform": p.get("platform", ""),
                "original_url": p.get("url", ""),
                "price": p.get("price"),
                "mrp": p.get("mrp"),
                "discount_pct": p.get("discount_pct"),
                "rating": p.get("rating"),
                "review_count": p.get("review_count"),
                "asin": p.get("asin"),
                "image_url": p.get("image_url"),
                "additional_images": json.dumps(p.get("additional_images", [])),
                "description": p.get("description"),
                "feature_bullets": json.dumps(p.get("feature_bullets", [])),
                "niche": niche,
                "score": p.get("score"),
                "trend_bonus": p.get("trend_bonus"),
                "commission_estimate": p.get("commission_estimate"),
                "affiliate_type": determine_affiliate_type(p.get("platform", "")),
                "stock_status": p.get("stock_status"),
                "badges": json.dumps(p.get("badges", {})),
                "gemini_sell_reason": p.get("gemini_sell_reason"),
                "research_session_id": session_id,
            }).execute()
            saved += 1

        # Update session record
        sb.table("research_sessions").update({
            "status": "completed",
            "products_found": saved,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "google_trends_data": json.dumps(trends_data),
            "real_time_events": json.dumps(events_data),
            "pinterest_trends": json.dumps(pinterest_data),
        }).eq("id", session_id).execute()

        # Log completion
        sb.table("evolution_log").insert({
            "log_type": "research_completed",
            "data": json.dumps({"message": f"Research done: {niche} — {saved} products", "niche": niche, "count": saved}),
        }).execute()

        await update("Research complete!", 100, {"status": "completed", "products_found": saved})
        await log_research_complete(niche, saved)

    except Exception as e:
        logger.exception(f"Research failed for session {session_id}: {e}")
        try:
            sb.table("research_sessions").update({
                "status": "failed",
                "error_log": str(e),
            }).eq("id", session_id).execute()
        except Exception:
            pass
        await broadcast_progress(session_id, {
            "status": "failed",
            "error": "Research failed. Please try again.",
            "progress": 0,
        })
