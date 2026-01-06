from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from models.base import Base
from models.grade import Grade

GRADE_ASSOCIATION_DICT = [
    {"value": "1", "eightanu_correspondence": 1, "correspondence": 1},
    {"value": "2", "eightanu_correspondence": 2, "correspondence": 2},
    {"value": "3A", "eightanu_correspondence": 3, "correspondence": 3},
    {"value": "3B", "eightanu_correspondence": 4, "correspondence": 4},
    {"value": "3C", "eightanu_correspondence": 5, "correspondence": 5},
    {"value": "4A", "eightanu_correspondence": 6, "correspondence": 6},
    {"value": "4B", "eightanu_correspondence": 7, "correspondence": 7},
    {"value": "4C", "eightanu_correspondence": 8, "correspondence": 8},
    {"value": "5A", "eightanu_correspondence": 9, "correspondence": 9},
    {"value": "5B", "eightanu_correspondence": 12, "correspondence": 10},
    {"value": "5C", "eightanu_correspondence": 14, "correspondence": 11},
    {"value": "6A", "eightanu_correspondence": 16, "correspondence": 12},
    {"value": "6A+", "eightanu_correspondence": 17, "correspondence": 13},
    {"value": "6B", "eightanu_correspondence": 18, "correspondence": 14},
    {"value": "6B+", "eightanu_correspondence": 19, "correspondence": 15},
    {"value": "6C", "eightanu_correspondence": 21, "correspondence": 16},
    {"value": "6C+", "eightanu_correspondence": 22, "correspondence": 17},
    {"value": "7A", "eightanu_correspondence": 23, "correspondence": 18},
    {"value": "7A+", "eightanu_correspondence": 24, "correspondence": 19},
    {"value": "7B", "eightanu_correspondence": 25, "correspondence": 20},
    {"value": "7B+", "eightanu_correspondence": 26, "correspondence": 21},
    {"value": "7C", "eightanu_correspondence": 27, "correspondence": 22},
    {"value": "7C+", "eightanu_correspondence": 28, "correspondence": 23},
    {"value": "8A", "eightanu_correspondence": 29, "correspondence": 24},
    {"value": "8A+", "eightanu_correspondence": 30, "correspondence": 25},
    {"value": "8B", "eightanu_correspondence": 31, "correspondence": 26},
    {"value": "8B+", "eightanu_correspondence": 32, "correspondence": 27},
    {"value": "8C", "eightanu_correspondence": 33, "correspondence": 28},
    {"value": "8C+", "eightanu_correspondence": 34, "correspondence": 29},
    {"value": "9A", "eightanu_correspondence": 35, "correspondence": 30},
    {"value": "9A+", "eightanu_correspondence": 36, "correspondence": 31},
]

GRADES_TO_SCRAPE = [
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    34,
    35,
    36,
]

db_path = "matchit.db"

DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, echo=False)

session_factory = sessionmaker(bind=engine, expire_on_commit=False)

Session = scoped_session(session_factory)


def get_grades_as_object():
    """
    Create and return a list of Grade Objects to initialize the 'grade' table
    in the database
    """
    grades = []
    for grade_data in GRADE_ASSOCIATION_DICT:
        grades.append(
            Grade(
                value=grade_data["value"],
                eightanu_correspondence=grade_data["eightanu_correspondence"],
                correspondence=grade_data["correspondence"],
            )
        )
    return grades


def initialize_empty_db():
    grades = get_grades_as_object()
    with Session() as session:
        Base.metadata.create_all(engine)
        session.add_all(grades)
        session.commit()


def drop_tables():
    Base.metadata.drop_all(engine)
