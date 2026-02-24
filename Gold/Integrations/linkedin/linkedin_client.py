"""
linkedin_client.py — LinkedIn Integration (Gold/Platinum Tier)
----------------------------------------------------------------
Post updates and fetch engagement summaries via LinkedIn API v2.

pip install: requests

Setup:
  1. Go to developers.linkedin.com
  2. Create an App (select "Create, manage and delete posts")
  3. Request access to "Share on LinkedIn" and "Sign In with LinkedIn using OpenID Connect"
  4. Generate Access Token (use OAuth 2.0 flow)
  5. Fill in Gold/Integrations/linkedin/linkedin_config.json

LinkedIn API Documentation:
- https://learn.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/share-api
- https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin
"""

import json
import os
import requests
from datetime import datetime, timedelta

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "linkedin_config.json")
AUDIT_DIR   = os.path.join(os.path.dirname(__file__), "..", "..", "Audit_Logs")

LINKEDIN_API = "https://api.linkedin.com/v2"


def load_config() -> dict:
    """Load LinkedIn configuration from linkedin_config.json."""
    with open(CONFIG_PATH) as f:
        return json.load(f)


def audit(action: str, result: str, duration_ms: int = 0) -> None:
    """Write audit log entry."""
    os.makedirs(AUDIT_DIR, exist_ok=True)
    log_file = os.path.join(AUDIT_DIR, f"{datetime.now():%Y-%m-%d}_audit.log")
    entry = (
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
        f"[linkedin_client] [{action}] [{result}] [{duration_ms}ms]\n"
    )
    with open(log_file, "a") as f:
        f.write(entry)


def _get_headers() -> dict:
    """Get authorization headers for LinkedIn API requests."""
    cfg = load_config()
    return {
        "Authorization": f"Bearer {cfg['access_token']}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }


# ── User Profile ──────────────────────────────────────────────────────────────

def get_user_profile() -> dict:
    """Get authenticated user's profile information."""
    start = datetime.now()
    resp = requests.get(
        f"{LINKEDIN_API}/userinfo",
        headers=_get_headers()
    )
    resp.raise_for_status()
    ms = int((datetime.now() - start).total_seconds() * 1000)
    profile = resp.json()
    user_id = profile.get("sub")  # OpenID Connect uses 'sub' instead of 'id'
    audit("get_user_profile", f"user_id={user_id}", ms)
    return profile


# ── Post ──────────────────────────────────────────────────────────────────────

def post_update(text: str, visibility: str = "PUBLIC") -> dict:
    """
    Post a text update to LinkedIn.

    Args:
        text: The content to post (max 3000 characters)
        visibility: "PUBLIC" or "CONNECTIONS" (default: PUBLIC)

    Returns:
        API response with post details
    """
    if len(text) > 3000:
        raise ValueError(f"Post too long: {len(text)} chars (max 3000)")

    cfg = load_config()
    start = datetime.now()

    # Get user URN
    profile = get_user_profile()
    author = f"urn:li:person:{profile['sub']}"

    payload = {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": text
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": visibility
        }
    }

    resp = requests.post(
        f"{LINKEDIN_API}/ugcPosts",
        headers=_get_headers(),
        json=payload
    )
    resp.raise_for_status()
    ms = int((datetime.now() - start).total_seconds() * 1000)
    result = resp.json()
    post_id = result.get("id", "unknown")
    audit("post_update", f"post_id={post_id}", ms)
    return result


def post_article_share(article_url: str, comment: str = "") -> dict:
    """
    Share an article with optional comment on LinkedIn.

    Args:
        article_url: URL of the article to share
        comment: Optional commentary text (max 1300 characters)

    Returns:
        API response with post details
    """
    if len(comment) > 1300:
        raise ValueError(f"Comment too long: {len(comment)} chars (max 1300)")

    cfg = load_config()
    start = datetime.now()

    # Get user URN
    profile = get_user_profile()
    author = f"urn:li:person:{profile['sub']}"

    payload = {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": comment
                },
                "shareMediaCategory": "ARTICLE",
                "media": [
                    {
                        "status": "READY",
                        "originalUrl": article_url
                    }
                ]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    resp = requests.post(
        f"{LINKEDIN_API}/ugcPosts",
        headers=_get_headers(),
        json=payload
    )
    resp.raise_for_status()
    ms = int((datetime.now() - start).total_seconds() * 1000)
    result = resp.json()
    post_id = result.get("id", "unknown")
    audit("post_article_share", f"post_id={post_id} url={article_url}", ms)
    return result


