import sys
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database import engine

def create_indexes(engine):
    with engine.connect() as conn:
        indexes = [
            # Foreign key indexes (critical for joins and relationship navigation)
            "CREATE INDEX IF NOT EXISTS ix_ascent_boulder_id ON ascent (boulder_id);",
            "CREATE INDEX IF NOT EXISTS ix_ascent_user_id ON ascent (user_id);",
            "CREATE INDEX IF NOT EXISTS ix_ascent_log_grade_id ON ascent (log_grade_id);",
            "CREATE INDEX IF NOT EXISTS ix_boulder_grade_id ON boulder (grade_id);",
            "CREATE INDEX IF NOT EXISTS ix_boulder_crag_id ON boulder (crag_id);",
            "CREATE INDEX IF NOT EXISTS ix_crag_area_id ON crag (area_id);",
            "CREATE INDEX IF NOT EXISTS ix_area_country_id ON area (country_id);",
        ]

        for index in indexes:
            conn.execute(text(index))
            conn.commit()

        print("Running ANALYZE...")
        conn.execute(text("ANALYZE"))
        conn.commit()

    print("✓ All indexes created!")


if __name__ == "__main__":
    create_indexes(engine=engine)
