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

    conn.commit()
