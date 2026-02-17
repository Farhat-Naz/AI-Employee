"""
fb_ig_client.py — Facebook & Instagram Integration (Gold Tier)
--------------------------------------------------------------
Post messages and fetch engagement summaries via Graph API.

pip install: requests

Setup:
  1. Go to developers.facebook.com
  2. Create App → Business type
  3. Add Facebook Login + Instagram Graph API products
  4. Generate Page Access Token (long-lived)
  5. Fill in Gold/Integrations/facebook_instagram/fb_ig_config.json
"""

import json
import os
import requests
from datetime import datetime

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "fb_ig_config.json")
AUDIT_DIR   = os.path.join(os.path.dirname(__file__), "..", "..", "Audit_Logs")


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def audit(action: str, result: str, duration_ms: int = 0) -> None:
    os.makedirs(AUDIT_DIR, exist_ok=True)
    log_file = os.path.join(AUDIT_DIR, f"{datetime.now():%Y-%m-%d}_audit.log")
    entry = (
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
        f"[fb_ig_client] [{action}] [{result}] [{duration_ms}ms]\n"
    )
    with open(log_file, "a") as f:
        f.write(entry)


# ── Facebook ──────────────────────────────────────────────────────────────────

def post_to_facebook(message: str) -> dict:
    """Post a message to the configured Facebook Page."""
    cfg   = load_config()
    start = datetime.now()
    url   = f"https://graph.facebook.com/{cfg['api_version']}/{cfg['page_id']}/feed"
    resp  = requests.post(url, data={
        "message": message,
        "access_token": cfg["page_access_token"]
    })
    resp.raise_for_status()
    ms = int((datetime.now() - start).total_seconds() * 1000)
    result = resp.json()
    audit("post_facebook", f"post_id={result.get('id')}", ms)
    return result


def get_facebook_summary(days: int = 7) -> dict:
    """Fetch last N days engagement summary from Facebook Page."""
    cfg   = load_config()
    start = datetime.now()
    url   = (
        f"https://graph.facebook.com/{cfg['api_version']}/{cfg['page_id']}/insights"
        f"?metric=page_impressions,page_engaged_users,page_fans"
        f"&period=day&access_token={cfg['page_access_token']}"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    ms = int((datetime.now() - start).total_seconds() * 1000)
    audit("get_facebook_summary", "success", ms)
    return resp.json()


# ── Instagram ─────────────────────────────────────────────────────────────────

def post_to_instagram(image_url: str, caption: str) -> dict:
    """Post an image with caption to Instagram Business account."""
    cfg   = load_config()
    start = datetime.now()
    ig_id = cfg["instagram_account_id"]
    token = cfg["page_access_token"]
    ver   = cfg["api_version"]

    # Step 1: Create media container
    media_resp = requests.post(
        f"https://graph.facebook.com/{ver}/{ig_id}/media",
        data={"image_url": image_url, "caption": caption, "access_token": token}
    )
    media_resp.raise_for_status()
    container_id = media_resp.json()["id"]

    # Step 2: Publish container
    pub_resp = requests.post(
        f"https://graph.facebook.com/{ver}/{ig_id}/media_publish",
        data={"creation_id": container_id, "access_token": token}
    )
    pub_resp.raise_for_status()
    ms = int((datetime.now() - start).total_seconds() * 1000)
    result = pub_resp.json()
    audit("post_instagram", f"media_id={result.get('id')}", ms)
    return result


def get_instagram_summary() -> dict:
    """Fetch Instagram account insights."""
    cfg   = load_config()
    start = datetime.now()
    ig_id = cfg["instagram_account_id"]
    token = cfg["page_access_token"]
    ver   = cfg["api_version"]
    url   = (
        f"https://graph.facebook.com/{ver}/{ig_id}/insights"
        f"?metric=impressions,reach,profile_views&period=day&access_token={token}"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    ms = int((datetime.now() - start).total_seconds() * 1000)
    audit("get_instagram_summary", "success", ms)
    return resp.json()


if __name__ == "__main__":
    print("Facebook/Instagram client loaded.")
    print("Fill in fb_ig_config.json before use.")
