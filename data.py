import json
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data.json"


def get_films():
    if not DATA_FILE.exists():
        return []
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
            if isinstance(data, list):
                return data
            return []
    except json.JSONDecodeError:
        return []


def save_films(films):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(films, file, ensure_ascii=False, indent=4)


def add_film(film: dict) -> None:
    films = get_films()
    if not isinstance(films, list):
        films = []
    films.append(film)
    save_films(films)


def remove_film(identifier: str) -> None:
    films = get_films()
    updated_films = [
        f for f in films 
        if isinstance(f, dict) and f.get("imdbID") != identifier and f.get("title") != identifier and f.get("Title") != identifier
    ]
    save_films(updated_films)


def clear_films() -> None:
    save_films([])