from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from models.base import Base
from models.grade import Grade

GRADE_ASSOCIATION_DICT = {
    "P": 0,
    "1": 1,
    "1+": 2,
    "2-": 3,
    "2": 4,
    "2+": 5,
    "3-": 6,
    "3": 7,
    "3+": 8,
    "4-": 9,
    "4": 10,
    "4+": 11,
    "5-": 12,
    "5": 13,
    "5+": 14,
    "6a": 15,
    "6a+": 16,
    "6b": 17,
    "6b+": 18,
    "6c": 19,
    "6c+": 20,
    "7a": 21,
    "7a+": 22,
    "7b": 23,
    "7b+": 24,
    "7c": 25,
    "7c+": 26,
    "8a": 27,
    "8a+": 28,
    "8b": 29,
    "8b+": 30,
    "8c": 31,
    "8c+": 32,
    "9a": 33,
}

db_path = "bleau_info_stats.db"

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
