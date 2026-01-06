import string
import sys
import unicodedata

from config import VALID_COUNTRY_AREAS


# Graceful shutdown flag
shutdown_requested = False


# Signal handler for graceful shutdown
def signal_handler(signum, frame):
    """Handle termination signals to allow graceful shutdown."""
    global shutdown_requested
    if shutdown_requested:
        print("\nForce quit.")
        sys.exit(1)
    shutdown_requested = True
    print("\nShutdown requested. Finishing current page...")


def text_normalizer(text: str):
    # Decompose accents
    text = unicodedata.normalize("NFD", text)
    # Remove decomposed part of accents to only keep letter
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    # Lower case aggressively
    text = text.casefold()

    return text


def check_country_validity(country_slug: str) -> bool:
    """Check if the given country and area slugs are valid."""
    if country_slug not in VALID_COUNTRY_AREAS:
        return False
    return True


def check_area_validity(country_slug: str, area_slug: str) -> bool:
    """Check if the given area slug is valid for the specified country."""
    valid_areas = [
        config["area"] for config in VALID_COUNTRY_AREAS[country_slug]
    ]
    return area_slug in valid_areas


def get_area_config(country_slug: str, area_slug: str) -> dict:
    """Retrieve the configuration dictionary for the specified country and area slugs."""
    for config in VALID_COUNTRY_AREAS[country_slug]:
        if config["area"] == area_slug:
            return config
    return {}


def get_all_areas_to_process() -> list[dict]:
    """Retrieve all area configurations to process."""
    areas = []
    for country_configs in VALID_COUNTRY_AREAS.values():
        for config in country_configs:
            areas.append(config)
    return areas
