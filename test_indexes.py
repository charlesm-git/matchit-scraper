# test_indexes.py
from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///bleau_info_stats.db")

# Check what indexes exist on the ascent table
with engine.connect() as conn:
    result = conn.execute(
        text(
            """
        SELECT name, sql 
        FROM sqlite_master 
        WHERE type='index' AND tbl_name='ascent'
    """
        )
    )

    print("Indexes on 'ascent' table:")
    for row in result:
        print(f"  {row[0]}: {row[1]}")

    # Check the query plan for your JOIN
    print("\n" + "=" * 60)
    print("Query plan for: JOIN ascent ON ascent.boulder_id = boulder.id")
    print("=" * 60)

    result = conn.execute(
        text(
            """
        EXPLAIN QUERY PLAN
        SELECT boulder.*, COUNT(ascent.user_id) as ascents
        FROM boulder
        JOIN ascent ON boulder.id = ascent.boulder_id
        JOIN grade ON grade.id = boulder.grade_id
        WHERE grade.id = 1
        GROUP BY ascent.boulder_id
        ORDER BY ascents DESC
        LIMIT 10
    """
        )
    )

    for row in result:
        print(row)
