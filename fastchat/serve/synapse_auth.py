import os
import json
import requests
from urllib.parse import quote
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

SYNAPSE_CLIENT_ID = os.environ["SYNAPSE_CLIENT_ID"]
SYNAPSE_CLIENT_SECRET = os.environ["SYNAPSE_CLIENT_SECRET"]
# Must remain http://127.0.0.1:8100
SYNAPSE_REDIRECT_URI = os.environ["SYNAPSE_REDIRECT_URI"]


@router.get("/login/synapse")
async def login_synapse():
    claims = {
        "userinfo": {
            "user_name": None,
            "email": None,
            "given_name": None,
            "family_name": None
        }
    }
    claims_encoded = quote(json.dumps(claims))

    auth_url = (
        "https://signin.synapse.org"
        f"?response_type=code"
        f"&client_id={SYNAPSE_CLIENT_ID}"
        f"&redirect_uri={SYNAPSE_REDIRECT_URI}"
        f"&scope=openid"
        f"&claims={claims_encoded}"
    )
    return RedirectResponse(url=auth_url)


@router.get("/login/synapse/callback")
async def oauth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return HTMLResponse("<h1>Synapse login failed: missing code</h1>")

    token_resp = requests.post(
        "https://repo-prod.prod.sagebase.org/auth/v1/oauth2/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": SYNAPSE_REDIRECT_URI,
            "client_id": SYNAPSE_CLIENT_ID,
            "client_secret": SYNAPSE_CLIENT_SECRET,
        },
    )

    if token_resp.status_code != 200:
        return HTMLResponse(f"<h1>Token exchange failed</h1><pre>{token_resp.text}</pre>")

    access_token = token_resp.json().get("access_token")
    if not access_token:
        return HTMLResponse("<h1>Token not received</h1>")

    user_info = requests.get(
        "https://repo-prod.prod.sagebase.org/auth/v1/oauth2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if user_info.status_code != 200:
        return HTMLResponse(f"<h1>User info fetch failed</h1><pre>{user_info.text}</pre>")

    user = user_info.json()
    username = user.get("user_name") or user.get(
        "email") or user.get("sub") or "Unknown"
    print(f"✅ Login successful for user: {username}")
    print("🔍 Raw user info:", user)

    # Save full profile info in cookie (lightweight)
    response = RedirectResponse(url="/")
    response.set_cookie("synapse_logged_in", "true",
                        httponly=False, max_age=3600)
    response.set_cookie("synapse_username", username,
                        httponly=False, max_age=3600)
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("synapse_logged_in")
    response.delete_cookie("synapse_username")
    return response
