import sqlite3
from pathlib import Path

# Database path

DB_PATH = Path(__file__).parent.parent / "matchit.db"

# SQL statements to execute
# Update this section with your migration SQL
SQL_STATEMENTS = """
-- Add indexes on foreign keys for performance
CREATE INDEX IF NOT EXISTS ix_ascent_boulder_id ON ascent (boulder_id);
CREATE INDEX IF NOT EXISTS ix_ascent_user_id ON ascent (user_id);
CREATE INDEX IF NOT EXISTS ix_ascent_log_grade_id ON ascent (log_grade_id);
CREATE INDEX IF NOT EXISTS ix_boulder_grade_id ON boulder (grade_id);
CREATE INDEX IF NOT EXISTS ix_boulder_crag_id ON boulder (crag_id);
CREATE INDEX IF NOT EXISTS ix_crag_area_id ON crag (area_id);
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
