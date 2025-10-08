import json

import arxiv

# Search for newest AI articles
search = arxiv.Search(
    query="cat:cs.AI",
    max_results=5,
    sort_by=arxiv.SortCriterion.SubmittedDate,
    sort_order=arxiv.SortOrder.Descending,
)

results = []
for result in search.results():
    results.append(
        {
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "summary": result.summary,
            "published": result.published.strftime("%Y-%m-%d"),
            "pdf_url": result.pdf_url,
        }
    )

print(json.dumps(results, indent=2))
