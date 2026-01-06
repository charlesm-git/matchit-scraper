import pandas as pd
import numpy as np
from scipy.sparse import coo_matrix

from database import Session
from ml.crud import get_ascents_for_similarity


def similarity_ascents(area_slug: str) -> coo_matrix:
    # DB query
    with Session() as db:
        ascents = get_ascents_for_similarity(session=db, area_slug=area_slug)
        ascents_df = pd.DataFrame(data=ascents, columns=["user_id", "id"])

    boulder_user_matrix = ascents_df.pivot_table(
        index="id",
        columns="user_id",
        aggfunc="size",
        fill_value=0,
        dropna=True,
    )
    boulder_ids = boulder_user_matrix.index

    # Conversion of boulder_user matrix to sparce matrix
    boulder_user_matrix = coo_matrix(boulder_user_matrix)

    similarity_ascents = jaccard_pairwise_similarity(
        boulder_user_matrix, boulder_ids=boulder_ids
    )

    return similarity_ascents


def jaccard_pairwise_similarity(X, boulder_ids):
    # CSR matrix storing the number of shared ascents for each pair of
    # boulders sharing at least one ascent

    intersection = X @ X.T

    # 1D array storing the total number of ascent for each boulder
    row_sums = np.asarray(X.sum(axis=1)).ravel()

    # intersection decomposition for calculation on 1D arrays
    rows, cols = intersection.nonzero()
    intersection_data = intersection.data

    union = row_sums[rows] + row_sums[cols] - intersection_data

    jaccard = intersection_data / union

    # Index remapping based on the boulder ids
    new_rows = boulder_ids[rows]
    new_cols = boulder_ids[cols]

    return coo_matrix(
        (jaccard, (new_rows, new_cols)),
        dtype=np.float32,
    )
