# helpers.py
import requests

def fetch_facebook_profile(access_token, version="10.0"):
    """
    Call Facebook’s Graph API /me endpoint to get id, name and email.
    Returns a dict like: { "id": "...", "name": "...", "email": "..." }
    """
    url = f"https://graph.facebook.com/v{version}/me"
    params = {
        "fields": "id,name,email",
        "access_token": access_token
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()
