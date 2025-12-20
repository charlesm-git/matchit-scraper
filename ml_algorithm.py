from scipy.sparse import save_npz

from ml.matrix_cleaning import grade_matrix_cleaning, matrix_cleaning
from ml.feature_similarity import similarity_features
from ml.ascents_similarity import similarity_ascents


def similarity_algorithm():
    """Compute similarity matrices, clean them, convert them to csr and save
    them as .npz"""

    # Similarity matrix computation. All in COO format
    print("Ascent similarity calculation...")
    similarity_ascents_matrix = similarity_ascents()
    print("Feature similarity calculation...")
    similarity_styles_matrix, similarity_grades_matrix = similarity_features()

    # Matrix cleaning (removing irrelevant values)
    print("Matrix cleaning...")
    similarity_grades_matrix = grade_matrix_cleaning(similarity_grades_matrix)
    similarity_styles_matrix = matrix_cleaning(
        cleaning_matrix=similarity_grades_matrix,
        matrix_to_clean=similarity_styles_matrix,
    )
    similarity_ascents_matrix = matrix_cleaning(
        cleaning_matrix=similarity_grades_matrix,
        matrix_to_clean=similarity_ascents_matrix,
    )

    # Matrix saving
    print("Matrix saving...")
    save_npz("./similarity_ascent.npz", similarity_ascents_matrix)
    save_npz("./similarity_style.npz", similarity_styles_matrix)
    save_npz("./similarity_grade.npz", similarity_grades_matrix)
    
    print("ML algorythm completed successfully.")


if __name__ == "__main__":
    similarity_algorithm()
