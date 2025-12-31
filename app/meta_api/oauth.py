import urllib.parse
import httpx
from datetime import datetime, timedelta

from app.core.config import settings


META_AUTH_BASE = "https://www.facebook.com/v19.0/dialog/oauth"
META_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"


def build_meta_oauth_url(state: str) -> str:
    params = {
        "client_id": settings.META_APP_ID,
        "redirect_uri": settings.META_REDIRECT_URI,
        "state": state,
        "scope": "ads_read,business_management",
        "response_type": "code",
    }

    return f"{META_AUTH_BASE}?{urllib.parse.urlencode(params)}"


async def exchange_code_for_token(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            META_TOKEN_URL,
            params={
                "client_id": settings.META_APP_ID,
                "client_secret": settings.META_APP_SECRET,
                "redirect_uri": settings.META_REDIRECT_URI,
                "code": code,
            },
            timeout=10,
        )

        response.raise_for_status()
        return response.json()
