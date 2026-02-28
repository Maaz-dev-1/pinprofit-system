"""
Pinterest API Service
Handles OAuth, pin creation, analytics fetching.
Uses Pinterest API v5.
"""
import logging
import httpx
import os
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

PINTEREST_API_BASE = "https://api.pinterest.com/v5"
PINTEREST_OAUTH_URL = "https://api.pinterest.com/oauth/"


class PinterestAPI:
    def __init__(self, access_token: str = None):
        self.access_token = access_token or os.getenv("PINTEREST_ACCESS_TOKEN", "")
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def get_user(self) -> dict:
        """Get authenticated user info."""
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{PINTEREST_API_BASE}/user_account", headers=self.headers)
            r.raise_for_status()
            return r.json()

    async def create_pin(
        self,
        board_id: str,
        title: str,
        description: str,
        link: str,
        media_url: str,
        alt_text: str = "",
    ) -> dict:
        """Create a pin on Pinterest."""
        payload = {
            "board_id": board_id,
            "title": title[:100],  # Pinterest title limit
            "description": description[:500],
            "link": link,
            "media_source": {
                "source_type": "image_url",
                "url": media_url,
            },
        }
        if alt_text:
            payload["alt_text"] = alt_text[:500]

        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{PINTEREST_API_BASE}/pins",
                headers=self.headers,
                json=payload,
            )
            r.raise_for_status()
            return r.json()

    async def get_boards(self) -> list[dict]:
        """Get user's boards."""
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{PINTEREST_API_BASE}/boards",
                headers=self.headers,
                params={"page_size": 50},
            )
            r.raise_for_status()
            return r.json().get("items", [])

    async def get_pin_analytics(self, pin_id: str, days: int = 30) -> dict:
        """Get analytics for a specific pin."""
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{PINTEREST_API_BASE}/pins/{pin_id}/analytics",
                headers=self.headers,
                params={
                    "start_date": f"2024-01-01",
                    "end_date": "2026-12-31",
                    "metric_types": "IMPRESSION,SAVE,PIN_CLICK,OUTBOUND_CLICK",
                },
            )
            if r.status_code == 200:
                return r.json()
            return {}

    async def delete_pin(self, pin_id: str) -> bool:
        """Delete a pin."""
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.delete(
                f"{PINTEREST_API_BASE}/pins/{pin_id}",
                headers=self.headers,
            )
            return r.status_code == 204


def get_oauth_url(app_id: str, redirect_uri: str, state: str = "pinprofit") -> str:
    """Generate Pinterest OAuth authorization URL."""
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "boards:read,boards:write,pins:read,pins:write,user_accounts:read",
        "state": state,
    }
    return f"{PINTEREST_OAUTH_URL}?{urlencode(params)}"


async def exchange_code_for_token(
    code: str,
    app_id: str,
    app_secret: str,
    redirect_uri: str,
) -> dict:
    """Exchange authorization code for access token."""
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"{PINTEREST_API_BASE}/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            auth=(app_id, app_secret),
        )
        r.raise_for_status()
        return r.json()
