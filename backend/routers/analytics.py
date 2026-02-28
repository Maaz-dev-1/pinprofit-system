from fastapi import APIRouter
from services.supabase_client import get_supabase

router = APIRouter()


@router.get("/overview")
async def overview():
    sb = get_supabase()
    try:
        r = sb.table("published_pins").select(
            "pinterest_clicks,instagram_clicks,pinterest_saves,estimated_commission"
        ).eq("status", "posted").execute()

        total_pins = len(r.data or [])
        total_clicks = 0
        total_saves = 0
        total_commission = 0.0

        for row in r.data or []:
            total_clicks += (row.get("pinterest_clicks") or 0) + (row.get("instagram_clicks") or 0)
            total_saves += row.get("pinterest_saves") or 0
            total_commission += row.get("estimated_commission") or 0

        return {
            "total_pins":       total_pins,
            "total_clicks":     total_clicks,
            "total_saves":      total_saves,
            "total_commission": round(total_commission, 2),
        }
    except Exception:
        return {"total_pins": 0, "total_clicks": 0, "total_saves": 0, "total_commission": 0}
