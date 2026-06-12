import json
import os
import re
import subprocess
import sys
from collections import Counter

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "scikit-learn"])
    from sklearn.feature_extraction.text import TfidfVectorizer


SECTION_SIZE = 1000
MIN_TEXT_WORDS = 30
MIN_SECTION_WORDS = 80
MIN_SECTIONS = 3
TOPICS_PER_SECTION = 10
RANKED_WORDS_FOR_CATEGORY = 80
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")
BOOKS_COLLECTION_PATH = os.path.join(os.path.dirname(__file__), "books_collection.json")
CROSS_SECTION_THRESHOLD = 0.35


def tokenize_words(text):
    return re.findall(r"\b[a-zA-Z']{2,}\b", text.lower())


def split_into_sections(text, section_size=SECTION_SIZE):
    words = tokenize_words(text)
    if not words:
        return []

    total_words = len(words)
    if total_words < MIN_SECTION_WORDS * MIN_SECTIONS:
        return [" ".join(words)] if total_words >= MIN_TEXT_WORDS else []

    target_sections = max(MIN_SECTIONS, total_words // section_size)
    effective_size = max(MIN_SECTION_WORDS, total_words // target_sections)

    sections = []
    for start in range(0, total_words, effective_size):
        chunk = words[start:start + effective_size]
        if len(chunk) >= MIN_SECTION_WORDS:
            sections.append(" ".join(chunk))

    return sections


def get_cross_section_words(sections, threshold=CROSS_SECTION_THRESHOLD):
    if len(sections) < MIN_SECTIONS:
        return set()

    word_doc_count = Counter()
    for section in sections:
        for word in set(section.split()):
            word_doc_count[word] += 1

    section_count = len(sections)
    return {
        word for word, count in word_doc_count.items()
        if count / section_count > threshold
    }


def vectorize_sections(sections, cross_words):
    filtered_sections = []
    for section in sections:
        filtered_sections.append(" ".join(
            word for word in section.split()
            if word not in cross_words
        ))

    vectorizer = TfidfVectorizer(
        lowercase=False,
        stop_words="english",
        token_pattern=r"\b[a-zA-Z']{3,}\b",
        max_features=5000,
        min_df=1,
        max_df=1.0 if len(filtered_sections) < MIN_SECTIONS else 0.85,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(filtered_sections)
    vocabulary = vectorizer.get_feature_names_out()
    return matrix, vocabulary


def get_ranked_words_per_section(matrix, vocabulary, top_n=RANKED_WORDS_FOR_CATEGORY):
    result = []
    for i in range(matrix.shape[0]):
        row = matrix[i].toarray()[0]
        top_idx = row.argsort()[-top_n:][::-1]
        result.append([
            (vocabulary[j], float(row[j]))
            for j in top_idx
            if row[j] > 0
        ])
    return result


def load_categories():
    if os.path.exists(CATEGORIES_PATH):
        with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
    else:
        raw = {}

    low_value_labels = set(raw.get("_low_value_labels", []))
    family_hints = {
        family: set(labels)
        for family, labels in raw.get("_family_hints", {}).items()
    }
    categories = {
        cat: set(words)
        for cat, words in raw.items()
        if not cat.startswith("_")
    }

    word_freq = Counter()
    for words in categories.values():
        for word in words:
            word_freq[word] += 1

    return categories, word_freq, low_value_labels, family_hints


def load_book_family(book_id):
    if not book_id or not os.path.exists(BOOKS_COLLECTION_PATH):
        return None

    with open(BOOKS_COLLECTION_PATH, "r", encoding="utf-8") as f:
        collection = json.load(f)

    book_info = collection.get(str(book_id))
    if not book_info:
        return None

    return book_info.get("category")


def get_specific_category_words(categories, word_freq):
    category_count = len(categories)
    if category_count == 0:
        return {}

    return {
        cat: {
            word for word in words
            if word_freq[word] / category_count <= 0.30
        }
        for cat, words in categories.items()
    }


def get_section_topics(ranked_words, categories, word_freq, category_hints=None):
    if not ranked_words or not categories:
        return []

    specific_categories = get_specific_category_words(categories, word_freq)
    weighted_words = dict(ranked_words)
    topics = []

    for cat, words in specific_categories.items():
        matches = [
            (word, weighted_words[word])
            for word, _ in ranked_words
            if word in words
        ]
        if not matches:
            continue

        score = sum(weight for _, weight in matches)
        score *= 1.0 + min(len(matches), 8) * 0.25
        score /= len(words) ** 0.20
        if category_hints:
            score *= 1.8 if cat in category_hints else 0.55

        topics.append({
            "category": cat,
            "score": score,
            "words": [word for word, _ in matches],
            "match_count": len(matches),
        })

    if not topics:
        return []

    max_matches = max(topic["match_count"] for topic in topics)
    if max_matches >= 2:
        topics = [
            topic for topic in topics
            if topic["match_count"] >= 2
        ]

    return sorted(topics, key=lambda topic: topic["score"], reverse=True)


def choose_best_section_topic(
    ranked_words,
    categories,
    word_freq,
    low_value_labels,
    category_hints=None
):
    topics = get_section_topics(
        ranked_words,
        categories,
        word_freq,
        category_hints=category_hints
    )
    if not topics:
        return "topics", []

    filtered = [
        topic for topic in topics
        if topic["category"] not in low_value_labels
    ]
    if filtered:
        topics = filtered

    best_topic = topics[0]
    return best_topic["category"], best_topic["words"]


def select_section_words(ranked_words, topic_words, top_n=TOPICS_PER_SECTION):
    selected = []
    seen = set()

    for word in topic_words:
        if word not in seen:
            selected.append(word)
            seen.add(word)
        if len(selected) == top_n:
            return selected

    for word, _ in ranked_words:
        if word not in seen:
            selected.append(word)
            seen.add(word)
        if len(selected) == top_n:
            break

    return selected


def extract_topics(array, book_id=None):
    if not array:
        print("Aucun livre à traiter")
        return {}

    text = array[1]
    if not text or len(tokenize_words(text)) < MIN_TEXT_WORDS:
        print("Texte trop court pour extraire des topics.")
        return {}

    print("  Découpage du body en sections...")
    sections = split_into_sections(text)
    if not sections:
        print(f"  Trop peu de sections ({len(sections)}).")
        return {}
    print(f"  [{len(sections)} sections]")

    cross_words = get_cross_section_words(sections)
    print(f"  [{len(cross_words)} mots transversaux supprimés]")

    try:
        matrix, vocabulary = vectorize_sections(sections, cross_words)
    except ValueError:
        print("  Vocabulaire insuffisant pour extraire des topics.")
        return {}

    categories, word_freq, low_value_labels, family_hints = load_categories()
    print(f"  [{len(categories)} catégories disponibles]")
    family = load_book_family(book_id)
    category_hints = family_hints.get(family)
    if category_hints:
        print(f"  [contexte livre: {family}]")

    ranked_words_per_section = get_ranked_words_per_section(matrix, vocabulary)

    result = {}
    for i, ranked_words in enumerate(ranked_words_per_section, 1):
        if not ranked_words:
            continue
        category, topic_words = choose_best_section_topic(
            ranked_words,
            categories,
            word_freq,
            low_value_labels,
            category_hints=category_hints
        )
        words = select_section_words(ranked_words, topic_words)
        result[f"{i}: {category}"] = words

    return result
