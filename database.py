from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from models.base import Base
from models.grade import Grade

GRADE_ASSOCIATION_DICT = {
    "1": 1,
    "2": 2,
    "3a": 3,
    "3b": 4,
    "3c": 5,
    "4a": 6,
    "4b": 7,
    "4c": 8,
    "5a": 9,
    "5b": 12,
    "5c": 14,
    "6a": 16,
    "6a+": 17,
    "6b": 18,
    "6b+": 20,
    "6c": 21,
    "6c+": 22,
    "7a": 23,
    "7a+": 24,
    "7b": 25,
    "7b+": 26,
    "7c": 27,
    "7c+": 28,
    "8a": 29,
    "8a+": 30,
    "8b": 31,
    "8b+": 32,
    "8c": 33,
    "8c+": 34,
    "9a": 35,
    "9a+": 36,
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
