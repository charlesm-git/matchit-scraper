from sqlalchemy import and_, delete, select
from sqlalchemy.orm import joinedload, scoped_session
from scipy.sparse import coo_matrix
import numpy as np

from database import Session
from models.area import Area
from models.ascent import Ascent
from models.boulder import Boulder
from models.crag import Crag
from models.grade import Grade
from models.similarity import Similarity


def get_boulders_for_similarity(session, area_slug):
    boulders = session.scalars(
        select(Boulder)
        .join(Boulder.crag)
        .join(Crag.area)
        .join(Boulder.grade)
        .options(joinedload(Boulder.grade))
        .where(and_(Area.slug == area_slug, Boulder.ascents.any()))
        .order_by(Grade.correspondence, Boulder.name)
    ).all()
    return boulders


def get_ascents_for_similarity(session, area_slug):
    ascents = session.execute(
        select(Ascent.user_id, Boulder.similarity_matrix_id)
        .join(Ascent.boulder)
        .join(Boulder.crag)
        .join(Crag.area)
        .where(
            and_(
                Area.slug == area_slug,
                Boulder.similarity_matrix_id.is_not(None),
            )
        )
    ).all()
    return ascents


def delete_similarity_data(session, area_slug):
    subquery = (
        select(Boulder.id)
        .join(Boulder.crag)
        .join(Crag.area)
        .where(Area.slug == area_slug)
    ).subquery()

    session.execute(
        delete(Similarity).where(
            (Similarity.id1.in_(select(subquery)))
            | (Similarity.id2.in_(select(subquery)))
        )
    )

    session.commit()

    boulders = session.scalars(
        select(Boulder)
        .join(Boulder.crag)
        .join(Crag.area)
        .where(Area.slug == area_slug)
    ).all()
    for boulder in boulders:
        boulder.similarity_matrix_id = None
        session.add(boulder)
    session.commit()


def create_similarity_ids(area_slug: str, session):
    boulders: list[Boulder] = get_boulders_for_similarity(
        session=session, area_slug=area_slug
    )
    for index, boulder in enumerate(boulders):
        boulder.similarity_matrix_id = index
        session.add(boulder)
    session.commit()
    return boulders


def save_similarity_matrix(
    session: scoped_session,
    similarity_matrix: coo_matrix,
    area_slug: str,
    top_N: int = 100,
):
    """Saves the top N similarities per boulder into the database."""

    # Get mapping from matrix_id to actual boulder id
    boulders = session.execute(
        select(Boulder.similarity_matrix_id, Boulder.id)
        .join(Boulder.crag)
        .join(Crag.area)
        .where(Area.slug == area_slug)
    ).all()

    matrix_id_to_boulder_id = {
        matrix_id: boulder_id for matrix_id, boulder_id in boulders
    }

    # Convert to CSR for efficient row slicing
    csr = similarity_matrix.tocsr()

    similarities = []
    for row_id in range(csr.shape[0]):
        # Get all similarities for this boulder
        row = csr.getrow(row_id)
        if row.nnz == 0:
            continue

        indices = row.indices
        data = row.data

        data[row_id == indices] = -1  # Exclude self-similarity

        top_indices = np.argsort(-data)[:top_N]

        boulder_id = matrix_id_to_boulder_id[row_id]
        for idx in top_indices:
            similar_boulder_id = matrix_id_to_boulder_id[indices[idx]]
            similarity = Similarity(
                id1=boulder_id,
                id2=similar_boulder_id,
                score=float(data[idx]),
            )
            similarities.append(similarity)

    session.bulk_save_objects(similarities)
    session.commit()
