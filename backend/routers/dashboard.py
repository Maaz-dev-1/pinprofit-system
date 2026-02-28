from fastapi import APIRouter
from datetime import datetime, timezone, timedelta
from services.supabase_client import get_supabase
from models.schemas import DashboardStats, ActivityOut, ActivityItem
import json

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_stats():
    sb = get_supabase()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Pins posted today
    try:
        r = sb.table("published_pins").select("id", count="exact").eq("status", "posted").gte("posted_at", f"{today}T00:00:00Z").execute()
        pins_today = r.count or 0
    except Exception:
        pins_today = 0

    # Total clicks + commission + pending
    try:
        r = sb.table("published_pins").select("pinterest_clicks,instagram_clicks,estimated_commission,status").execute()
        total_clicks = 0
        commission = 0.0
        pending = 0
        for row in r.data or []:
            if row.get("status") == "posted":
                total_clicks += (row.get("pinterest_clicks") or 0) + (row.get("instagram_clicks") or 0)
                commission += row.get("estimated_commission") or 0
            if row.get("status") == "pending":
                pending += 1
    except Exception:
        total_clicks = 0
        commission = 0.0
        pending = 0

    return DashboardStats(
        pins_today=pins_today,
        total_clicks=total_clicks,
        commission=round(commission, 2),
        pending=pending,
    )


@router.get("/activity", response_model=ActivityOut)
async def get_activity():
    sb = get_supabase()

    def _time_ago(dt_str):
        if not dt_str:
            return "—"
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            diff = datetime.now(timezone.utc) - dt
            if diff.seconds < 60:    return "Just now"
            if diff.seconds < 3600:  return f"{diff.seconds // 60}m ago"
            if diff.days < 1:        return f"{diff.seconds // 3600}h ago"
            return f"{diff.days}d ago"
        except Exception:
            return "—"

    try:
        r = sb.table("evolution_log").select("*").order("created_at", desc=True).limit(10).execute()
        items = []
        for i, log in enumerate(r.data or []):
            try:
                data = json.loads(log.get("data") or '{}')
                msg = data.get("message", log.get("log_type", "Event").replace("_", " ").title())
            except Exception:
                msg = log.get("log_type", "Event").replace("_", " ").title()
            items.append(ActivityItem(id=i + 1, message=msg, time=_time_ago(log.get("created_at"))))
    except Exception:
        items = []

    if not items:
        items = [ActivityItem(id=1, message="Welcome to PinProfit! Start by typing a niche below.", time="Just now")]

    return ActivityOut(items=items)
