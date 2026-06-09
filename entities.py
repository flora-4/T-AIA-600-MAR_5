import re, subprocess, sys, json, os

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

BLACKLIST_FILE = os.path.join(
    os.path.dirname(__file__),
    "entities_blacklists.json"
)

with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
    BLACKLISTS = json.load(f)

PERSON_BLACKLIST = set(BLACKLISTS["person_blacklist"])
LOCATION_BLACKLIST = set(BLACKLISTS["location_blacklist"])

def is_valid_entity(text):
    if '\n' in text or '\r' in text:
        return False

    if re.search(r'[\\/<>{}|\[\]@#$%^*+=~`]', text):
        return False
    if re.fullmatch(r'[IVXLCDM]{2,}', text.strip()):
        return False
    if len(text.strip()) < 2 or len(text.strip()) > 40:
        return False
    if not re.search(r'[a-zA-Z]', text):
        return False
    if len(text.strip().split()) > 4:
        return False
    if text[0].islower():
        return False
    return True


def clean_entity_text(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.strip(".,;:!?\"'()--_")
    return text


def deduplicate_by_frequency(entity_dict):
    sorted_names = sorted(entity_dict.keys(), key=lambda x: entity_dict[x], reverse=True)
    kept = []
    for name in sorted_names:
        is_variant = any(
            name != existing and name.startswith(existing)
            for existing in kept
        )
        if not is_variant:
            kept.append(name)
    return kept


def extract_entities(array):
   
    if not array:
        print("aucun livre à traiter")
        return {}

    text = array[1]
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        raise OSError("Modèle spaCy manquant. Lance : python -m spacy download en_core_web_sm")
    chunk_size = 100_000
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    characters = {}
    locations = {}

    for chunk in chunks:
        doc = nlp(chunk)
        for ent in doc.ents:
            raw = ent.text
            cleaned = clean_entity_text(raw)

            if not is_valid_entity(cleaned):
                continue

            lower = cleaned.lower()

            if ent.label_ == "PERSON":
                if lower not in PERSON_BLACKLIST:
                    characters[cleaned] = characters.get(cleaned, 0) + 1

            elif ent.label_ in ("GPE", "LOC"):
                if lower not in LOCATION_BLACKLIST:
                    locations[cleaned] = locations.get(cleaned, 0) + 1

    return {
        "characters": deduplicate_by_frequency(characters),
        "locations":  deduplicate_by_frequency(locations),
    }