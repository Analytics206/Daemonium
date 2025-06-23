#!/usr/bin/env python3
"""
Script to import and merge school data from CSV into PostgreSQL.
Handles both new records and updates to existing ones based on name.
"""
import os
import sys
import argparse
from pathlib import Path
import psycopg2
from psycopg2 import sql

# Configuration
DB_CONFIG = {
    'dbname': 'daemonium',
    'user': 'postgres',
    'password': 'ch@ng3m300',
    'host': 'localhost',
    'port': '5432'
}

def run_migration(conn, migration_file):
    """Run a SQL migration file."""
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        with conn.cursor() as cur:
            cur.execute(migration_sql)
        conn.commit()
        print(f"Successfully ran migration: {migration_file}")
        return True
    except Exception as e:
        print(f"Error running migration {migration_file}: {e}")
        conn.rollback()
        return False

def get_connection():
    """Create and return a database connection."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def import_schools(conn, csv_path):
    """Import and merge school data from CSV."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"File not found: {csv_path}")

    with conn.cursor() as cur:
        # Ensure name column has a unique constraint
        try:
            cur.execute("""
                ALTER TABLE schools 
                ADD CONSTRAINT schools_name_key UNIQUE (name);
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
            CREATE TEMP TABLE temp_schools (
                name VARCHAR(255) NOT NULL,
                category VARCHAR(100)
            )
        """)


        # Import CSV to temp table
        with open(csv_path, 'r', encoding='utf-8') as f:
            with conn.cursor() as copy_cur:
                copy_cur.copy_expert(
                    """
                    COPY temp_schools (name, category)
                    FROM STDIN WITH (FORMAT csv, DELIMITER '|', HEADER true, NULL '')
                    """,
                    f
                )

        # Upsert data
        cur.execute("""
            -- First, handle updates
            UPDATE schools s
            SET 
                name = t.name,
                updated_at = CURRENT_TIMESTAMP
            FROM temp_schools t
            WHERE s.name = t.name;
            
            -- Then insert new records
            INSERT INTO schools (name, created_at, updated_at)
            SELECT 
                t.name, 
                CURRENT_TIMESTAMP, 
                CURRENT_TIMESTAMP
            FROM temp_schools t
            WHERE NOT EXISTS (
                SELECT 1 FROM schools s WHERE s.name = t.name
            );

            -- Clean up
            DROP TABLE temp_schools;
        """)
        
        conn.commit()
        print(f"Successfully imported/updated schools from {csv_path}")
        return True

def main():
    parser = argparse.ArgumentParser(description='Import school data from CSV')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('--run-migration', action='store_true', 
                       help='Run the migration before importing data')
    parser.add_argument('--migration-file', default='migrations/0002_create_schools_table.sql',
                       help='Path to the migration file (default: migrations/0002_create_schools_table.sql)')
    
    args = parser.parse_args()
    csv_path = Path(args.csv_file).resolve()
    
    try:
        conn = get_connection()
        
        if args.run_migration:
            migration_file = Path(args.migration_file).resolve()
            print(f"Running migration: {migration_file}")
            if not run_migration(conn, migration_file):
                print("Migration failed. Exiting.")
                return 1
        
        print(f"Importing schools from: {csv_path}")
        import_schools(csv_path)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    sys.exit(main())
