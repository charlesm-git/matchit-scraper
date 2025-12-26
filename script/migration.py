import sqlite3
from pathlib import Path

# Database path

DB_PATH = Path(__file__).parent.parent / "matchit.db"

# SQL statements to execute
# Update this section with your migration SQL
SQL_STATEMENTS = """
-- Write your SQL migration statements here
UPDATE grade SET correspondence =
    CASE value
        WHEN '1' THEN 1
        WHEN '2' THEN 2
        WHEN '3A' THEN 3
        WHEN '3B' THEN 4
        WHEN '3C' THEN 5
        WHEN '4A' THEN 6
        WHEN '4B' THEN 7
        WHEN '4C' THEN 8
        WHEN '5A' THEN 9
        WHEN '5B' THEN 10
        WHEN '5C' THEN 11
        WHEN '6A' THEN 12
        WHEN '6A+' THEN 13
        WHEN '6B' THEN 14
        WHEN '6B+' THEN 15
        WHEN '6C' THEN 16
        WHEN '6C+' THEN 17
        WHEN '7A' THEN 18
        WHEN '7A+' THEN 19
        WHEN '7B' THEN 20
        WHEN '7B+' THEN 21
        WHEN '7C' THEN 22
        WHEN '7C+' THEN 23
        WHEN '8A' THEN 24
        WHEN '8A+' THEN 25
        WHEN '8B' THEN 26
        WHEN '8B+' THEN 27
        WHEN '8C' THEN 28
        WHEN '8C+' THEN 29
        WHEN '9A' THEN 30
        WHEN '9A+' THEN 31
    END;
"""


def run_migration():
    """Execute SQL migration on the database."""
    print(f"Connecting to database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Execute SQL statements
        print("Executing migration...")
        cursor.executescript(SQL_STATEMENTS)
        conn.commit()
        print("Migration completed successfully.")

    except sqlite3.Error as e:
        print(f"ERROR during migration: {e}")
        conn.rollback()

    finally:
        conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION")
    print("=" * 60)
    print()

    # Show SQL to be executed
    print("SQL to execute:")
    print("-" * 60)
    print(SQL_STATEMENTS.strip())
    print("-" * 60)
    print()

    # Confirm execution
    response = input("Execute migration? (yes/no): ").lower()
    if response == "yes":
        run_migration()
    else:
        print("Migration cancelled.")
