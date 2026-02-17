"""
twitter_client.py — Twitter/X Integration (Gold Tier)
------------------------------------------------------
Post tweets and fetch engagement summaries via Twitter API v2.

pip install: requests requests-oauthlib

Setup:
  1. Go to developer.twitter.com
  2. Create a Project + App (Free tier works for basic posting)
  3. Enable Read + Write permissions
  4. Generate all 4 keys + Bearer Token
  5. Fill in Gold/Integrations/twitter/twitter_config.json
"""

import json
import os
import requests
from requests_oauthlib import OAuth1
from datetime import datetime, timedelta

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "twitter_config.json")
AUDIT_DIR   = os.path.join(os.path.dirname(__file__), "..", "..", "Audit_Logs")

TWITTER_API  = "https://api.twitter.com/2"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def audit(action: str, result: str, duration_ms: int = 0) -> None:
    os.makedirs(AUDIT_DIR, exist_ok=True)
    log_file = os.path.join(AUDIT_DIR, f"{datetime.now():%Y-%m-%d}_audit.log")
    entry = (
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
        f"[twitter_client] [{action}] [{result}] [{duration_ms}ms]\n"
    )
    with open(log_file, "a") as f:
        f.write(entry)


def _get_auth() -> OAuth1:
    cfg = load_config()
    return OAuth1(
        cfg["api_key"], cfg["api_secret"],
        cfg["access_token"], cfg["access_token_secret"]
    )


def _bearer_headers() -> dict:
    cfg = load_config()
    return {"Authorization": f"Bearer {cfg['bearer_token']}"}


# ── Post ──────────────────────────────────────────────────────────────────────

def post_tweet(text: str) -> dict:
    """Post a tweet. Max 280 characters."""
    if len(text) > 280:
        raise ValueError(f"Tweet too long: {len(text)} chars (max 280)")
    start = datetime.now()
    resp  = requests.post(
        f"{TWITTER_API}/tweets",
        auth=_get_auth(),
        json={"text": text}
    )
    resp.raise_for_status()
    ms     = int((datetime.now() - start).total_seconds() * 1000)
    result = resp.json()
    tweet_id = result.get("data", {}).get("id")
    audit("post_tweet", f"tweet_id={tweet_id}", ms)
    return result


# ── Summary ───────────────────────────────────────────────────────────────────

def get_user_id() -> str:
    """Get authenticated user's ID."""
    resp = requests.get(f"{TWITTER_API}/users/me", headers=_bearer_headers())
    resp.raise_for_status()
    return resp.json()["data"]["id"]


def get_tweet_summary(days: int = 7) -> dict:
    """Fetch tweet engagement summary for last N days."""
    start   = datetime.now()
    user_id = get_user_id()
    since   = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    resp = requests.get(
        f"{TWITTER_API}/users/{user_id}/tweets",
        headers=_bearer_headers(),
        params={
            "start_time": since,
            "tweet.fields": "public_metrics,created_at",
            "max_results": 100
        }
    )
    resp.raise_for_status()
    data = resp.json()

    tweets = data.get("data", [])
    summary = {
        "tweet_count": len(tweets),
        "total_impressions": sum(t["public_metrics"].get("impression_count", 0) for t in tweets),
        "total_likes": sum(t["public_metrics"].get("like_count", 0) for t in tweets),
        "total_retweets": sum(t["public_metrics"].get("retweet_count", 0) for t in tweets),
        "total_replies": sum(t["public_metrics"].get("reply_count", 0) for t in tweets),
    }
    ms = int((datetime.now() - start).total_seconds() * 1000)
    audit("get_tweet_summary", f"{summary['tweet_count']} tweets fetched", ms)
    return summary


if __name__ == "__main__":
    print("Twitter/X client loaded.")
    print("Fill in twitter_config.json before use.")
