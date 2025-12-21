import argparse
import sys
from config import VALID_COUNTRY_AREAS
from database import Session, drop_tables, initialize_empty_db
from models.area import Area
from models.country import Country
from scraping.boulder import scrape_boulders_by_grade


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

    with Session() as db:
        country: Country = Country.get_by_slug(db, args.country)
        area: Area = Area.get_by_slug(db, args.area)
        
        if not country:
            country = Country.create(
                db,
                name=args.country.capitalize(),
                name_normalized=args.country,
                slug=args.country,
            )
        if not area:
            area = Area.create(
                db,
                name=args.area.capitalize(),
                name_normalized=args.area,
                slug=args.area,
                country_id=country.id,
            )

        page_index = None
        if (
            not area.scraped_boulders
            and area.current_scraping_page is not None
        ):
            page_index = area.current_scraping_page

        scrape_boulders_by_grade(db, country, area, 16, page_index)
