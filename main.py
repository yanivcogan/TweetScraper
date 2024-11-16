import asyncio
from datetime import date, datetime, timezone

from twscrape import API, gather

from git_helper import has_uncommitted_changes, get_current_commit_id


async def main():
    if has_uncommitted_changes():
        response = input("You have uncommitted changes. Are you sure you want to proceed? (yes/no): ").strip().lower()
        if response not in {"yes", "y"}:
            print("Exiting...")
            return
    print("Proceeding with execution...")
    commit_id = get_current_commit_id()

    api = API()  # or API("path-to.db") - default is `accounts.db`
    await fetch_user_tweets(api, "yoavgallant")


async def fetch_user_tweets(api: API, username: str):
    # find user by username
    user = await api.user_by_login(username)  # User
    user_id = user.id
    # fetch user's tweets and replies
    fetch_started = datetime.now(timezone.utc)
    fetch_method = "user_tweets_and_replies"
    user_tweets_and_replies = await gather(api.user_tweets_and_replies(user_id))
    fetch_ended = datetime.now(timezone.utc)
    oldest_tweet_date = user_tweets_and_replies[len(user_tweets_and_replies) - 1].date
    fetch_job_info = {
        "started_at": fetch_started,
        "ended_at": fetch_ended,
        "user_id": user_id,
        "fetch_method": fetch_method,
        "covering_from": oldest_tweet_date,
        "covering_to": fetch_started,
        "tweets_counts": len(user_tweets_and_replies),
    }
    # TODO: insert fetch_job_info into a mysql DB, and store the id in fetch_job_id
    fetch_job_id = 1
    tweet_jsons = [{
        "id": t.id,
        "json": t.json(),
        "fetch_job_id": fetch_job_id,
    } for t in user_tweets_and_replies if t.date > date(2023, 10, 6)]
    print(tweet_jsons)


if __name__ == "__main__":
    asyncio.run(main())
