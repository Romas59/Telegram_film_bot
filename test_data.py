import json
import data

def test_get_films_return_empty_list_when_file_does_not_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(data, "DATA_FILE", tmp_path/"data.json")
    films = data.get_films()
    assert films == []

def test_get_films_reads_films_from_json(tmp_path, monkeypatch):
    data_file = tmp_path / "data.json"
    expected_films = [
        {
            "title": "interstellar",
            "year": 2014,
            "genre": "Sci-Fi",
            "rating": 8.7,
            "actors": "Matthew McConaughey",
            "poster": "https://m.media-amazon.com/images/I/61wrhEawgQL._SY450_.jpg"
        }
    ]

    data_file.write_text(json.dumps(expected_films, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(data, "DATA_FILE", data_file)
    films = data.get_films()
    assert films == expected_films