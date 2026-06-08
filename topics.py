import subprocess
import sys

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from sklearn.decomposition import TruncatedSVD
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "scikit-learn"])
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from sklearn.decomposition import TruncatedSVD

SECTION_SIZE = 1000
MIN_SECTIONS = 5 


def split_into_sections(text, section_size=SECTION_SIZE):
    words = text.split()
    total_words = len(words)

    if total_words == 0:
        return []

    effective_size = section_size
    if total_words // section_size < MIN_SECTIONS:
        effective_size = max(100, total_words // MIN_SECTIONS)

    sections = []
    for i in range(0, total_words, effective_size):
        chunk = words[i:i + effective_size]
        if len(chunk) >= 50:
            sections.append(" ".join(chunk))

    return sections

def choose_n_clusters(n_sections):
    return max(4, min(12, n_sections // 5))


def extract_topics(array):
    if not array:
        print("Aucun livre à traiter")
        return {}

    text = array[1]

    if not text or len(text.split()) < 200:
        print("Texte trop court pour extraire des topics.")
        return {}
 
    sections = split_into_sections(text)
    if len(sections) < 4:
        print(f"Trop peu de sections ({len(sections)}), impossible d'extraire des topics.")
        return {}
    print(f"  [{len(sections)} sections → {choose_n_clusters(len(sections))} clusters]")


    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        token_pattern=r"\b[a-zA-Z]{3,}\b",
        max_features=5000,
        min_df=2,
        max_df=0.85,
        sublinear_tf=True,
    )
    tfidf_matrix = vectorizer.fit_transform(sections)
    vocabulary = vectorizer.get_feature_names_out()


    n_comp = min(50, tfidf_matrix.shape[0] - 1, tfidf_matrix.shape[1] - 1)
    if n_comp < 2:
        print("Vocabulaire insuffisant pour SVD.")
        return {}

    svd = TruncatedSVD(n_components=n_comp, random_state=42)
    reduced = svd.fit_transform(tfidf_matrix)


    n_clusters = choose_n_clusters(len(sections))
    n_clusters = min(n_clusters, len(sections))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(reduced)


    result = {}
    for cid in range(n_clusters):
        indices = [i for i, label in enumerate(labels) if label == cid]
        if not indices:
            continue
        cluster_matrix = tfidf_matrix[indices]
        mean_scores = cluster_matrix.mean(axis=0).A1
        top_idx = mean_scores.argsort()[-10:][::-1]
        top_words = [vocabulary[j] for j in top_idx]
        result[cid + 1] = top_words

    return result