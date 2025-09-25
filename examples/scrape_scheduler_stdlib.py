import logging
import random
import time
from datetime import datetime

from omni.scraper.job_queue import ScraperJobQueue


# Mock job functions
def fetch_feed_job(limit: int = 50) -> None:
    print(f"[{datetime.now()}] Fetched {random.randint(10, limit)} tweets")
    time.sleep(3)


def subscribe_users_job(users: list[str]) -> None:
    print(f"[{datetime.now()}] Subscribed to {len(users)} users")
    time.sleep(3)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    jq = ScraperJobQueue(
        max_queue_size=100,
        worker_delay=(1, 5),  # Random delay between 1 and 5 seconds
    )
    jq.start()

    jq.add_schedule(
        fetch_feed_job,
        (5, 15),
        kwargs={"limit": 500},
        next_run=datetime.now(),
    )

    # Add immediate jobs
    for i in range(5):
        print(f"Scheduling immediate subscription {i}")
        users = [f"user{j}" for j in range(i + 1)]
        jq.add_job(subscribe_users_job, (users,))

    time.sleep(5)
    for i in range(5):
        users = [f"user{j}" for j in range(i + 1)]
        jq.add_job(subscribe_users_job, (users,))

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        jq.stop()
