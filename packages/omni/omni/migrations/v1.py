import sqlite3


def run_v1_migrations(conn):
    """Run version 1 database migrations"""
    cursor = conn.cursor()

    # Handle migration for existing databases that don't have the model column
    try:
        cursor.execute("SELECT model FROM smart_list_summaries LIMIT 1")
    except sqlite3.OperationalError:
        # Column doesn't exist, add it
        cursor.execute("ALTER TABLE smart_list_summaries ADD COLUMN model TEXT")
        print("Added model column to smart_list_summaries table")

    # Handle migration for existing databases that don't have the user_email column
    try:
        cursor.execute("SELECT user_email FROM smart_lists LIMIT 1")
    except sqlite3.OperationalError:
        # Column doesn't exist, add it with default value
        cursor.execute(
            "ALTER TABLE smart_lists ADD COLUMN user_email TEXT DEFAULT 'example@list.org'"
        )
        # Update existing rows to have the default value
        cursor.execute(
            "UPDATE smart_lists SET user_email = 'example@list.org' WHERE user_email IS NULL"
        )
        print("Added user_email column to smart_lists table")

    # Handle migration for threshold -> cosine_threshold and add reranking_threshold
    try:
        cursor.execute("SELECT cosine_threshold FROM list_filters LIMIT 1")
    except sqlite3.OperationalError:
        # Column doesn't exist, need to migrate
        # SQLite doesn't support renaming columns directly in older versions,
        # so we'll add the new columns and copy data
        cursor.execute(
            "ALTER TABLE list_filters ADD COLUMN cosine_threshold REAL DEFAULT 0.4"
        )
        cursor.execute(
            "ALTER TABLE list_filters ADD COLUMN reranking_threshold REAL DEFAULT 0.82"
        )
        # Copy data from threshold to cosine_threshold if threshold column exists
        try:
            cursor.execute("UPDATE list_filters SET cosine_threshold = threshold")
        except sqlite3.OperationalError:
            # threshold column doesn't exist, skip
            pass
        print(
            "Added cosine_threshold and reranking_threshold columns to list_filters table"
        )

    # Drop the old threshold column if it exists
    try:
        cursor.execute("SELECT threshold FROM list_filters LIMIT 1")
        # Column exists, drop it
        cursor.execute("ALTER TABLE list_filters DROP COLUMN threshold")
        print("Dropped old threshold column from list_filters table")
    except sqlite3.OperationalError:
        # Column doesn't exist, nothing to drop
        pass

    conn.commit()
