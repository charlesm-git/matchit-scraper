import sys
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse

from database import drop_tables, initialize_empty_db
from scraping.ascent import scrape_ascents_for_boulders
from scraping.boulder import scrape_area
from scraping.helper import (
    check_area_validity,
    check_country_validity,
    retrieve_area_config,
)


def reset_db():
    drop_tables()
    initialize_empty_db()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--country", help="Country slug")
    parser.add_argument("-a", "--area", help="Area slug")
    parser.add_argument(
        "--reset", action="store_true", help="Reset database before scraping"
    )
    parser.add_argument(
        "-sb", "--scrape-boulders", action="store_true", help="Scrape boulders"
    )
    parser.add_argument(
        "-sa", "--scrape-ascents", action="store_true", help="Scrape ascents"
    )
    parser.add_argument(
        "--delete-and-rescrape-entire-area",
        action="store_true",
        help="Delete all boulders and ascents in the area and rescrape from scratch",
    )
    parser.add_argument(
        "--delete-and-rescrape-all-ascents",
        action="store_true",
        help="Delete all ascents in the area and rescrape from scratch",
    )

    args = parser.parse_args()

    # Reset database if requested
    if args.reset:
        confirm = input(
            "Are you sure you want to reset the database? This will delete all data. (yes/no): "
        )
        if confirm.lower() != "yes":
            print("Database reset cancelled.")
            sys.exit(0)
        reset_db()

    if not args.scrape_boulders and not args.scrape_ascents:
        print(
            "No scraping action specified. Use --scrape-boulders (-sb) or --scrape-ascents (-sa)."
        )
        sys.exit(0)

    # Scrape boulders if requested
    if args.scrape_boulders:
        if not args.country or not args.area:
            print("Specify both country and area to scrape boulders.")
            sys.exit(0)

        if not check_country_validity(args.country):
            print(f"Invalid country slug: {args.country}")
            sys.exit(0)

        if not check_area_validity(args.country, args.area):
            print(
                f"Invalid area slug: {args.area} for country: {args.country}"
            )
            sys.exit(0)

        # Retrieve area configuration
        area_config = retrieve_area_config(args.country, args.area)

        # Determine if force rescrape is needed
        force_rescrape = args.delete_and_rescrape_entire_area
        scrape_area(args.country, area_config, force_rescrape=force_rescrape)

    # Scrape ascents if requested
    if args.scrape_ascents:
        force_rescrape = args.delete_and_rescrape_all_ascents

        if not args.country or not args.area:
            print(
                "\nNo country or area specified, scraping ascents for all areas."
            )
            scrape_ascents_for_boulders(force_rescrape=force_rescrape)

        if not check_country_validity(args.country):
            print(f"\nInvalid country slug: {args.country}")
            sys.exit(0)

        if not check_area_validity(args.country, args.area):
            print(
                f"\nInvalid area slug: {args.area} for country: {args.country}"
            )
            sys.exit(0)

        area_config = retrieve_area_config(args.country, args.area)
        scrape_ascents_for_boulders(area_config, force_rescrape=force_rescrape)
