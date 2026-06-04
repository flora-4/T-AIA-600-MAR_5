import os
import json
import spacy

BOOK_DIR = os.path.join(os.path.dirname(__file__), "books")
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")


def read_book(book_id):
    path = os.path.join(BOOK_DIR, f"{book_id}.txt")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Le livre {book_id}.txt n'existe pas dans books/")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def clean_gutenberg_text(text):
    start = text.find("*** START")
    end = text.find("*** END")
    if start != -1:
        text = text[start:]
    if end != -1:
        text = text[:end]
    return text


def extract_entities(book_id):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{book_id}_entities.json")

    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            return json.load(f)
    text = read_book(book_id)
    text = clean_gutenberg_text(text)
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        raise OSError(
            "Modèle spaCy manquant. Lance : python -m spacy download en_core_web_sm"
        )
    chunk_size = 100_000
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    characters = set()  
    locations = set()

    for chunk in chunks:
        doc = nlp(chunk)

        for ent in doc.ents:

            if ent.label_ == "PERSON":
                characters.add(ent.text.strip())

            elif ent.label_ in ("GPE", "LOC"):
                locations.add(ent.text.strip())

    result = {
        "characters": sorted(list(characters)),
        "locations": sorted(list(locations))
    }
    with open(cache_path, "w") as f:
        json.dump(result, f)

    return result
