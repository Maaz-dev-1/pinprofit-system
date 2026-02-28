"""Storage Manager — Supabase Storage for pin images."""
import os
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


async def upload_pin_image(file_bytes: bytes, filename: str, content_type: str = "image/jpeg") -> tuple[str | None, str]:
    """Upload image to Supabase Storage pin-images bucket. Returns (url, error_message)."""
    try:
        from services.supabase_client import get_supabase
        sb = get_supabase()
        storage = sb.storage.from_("pin-images")
        storage.upload(
            path=filename,
            file=file_bytes,
            file_options={"content-type": content_type},
        )
        project_ref = os.getenv("SUPABASE_URL", "").replace("https://", "").split(".")[0]
        public_url = f"https://{project_ref}.supabase.co/storage/v1/object/public/pin-images/{filename}"
        return public_url, "ok"
    except Exception as e:
        logger.error(f"Supabase Storage upload failed: {e}")
        return None, str(e)


async def delete_old_images(days: int = 7) -> tuple[int, str]:
    """Delete images older than `days` from Supabase Storage. Returns (count_deleted, message)."""
    try:
        from services.supabase_client import get_supabase
        sb = get_supabase()
        storage = sb.storage.from_("pin-images")
        files = storage.list()

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        deleted = 0

        for f in files:
            created = f.get("created_at") or f.get("updated_at")
            if created:
                try:
                    file_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if file_dt < cutoff:
                        storage.remove([f["name"]])
                        deleted += 1
                except Exception:
                    pass

        msg = f"Deleted {deleted} images older than {days} days."
        logger.info(msg)
        return deleted, msg
    except Exception as e:
        logger.error(f"Image cleanup failed: {e}")
        return 0, str(e)


async def get_storage_usage() -> dict:
    """Get Supabase Storage usage stats."""
    try:
        from services.supabase_client import get_supabase
        sb = get_supabase()
        storage = sb.storage.from_("pin-images")
        files = storage.list()

        total_bytes = sum(f.get("metadata", {}).get("size", 0) for f in files if f.get("metadata"))
        total_mb = round(total_bytes / (1024 * 1024), 2)
        file_count = len(files)

        return {
            "total_mb": total_mb,
            "file_count": file_count,
            "limit_mb": 1024,  # 1GB free tier
            "usage_pct": round((total_mb / 1024) * 100, 1),
        }
    except Exception as e:
        logger.error(f"Could not get storage usage: {e}")
        return {"total_mb": 0, "file_count": 0, "limit_mb": 1024, "usage_pct": 0}
