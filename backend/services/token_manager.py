"""
Token Manager — Auto-refresh, health monitoring, and usage tracking.
All state stored in Supabase (evolution_strategy_memory table).
Replaces Cloudinary monitoring with Supabase Storage monitoring.
"""
import os
import json
import logging
from datetime import datetime, timezone, timedelta

import httpx

logger = logging.getLogger(__name__)


# ── State persistence in Supabase ─────────────

def _load_state() -> dict:
    """Load token health state from Supabase."""
    try:
        from services.supabase_client import get_supabase
        r = get_supabase().table("evolution_strategy_memory").select("value").eq("key", "_token_health_state").execute()
        if r.data:
            return json.loads(r.data[0]["value"])
    except Exception:
        pass
    return {}


def _save_state(state: dict):
    """Persist token health state to Supabase."""
    try:
        from services.supabase_client import get_supabase
        get_supabase().table("evolution_strategy_memory").upsert({
            "key": "_token_health_state",
            "value": json.dumps(state, default=str),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        logger.warning(f"Could not save token health state: {e}")


# ── System Health ─────────────────────────────

def get_system_health() -> dict:
    """Return health status for all 8 services (includes Supabase DB + Storage)."""
    from routers.settings_router import _get_setting
    state = _load_state()
    services = []

    # 1. Supabase Database
    try:
        from services.supabase_client import test_connection
        ok, _ = test_connection()
        if ok:
            services.append({"service": "supabase_db", "label": "Supabase Database", "status": "green", "message": "Connected", "icon": "🗄️"})
        else:
            services.append({"service": "supabase_db", "label": "Supabase Database", "status": "red", "message": "Connection failed", "icon": "🗄️"})
    except Exception:
        services.append({"service": "supabase_db", "label": "Supabase Database", "status": "red", "message": "Unreachable", "icon": "🗄️"})

    # 2. Supabase Storage
    storage_usage = state.get("supabase_storage", {})
    storage_pct = storage_usage.get("usage_pct", 0)
    if storage_pct >= 90:
        services.append({"service": "supabase_storage", "label": "Supabase Storage", "status": "red", "message": f"Usage at {storage_pct}%", "icon": "📦", "usage_pct": storage_pct})
    elif storage_pct >= 80:
        services.append({"service": "supabase_storage", "label": "Supabase Storage", "status": "yellow", "message": f"Usage at {storage_pct}%", "icon": "📦", "usage_pct": storage_pct})
    else:
        services.append({"service": "supabase_storage", "label": "Supabase Storage", "status": "green", "message": f"Active ({storage_pct}% used)", "icon": "📦", "usage_pct": storage_pct})

    # 3. Gemini
    key = _get_setting("gemini_api_key")
    gemini_usage = state.get("gemini_daily_usage", 0)
    gemini_limit = 1500
    if not key:
        services.append({"service": "gemini", "label": "Gemini AI", "status": "grey", "message": "Not connected yet", "icon": "🤖"})
    elif gemini_usage >= gemini_limit:
        services.append({"service": "gemini", "label": "Gemini AI", "status": "red", "message": "Daily limit reached", "icon": "🤖", "usage_pct": 100})
    elif gemini_usage >= gemini_limit * 0.8:
        pct = int(gemini_usage / gemini_limit * 100)
        services.append({"service": "gemini", "label": "Gemini AI", "status": "yellow", "message": f"Usage at {pct}%", "icon": "🤖", "usage_pct": pct})
    else:
        pct = int(gemini_usage / gemini_limit * 100) if gemini_limit else 0
        services.append({"service": "gemini", "label": "Gemini AI", "status": "green", "message": f"Active ({100-pct}% left)", "icon": "🤖", "usage_pct": pct})

    # 4. Pinterest
    token = _get_setting("pinterest_access_token")
    pin_expiry = state.get("pinterest_token_expiry")
    if not token:
        services.append({"service": "pinterest", "label": "Pinterest", "status": "grey", "message": "Not connected yet", "icon": "📌"})
    elif pin_expiry:
        exp = datetime.fromisoformat(pin_expiry)
        days_left = (exp - datetime.now(timezone.utc)).days
        if days_left < 0:
            services.append({"service": "pinterest", "label": "Pinterest", "status": "red", "message": "Token expired", "icon": "📌"})
        elif days_left < 7:
            services.append({"service": "pinterest", "label": "Pinterest", "status": "yellow", "message": f"Expires in {days_left}d", "icon": "📌"})
        else:
            services.append({"service": "pinterest", "label": "Pinterest", "status": "green", "message": f"Active ({days_left}d left)", "icon": "📌"})
    else:
        last_check = state.get("pinterest_last_check_ok")
        if last_check:
            services.append({"service": "pinterest", "label": "Pinterest", "status": "green", "message": "Active", "icon": "📌"})
        else:
            services.append({"service": "pinterest", "label": "Pinterest", "status": "yellow", "message": "Token set — not verified", "icon": "📌"})

    # 5. Instagram
    ig_token = _get_setting("instagram_access_token")
    ig_refreshed = state.get("instagram_last_refreshed")
    if not ig_token:
        services.append({"service": "instagram", "label": "Instagram", "status": "grey", "message": "Not connected yet", "icon": "📸"})
    elif ig_refreshed:
        last = datetime.fromisoformat(ig_refreshed)
        days_since = (datetime.now(timezone.utc) - last).days
        days_left = 60 - days_since
        if days_left <= 0:
            services.append({"service": "instagram", "label": "Instagram", "status": "red", "message": "Token likely expired", "icon": "📸"})
        elif days_left <= 15:
            services.append({"service": "instagram", "label": "Instagram", "status": "yellow", "message": f"Expires in ~{days_left}d", "icon": "📸"})
        else:
            services.append({"service": "instagram", "label": "Instagram", "status": "green", "message": f"Active ({days_left}d left)", "icon": "📸"})
    else:
        services.append({"service": "instagram", "label": "Instagram", "status": "yellow", "message": "Token set — refresh pending", "icon": "📸"})

    # 6. Amazon
    amz_key = _get_setting("amazon_access_key")
    amz_fails = state.get("amazon_consecutive_failures", 0)
    if not amz_key:
        services.append({"service": "amazon", "label": "Amazon", "status": "grey", "message": "Not connected yet", "icon": "🟠"})
    elif amz_fails >= 3:
        services.append({"service": "amazon", "label": "Amazon", "status": "red", "message": f"API failing ({amz_fails}x)", "icon": "🟠"})
    else:
        services.append({"service": "amazon", "label": "Amazon", "status": "green", "message": "Active", "icon": "🟠"})

    # 7. Cuelinks
    cue_key = _get_setting("cuelinks_api_key")
    cue_fails = state.get("cuelinks_consecutive_failures", 0)
    if not cue_key:
        services.append({"service": "cuelinks", "label": "Cuelinks", "status": "grey", "message": "Not connected yet", "icon": "🔵"})
    elif cue_fails >= 3:
        services.append({"service": "cuelinks", "label": "Cuelinks", "status": "red", "message": "API failing", "icon": "🔵"})
    else:
        services.append({"service": "cuelinks", "label": "Cuelinks", "status": "green", "message": "Active", "icon": "🔵"})

    # 8. Gmail
    gmail = _get_setting("gmail_address")
    gmail_pwd = _get_setting("gmail_app_password")
    if not gmail or not gmail_pwd:
        services.append({"service": "email", "label": "Gmail", "status": "grey", "message": "Not connected yet", "icon": "📧"})
    else:
        gmail_ok = state.get("gmail_last_check_ok", False)
        if gmail_ok:
            services.append({"service": "email", "label": "Gmail", "status": "green", "message": "Active", "icon": "📧"})
        else:
            services.append({"service": "email", "label": "Gmail", "status": "yellow", "message": "Credentials set — not verified", "icon": "📧"})

    has_issues = any(s["status"] in ("red", "yellow") for s in services)
    return {"services": services, "has_issues": has_issues}


# ── Token Refresh Logic ──────────────────────

async def check_all_tokens():
    """Called every 6 hours by scheduler. Refreshes expiring tokens and monitors usage."""
    from routers.settings_router import _get_setting, _set_setting

    state = _load_state()

    # Reset daily Gemini usage at midnight
    today = datetime.now().strftime("%Y-%m-%d")
    if state.get("gemini_usage_date") != today:
        state["gemini_daily_usage"] = 0
        state["gemini_usage_date"] = today

    # ── Pinterest Token Check ──
    pin_token = _get_setting("pinterest_access_token")
    if pin_token:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    "https://api.pinterest.com/v5/user_account",
                    headers={"Authorization": f"Bearer {pin_token}"},
                )
                if r.status_code == 200:
                    state["pinterest_last_check_ok"] = True
                    logger.info("Pinterest token check: OK")
                elif r.status_code == 401:
                    refresh_token = _get_setting("pinterest_refresh_token")
                    app_id = _get_setting("pinterest_app_id")
                    app_secret = _get_setting("pinterest_app_secret")

                    if refresh_token and app_id and app_secret:
                        refreshed = await _refresh_pinterest_token(refresh_token, app_id, app_secret)
                        if refreshed:
                            _set_setting("pinterest_access_token", refreshed["access_token"])
                            if refreshed.get("refresh_token"):
                                _set_setting("pinterest_refresh_token", refreshed["refresh_token"])
                            state["pinterest_last_check_ok"] = True
                            logger.info("Pinterest token refreshed successfully!")
                        else:
                            state["pinterest_last_check_ok"] = False
                            await _send_token_alert("Pinterest",
                                "Pinterest token expired and refresh failed. Please reconnect in Settings → Pinterest.")
                    else:
                        state["pinterest_last_check_ok"] = False
                        await _send_token_alert("Pinterest",
                            "Pinterest token expired. Please reconnect in Settings → Pinterest.")
        except Exception as e:
            logger.error(f"Pinterest token check failed: {e}")

    # ── Instagram Token Refresh ──
    ig_token = _get_setting("instagram_access_token")
    if ig_token:
        last_refreshed = state.get("instagram_last_refreshed")
        should_refresh = False

        if not last_refreshed:
            state["instagram_last_refreshed"] = datetime.now(timezone.utc).isoformat()
        else:
            last = datetime.fromisoformat(last_refreshed)
            days_since = (datetime.now(timezone.utc) - last).days
            if days_since >= 45:
                should_refresh = True

        if should_refresh:
            new_token = await _refresh_instagram_token(ig_token)
            if new_token:
                _set_setting("instagram_access_token", new_token)
                state["instagram_last_refreshed"] = datetime.now(timezone.utc).isoformat()
                logger.info("Instagram token refreshed successfully!")
                await _send_token_alert("Instagram",
                    "Instagram token refreshed successfully. No action needed.", is_success=True)
            else:
                await _send_token_alert("Instagram",
                    "Instagram token refresh failed. Please reconnect in Settings → Instagram.")

    # ── Supabase Storage Usage Check ──
    try:
        from services.storage_manager import get_storage_usage
        usage = await get_storage_usage()
        state["supabase_storage"] = usage
        if usage.get("usage_pct", 0) >= 80:
            await _send_token_alert("Supabase Storage",
                f"Supabase Storage at {usage['usage_pct']}%. Consider cleaning up old images.")
    except Exception as e:
        logger.warning(f"Supabase Storage usage check failed: {e}")

    # ── Gmail Check ──
    gmail = _get_setting("gmail_address")
    gmail_pwd = _get_setting("gmail_app_password")
    if gmail and gmail_pwd:
        try:
            import smtplib
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as s:
                s.login(gmail, gmail_pwd)
            state["gmail_last_check_ok"] = True
        except Exception as e:
            state["gmail_last_check_ok"] = False
            logger.warning(f"Gmail check failed: {e}")

    _save_state(state)
    logger.info("Token health check complete.")


# ── Helpers ───────────────────────────────────

async def _refresh_pinterest_token(refresh_token: str, app_id: str, app_secret: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                "https://api.pinterest.com/v5/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                auth=(app_id, app_secret),
            )
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logger.error(f"Pinterest refresh failed: {e}")
    return None


async def _refresh_instagram_token(current_token: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                "https://graph.instagram.com/refresh_access_token",
                params={
                    "grant_type": "ig_exchange_token",
                    "access_token": current_token,
                },
            )
            if r.status_code == 200:
                return r.json().get("access_token")
    except Exception as e:
        logger.error(f"Instagram refresh failed: {e}")
    return None


async def _send_token_alert(service: str, message: str, is_success: bool = False):
    """Send email alert and create in-app notification."""
    from services.supabase_client import get_supabase
    from routers.settings_router import _get_setting

    sb = get_supabase()

    # Create in-app notification
    try:
        sb.table("notifications").insert({
            "type": "token_alert" if not is_success else "token_info",
            "title": f"{service} Token Alert" if not is_success else f"{service} Update",
            "message": message,
            "action_url": "/settings",
        }).execute()
    except Exception:
        pass

    # Send email alert
    if not is_success:
        gmail = _get_setting("gmail_address")
        pwd = _get_setting("gmail_app_password")
        to = _get_setting("notification_email") or gmail
        if gmail and pwd and to:
            try:
                from services.email_service import send_email, _base_template
                await send_email(gmail, pwd, to,
                    f"⚠️ PinProfit: {service} Needs Attention",
                    _base_template(f"{service} Token Alert",
                        f"<p>{message}</p>"
                        "<p>Open your PinProfit app → Settings to resolve this.</p>"
                    ),
                )
            except Exception as e:
                logger.warning(f"Could not send alert email: {e}")


# ── Usage Tracking ────────────────────────────

def track_gemini_usage():
    """Call after each Gemini API request."""
    state = _load_state()
    today = datetime.now().strftime("%Y-%m-%d")
    if state.get("gemini_usage_date") != today:
        state["gemini_daily_usage"] = 0
        state["gemini_usage_date"] = today
    state["gemini_daily_usage"] = state.get("gemini_daily_usage", 0) + 1
    _save_state(state)
    return state["gemini_daily_usage"]


def track_amazon_failure(success: bool):
    """Track Amazon API consecutive failures."""
    state = _load_state()
    if success:
        state["amazon_consecutive_failures"] = 0
    else:
        state["amazon_consecutive_failures"] = state.get("amazon_consecutive_failures", 0) + 1
    _save_state(state)
    return state["amazon_consecutive_failures"]


def track_cuelinks_failure(success: bool):
    """Track Cuelinks API consecutive failures."""
    state = _load_state()
    if success:
        state["cuelinks_consecutive_failures"] = 0
    else:
        state["cuelinks_consecutive_failures"] = state.get("cuelinks_consecutive_failures", 0) + 1
    _save_state(state)
    return state["cuelinks_consecutive_failures"]
