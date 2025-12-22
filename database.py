from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from models.base import Base
from models.grade import Grade

GRADE_ASSOCIATION_DICT = {
    "1": 1,
    "2": 2,
    "3A": 3,
    "3B": 4,
    "3C": 5,
    "4A": 6,
    "4B": 7,
    "4C": 8,
    "5A": 9,
    "5B": 12,
    "5C": 14,
    "6A": 16,
    "6A+": 17,
    "6B": 18,
    "6B+": 20,
    "6C": 21,
    "6C+": 22,
    "7A": 23,
    "7A+": 24,
    "7B": 25,
    "7B+": 26,
    "7C": 27,
    "7C+": 28,
    "8A": 29,
    "8A+": 30,
    "8B": 31,
    "8B+": 32,
    "8C": 33,
    "8C+": 34,
    "9A": 35,
    "9A+": 36,
}

db_path = "matchit.db"

DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, echo=False)

session_factory = sessionmaker(bind=engine)

Session = scoped_session(session_factory)


def get_grades_as_object():
    """
    Create and return a list of Grade Objects to initialize the 'grade' table
    in the database
    """
    grades = []
    for value, correspondence in GRADE_ASSOCIATION_DICT.items():
        grades.append(Grade(value=value, correspondence=correspondence))
    return grades


def initialize_empty_db():
    grades = get_grades_as_object()
    with Session() as session:
        Base.metadata.create_all(engine)
        session.add_all(grades)
        session.commit()


def drop_tables():
    Base.metadata.drop_all(engine)
