import argparse
import sys

from sqlalchemy import select
from config import VALID_COUNTRY_AREAS
from database import Session, drop_tables, initialize_empty_db
from models.area import Area
from models.boulder import Boulder
from models.country import Country
from models.grade import Grade
from scraping.ascent import scrape_ascents_for_boulders_in_area, scrape_ascents_from_boulder
from scraping.boulder import scrape_area


def reset_db():
    drop_tables()
    initialize_empty_db()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--country", required=True, help="Country slug")
    parser.add_argument("--area", required=True, help="Area slug")
    parser.add_argument(
        "--reset", action="store_true", help="Reset database before scraping"
    )
    parser.add_argument(
        "--scrape-boulders", action="store_true", help="Scrape boulders"
    )
    parser.add_argument(
        "--scrape-ascents", action="store_true", help="Scrape ascents"
    )
    args = parser.parse_args()

    # Validate country and area
    if args.country not in VALID_COUNTRY_AREAS:
        print(f"Error: Unknown country '{args.country}'")
        print(f"Valid countries: {', '.join(VALID_COUNTRY_AREAS.keys())}")
        sys.exit(1)
    if args.area not in VALID_COUNTRY_AREAS[args.country]:
        print(
            f"Error: Area '{args.area}' not valid for country '{args.country}'"
        )
        print(f"Valid areas: {', '.join(VALID_COUNTRY_AREAS[args.country])}")
        sys.exit(1)

    # Reset database if requested
    if args.reset:
        reset_db()
    
    if not args.scrape_boulders and not args.scrape_ascents:
        print("No scraping action specified. Use --scrape-boulders or --scrape-ascents.")
        sys.exit(0)
    
    # Scrape boulders if requested
    if args.scrape_boulders:
        scrape_area(args.country, args.area)

    # Scrape ascents if requested
    if args.scrape_ascents:
        scrape_ascents_for_boulders_in_area(args.area)