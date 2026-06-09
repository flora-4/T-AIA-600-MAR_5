import subprocess, sys, json, os

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "scikit-learn"])
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity


BOOKS_FILE = os.path.join(
    os.path.dirname(__file__),
    "books_collection.json"
)

with open(BOOKS_FILE, "r", encoding="utf-8") as f:
    BOOKS = json.load(f)

# Conversion des clés JSON (chaînes) en entiers
BOOKS = {int(k): v for k, v in BOOKS.items()}

def extract_similar(bookid, books_content):
    bookid = int(bookid)

    valid_ids = []
    valid_texts = []

    for bid, text in books_content.items():
        if text and len(text.split()) > 200:
            valid_ids.append(int(bid))
            valid_texts.append(text)

    if bookid not in valid_ids:
        print("Livre cible introuvable dans la collection.")
        return []

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        token_pattern=r"\b[a-zA-Z]{3,}\b",
        max_features=10000,
        sublinear_tf=True,
        min_df=2,
        max_df=0.85,
        ngram_range=(1, 2)
    )

    matrix = vectorizer.fit_transform(valid_texts)

    target_idx = valid_ids.index(bookid)

    scores = cosine_similarity(matrix[target_idx], matrix)[0]

    target_category = BOOKS.get(bookid, {}).get("category")

    ranked = []

    for i in range(len(valid_ids)):
        other_id = valid_ids[i]

        if other_id == bookid:
            continue

        score = scores[i]

        other_category = BOOKS.get(other_id, {}).get("category")

        if target_category and other_category == target_category:
            score += 0.15

        ranked.append((other_id, score))

    ranked = sorted(ranked, key=lambda x: x[1], reverse=True)

    return [
        BOOKS.get(bid, {"title": str(bid)})["title"]
        for bid, _ in ranked[:5]
    ]