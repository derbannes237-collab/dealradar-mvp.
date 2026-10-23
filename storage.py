
import json
from pathlib import Path

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "listings.json"


def load_listings():
    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_listings(listings):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(listings, file, ensure_ascii=False, indent=2)


def add_listing(listing):
    listings = load_listings()
    listings.append(listing)
    save_listings(listings)
    return listing
