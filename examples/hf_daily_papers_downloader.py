import os
from datetime import datetime, timedelta

import requests

# --- CONFIG ---
API_KEY = os.getenv("HF_PAPERS_KEY")
MONTH = 9  # September
YEAR = 2025
TOP_N = 10


# --- FUNCTION TO FETCH PAPERS FOR A GIVEN DATE ---
def fetch_papers_for_date(date_str):
    url = f"https://huggingface.co/api/daily_papers?date={date_str}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()  # List of papers
    else:
        print(f"Failed to fetch {date_str}: {response.status_code}")
        return []


# --- COLLECT PAPERS FOR THE MONTH ---
papers = []
start_date = datetime(YEAR, MONTH, 1)
end_date = (start_date.replace(month=MONTH % 12 + 1) - timedelta(days=1)).day

for day in range(1, end_date + 1):
    # INSERT_YOUR_CODE
    date_obj = datetime(YEAR, MONTH, day)
    if date_obj > datetime.now():
        continue
    date_str = f"{YEAR}-{MONTH:02d}-{day:02d}"
    daily_papers = fetch_papers_for_date(date_str)
    papers.extend(daily_papers)

# --- SORT BY POPULARITY (UPVOTES) ---
print(papers[0]["paper"]["upvotes"])
papers_sorted = sorted(
    papers, key=lambda x: x.get("paper", {}).get("upvotes", 0), reverse=True
)
# print(papers_sorted[0])
print(len(papers_sorted))

# --- TAKE TOP N ---
top_papers = papers_sorted[:TOP_N]

# --- PRINT RESULTS ---
for i, paper in enumerate(top_papers, start=1):
    print(
        f"{i}. {paper['title']} ({paper.get('paper', {}).get('upvotes', 0)} upvotes) - {paper.get('url', '')}"
    )
