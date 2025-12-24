import argparse
import sys

from config import VALID_COUNTRY_AREAS
from database import drop_tables, initialize_empty_db
from scraping.ascent import scrape_ascents_for_boulders_in_area
from scraping.boulder import scrape_area


def reset_db():
    drop_tables()
    initialize_empty_db()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--country", required=True, help="Country slug")
    parser.add_argument("-a", "--area", required=True, help="Area slug")
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

    # Validate country and area
    if args.country not in VALID_COUNTRY_AREAS:
        print(f"Error: Unknown country '{args.country}'")
        print(f"Valid countries: {', '.join(VALID_COUNTRY_AREAS.keys())}")
        sys.exit(1)

    # Find area config
    area_config = next(
        (
            config
            for config in VALID_COUNTRY_AREAS[args.country]
            if config["area"] == args.area
        ),
        None,
    )
    if not area_config:
        valid_areas = [
            config["area"] for config in VALID_COUNTRY_AREAS[args.country]
        ]
        print(
            f"Error: Area '{args.area}' not valid for country '{args.country}'"
        )
        print(f"Valid areas: {', '.join(valid_areas)}")
        sys.exit(1)

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
        # Determine if force rescrape is needed
        force_rescrape = args.delete_and_rescrape_entire_area
        scrape_area(
            args.country, area_config, force_rescrape=force_rescrape
        )

    # Scrape ascents if requested
    if args.scrape_ascents:
        force_rescrape = args.delete_and_rescrape_all_ascents
        scrape_ascents_for_boulders_in_area(
            area_config, force_rescrape=force_rescrape
        )
