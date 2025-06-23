#!/usr/bin/env python3
"""
Script to import and merge philosopher data from CSV into PostgreSQL.
Handles both new records and updates to existing ones based on name.
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

# Configuration
DB_CONFIG = {
    'dbname': 'daemonium',
    'user': 'postgres',
    'password': 'ch@ng3m300',
    'host': 'localhost',
    'port': '5432'
}

def get_connection():
    """Create and return a database connection."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def import_philosophers(csv_path):
    """Import and merge philosopher data from CSV."""
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # Ensure name column has a unique constraint
            try:
                cur.execute("""
                    ALTER TABLE philosophers 
                    ADD CONSTRAINT philosophers_name_key UNIQUE (name);
                """)
                conn.commit()
                print("Added unique constraint on name column")
            except psycopg2.Error as e:
                # Ignore if constraint already exists
                if 'already exists' not in str(e):
                    raise e
                conn.rollback()

            # Create temp table
            cur.execute("""
                CREATE TEMP TABLE temp_philosophers (
                    name VARCHAR(255) NOT NULL,
                    dob VARCHAR(20),
                    dod VARCHAR(20),
                    summary TEXT,
                    content TEXT,
                    school_id INTEGER,
                    tag_id INTEGER
                )
            """)

            # Import CSV to temp table
            with open(csv_path, 'r', encoding='utf-8') as f:
                with conn.cursor() as copy_cur:
                    copy_cur.copy_expert(
                        """
                        COPY temp_philosophers (name, dob, dod, summary, content, school_id, tag_id)
                        FROM STDIN WITH (FORMAT csv, DELIMITER '|', HEADER true, NULL 'NULL')
                        """,
                        f
                    )

            # Upsert data
            cur.execute("""
                -- First, handle updates
                UPDATE philosophers p
                SET 
                    dob = t.dob,
                    dod = t.dod,
                    summary = t.summary,
                    content = t.content,
                    school_id = t.school_id,
                    tag_id = t.tag_id,
                    updated_at = CURRENT_TIMESTAMP
                FROM temp_philosophers t
                WHERE p.name = t.name;
                
                -- Then insert new records
                INSERT INTO philosophers (name, dob, dod, summary, content, school_id, tag_id, created_at, updated_at)
                SELECT 
                    t.name, t.dob, t.dod, t.summary, t.content, t.school_id, t.tag_id,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                FROM temp_philosophers t
                LEFT JOIN philosophers p ON p.name = t.name
                WHERE p.id IS NULL
                RETURNING id, name, updated_at
            """)
            
            # Get results
            results = cur.fetchall()
            print(f"Processed {len(results)} philosopher records")
            for row in results:
                print(f"- {row[1]} (ID: {row[0]}) - Updated: {row[2]}")

            # Clean up
            cur.execute("DROP TABLE IF EXISTS temp_philosophers")
            conn.commit()

    except Exception as e:
        print(f"Error during import: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import philosopher data from CSV')
    parser.add_argument('csv_file', help='Path to the CSV file')
    args = parser.parse_args()
    
    print(f"Starting import from {args.csv_file}")
    import_philosophers(args.csv_file)
    print("Import completed successfully")
