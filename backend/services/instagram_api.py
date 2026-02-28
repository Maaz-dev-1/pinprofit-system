"""
Instagram API Service
Handles OAuth, content publishing via Instagram Graph API.
Uses Facebook/Instagram Graph API for business accounts.
"""
import logging
import httpx
import os
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.instagram.com"
FACEBOOK_GRAPH_BASE = "https://graph.facebook.com/v19.0"
FACEBOOK_OAUTH_URL = "https://www.facebook.com/v19.0/dialog/oauth"


class InstagramAPI:
    def __init__(self, access_token: str = None):
        self.access_token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN", "")

    async def get_user(self) -> dict:
        """Get authenticated user info."""
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{GRAPH_API_BASE}/me",
                params={
                    "fields": "id,username,account_type,media_count",
                    "access_token": self.access_token,
                },
            )
            r.raise_for_status()
            return r.json()

    async def get_ig_business_account(self) -> str | None:
        """Get Instagram business account ID linked to Facebook page."""
        async with httpx.AsyncClient(timeout=15) as client:
            # Get Facebook pages
            r = await client.get(
                f"{FACEBOOK_GRAPH_BASE}/me/accounts",
                params={"access_token": self.access_token},
            )
            if r.status_code != 200:
                return None

            pages = r.json().get("data", [])
            if not pages:
                return None

            # Get IG business account from first page
            page_id = pages[0]["id"]
            page_token = pages[0]["access_token"]

            r2 = await client.get(
                f"{FACEBOOK_GRAPH_BASE}/{page_id}",
                params={
                    "fields": "instagram_business_account",
                    "access_token": page_token,
                },
            )
            if r2.status_code == 200:
                data = r2.json()
                ig = data.get("instagram_business_account", {})
                return ig.get("id")
            return None

    async def publish_image(
        self,
        ig_account_id: str,
        image_url: str,
        caption: str,
    ) -> dict:
        """
        Publish an image post to Instagram.
        Two-step process: create media container, then publish.
        """
        async with httpx.AsyncClient(timeout=30) as client:
            # Step 1: Create media container
            r1 = await client.post(
                f"{FACEBOOK_GRAPH_BASE}/{ig_account_id}/media",
                params={
                    "image_url": image_url,
                    "caption": caption[:2200],  # Instagram caption limit
                    "access_token": self.access_token,
                },
            )
            r1.raise_for_status()
            container_id = r1.json().get("id")

            if not container_id:
                return {"error": "Failed to create media container"}

            # Step 2: Publish
            r2 = await client.post(
                f"{FACEBOOK_GRAPH_BASE}/{ig_account_id}/media_publish",
                params={
                    "creation_id": container_id,
                    "access_token": self.access_token,
                },
            )
            r2.raise_for_status()
            return r2.json()

    async def get_media_insights(self, media_id: str) -> dict:
        """Get insights for a published post."""
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{FACEBOOK_GRAPH_BASE}/{media_id}/insights",
                params={
                    "metric": "impressions,reach,engagement,saved",
                    "access_token": self.access_token,
                },
            )
            if r.status_code == 200:
                return r.json()
            return {}


def get_oauth_url(app_id: str, redirect_uri: str, state: str = "pinprofit") -> str:
    """Generate Facebook/Instagram OAuth authorization URL."""
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement",
        "state": state,
    }
    return f"{FACEBOOK_OAUTH_URL}?{urlencode(params)}"


async def exchange_code_for_token(
    code: str,
    app_id: str,
    app_secret: str,
    redirect_uri: str,
) -> dict:
    """Exchange authorization code for long-lived access token."""
    async with httpx.AsyncClient(timeout=15) as client:
        # Step 1: Get short-lived token
        r = await client.get(
            f"{FACEBOOK_GRAPH_BASE}/oauth/access_token",
            params={
                "client_id": app_id,
                "client_secret": app_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        r.raise_for_status()
        short_token = r.json().get("access_token")

        # Step 2: Exchange for long-lived token (60 days)
        r2 = await client.get(
            f"{FACEBOOK_GRAPH_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": app_id,
                "client_secret": app_secret,
                "fb_exchange_token": short_token,
            },
        )
        r2.raise_for_status()
        return r2.json()
