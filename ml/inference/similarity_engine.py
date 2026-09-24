"""
Duplicate/similarity detection using TF-IDF + cosine similarity.

Unlike the category/priority models, this is NOT a persisted trained model —
it fits a fresh TF-IDF vectorizer over the current candidate pool (recent
open issues) plus the new issue text every time it runs. This is the correct
approach for similarity search: the "training data" is simply whatever
issues currently exist, and it changes constantly.

Similarity never implies duplication with certainty — results are always
surfaced as "potentially related", and merging remains a manual decision.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ml.preprocessing.text_preprocessing import combine_title_description

DEFAULT_THRESHOLD = 0.30
DEFAULT_TOP_N = 5


def find_similar_issues(new_title, new_description, candidate_issues, threshold=DEFAULT_THRESHOLD, top_n=DEFAULT_TOP_N):
    """
    candidate_issues: list of (issue_id, title, description) tuples to compare against.
    Returns a list of (issue_id, similarity_score) sorted by score descending,
    limited to those >= threshold.
    """
    if not candidate_issues:
        return []

    new_text = combine_title_description(new_title, new_description)
    candidate_texts = [combine_title_description(t, d) for _, t, d in candidate_issues]

    corpus = [new_text] + candidate_texts
    vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2))
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        # Happens if the corpus is entirely empty strings — nothing to compare.
        return []

    new_vec = tfidf_matrix[0:1]
    candidate_vecs = tfidf_matrix[1:]
    scores = cosine_similarity(new_vec, candidate_vecs)[0]

    results = [
        (candidate_issues[i][0], float(scores[i]))
        for i in range(len(candidate_issues))
        if scores[i] >= threshold
    ]
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]
