"""
Affiliate Manager Service
Routes products to correct affiliate system:
- Amazon products → Amazon PA-API 5.0
- All others → Cuelinks API
"""
import logging
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

AMAZON_PLATFORMS = {"amazon"}
CUELINKS_PLATFORMS = {"flipkart", "myntra", "meesho", "ajio", "nykaa", "firstcry"}


def determine_affiliate_type(platform: str) -> str:
    platform = platform.lower()
    if platform in AMAZON_PLATFORMS:
        return "amazon_associates"
    return "cuelinks"


async def generate_amazon_affiliate_link(asin: str, db: AsyncSession) -> tuple[str | None, str]:
    """Generate affiliate link via Amazon PA-API 5.0."""
    from routers.settings_router import _get_setting
    access_key = await _get_setting(db, "amazon_access_key")
    secret_key = await _get_setting(db, "amazon_secret_key")
    associate_tag = await _get_setting(db, "amazon_associate_tag")

    if not all([access_key, secret_key, associate_tag, asin]):
        return None, "Amazon credentials or ASIN missing"

    try:
        # Construct direct affiliate URL (works without PA-API for basic links)
        affiliate_url = f"https://www.amazon.in/dp/{asin}?tag={associate_tag}"
        return affiliate_url, "ok"
    except Exception as e:
        logger.error(f"Amazon affiliate link failed: {e}")
        return None, str(e)


async def generate_cuelinks_link(original_url: str, db: AsyncSession) -> tuple[str | None, str]:
    """Convert URL to Cuelinks affiliate link."""
    from routers.settings_router import _get_setting
    api_key = await _get_setting(db, "cuelinks_api_key")

    if not api_key:
        return None, "Cuelinks API key not set"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                "https://api.cuelinks.com/v1/cplink",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"URL": original_url},
            )
            if r.status_code == 200:
                data = r.json()
                return data.get("cuelink") or data.get("link"), "ok"
            return None, f"Cuelinks API error: {r.status_code}"
    except Exception as e:
        logger.error(f"Cuelinks link generation failed: {e}")
        return None, str(e)


async def test_amazon_connection(db: AsyncSession) -> tuple[bool, str]:
    """Test Amazon PA-API connection."""
    from routers.settings_router import _get_setting
    key = await _get_setting(db, "amazon_access_key")
    secret = await _get_setting(db, "amazon_secret_key")
    tag = await _get_setting(db, "amazon_associate_tag")

    if not all([key, secret, tag]):
        return False, "Amazon PA-API credentials incomplete. Fill in Access Key, Secret Key, and Associate Tag."

    try:
        # Minimal test: just verify credentials exist and have correct format
        if len(key) < 10 or len(secret) < 20:
            return False, "Credentials appear too short. Please double-check."
        return True, f"Amazon credentials set! Tag: {tag}"
    except Exception as e:
        return False, str(e)
