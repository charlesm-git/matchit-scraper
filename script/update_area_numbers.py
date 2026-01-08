import sys
from pathlib import Path

from scraping.crud import update_area_counts

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse

from config import VALID_COUNTRY_AREAS



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
            if config["area_slug"] == args.area
        ),
        None,
    )
    if not area_config:
        valid_areas = [
            config["area_slug"] for config in VALID_COUNTRY_AREAS[args.country]
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
        area_config=area_config,
        boulders_count=int(boulder_count),
        ascents_count=int(ascent_count),
    )
