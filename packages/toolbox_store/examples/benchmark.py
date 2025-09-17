"""
❯ python benchmark.py
Loading documents...
Loaded 5000 documents from /Users/eelco/dev/toolbox/packages/toolbox_store/examples/fineweb-bbc-news

==================================================
INGESTION BENCHMARK
==================================================
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2272/2272 [10:42<00:00,  3.54it/s]
Ingested 5000 documents:
  Total time: 644.85s
  Rate: 7.8 docs/sec
  Per doc: 128.97ms

==================================================
QUERY BENCHMARKS (50 iterations each)
==================================================

1. Semantic Search
  Mean: 143.26ms | P50: 143.59ms | P95: 150.58ms | P99: 160.77ms

2. Semantic Search + Filter
  Mean: 259.54ms | P50: 258.97ms | P95: 266.13ms | P99: 273.74ms

3. Keyword Search (FTS5)
  Mean: 1.02ms | P50: 0.43ms | P95: 2.22ms | P99: 2.28ms

4. Keyword Search + Filter
  Mean: 8.83ms | P50: 9.04ms | P95: 9.99ms | P99: 10.54ms

5. Hybrid Search (RRF)
  Mean: 153.79ms | P50: 156.24ms | P95: 162.01ms | P99: 166.67ms

6. Hybrid Search + Filter
  Mean: 276.96ms | P50: 277.54ms | P95: 289.25ms | P99: 296.46ms

==================================================
CORPUS STATISTICS
==================================================
Documents: 5000
Chunks: 18172
Avg chunks/doc: 3.6
Database size: 125.5 MB
"""

import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import numpy as np
from toolbox_store.data_loaders import load_from_dir
from toolbox_store.models import TBDocument
from toolbox_store.store import ToolboxStore


def benchmark_ingestion(
    store: ToolboxStore, documents: List[TBDocument]
) -> Dict[str, float]:
    """Benchmark document ingestion with embeddings."""
    start = time.perf_counter()
    store.insert_docs(documents, create_embeddings=True)
    elapsed = time.perf_counter() - start

    return {
        "total_time": elapsed,
        "docs_per_second": len(documents) / elapsed,
        "ms_per_doc": (elapsed * 1000) / len(documents),
    }


def benchmark_query(
    store: ToolboxStore, query_fn, iterations: int = 50
) -> Dict[str, float]:
    """Benchmark a query function multiple times."""
    latencies = []

    for _ in range(iterations):
        start = time.perf_counter()
        results = query_fn()  # noqa
        elapsed = time.perf_counter() - start
        latencies.append(elapsed * 1000)  # Convert to ms

    return {
        "mean_ms": np.mean(latencies),
        "p50_ms": np.percentile(latencies, 50),
        "p95_ms": np.percentile(latencies, 95),
        "p99_ms": np.percentile(latencies, 99),
        "min_ms": np.min(latencies),
        "max_ms": np.max(latencies),
    }


