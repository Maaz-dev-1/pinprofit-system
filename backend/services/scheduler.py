"""
Background Scheduler — All automated tasks.
Uses APScheduler for all scheduled jobs.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


async def start_scheduler():
    """Register all background tasks and start scheduler."""

    # 1. Pin publisher — every minute
    scheduler.add_job(
        _publish_due_pins,
        trigger="interval",
        minutes=1,
        id="pin_publisher",
        replace_existing=True,
    )

    # 2. Analytics sync — every 6 hours
    scheduler.add_job(
        _sync_analytics,
        trigger="interval",
        hours=6,
        id="analytics_sync",
        replace_existing=True,
    )

    # 3. Competitor analysis — every Monday 6 AM IST
    scheduler.add_job(
        _run_competitor_analysis,
        trigger=CronTrigger(day_of_week="mon", hour=6, minute=0),
        id="competitor_analysis",
        replace_existing=True,
    )

    # 4. Nightly evolution — every night 3 AM IST
    scheduler.add_job(
        _run_nightly_evolution,
        trigger=CronTrigger(hour=3, minute=0),
        id="nightly_evolution",
        replace_existing=True,
    )

    # 5. Weekly report — Sunday 8 PM IST
    scheduler.add_job(
        _generate_weekly_report,
        trigger=CronTrigger(day_of_week="sun", hour=20, minute=0),
        id="weekly_report",
        replace_existing=True,
    )

    # 6. Storage cleanup — every night 2 AM IST
    scheduler.add_job(
        _cleanup_storage,
        trigger=CronTrigger(hour=2, minute=0),
        id="storage_cleanup",
        replace_existing=True,
    )

    # 7. Trend alerts — every 6 hours
    scheduler.add_job(
        _check_trend_alerts,
        trigger="interval",
        hours=6,
        id="trend_alerts",
        replace_existing=True,
    )

    # 8. Token health check — every 6 hours
    scheduler.add_job(
        _check_token_health,
        trigger="interval",
        hours=6,
        id="token_health",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with all 8 jobs.")


async def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")


# ────────────────────────────────────────────────
# JOB HANDLERS (stubs — will be fully implemented
# in their respective phases)
# ────────────────────────────────────────────────
async def _publish_due_pins():
    """Post scheduled pins to Pinterest + Instagram. Phase 5."""
    pass


async def _sync_analytics():
    """Fetch latest analytics from Pinterest/Instagram APIs. Phase 6."""
    pass


async def _run_competitor_analysis():
    """Scrape competitor Pinterest accounts. Phase 3."""
    pass


async def _run_nightly_evolution():
    """Run evolution engine analysis. Phase 7."""
    from services.evolution_engine import run_nightly_analysis
    try:
        await run_nightly_analysis()
    except Exception as e:
        logger.error(f"Nightly evolution failed: {e}")


async def _generate_weekly_report():
    """Generate and email weekly report. Phase 6."""
    pass


async def _cleanup_storage():
    """Delete old pin images from Supabase Storage (>7 days). Runs at 2 AM IST."""
    from services.storage_manager import delete_old_images
    try:
        count, msg = await delete_old_images(days=7)
        logger.info(f"Storage cleanup: {msg}")
    except Exception as e:
        logger.error(f"Storage cleanup failed: {e}")
        # Send email alert on failure
        try:
            from models.database import get_setting_sync
            from services.email_service import send_email, _base_template
            gmail = get_setting_sync("gmail_address")
            pwd = get_setting_sync("gmail_app_password")
            if gmail and pwd:
                await send_email(gmail, pwd, gmail,
                    "⚠️ PinProfit: Storage Cleanup Failed",
                    _base_template("Storage Cleanup Failed", f"<p>Error: {str(e)[:200]}</p>"),
                )
        except Exception:
            pass

    # Also flush any queued writes
    try:
        from services.supabase_client import flush_write_queue
        await flush_write_queue()
    except Exception as e:
        logger.warning(f"Write queue flush failed: {e}")


async def _check_trend_alerts():
    """Check for sudden trend spikes and notify. Phase 3."""
    pass


async def _check_token_health():
    """Check token expiry, refresh if needed, monitor usage. Phase 2."""
    from services.token_manager import check_all_tokens
    try:
        await check_all_tokens()
    except Exception as e:
        logger.error(f"Token health check failed: {e}")
