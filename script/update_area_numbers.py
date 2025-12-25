import sys
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from sqlalchemy import select

from config import VALID_COUNTRY_AREAS
from database import Session
from models.area import Area
from models.country import Country


def update_area_counts(
    country: str, area: str, boulders_count: int, ascents_count: int
):
    """Update area counts for boulders and ascents."""
    with Session() as session:
        area_obj = session.scalar(
            select(Area)
            .join(Area.country)
            .where(
                Area.name_normalized == area,
                Country.name_normalized == country,
            ),
        )
        
        if not area_obj:
            print(f"Error: Area '{area}' not found in country '{country}'")
            return

        area_obj.boulders_count = boulders_count
        area_obj.ascents_count = ascents_count
        session.add(area_obj)
        session.commit()

        print("Area counts updated successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--country", required=True, help="Country slug")
    parser.add_argument("-a", "--area", required=True, help="Area slug")

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

    print(f"Updating area numbers for {args.country} - {args.area}...")

    boulder_count = input("Enter the number of boulders: ")
    ascent_count = input("Enter the number of ascents: ")
    update_area_counts(
        country=args.country,
        area=args.area,
        boulders_count=int(boulder_count),
        ascents_count=int(ascent_count),
    )
