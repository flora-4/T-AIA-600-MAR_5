import re
import subprocess
import sys
import json
import os
from collections import Counter

try:
    import spacy
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "spacy"])
    import spacy

try:
    spacy.load("en_core_web_sm")
except OSError:
    subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    import importlib
    importlib.reload(spacy)


BLACKLIST_FILE = os.path.join(os.path.dirname(__file__), "entities_blacklists.json")

with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
    BLACKLISTS = json.load(f)

PERSON_BLACKLIST = set(w.lower() for w in BLACKLISTS["person_blacklist"])
LOCATION_BLACKLIST = set(w.lower() for w in BLACKLISTS["location_blacklist"])

LOCATION_INDICATORS = set(w.lower() for w in BLACKLISTS.get("location_indicators", []))
PERSON_INDICATORS = set(w.lower() for w in BLACKLISTS.get("person_indicators", []))


def trim_front_matter(text):
    patterns = [
        r"\n\s*CHAPTER\s+1[\.\s]",
        r"\n\s*CHAPTER\s+I[\.\s]",
        r"\n\s*Chapter\s+1[\.\s]",
        r"\n\s*Chapter\s+I[\.\s]",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return text[match.start():]

    return text


def clean_entity_text(text):
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip(".,;:!?\"'()[]{}--_")
    return text


def is_valid_entity(text):
    if not text:
        return False

    if "\n" in text or "\r" in text:
        return False

    if re.search(r'[\\/<>{}|\[\]@#$%^*+=~`]', text):
        return False

    if re.fullmatch(r"[IVXLCDM]{1,6}\.?", text.strip()):
        return False

    if len(text.strip()) < 2 or len(text.strip()) > 40:
        return False

    if not re.search(r"[a-zA-Z]", text):
        return False

    if len(text.strip().split()) > 4:
        return False

    if text[0].islower():
        return False

    # Rejette les mots entièrement en majuscules trop suspects.
    if text.isupper() and len(text) > 4:
        return False

    return True


def get_preceding_context(ent, size=3):
    start = ent.start
    tokens = []

    for i in range(max(0, start - size), start):
        token = ent.doc[i].text.lower().strip(".,;:!?\"'()")
        tokens.append(token)

    return tokens


def has_indicator(ent, indicators):
    preceding = get_preceding_context(ent)
    context_str = " ".join(preceding)

    for token in preceding:
        if token in indicators:
            return True

    for indicator in indicators:
        if " " in indicator and indicator in context_str:
            return True

    return False


def deduplicate_by_frequency(entity_counter):
    sorted_names = sorted(
        entity_counter.keys(),
        key=lambda name: entity_counter[name],
        reverse=True
    )

    kept = []

    for name in sorted_names:
        lower_name = name.lower()

        is_variant = any(
            lower_name != existing.lower()
            and lower_name.startswith(existing.lower())
            for existing in kept
        )

        if not is_variant:
            kept.append(name)

    return kept


def filter_entities(entity_counter, min_count=2, max_items=25):
    filtered = Counter()

    for name, count in entity_counter.items():
        if count >= min_count:
            filtered[name] = count

    return Counter(dict(filtered.most_common(max_items)))


def get_title_words(header):
    """
    Essaie de récupérer les mots importants du titre depuis le header Gutenberg.
    Cela aide à prioriser un lieu/personnage central comme Wonderland.
    """
    title_words = set()

    for line in header.splitlines():
        if line.lower().startswith("title:"):
            title = line.split(":", 1)[1]
            words = re.findall(r"[A-Z][a-zA-Z]+", title)
            title_words.update(w.lower() for w in words)

    return title_words


def extract_entities(array):
    if not array:
        print("Aucun livre à traiter")
        return {}

    header = array[0] if len(array) > 0 else ""
    text = array[1]

    if not text or len(text.split()) < 100:
        print("Texte trop court pour extraire des entités")
        return {}

    title_words = get_title_words(header)

    text = trim_front_matter(text)

    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        raise OSError("Modèle spaCy manquant. Lance : python -m spacy download en_core_web_sm")

    nlp.max_length = len(text) + 100

    chunk_size = 100_000
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    characters = Counter()
    locations = Counter()

    for chunk in chunks:
        doc = nlp(chunk)

        for ent in doc.ents:
            cleaned = clean_entity_text(ent.text)

            if not is_valid_entity(cleaned):
                continue

            lower = cleaned.lower()

            if ent.label_ == "PERSON":
                if lower not in PERSON_BLACKLIST:
                    score = 1

                    if has_indicator(ent, PERSON_INDICATORS):
                        score += 1

                    if lower in title_words:
                        score += 3

                    characters[cleaned] += score

            elif ent.label_ in ("GPE", "LOC"):
                if lower not in LOCATION_BLACKLIST:
                    score = 1

                    if has_indicator(ent, LOCATION_INDICATORS):
                        score += 1

                    if lower in title_words:
                        score += 4

                    locations[cleaned] += score

    word_count = len(text.split())

    if word_count > 100000:
        min_char_count = 4
        min_loc_count = 2
    elif word_count > 40000:
        min_char_count = 3
        min_loc_count = 1
    else:
        min_char_count = 2
        min_loc_count = 1

    characters = filter_entities(characters, min_count=min_char_count, max_items=25)
    locations = filter_entities(locations, min_count=min_loc_count, max_items=20)

    return {
        "characters": deduplicate_by_frequency(characters),
        "locations": deduplicate_by_frequency(locations),
    }