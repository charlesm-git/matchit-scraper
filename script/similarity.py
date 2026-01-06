import argparse
import sys
from pathlib import Path

from sqlalchemy import text

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SIMILARITY_ASCENT_WEIGHT, SIMILARITY_GRADE_WEIGHT
from database import Session
from ml.crud import (
    create_similarity_ids,
    delete_similarity_data,
    save_similarity_matrix,
)
from ml.matrix_cleaning import grade_matrix_cleaning, matrix_cleaning
from ml.grade_similarity import similarity_grade
from ml.ascents_similarity import similarity_ascents
from scraping.helper import (
    check_area_validity,
    check_country_validity,
    get_all_areas_to_process,
    get_area_config,
)


def similarity_algorithm(area_config: dict):
    """Compute similarity matrices, clean them, convert them to csr and save
    them as .npz"""

    print(
        f"\nStarting similarity algorithm for area: {area_config["area_name"]}"
    )

    with Session() as session:
        print("\nStep 1: Deleting existing similarity data...")
        delete_similarity_data(
            session=session, area_slug=area_config["area_slug"]
        )
        print("Step 1 completed.")

        print("\nStep 2: Creating similarity IDs...")
        boulders = create_similarity_ids(
            session=session, area_slug=area_config["area_slug"]
        )
        print(f"Step 2 completed. {len(boulders)} boulders processed.")

        print("\nStep 3: Computing similarity matrices...")
        # Similarity matrix computation. All in COO format
        print("Ascent similarity calculation")
        similarity_ascents_matrix = similarity_ascents(
            area_slug=area_config["area_slug"]
        )
        print("Grade similarity calculation")
        similarity_grades_matrix = similarity_grade(boulders=boulders)
        print("Step 3 completed.")

        # Matrix cleaning (removing irrelevant values)
        print("\nStep 4: Matrix cleaning...")
        similarity_grades_matrix = grade_matrix_cleaning(
            similarity_grades_matrix
        )
        similarity_ascents_matrix = matrix_cleaning(
            cleaning_matrix=similarity_grades_matrix,
            matrix_to_clean=similarity_ascents_matrix,
        )
        print("Step 4 completed.")

        # Matrix saving
        print("\nStep 5: Matrix aggregation...")
        similarity_matrix = (
            SIMILARITY_ASCENT_WEIGHT * similarity_ascents_matrix
        )
        print("Step 5 completed.")

        print("\nStep 6: Saving similarity data to database...")
        save_similarity_matrix(
            session=session,
            similarity_matrix=similarity_matrix,
            area_slug=area_config["area_slug"],
            top_N=150,
        )
        print("Step 6 completed.")

        print("\nStep 7: Optimizing database...")
        session.execute(text("ANALYZE"))
        session.commit()
        print("Step 7 completed.")

    print("ML algorithm completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--country", help="Country slug")
    parser.add_argument("--area", help="Area slug")
    parser.add_argument("--all", action="store_true", help="Run for all areas")
    args = parser.parse_args()

    if (not args.country or not args.area) and not args.all:
        print(
            "Specify both country and area to scrape boulders, or use --all to run for all areas."
        )
        sys.exit(0)

    if args.all:
        areas = get_all_areas_to_process()
        for area_config in areas:
            user_input = input(
                f"\nSimilarity algorithm is running for {area_config['area_name']}"
                f"\nAll current similarity data will be overwritten. Proceed? (yes/no): "
            )

            if user_input.lower() == "yes":
                similarity_algorithm(area_config=area_config)
    else:
        if not check_country_validity(args.country):
            print(f"Invalid country slug: {args.country}")
            sys.exit(0)

        if not check_area_validity(args.country, args.area):
            print(
                f"Invalid area slug: {args.area} for country: {args.country}"
            )
            sys.exit(0)

        user_input = input(
            f"\nSimilarity algorithm is running for {args.area}"
            f"\nAll current similarity data will be overwritten. Proceed? (yes/no): "
        )

        if user_input.lower() == "yes":
            area_config = get_area_config(args.country, args.area)
            similarity_algorithm(area_config=area_config)
