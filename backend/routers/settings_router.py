"""
Settings router — save/load API keys in Supabase, test connections, OAuth flows.
"""
import os
import json
import logging
from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse
from services.supabase_client import get_supabase
from models.schemas import SettingsIn, TestConnectionOut

logger = logging.getLogger(__name__)
router = APIRouter()

MASKED_KEYS = {
    "pinterest_app_secret", "pinterest_access_token",
    "instagram_app_secret", "instagram_access_token",
    "amazon_secret_key", "cuelinks_api_key",
    "gmail_app_password", "gemini_api_key",
}


def _get_setting(key: str) -> str | None:
    """Get setting from Supabase."""
    try:
        sb = get_supabase()
        r = sb.table("settings").select("value").eq("key", key).execute()
        if r.data:
            return r.data[0]["value"]
    except Exception:
        pass
    return None


def _set_setting(key: str, value: str):
    """Upsert setting in Supabase."""
    from datetime import datetime, timezone
    sb = get_supabase()
    sb.table("settings").upsert({
        "key": key,
        "value": value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


# ── System Health ─────────────────────────────

@router.get("/health")
async def system_health():
    """Return health status for all 8 services (includes Supabase)."""
    from services.token_manager import get_system_health
    return get_system_health()


# ── GET / POST Settings ──────────────────────

@router.get("")
async def get_settings():
    """Return all settings. Masked fields show '••••••••' if set. Includes updated_at."""
    sb = get_supabase()
    all_keys = [
        "gemini_api_key", "pinterest_app_id", "pinterest_app_secret",
        "pinterest_access_token", "instagram_app_id", "instagram_app_secret",
        "instagram_access_token", "amazon_access_key", "amazon_secret_key",
        "amazon_associate_tag", "cuelinks_api_key",
        "gmail_address", "gmail_app_password", "notification_email",
    ]

    def _mask(key, val):
        if not val:
            return ""
        if key in MASKED_KEYS:
            return "••••••••"
        return val

    result = sb.table("settings").select("key,value,updated_at").execute()
    db_map = {row["key"]: row for row in result.data or []}

    settings = {}
    timestamps = {}
    for k in all_keys:
        row = db_map.get(k)
        settings[k] = _mask(k, row["value"] if row else "")
        timestamps[k] = row["updated_at"] if row else None

    return {"settings": settings, "timestamps": timestamps}


@router.post("")
async def save_settings(data: SettingsIn):
    raw = data.model_dump()
    for key, val in raw.items():
        if val and val != "••••••••":
            _set_setting(key, val)

    return {"ok": True, "message": "Settings saved successfully."}


# ── Pinterest OAuth ───────────────────────────
@router.get("/oauth/pinterest/url")
async def pinterest_oauth_url(request: Request):
    """Generate Pinterest OAuth authorization URL."""
    from services.pinterest_api import get_oauth_url
    app_id = _get_setting("pinterest_app_id")
    if not app_id:
        return {"ok": False, "message": "Pinterest App ID not set. Save it first."}

    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/settings/oauth/pinterest/callback"
    url = get_oauth_url(app_id, redirect_uri)
    return {"ok": True, "url": url}


@router.get("/oauth/pinterest/callback")
async def pinterest_oauth_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    request: Request = None,
):
    """Handle Pinterest OAuth callback — exchange code for token."""
    if error or not code:
        return RedirectResponse(url="/settings?oauth=pinterest&status=failed")

    from services.pinterest_api import exchange_code_for_token
    app_id = _get_setting("pinterest_app_id")
    app_secret = _get_setting("pinterest_app_secret")
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/settings/oauth/pinterest/callback"

    try:
        token_data = await exchange_code_for_token(code, app_id, app_secret, redirect_uri)
        access_token = token_data.get("access_token", "")
        if access_token:
            _set_setting("pinterest_access_token", access_token)
            return RedirectResponse(url="/settings?oauth=pinterest&status=success")
        return RedirectResponse(url="/settings?oauth=pinterest&status=failed")
    except Exception as e:
        logger.error(f"Pinterest OAuth failed: {e}")
        return RedirectResponse(url="/settings?oauth=pinterest&status=failed")


# ── Instagram OAuth ───────────────────────────
@router.get("/oauth/instagram/url")
async def instagram_oauth_url(request: Request):
    """Generate Instagram/Facebook OAuth authorization URL."""
    from services.instagram_api import get_oauth_url
    app_id = _get_setting("instagram_app_id")
    if not app_id:
        return {"ok": False, "message": "Instagram App ID not set. Save it first."}

    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/settings/oauth/instagram/callback"
    url = get_oauth_url(app_id, redirect_uri)
    return {"ok": True, "url": url}


@router.get("/oauth/instagram/callback")
async def instagram_oauth_callback(
    code: str = Query(None),
    error: str = Query(None),
    request: Request = None,
):
    """Handle Instagram OAuth callback — exchange code for long-lived token."""
    if error or not code:
        return RedirectResponse(url="/settings?oauth=instagram&status=failed")

    from services.instagram_api import exchange_code_for_token
    app_id = _get_setting("instagram_app_id")
    app_secret = _get_setting("instagram_app_secret")
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/settings/oauth/instagram/callback"

    try:
        token_data = await exchange_code_for_token(code, app_id, app_secret, redirect_uri)
        access_token = token_data.get("access_token", "")
        if access_token:
            _set_setting("instagram_access_token", access_token)
            return RedirectResponse(url="/settings?oauth=instagram&status=success")
        return RedirectResponse(url="/settings?oauth=instagram&status=failed")
    except Exception as e:
        logger.error(f"Instagram OAuth failed: {e}")
        return RedirectResponse(url="/settings?oauth=instagram&status=failed")


# ── Test Email ────────────────────────────────
@router.post("/test-email")
async def send_test_email():
    """Send a test email to verify Gmail SMTP works."""
    gmail = _get_setting("gmail_address")
    pwd = _get_setting("gmail_app_password")
    to = _get_setting("notification_email") or gmail

    if not gmail or not pwd:
        return {"ok": False, "message": "Gmail credentials not set."}

    from services.email_service import send_email, _base_template
    try:
        ok = await send_email(
            gmail, pwd, to,
            "PinProfit Test Email ✅",
            _base_template("Test Email Successful! 🎉",
                "<p>If you're reading this, your email notification system is working perfectly!</p>"
                "<p>You'll receive notifications for research completion, pin posting, weekly reports, and more.</p>"
            ),
        )
        if ok:
            return {"ok": True, "message": f"Test email sent to {to}!"}
        return {"ok": False, "message": "Email send failed. Check your credentials."}
    except Exception as e:
        return {"ok": False, "message": f"Email error: {str(e)[:100]}"}


# ── Pinterest Boards (for pin publishing) ─────
@router.get("/pinterest/boards")
async def get_pinterest_boards():
    """Get user's Pinterest boards for the board selector."""
    token = _get_setting("pinterest_access_token")
    if not token:
        return {"ok": False, "boards": [], "message": "Pinterest not connected."}

    from services.pinterest_api import PinterestAPI
    try:
        api = PinterestAPI(access_token=token)
        boards = await api.get_boards()
        return {"ok": True, "boards": boards}
    except Exception as e:
        return {"ok": False, "boards": [], "message": str(e)[:100]}


# ── Connection Tests ──────────────────────────
@router.post("/test/{service}", response_model=TestConnectionOut)
async def test_connection(service: str):
    try:
        if service == "gemini":
            import google.generativeai as genai
            key = _get_setting("gemini_api_key")
            if not key:
                return TestConnectionOut(ok=False, message="Gemini API key not set.")
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content("Say: PinProfit connected!")
            if resp.text:
                return TestConnectionOut(ok=True, message="Gemini AI connected successfully!")
            return TestConnectionOut(ok=False, message="Gemini responded but with empty content.")

        elif service == "supabase":
            from services.supabase_client import test_connection as test_sb
            ok, msg = test_sb()
            return TestConnectionOut(ok=ok, message=msg)

        elif service == "email":
            import smtplib
            gmail = _get_setting("gmail_address")
            pwd   = _get_setting("gmail_app_password")
            if not gmail or not pwd:
                return TestConnectionOut(ok=False, message="Gmail credentials not set.")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(gmail, pwd)
            return TestConnectionOut(ok=True, message="Gmail SMTP connected!")

        elif service == "pinterest":
            import httpx
            token = _get_setting("pinterest_access_token")
            if not token:
                return TestConnectionOut(ok=False, message="Pinterest access token not set. Use 'Connect Pinterest' button.")
            r = httpx.get("https://api.pinterest.com/v5/user_account",
                          headers={"Authorization": f"Bearer {token}"})
            if r.status_code == 200:
                data = r.json()
                return TestConnectionOut(ok=True, message=f"Pinterest connected as @{data.get('username', 'unknown')}")
            return TestConnectionOut(ok=False, message=f"Pinterest API error: {r.status_code}")

        elif service == "instagram":
            import httpx
            token = _get_setting("instagram_access_token")
            if not token:
                return TestConnectionOut(ok=False, message="Instagram access token not set. Use 'Connect Instagram' button.")
            r = httpx.get(f"https://graph.instagram.com/me?fields=id,username&access_token={token}")
            if r.status_code == 200:
                data = r.json()
                return TestConnectionOut(ok=True, message=f"Instagram connected as @{data.get('username', 'unknown')}")
            return TestConnectionOut(ok=False, message=f"Instagram API error: {r.status_code}")

        elif service == "amazon":
            from services.affiliate_manager import test_amazon_connection_sync
            ok, msg = test_amazon_connection_sync()
            return TestConnectionOut(ok=ok, message=msg)

        elif service == "cuelinks":
            import httpx
            key = _get_setting("cuelinks_api_key")
            if not key:
                return TestConnectionOut(ok=False, message="Cuelinks API key not set.")
            r = httpx.get("https://api.cuelinks.com/v1/publisher/profile",
                          headers={"Authorization": f"Bearer {key}"})
            if r.status_code == 200:
                return TestConnectionOut(ok=True, message="Cuelinks API connected!")
            return TestConnectionOut(ok=False, message=f"Cuelinks API error: {r.status_code}")

        else:
            return TestConnectionOut(ok=False, message=f"Unknown service: {service}")

    except Exception as e:
        logger.exception(f"Connection test failed for {service}: {e}")
        return TestConnectionOut(ok=False, message=f"Connection failed: {str(e)[:100]}")
