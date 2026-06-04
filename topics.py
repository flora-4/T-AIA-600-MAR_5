import os
import json
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

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


def split_into_sections(text, n=4):
    words = text.split()
    section_size = len(words) // n

    sections = []
    for i in range(n):
        start = i * section_size
        end = len(words) if i == n - 1 else (i + 1) * section_size
        sections.append(" ".join(words[start:end]))

    return sections


def extract_topics(book_id):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{book_id}_topics.json")

    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            raw = json.load(f)
        return {int(k): v for k, v in raw.items()}

    text = read_book(book_id)
    text = clean_gutenberg_text(text)
    sections = split_into_sections(text)
    vectorizer = CountVectorizer(
        lowercase=True,
        stop_words="english",
        token_pattern=r"\b[a-zA-Z]{3,}\b",
        max_features=5000,
        min_df=2
    )
    matrix = vectorizer.fit_transform(sections)
    lda = LatentDirichletAllocation(n_components=4, random_state=42)
    lda.fit(matrix)
    vocabulary = vectorizer.get_feature_names_out()

    result = {}
    for i, topic in enumerate(lda.components_):
        top_indices = topic.argsort()[-10:][::-1]
        top_words = [vocabulary[j] for j in top_indices]
        result[i + 1] = top_words 
    with open(cache_path, "w") as f:
        json.dump(result, f)

    return result