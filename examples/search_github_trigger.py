# /// script
# dependencies = [
#   "requests<3",
# ]
# ///

import json
from datetime import datetime
from pathlib import Path

import requests

OUTPUT_FOLDER = Path.home() / "github_trending"


def search_github_repositories(keyword, token=None):
    """Search GitHub repositories - returns raw API response data"""
    url = "https://api.github.com/search/repositories"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    params = {
        "q": keyword,
        "sort": "stars",
        "order": "desc",
        "per_page": 5,  # limit to top 5 results
    }
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        return {
            "timestamp": datetime.now().isoformat(),
            "keyword": keyword,
            "repositories": data.get("items", []),
        }
    else:
        return {
            "timestamp": datetime.now().isoformat(),
            "keyword": keyword,
            "error": f"Error: {response.status_code} - {response.json().get('message', 'Unknown error')}",
        }


# Get the results
results = search_github_repositories("MCP")

# Save to file
OUTPUT_FOLDER.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filepath = OUTPUT_FOLDER / f"{timestamp}.json"

with open(filepath, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# Print the results
if "repositories" in results:
    for repo in results["repositories"]:
        print(f"{repo['full_name']} - ⭐ {repo['stargazers_count']}")
        print(f"{repo['html_url']}")
        if repo.get("description"):
            print(f"Description: {repo['description']}")
        print()
else:
    print(results.get("error", "Unknown error"))

print(f"Results saved to: {filepath}")
