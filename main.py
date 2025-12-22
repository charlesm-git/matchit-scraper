import argparse
import sys
from config import VALID_COUNTRY_AREAS
from database import drop_tables, initialize_empty_db
from models.area import Area
from models.country import Country
from models.grade import Grade
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
    args = parser.parse_args()
    
    if args.country not in VALID_COUNTRY_AREAS:
        print(f"Error: Unknown country '{args.country}'")
        print(f"Valid countries: {', '.join(VALID_COUNTRY_AREAS.keys())}")
        sys.exit(1)
    
    if args.area not in VALID_COUNTRY_AREAS[args.country]:
        print(f"Error: Area '{args.area}' not valid for country '{args.country}'")
        print(f"Valid areas: {', '.join(VALID_COUNTRY_AREAS[args.country])}")
        sys.exit(1)

    if args.reset:
        reset_db()
        
    scrape_area(args.country, args.area)
