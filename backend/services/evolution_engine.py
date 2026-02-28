"""
Evolution Engine — The learning brain of PinProfit.
Logs every action. Runs nightly analysis.
Gets smarter every day. All data stored in Supabase.
"""
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _sb():
    from services.supabase_client import get_supabase
    return get_supabase()


async def log_research_complete(niche: str, products_found: int):
    try:
        _sb().table("evolution_performance_log").insert({
            "event_type": "research_complete",
            "data": json.dumps({
                "niche": niche,
                "products_found": products_found,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }),
        }).execute()
    except Exception as e:
        logger.warning(f"Could not log research completion: {e}")


async def log_pin_approved(pin_id: int, niche: str, content: dict):
    try:
        _sb().table("evolution_performance_log").insert({
            "event_type": "pin_approved",
            "data": json.dumps({
                "pin_id": pin_id,
                "niche": niche,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }),
        }).execute()
    except Exception as e:
        logger.warning(f"Could not log pin approval: {e}")


async def log_pin_skipped(pin_id: int, reason: str):
    try:
        _sb().table("evolution_performance_log").insert({
            "event_type": "pin_skipped",
            "data": json.dumps({
                "pin_id": pin_id,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }),
        }).execute()
    except Exception as e:
        logger.warning(f"Could not log pin skip: {e}")


async def run_nightly_analysis():
    """
    Runs every night at 3 AM IST.
    Analyzes all performance data from Supabase.
    Updates strategy_memory and learning_history tables.
    """
    logger.info("Starting nightly evolution analysis...")

    sb = _sb()

    try:
        # Read performance events
        r = sb.table("evolution_performance_log").select("*").eq("event_type", "research_complete").execute()
        research_events = r.data or []

        # Analyze top niches
        niche_counts = {}
        for event in research_events:
            try:
                data = json.loads(event.get("data", "{}")) if isinstance(event.get("data"), str) else event.get("data", {})
                niche = data.get("niche", "unknown")
                niche_counts[niche] = niche_counts.get(niche, 0) + 1
            except Exception:
                pass

        top_niches = sorted(niche_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Upsert strategy memory
        sb.table("evolution_strategy_memory").upsert({
            "key": "top_niches",
            "value": json.dumps(top_niches),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

        sb.table("evolution_strategy_memory").upsert({
            "key": "last_updated",
            "value": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

        # Add learning history entry
        insights = f"Analyzed {len(research_events)} research sessions. Top niche: {top_niches[0][0] if top_niches else 'N/A'}"
        sb.table("evolution_learning_history").insert({
            "date": datetime.now(timezone.utc).isoformat(),
            "research_sessions": len(research_events),
            "insights": insights,
        }).execute()

        logger.info("Nightly evolution analysis complete.")
        return {"top_niches": top_niches}

    except Exception as e:
        logger.error(f"Nightly evolution analysis failed: {e}")
        return {}
