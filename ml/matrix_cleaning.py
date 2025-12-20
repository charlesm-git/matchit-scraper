from scipy.sparse import csr_matrix, coo_matrix


def matrix_cleaning(
    cleaning_matrix: csr_matrix, matrix_to_clean: coo_matrix
) -> csr_matrix:
    """Remove all values in matrix_to_clean that are not indexed in 
    cleaning_matrix

    :parameters:
    cleaning_matrix: CSR matrix that serves as reference for data existence
    matrix_to_clean: COO matrix from which some indexes are removed"""

    # Boolean mask creation (1D array) - Fancy indexing converted to boolean
    # Check if cleaning_matrix contains the indexes of matrix_to_clean
    mask = cleaning_matrix[matrix_to_clean.row, matrix_to_clean.col].A1 != 0

    # Fancy indexing to remove values from matrix_to_clean that are equal to 0
    # in cleaning_matrix
    new_rows = matrix_to_clean.row[mask]
    new_cols = matrix_to_clean.col[mask]
    new_data = matrix_to_clean.data[mask]

    return csr_matrix(
        (new_data, (new_rows, new_cols)), shape=matrix_to_clean.shape
    )


def grade_matrix_cleaning(grade_similarity_matrix: coo_matrix) -> csr_matrix:
    similarity_grade_cleaned = grade_similarity_matrix.copy()
    similarity_grade_cleaned.data[similarity_grade_cleaned.data < 0.5] = 0
    similarity_grade_cleaned.eliminate_zeros()

    return similarity_grade_cleaned.tocsr()
