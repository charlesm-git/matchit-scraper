# scraper/config.py
from pathlib import Path

# Paths
SCRAPER_DIR = Path(__file__).parent
API_DIR = Path(__file__).parent.parent / "api"

# Files
DB_FILE = "bleau_info_stats.db"
ASCENT_MATRIX_FILE = "similarity_ascent.npz"
GRADE_MATRIX_FILE = "similarity_grade.npz"
STYLE_MATRIX_FILE = "similarity_style.npz"


# Git
GIT_BRANCH = "main"
REMOTE_NAME = "origin"

VALID_COUNTRY_AREAS = {
    "austria": [
        {
            "area": "silvretta",
            "area_slug": "silvretta",
            "area_name": "Silvretta",
            "is_crag_in_db": True,
            "single_layer_division": False,
        }
    ],
    "france": [
        {
            "area": "fontainebleau",
            "area_slug": "fontainebleau",
            "area_name": "Fontainebleau",
            "is_crag_in_db": False,
            "single_layer_division": False,
        }
    ],
    "italy": [
        {
            "area": "val-daone",
            "area_slug": "val-daone",
            "area_name": "Val Daone",
            "is_crag_in_db": False,
            "single_layer_division": True,
        },
        {
            "area": "val-di-mello",
            "area_slug": "val-di-mello",
            "area_name": "Val di Mello",
            "is_crag_in_db": False,
            "single_layer_division": True,
        },
    ],
    "spain": [
        {
            "area": "albarracin",
            "area_slug": "unknown-crag",
            "area_name": "Albarracín",
            "is_crag_in_db": True,
            "single_layer_division": False,
        }
    ],
    "sweden": [
        {
            "area": "vastervik",
            "area_slug": "vaestervik",
            "area_name": "Västervik",
            "is_crag_in_db": True,
            "single_layer_division": False,
        }
    ],
    "switzerland": [
        {
            "area": "bas-valais",
            "area_slug": "bas-valais",
            "area_name": "Bas-Valais",
            "is_crag_in_db": False,
            "single_layer_division": False,
        },
        {
            "area": "magic-wood",
            "area_slug": "magic-wood",
            "area_name": "Magic Wood",
            "is_crag_in_db": True,
            "single_layer_division": True,
        },
        {
            "area": "ticino",
            "area_slug": "ticino",
            "area_name": "Ticino",
            "is_crag_in_db": False,
            "single_layer_division": False,
            "added_crags": [
                {
                    "name": "Bodio",
                    "slug": "bodio",
                },
                {
                    "name": "Osogna",
                    "slug": "osogna",
                },
                {
                    "name": "Val Calanca",
                    "slug": "val-calanca",
                },
                {
                    "name": "Sobrio",
                    "slug": "sobrio",
                }
            ],
        },
    ],
    "south africa": [
        {
            "area": "rocklands",
            "area_slug": "rocklands",
            "area_name": "Rocklands",
            "is_crag_in_db": False,
            "single_layer_division": False,
        }
    ],
}

AUTHENTICATION_COOKIE = "a8ca6c30-b0f4-40d9-b509-a7566eb36a4d"

SIMILARITY_GRADE_WEIGHT = 1
SIMILARITY_ASCENT_WEIGHT = 5
