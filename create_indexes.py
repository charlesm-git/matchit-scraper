from sqlalchemy import text
from database import engine


def create_indexes(engine):
    with engine.connect() as conn:
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_ascent_boulder ON ascent(boulder_id)",  # For one boulder_id, list all the user.id
            "CREATE INDEX IF NOT EXISTS idx_boulder_grade_id ON boulder(grade_id)",  # For one grade, list all the boulders
            "CREATE INDEX IF NOT EXISTS idx_boulder_grade_rating ON boulder(grade_id, number_of_rating, rating DESC)",
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
