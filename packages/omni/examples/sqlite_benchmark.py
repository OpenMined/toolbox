#!/usr/bin/env python3
"""
SQLite Benchmark Script

This script creates two SQLite databases:
1. First DB: Contains rows that will return 100k IDs when queried
2. Second DB: Contains detailed data for those IDs

The script measures the time it takes to query the second database
using the IDs from the first database.
"""

import os
import random
import sqlite3
import time


def create_first_database():
    """Create the first database with 150k rows to ensure we get 100k results"""
    print("Creating first database...")

    # Remove existing file if it exists
    if os.path.exists("first.db"):
        os.remove("first.db")

    conn = sqlite3.connect("first.db")
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE source_data (
            id INTEGER PRIMARY KEY,
            category TEXT,
            value INTEGER,
            active BOOLEAN
        )
    """)

    # Insert 150k rows with random data
    # We'll make sure about 100k of them meet our query criteria
    data_batch = []
    for i in range(1, 150001):
        # Make roughly 70% of records "active" to ensure we get 100k+ results
        active = random.choice([True, True, True, False])  # 75% chance of True
        category = random.choice(["A", "B", "C", "D"])
        value = random.randint(1, 1000)
        data_batch.append((i, category, value, active))

        # Insert in batches for better performance
        if len(data_batch) == 1000:
            cursor.executemany(
                "INSERT INTO source_data (id, category, value, active) VALUES (?, ?, ?, ?)",
                data_batch,
            )
            data_batch = []

    # Insert any remaining data
    if data_batch:
        cursor.executemany(
            "INSERT INTO source_data (id, category, value, active) VALUES (?, ?, ?, ?)",
            data_batch,
        )

    # Create index for better query performance
    cursor.execute("CREATE INDEX idx_active ON source_data(active)")

    conn.commit()
    conn.close()
    print("First database created successfully!")


def create_second_database(ids):
    """Create the second database with detailed data for the given IDs"""
    print(f"Creating second database with data for {len(ids)} IDs...")

    # Remove existing file if it exists
    if os.path.exists("second.db"):
        os.remove("second.db")

    conn = sqlite3.connect("second.db")
    cursor = conn.cursor()

    # Create table with more detailed data
    cursor.execute("""
        CREATE TABLE detailed_data (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            department TEXT,
            salary INTEGER,
            hire_date TEXT,
            description TEXT
        )
    """)

    # Generate detailed data for each ID
    departments = ["Engineering", "Sales", "Marketing", "HR", "Finance"]
    data_batch = []

    for i, record_id in enumerate(ids):
        name = f"User_{record_id}"
        email = f"user_{record_id}@company.com"
        department = random.choice(departments)
        salary = random.randint(50000, 150000)
        hire_date = f"2020-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        description = f"Description for user {record_id} in {department} department"

        data_batch.append(
            (record_id, name, email, department, salary, hire_date, description)
        )

        # Insert in batches
        if len(data_batch) == 1000:
            cursor.executemany(
                "INSERT INTO detailed_data VALUES (?, ?, ?, ?, ?, ?, ?)", data_batch
            )
            data_batch = []
            if i % 10000 == 0:
                print(f"  Inserted {i} records...")

    # Insert any remaining data
    if data_batch:
        cursor.executemany(
            "INSERT INTO detailed_data VALUES (?, ?, ?, ?, ?, ?, ?)", data_batch
        )

    # Create index on ID for fast lookups
    cursor.execute("CREATE INDEX idx_id ON detailed_data(id)")

    conn.commit()
    conn.close()
    print("Second database created successfully!")


def get_ids_from_first_db():
    """Query the first database to get 100k IDs"""
    print("Querying first database for IDs...")

    conn = sqlite3.connect("first.db")
    cursor = conn.cursor()

    # Query to get active records (should return around 100k IDs)
    cursor.execute("SELECT id FROM source_data WHERE active = 1 LIMIT 1000")
    results = cursor.fetchall()
    ids = [row[0] for row in results]

    conn.close()
    print(f"Retrieved {len(ids)} IDs from first database")
    return ids


def benchmark_second_query(ids):
    """Benchmark the query on the second database using the IDs"""
    print(f"Benchmarking query on second database with {len(ids)} IDs...")

    conn = sqlite3.connect("second.db")
    cursor = conn.cursor()

    # Create a temporary table
    cursor.execute("CREATE TEMP TABLE temp_ids(id INTEGER)")
    cursor.executemany("INSERT INTO temp_ids(id) VALUES (?)", [(i,) for i in ids])

    # Perform a join
    start_time = time.time()
    cursor.execute("""
        SELECT d.*
        FROM detailed_data d
        JOIN temp_ids t ON d.id = t.id
    """)
    results = cursor.fetchall()
    end_time = time.time()

    print("Time:", end_time - start_time)

    conn.close()

    query_time = end_time - start_time
    print(f"Query completed in {query_time:.4f} seconds")
    print(f"Retrieved {len(results)} rows")

    return query_time, len(results)


def main():
    """Main benchmark function"""
    print("=" * 60)
    print("SQLite Benchmark Script")
    print("=" * 60)

    # Step 1: Create and populate first database
    create_first_database()

    # Step 2: Get IDs from first database
    ids = get_ids_from_first_db()

    if len(ids) == 0:
        print("ERROR: No IDs retrieved from first database!")
        return

    # Step 3: Create second database with data for those IDs
    create_second_database(ids)

    # Step 4: Benchmark the second query
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)

    query_time, result_count = benchmark_second_query(ids)

    print(f"Query execution time: {query_time:.4f} seconds")
    print(f"Rows returned: {result_count:,}")
    print(f"Average time per row: {(query_time / result_count * 1000):.6f} ms")

    # Clean up
    print("\nDatabase files created:")
    print(f"- first.db ({os.path.getsize('first.db') / 1024 / 1024:.1f} MB)")
    print(f"- second.db ({os.path.getsize('second.db') / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
