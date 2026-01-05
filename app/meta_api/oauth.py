import os
import urllib.parse
import httpx

META_AUTH_BASE = "https://www.facebook.com/v19.0/dialog/oauth"
META_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"


def build_meta_oauth_url(state: str) -> str:
    meta_app_id = os.environ.get("META_APP_ID")
    meta_redirect_uri = os.environ.get("META_REDIRECT_URI")

    if not meta_app_id:
        raise RuntimeError("META_APP_ID is not set in environment")

    if not meta_redirect_uri:
        raise RuntimeError("META_REDIRECT_URI is not set in environment")

    params = {
        "client_id": meta_app_id,
        "redirect_uri": meta_redirect_uri,
        "state": state,
        "scope": "ads_read,business_management",
        "response_type": "code",
    }

    return f"{META_AUTH_BASE}?{urllib.parse.urlencode(params)}"


async def exchange_code_for_token(code: str) -> dict:
    meta_app_id = os.environ.get("META_APP_ID")
    meta_app_secret = os.environ.get("META_APP_SECRET")
    meta_redirect_uri = os.environ.get("META_REDIRECT_URI")

    if not meta_app_id or not meta_app_secret or not meta_redirect_uri:
        raise RuntimeError("Meta OAuth environment variables are missing")

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            META_TOKEN_URL,
            params={
                "client_id": meta_app_id,
                "client_secret": meta_app_secret,
                "redirect_uri": meta_redirect_uri,
                "code": code,
            },
        )

        response.raise_for_status()
        return response.json()
