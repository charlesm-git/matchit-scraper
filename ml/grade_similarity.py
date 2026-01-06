import pandas as pd
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import coo_matrix


def grade_fuzzy_one_hot(row, min_grade, max_grade):
    grade_index = row.idxmax()

    if grade_index == 0:
        return row

    values = np.array([0.5, 0.75, 0.75, 0.5], dtype=np.float32)
    offsets = np.array([-2, -1, 1, 2])

    for offset, value in zip(offsets, values):
        current_column = grade_index + offset
        if min_grade < current_column <= max_grade:
            row[current_column] = value
    return row


def similarity_grade(boulders):
    # Data extraction
    boulders = [
        {
            "id": boulder.id,
            "grade": boulder.grade.correspondence,
        }
        for boulder in boulders
    ]

    # Dataframe setup
    boulders_df = pd.DataFrame(boulders)

    # Variable setup
    max_grade = boulders_df.grade.max()
    min_grade = boulders_df.grade.min()
    grade_df = pd.get_dummies(boulders_df.grade, dtype=np.float32)

    # Apply fuzzy one-hot encoding
    grade_df = grade_df.apply(
        lambda row: grade_fuzzy_one_hot(
            row, min_grade=min_grade, max_grade=max_grade
        ),
        axis=1,
    )
    grade_df.fillna(0, inplace=True)

    # Conversion to sparse matrix
    grade = coo_matrix(grade_df)

    # Cosine training
    similarity_grade = cosine_similarity(grade)

    # Conversion to COO matrix
    similarity_grade = coo_matrix(similarity_grade)

    return similarity_grade
