from fastapi import APIRouter
from services.supabase_client import get_supabase

router = APIRouter()


@router.get("/summary")
async def evolution_summary():
    sb = get_supabase()
    try:
        # Strategy memory
        mem_r = sb.table("evolution_strategy_memory").select("key,value").execute()
        memory = {row["key"]: row.get("value") for row in mem_r.data or []}

        # Learning history — latest 20 entries
        hist_r = sb.table("evolution_learning_history").select("*").order("created_at", desc=True).limit(20).execute()
        history = {"nightly_runs": hist_r.data or []}

        return {"memory": memory, "history": history}
    except Exception:
        return {"memory": {}, "history": {}}