def main():
    DATA_DIR = Path(__file__).parent / "fineweb-bbc-news"
    db_path = DATA_DIR / "benchmark.db"

    # Load documents
    print("Loading documents...")
    documents = load_from_dir(DATA_DIR, max_docs=5000)
    print(f"Loaded {len(documents)} documents from {DATA_DIR}")

    # Initialize store
    store = ToolboxStore("benchmark_collection", db_path=db_path, reset=True)

    # Benchmark ingestion
    print("\n" + "=" * 50)
    print("INGESTION BENCHMARK")
    print("=" * 50)
    ingestion_stats = benchmark_ingestion(store, documents)
    print(f"Ingested {len(documents)} documents:")
    print(f"  Total time: {ingestion_stats['total_time']:.2f}s")
    print(f"  Rate: {ingestion_stats['docs_per_second']:.1f} docs/sec")
    print(f"  Per doc: {ingestion_stats['ms_per_doc']:.2f}ms")

    # Prepare test queries
    test_queries = [
        "Airport security terrorism",
        "Economic policy rates",
        "Sports championship competition",
        "Technology privacy data",
        "Government politics election",
    ]

    test_keywords = ["yates", "airport", "security", "police", "minister"]

    # Date filter for recent docs (last 30 days for testing)
    date_filter = {"created_at__gte": datetime.now() - timedelta(days=30)}

    print("\n" + "=" * 50)
    print("QUERY BENCHMARKS (50 iterations each)")
    print("=" * 50)

    # 1. Semantic search
    print("\n1. Semantic Search")

    def semantic_query():
        query = random.choice(test_queries)
        return store.search_chunks().semantic(query).chunk_limit(10).get()

    stats = benchmark_query(store, semantic_query)
    print(
        f"  Mean: {stats['mean_ms']:.2f}ms | P50: {stats['p50_ms']:.2f}ms | P95: {stats['p95_ms']:.2f}ms | P99: {stats['p99_ms']:.2f}ms"
    )

    # 2. Semantic + filter
    print("\n2. Semantic Search + Filter")

    def semantic_filter_query():
        query = random.choice(test_queries)
        return (
            store.search_chunks()
            .semantic(query)
            .where(date_filter)
            .chunk_limit(10)
            .get()
        )

    stats = benchmark_query(store, semantic_filter_query)
    print(
        f"  Mean: {stats['mean_ms']:.2f}ms | P50: {stats['p50_ms']:.2f}ms | P95: {stats['p95_ms']:.2f}ms | P99: {stats['p99_ms']:.2f}ms"
    )

    # 3. Keyword search
    print("\n3. Keyword Search")

    def keyword_query():
        keyword = random.choice(test_keywords)
        return store.search_chunks().keyword(keyword).chunk_limit(10).get()

    stats = benchmark_query(store, keyword_query)
    print(
        f"  Mean: {stats['mean_ms']:.2f}ms | P50: {stats['p50_ms']:.2f}ms | P95: {stats['p95_ms']:.2f}ms | P99: {stats['p99_ms']:.2f}ms"
    )

    # 4. Keyword + filter
    print("\n4. Keyword Search + Filter")

    def keyword_filter_query():
        keyword = random.choice(test_keywords)
        return (
            store.search_chunks()
            .keyword(keyword)
            .where(date_filter)
            .chunk_limit(10)
            .get()
        )

    stats = benchmark_query(store, keyword_filter_query)
    print(
        f"  Mean: {stats['mean_ms']:.2f}ms | P50: {stats['p50_ms']:.2f}ms | P95: {stats['p95_ms']:.2f}ms | P99: {stats['p99_ms']:.2f}ms"
    )

    # 5. Hybrid search
    print("\n5. Hybrid Search (RRF)")

    def hybrid_query():
        query = random.choice(test_queries)
        keyword = random.choice(test_keywords)
        return (
            store.search_chunks()
            .semantic(query)
            .keyword(keyword)
            .hybrid(method="rrf")
            .chunk_limit(10)
            .get()
        )

    stats = benchmark_query(store, hybrid_query)
    print(
        f"  Mean: {stats['mean_ms']:.2f}ms | P50: {stats['p50_ms']:.2f}ms | P95: {stats['p95_ms']:.2f}ms | P99: {stats['p99_ms']:.2f}ms"
    )

    # 6. Hybrid + filter
    print("\n6. Hybrid Search + Filter")

    def hybrid_filter_query():
        query = random.choice(test_queries)
        keyword = random.choice(test_keywords)
        return (
            store.search_chunks()
            .semantic(query)
            .keyword(keyword)
            .hybrid(method="rrf")
            .where(date_filter)
            .chunk_limit(10)
            .get()
        )

    stats = benchmark_query(store, hybrid_filter_query)
    print(
        f"  Mean: {stats['mean_ms']:.2f}ms | P50: {stats['p50_ms']:.2f}ms | P95: {stats['p95_ms']:.2f}ms | P99: {stats['p99_ms']:.2f}ms"
    )

    # Summary stats
    print("\n" + "=" * 50)
    print("CORPUS STATISTICS")
    print("=" * 50)

    # Get actual chunk count
    cursor = store.db.conn.execute(f"SELECT COUNT(*) FROM {store.db.chunks_table}")
    chunk_count = cursor.fetchone()[0]

    print(f"Documents: {len(documents)}")
    print(f"Chunks: {chunk_count}")
    print(f"Avg chunks/doc: {chunk_count / len(documents):.1f}")
    print(f"Database size: {(db_path.stat().st_size / 1024 / 1024):.1f} MB")


if __name__ == "__main__":
    main()
