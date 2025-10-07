import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tweepy
from config import (TWITTER_API_KEY, TWITTER_API_KEY_SECRET,
                    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET,
                    TWITTER_BEARER_TOKEN)

# create a client (v2)
client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_KEY_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
    wait_on_rate_limit=True
)

def get_own_user_id() -> str:
    me = client.get_me()
    return me.data.id

def fetch_mentions(since_id: str = None, max_results: int = 10):
    """
    Fetch mentions of the authenticated user.
    Returns the Tweepy Response object; iterate response.data for tweets.
    """
    me = get_own_user_id()
    # get mentions (v2 endpoint)
    params = {}
    if since_id:
        params["since_id"] = since_id
    resp = client.get_users_mentions(me, max_results=max_results, **params)
    return resp

def post_reply(tweet_id: str, username: str, text: str):
    """
    Posts a reply to tweet_id. Include @username at start for clarity.
    Uses create_tweet with in_reply_to_tweet_id.
    """
    reply_text = f"@{username} {text}"
    resp = client.create_tweet(text=reply_text, in_reply_to_tweet_id=tweet_id)
    return resp
