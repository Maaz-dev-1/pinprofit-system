"""
Supabase Client — Central connection to Supabase PostgreSQL + Storage.
Handles retries, connection pooling, and write queue for resilience.
"""
import os
import time
import json
import logging
import asyncio
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_supabase_client = None
_write_queue: list[dict] = []  # In-memory queue for failed writes

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")


def get_supabase():
    """Get or create Supabase client singleton."""
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL", SUPABASE_URL)
        key = os.getenv("SUPABASE_SERVICE_KEY", SUPABASE_SERVICE_KEY)
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        from supabase import create_client
        _supabase_client = create_client(url, key)
        logger.info("Supabase client initialized.")
    return _supabase_client


def reset_client():
    """Force-reset the client (e.g. after credential change)."""
    global _supabase_client
    _supabase_client = None


# ── Retry Helper ──────────────────────────────

def with_retry(fn, max_retries=3, backoff_times=(5, 15, 45)):
    """Execute a supabase operation with exponential backoff."""
    last_err = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            last_err = e
            wait = backoff_times[attempt] if attempt < len(backoff_times) else 45
            logger.warning(f"Supabase operation failed (attempt {attempt+1}): {e}. Retrying in {wait}s...")
            time.sleep(wait)
    logger.error(f"Supabase operation failed after {max_retries} retries: {last_err}")
    raise last_err


# ── Write Queue (for resilience) ──────────────

def queue_write(table: str, operation: str, data: dict):
    """Queue a write operation if Supabase is unreachable."""
    _write_queue.append({
        "table": table,
        "operation": operation,
        "data": data,
        "queued_at": datetime.now(timezone.utc).isoformat(),
    })
    logger.warning(f"Queued {operation} to {table} — will retry. Queue size: {len(_write_queue)}")


async def flush_write_queue():
    """Retry all queued writes. Called periodically by scheduler."""
    if not _write_queue:
        return
    logger.info(f"Flushing {len(_write_queue)} queued writes...")
    failed = []
    sb = get_supabase()
    for item in _write_queue:
        try:
            table = sb.table(item["table"])
            if item["operation"] == "insert":
                table.insert(item["data"]).execute()
            elif item["operation"] == "upsert":
                table.upsert(item["data"]).execute()
            elif item["operation"] == "update":
                # data must have an "id" or "key" field for the match
                match_key = item["data"].pop("_match_key", "id")
                match_val = item["data"].pop("_match_val", None)
                if match_val:
                    table.update(item["data"]).eq(match_key, match_val).execute()
        except Exception as e:
            logger.warning(f"Queue flush failed for {item['table']}: {e}")
            failed.append(item)
    _write_queue.clear()
    _write_queue.extend(failed)
    if failed:
        logger.warning(f"{len(failed)} writes still queued.")
    else:
        logger.info("Write queue flushed successfully.")


# ── Supabase Storage Helper ───────────────────

def supabase_storage():
    """Get the storage client for file uploads."""
    return get_supabase().storage


# ── Connection Test ───────────────────────────

def test_connection() -> tuple[bool, str]:
    """Test Supabase connectivity."""
    try:
        sb = get_supabase()
        result = sb.table("settings").select("key").limit(1).execute()
        return True, "Supabase connected successfully"
    except Exception as e:
        return False, f"Supabase connection failed: {str(e)}"