# ── Analytics ─────────────────────────────────────────────────────────────────

def get_post_statistics(post_urn: str) -> dict:
    """
    Get statistics for a specific post.

    Args:
        post_urn: LinkedIn post URN (e.g., "urn:li:share:123456")

    Returns:
        Post statistics including likes, comments, shares, impressions
    """
    start = datetime.now()

    # LinkedIn API requires the share URN to fetch stats
    resp = requests.get(
        f"{LINKEDIN_API}/socialActions/{post_urn}",
        headers=_get_headers()
    )
    resp.raise_for_status()
    ms = int((datetime.now() - start).total_seconds() * 1000)
    stats = resp.json()
    audit("get_post_statistics", f"post_urn={post_urn}", ms)
    return stats


def get_engagement_summary(days: int = 7) -> dict:
    """
    Fetch engagement summary for the last N days.

    Note: LinkedIn's UGC Posts API has limited analytics access.
    For comprehensive analytics, use LinkedIn Marketing API or Analytics Finder API.
    This provides a basic summary based on available data.

    Args:
        days: Number of days to look back (default: 7)

    Returns:
        Dictionary with engagement metrics
    """
    start = datetime.now()

    # Get user profile
    profile = get_user_profile()
    author_id = profile['sub']

    # Fetch recent posts (LinkedIn limits this to certain access levels)
    # Note: This may require additional API permissions
    try:
        resp = requests.get(
            f"{LINKEDIN_API}/ugcPosts",
            headers=_get_headers(),
            params={
                "q": "authors",
                "authors": f"List(urn:li:person:{author_id})",
                "count": 50
            }
        )
        resp.raise_for_status()
        data = resp.json()

        posts = data.get("elements", [])

        # Filter posts by date (last N days)
        cutoff = datetime.now() - timedelta(days=days)
        recent_posts = []
        for post in posts:
            created = post.get("created", {}).get("time", 0)
            post_date = datetime.fromtimestamp(created / 1000)  # LinkedIn uses milliseconds
            if post_date >= cutoff:
                recent_posts.append(post)

        # Aggregate metrics (basic summary)
        summary = {
            "post_count": len(recent_posts),
            "total_likes": 0,
            "total_comments": 0,
            "total_shares": 0,
            "total_impressions": 0,
            "note": "Limited analytics - full metrics require LinkedIn Marketing API access"
        }

        ms = int((datetime.now() - start).total_seconds() * 1000)
        audit("get_engagement_summary", f"{len(recent_posts)} posts analyzed", ms)
        return summary

    except requests.exceptions.HTTPError as e:
        # If we don't have permission to fetch posts
        ms = int((datetime.now() - start).total_seconds() * 1000)
        audit("get_engagement_summary", f"error: {str(e)}", ms)
        return {
            "post_count": 0,
            "error": "Insufficient API permissions for analytics",
            "note": "Requires LinkedIn Marketing API or Analytics Finder API access"
        }


# ── Helper Functions ──────────────────────────────────────────────────────────

def validate_access_token() -> bool:
    """
    Validate that the access token is working.

    Returns:
        True if token is valid, False otherwise
    """
    try:
        get_user_profile()
        return True
    except Exception as e:
        print(f"Token validation failed: {e}")
        return False


if __name__ == "__main__":
    print("LinkedIn client loaded.")
    print("Fill in linkedin_config.json before use.")
    print("\nTo test connection, run:")
    print("  python linkedin_client.py")
