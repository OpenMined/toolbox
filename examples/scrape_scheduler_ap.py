import random
import time
from datetime import datetime, timedelta
from uuid import uuid4

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

jobstores = {"default": MemoryJobStore()}
executors = {"default": ThreadPoolExecutor(1)}
job_defaults = {
    "coalesce": False,
    "misfire_grace_time": 60,
}
scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=utc,
)


def fetch_feed_job(limit=50):
    print(f"[{datetime.now()}] Fetched {random.randint(10, limit)} tweets")
    time.sleep(3)


def subscribe_users_job(users=None):
    if users is None:
        users_to_subscribe = ["user1", "user2", "user3"]
    else:
        users_to_subscribe = users

    print(f"[{datetime.now()}] Subscribed to {len(users_to_subscribe)} users")
    time.sleep(3)


# On-demand example - immediate job
def schedule_immediate_subscription(new_users):
    scheduler.add_job(
        subscribe_users_job,
        args=[new_users],
        id=f"subscribe_immediate_{uuid4()}",
    )


def schedule_recurring_feed_job():
    scheduler.add_job(
        fetch_feed_job,
        trigger="interval",
        seconds=10,
        max_instances=2,
        coalesce=True,
        kwargs={"limit": 500},
        id="scheduled_feed",
        next_run_time=datetime.now(tz=utc) + timedelta(milliseconds=100),
    )


def submit_on_demand_feed_job():
    scheduler.add_job(
        fetch_feed_job,
        kwargs={"limit": 500},
        id="ondemand_feed",
        replace_existing=True,
        misfire_grace_time=60,
    )


if __name__ == "__main__":
    # Start scheduler
    scheduler.start()
    schedule_recurring_feed_job()

    # Example: User adds new handles
    for i in range(10):
        schedule_immediate_subscription(["new_user" + str(j) for j in range(i + 1)])

    # Example: Schedule recurring feed job

    # time.sleep(2)
    # submit_on_demand_feed_job()
    # time.sleep(2)
    # submit_on_demand_feed_job()
    # submit_on_demand_feed_job()
    # submit_on_demand_feed_job()
    # submit_on_demand_feed_job()

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
