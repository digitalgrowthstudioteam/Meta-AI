import urllib.parse
import httpx

from app.core.config import settings

META_AUTH_BASE = "https://www.facebook.com/v19.0/dialog/oauth"
META_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"


def build_meta_oauth_url(state: str) -> str:
    """
    Builds Meta OAuth authorization URL.

    - Uses centralized settings (not raw os.environ)
    - Prevents silent runtime crashes
    """

    if not settings.META_APP_ID:
        raise ValueError("META_APP_ID is not configured")

    if not settings.META_REDIRECT_URI:
        raise ValueError("META_REDIRECT_URI is not configured")

    params = {
        "client_id": settings.META_APP_ID,
        "redirect_uri": settings.META_REDIRECT_URI,
        "state": state,
        "scope": "ads_read,business_management",
        "response_type": "code",
    }

    return f"{META_AUTH_BASE}?{urllib.parse.urlencode(params)}"


async def exchange_code_for_token(code: str) -> dict:
    """
    Exchanges OAuth code for access token.
    """

    if not settings.META_APP_ID or not settings.META_APP_SECRET:
        raise ValueError("Meta OAuth credentials are not configured")

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            META_TOKEN_URL,
            params={
                "client_id": settings.META_APP_ID,
                "client_secret": settings.META_APP_SECRET,
                "redirect_uri": settings.META_REDIRECT_URI,
                "code": code,
            },
        )

        response.raise_for_status()
        return response.json()
