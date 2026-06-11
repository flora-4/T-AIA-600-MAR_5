import subprocess
import sys
import json
import os
from collections import Counter

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "scikit-learn"])
    from sklearn.feature_extraction.text import TfidfVectorizer

try:
    import spacy
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "spacy"])
    import spacy

try:
    spacy.load("en_core_web_sm")
except OSError:
    subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])


SECTION_SIZE = 1000
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")
CROSS_SECTION_THRESHOLD = 0.35


def split_into_sections(text, section_size=SECTION_SIZE):
    nlp = spacy.load("en_core_web_sm")
    nlp.add_pipe("sentencizer")
    nlp.max_length = len(text) + 10

    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    total_words    = sum(len(s.split()) for s in sentences)
    effective_size = section_size
    if total_words // section_size < 5:
        effective_size = max(100, total_words // 5)

    sections      = []
    current       = []
    current_words = 0

    for sent in sentences:
        words = len(sent.split())
        current.append(sent)
        current_words += words
        if current_words >= effective_size:
            sections.append(" ".join(current))
            current       = []
            current_words = 0

    if current and current_words >= 50:
        sections.append(" ".join(current))

    return sections


def get_cross_section_words(sections, threshold=CROSS_SECTION_THRESHOLD):
    n              = len(sections)
    word_doc_count = Counter()
    for section in sections:
        words = set(section.lower().split())
        for word in words:
            word_doc_count[word] += 1
    return {word for word, count in word_doc_count.items() if count / n > threshold}


def vectorize_sections(sections, cross_words):
    filtered = []
    for section in sections:
        words = section.split()
        filtered.append(" ".join(
            w for w in words if w.lower() not in cross_words
        ))

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        token_pattern=r"\b[a-zA-Z]{3,}\b",
        max_features=5000,
        min_df=2,
        max_df=0.85,
        sublinear_tf=True,
    )
    matrix     = vectorizer.fit_transform(filtered)
    vocabulary = vectorizer.get_feature_names_out()
    return matrix, vocabulary


def get_top_words_per_section(matrix, vocabulary, top_n=20):
    top_words_per_section = []
    for i in range(matrix.shape[0]):
        row     = matrix[i].toarray()[0]
        top_idx = row.argsort()[-top_n:][::-1]
        top_words_per_section.append(
            set(vocabulary[j] for j in top_idx if row[j] > 0.1)
        )
    return top_words_per_section


def load_categories():
    if not os.path.exists(CATEGORIES_PATH):
        return {}, Counter()
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    categories = {cat: set(words) for cat, words in raw.items()}
    word_freq  = Counter()
    for word_set in categories.values():
        for word in word_set:
            word_freq[word] += 1
    return categories, word_freq


def match_categories(top_words_per_section, categories, word_freq):
    n_categories = len(categories)
    n_sections   = len(top_words_per_section)
    category_scores = Counter()

    for top_words in top_words_per_section:
        for cat, word_set in categories.items():
            specific = {w for w in word_set if word_freq.get(w, 0) / n_categories <= 0.3}
            matches  = len(top_words & specific)
            if matches > 0:
                category_scores[cat] += matches

    normalized = {
        cat: (s / (len(categories[cat]) ** 0.5)) / n_sections
        for cat, s in category_scores.items()
        if s > 0
    }

    if not normalized:
        return {}

    # Garde seulement les catégories au-dessus de 50% du score max
    max_score = max(normalized.values())
    threshold = max_score * 0.5

    sorted_cats = sorted(
        {cat: s for cat, s in normalized.items() if s >= threshold}.items(),
        key=lambda x: x[1],
        reverse=True
    )
    return dict(sorted_cats)
def extract_topics(array):
    if not array:
        print("Aucun livre à traiter")
        return {}

    text = array[1]
    if not text or len(text.split()) < 200:
        print("Texte trop court pour extraire des topics.")
        return {}

    print("  Découpage en sections...")
    sections = split_into_sections(text)
    if len(sections) < 4:
        print(f"  Trop peu de sections ({len(sections)}).")
        return {}
    print(f"  [{len(sections)} sections]")

    cross_words = get_cross_section_words(sections)
    print(f"  [{len(cross_words)} mots transversaux supprimés]")

    matrix, vocabulary = vectorize_sections(sections, cross_words)

    top_words_per_section = get_top_words_per_section(matrix, vocabulary, top_n=20)

    categories, word_freq = load_categories()

    if not categories:
        print("  [categories.json absent, fallback numérique]")
        result = {}
        for i, top_words in enumerate(top_words_per_section[:12], 1):
            if top_words:
                result[i] = sorted(list(top_words))[:10]
        return result

    top_categories = match_categories(top_words_per_section, categories, word_freq)
    print(f"  [{len(top_categories)} catégories retenues]")

    result = {}
    for cat in top_categories:
        cat_word_set     = categories[cat]
        cat_words_scores = {}
        for j, word in enumerate(vocabulary):
            if word in cat_word_set:
                col = matrix[:, j].toarray().flatten()
                cat_words_scores[word] = float(col.mean())

        top10 = sorted(cat_words_scores, key=lambda w: cat_words_scores[w], reverse=True)[:10]
        if len(top10) >= 10:  # on garde seulement si on a 10 mots
            result[cat] = top10

    return {f"{i + 1}: {cat}": words for i, (cat, words) in enumerate(result.items())}