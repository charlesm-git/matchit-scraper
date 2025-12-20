import pandas as pd
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer
from scipy.sparse import coo_matrix
from sqlalchemy import select
from sqlalchemy.orm import joinedload


from models.boulder import Boulder
from database import Session


def similarity_features():
    with Session() as db:
        # Database request
        boulders = (
            db.scalars(
                select(Boulder).options(
                    joinedload(Boulder.grade), joinedload(Boulder.styles)
                )
            )
            .unique()
            .all()
        )

    # Data extraction
    boulders = [
        {
            "id": boulder.id,
            "grade": boulder.grade.correspondence,
            "styles": [style.style for style in boulder.styles],
        }
        for boulder in boulders
    ]

    # Dataframe setup
    boulders_df = pd.DataFrame(boulders)

    style = style_similarity(boulders_df=boulders_df)
    grade = grade_similarity(boulders_df=boulders_df)

    return style, grade


def style_similarity(boulders_df: pd.DataFrame):
    mlb = MultiLabelBinarizer()
    styles = mlb.fit_transform(boulders_df.styles)

    # Conversion to sparse matrix
    styles = coo_matrix(styles, dtype=np.float32)

    # Dot product
    similarity_style = (styles @ styles.T).tocoo()

    # Normalization
    off_diag_max = similarity_style.data[
        similarity_style.row != similarity_style.col
    ].max()
    similarity_style.data /= off_diag_max

    # Re-indexing tp match database
    new_shape = (similarity_style.shape[0] + 1, similarity_style.shape[1] + 1)
    similarity_style = coo_matrix(
        (
            similarity_style.data,
            (similarity_style.row + 1, similarity_style.col + 1),
        ),
        shape=new_shape,
    )

    return similarity_style


def grade_similarity(boulders_df: pd.DataFrame):
    max_grade = boulders_df.grade.max()
    grade_df = pd.get_dummies(boulders_df.grade, dtype=np.float32)

    def grade_fuzzy_one_hot(row, max_grade):
        grade_index = row.idxmax()

        if grade_index == 0:
            return row

        values = np.array([0.5, 0.5], dtype=np.float32)
        offsets = np.array([-1, 1])

        for offset, value in zip(offsets, values):
            current_column = grade_index + offset
            if 0 < current_column <= max_grade:
                row[current_column] = value
        return row

    grade_df = grade_df.apply(
        lambda row: grade_fuzzy_one_hot(row, max_grade=max_grade), axis=1
    )
    grade_df.fillna(0, inplace=True)

    grade = coo_matrix(grade_df)

    # Cosine training
    similarity_grade = cosine_similarity(grade)

    # Re-indexing to match database
    coo = coo_matrix(similarity_grade)

    new_shape = (coo.shape[0] + 1, coo.shape[1] + 1)
    similarity_grade = coo_matrix(
        (
            coo.data,
            (coo.row + 1, coo.col + 1),
        ),
        shape=new_shape,
    )

    return similarity_grade
