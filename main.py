import asyncio
import hashlib
import json
from datetime import date, datetime, timezone
from typing import Optional, Literal

from twscrape import API, gather

from db import execute_query
from git_helper import has_uncommitted_changes, get_current_commit_id


async def main():
    if has_uncommitted_changes():
        response = (input("You have may have uncommitted changes. Are you sure you want to proceed? (yes/no): ")
                    .strip().lower())
        if response not in {"yes", "y"}:
            print("Exiting...")
            return
    print("Proceeding with execution...")
    commit_id = get_current_commit_id()
    print(f"Commit ID: {commit_id}")

    api = API()  # or API("path-to.db") - default is `accounts.db`

    accounts = execute_query(
        "SELECT * FROM accounts WHERE scraping_status IN ('not_scraped', 'partial')",
        {},
        return_type="rows"
    )
    for acc in accounts:
        execute_query(
            "UPDATE accounts SET scraping_status = 'in_progress' WHERE id = %(id)s",
            {"id": acc["id"]},
            return_type="none"
        )
        new_status = await fetch_user_tweets(api, acc["account"], commit_id)
        execute_query(
            "UPDATE accounts SET scraping_status = %(new_status)s WHERE id = %(id)s",
            {"id": acc["id"], "new_status": new_status},
            return_type="none"
        )


async def fetch_user_tweets(api: API, username: str, commit_id: Optional[str]) \
        -> Literal["error", "done", "partial"]:
    try:
        # find user by username
        print(f"Fetching user {username}")
        user = await api.user_by_login(username)
        if not user:
            print(f"User {username} not found")
            return "error"
        user_id = user.id
        print(f"Found user {username}, their id is: {user_id}")
        # fetch user's tweets and replies
        fetch_method = "user_tweets_and_replies"
        print(f"Running {fetch_method} on: {user_id}")
        fetch_started = datetime.now(timezone.utc)
        user_tweets_and_replies = await gather(api.user_tweets_and_replies(user_id, limit=10))
        fetch_ended = datetime.now(timezone.utc)
        oldest_tweet_date = user_tweets_and_replies[len(user_tweets_and_replies) - 1].date
        fetch_job_info = {
            "started_at": fetch_started,
            "ended_at": fetch_ended,
            "user_id": user_id,
            "fetch_method": fetch_method,
            "covering_from": oldest_tweet_date,
            "covering_to": fetch_started,
            "tweet_count": len(user_tweets_and_replies),
            "commit_id": commit_id
        }
        fetch_job_id = execute_query(
            "INSERT INTO jobs"
            " (started_at, ended_at, user_id, fetch_method, covering_from, covering_to, tweet_count, commit_id) "
            "VALUES ("
            "%(started_at)s, %(ended_at)s, %(user_id)s,"
            " %(fetch_method)s,"
            " %(covering_from)s, %(covering_to)s"
            ", %(tweet_count)s, %(commit_id)s"
            ")",
            fetch_job_info,
            return_type="id"
        )

        tweet_rows = [
            {
                "id": t.id,
                "json": t.json(),
                "fetch_job_id": fetch_job_id,
                "hash": hashlib.md5(json.dumps(
                    {
                        "tweet": t.dict(),
                        "fetch_job_info": fetch_job_info
                    },
                    default=str
                ).encode('utf-8')).hexdigest()
            }
            for t in user_tweets_and_replies if datetime.date(t.date) > date(2023, 10, 6)
        ]

        batch_size = 100
        for i in range(0, len(tweet_rows), batch_size):
            batch = tweet_rows[i:i + batch_size]
            args = {"fetch_job_id": fetch_job_id}
            row_values = []
            for j, row in enumerate(batch):
                row_values.append(f"(%(id{j})s, %(json{j})s, %(fetch_job_id)s, %(hash{j})s)")
                args[f"id{j}"] = row["id"]
                args[f"json{j}"] = row["json"]
                args[f"hash{j}"] = row["hash"]
            query = (f"INSERT INTO tweets (tweet_id, data, job_id, hash_val) VALUES "
                     f"{', '.join(row_values)}"
                     f"ON DUPLICATE KEY UPDATE id = id")
            execute_query(query, args, return_type="none")

        if datetime.date(oldest_tweet_date) < date(2023, 10, 6):
            return "done"
        else:
            return "partial"
    except Exception as e:
        print(f"Error fetching user {username}: {e}")
        return "error"


if __name__ == "__main__":
    asyncio.run(main())
