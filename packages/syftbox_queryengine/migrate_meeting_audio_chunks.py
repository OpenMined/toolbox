#!/usr/bin/env python3
"""
Migration script to update meeting_audio_chunks table structure
Changes: chunkid -> audio_chunk_id
"""
import sqlite3
from pathlib import Path

SCREENPIPE_DB_PATH = Path.home() / ".screenpipe" / "db.sqlite"

def migrate_meeting_audio_chunks():
    """Migrate meeting_audio_chunks table from chunkid to audio_chunk_id"""
    
    if not SCREENPIPE_DB_PATH.exists():
        print(f"Database not found at {SCREENPIPE_DB_PATH}")
        return
    
    conn = sqlite3.connect(SCREENPIPE_DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check current schema
        cursor.execute("PRAGMA table_info(meeting_audio_chunks)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'chunkid' in columns and 'audio_chunk_id' not in columns:
            print("Starting migration: chunkid -> audio_chunk_id")
            
            # Create new table with correct schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_audio_chunks_new (
                    meeting_id INTEGER,
                    audio_chunk_id INTEGER,  
                    FOREIGN KEY (meeting_id) REFERENCES meeting_meta(meeting_id),
                    PRIMARY KEY (meeting_id, audio_chunk_id)
                )
            """)
            
            # Copy data from old table to new table
            cursor.execute("""
                INSERT INTO meeting_audio_chunks_new (meeting_id, audio_chunk_id)
                SELECT meeting_id, chunkid FROM meeting_audio_chunks
            """)
            
            # Drop old table
            cursor.execute("DROP TABLE meeting_audio_chunks")
            
            # Rename new table to original name
            cursor.execute("ALTER TABLE meeting_audio_chunks_new RENAME TO meeting_audio_chunks")
            
            conn.commit()
            print("✓ Migration completed successfully")
            
        elif 'audio_chunk_id' in columns:
            print("✓ Table already has audio_chunk_id column, no migration needed")
        else:
            print("⚠️  Unexpected table structure")
            print(f"Columns found: {columns}")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_meeting_audio_chunks()