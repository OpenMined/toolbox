import random
import time

from omni.data_fetchers.x_fetcher import XDataFetcher

# List of Twitter handles to scrape
HANDLES = [
    "elonmusk",
    "BillGates",
    "BarackObama",
    "naval",
    "paulg",
    "sama",
    "vitalikbuterin",
    "balajis",
    "pmarca",
    "ycombinator",
    "a16z",
    "naval",
    "cdixon",
    "openmined",
]

# Number of accounts to scrape per job
N = 2

# Initialize the data fetcher
scraper = XDataFetcher(headless=True)
scraper.start()


max_run_time = 5 * 60 * 60
start_time = time.time()
while True:
    # Wait random interval between 300-3600 seconds
    wait_time = random.randint(600, 3600)
    print(f"Waiting {wait_time} seconds until next scrape...")
    time.sleep(wait_time)

    # Check if max run time exceeded
    if time.time() - start_time > max_run_time:
        print("Max run time exceeded, exiting...")
        break
    # Choose N random accounts
    if HANDLES:
        selected_handles = random.sample(HANDLES, min(N, len(HANDLES)))
        print(f"Submitting scrape job for: {selected_handles}")
        scraper.add_follow_users_job(
            handles=selected_handles, fetch_timeline_duration=10
        )
    else:
        print("No handles configured, skipping scrape")

scraper.stop()
