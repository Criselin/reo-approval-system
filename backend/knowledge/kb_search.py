import json
import os
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_DATA_DIR = Path(__file__).parent / "data"
_categories = []
_articles = []
_article_texts = []
_vectorizer: TfidfVectorizer | None = None
_tfidf_matrix = None


def load_knowledge_base():
    """Load and index the troubleshooting knowledge base at startup."""
    global _categories, _articles, _article_texts, _vectorizer, _tfidf_matrix

    kb_path = _DATA_DIR / "troubleshooting.json"
    with open(kb_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _categories = data["categories"]
    _articles = []
    _article_texts = []

    for category in _categories:
        for article in category["articles"]:
            article_with_category = {
                **article,
                "category_id": category["id"],
                "category_name": category["name"],
            }
            _articles.append(article_with_category)

            text_parts = [
                article["title"],
                " ".join(article["symptoms"]),
                " ".join(article["steps"]),
                " ".join(category["keywords"]),
            ]
            _article_texts.append(" ".join(text_parts))

    _vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    _tfidf_matrix = _vectorizer.fit_transform(_article_texts)


def search_knowledge_base(
    query: str, category: str | None = None, top_k: int = 3
) -> list[dict]:
    """Search the knowledge base using TF-IDF similarity.

    Args:
        query: Search query string
        category: Optional category ID to filter results
        top_k: Number of top results to return

    Returns:
        List of matching articles with similarity scores
    """
    if _vectorizer is None or _tfidf_matrix is None:
        load_knowledge_base()

    query_vec = _vectorizer.transform([query])
    similarities = cosine_similarity(query_vec, _tfidf_matrix).flatten()

    indexed_sims = list(enumerate(similarities))

    if category:
        indexed_sims = [
            (i, sim)
            for i, sim in indexed_sims
            if _articles[i]["category_id"] == category
        ]

    indexed_sims.sort(key=lambda x: x[1], reverse=True)
    top_results = indexed_sims[:top_k]

    results = []
    for idx, score in top_results:
        if score > 0.0:
            article = _articles[idx]
            results.append(
                {
                    "article_id": article["id"],
                    "title": article["title"],
                    "category": article["category_name"],
                    "symptoms": article["symptoms"],
                    "relevance_score": round(float(score), 4),
                    "steps_preview": article["steps"][0] if article["steps"] else "",
                }
            )

    return results


def get_article_by_id(article_id: str) -> dict | None:
    """Get full article details by ID."""
    if not _articles:
        load_knowledge_base()

    for article in _articles:
        if article["id"] == article_id:
            return article
    return None


def get_categories() -> list[dict]:
    """Get all available categories."""
    if not _categories:
        load_knowledge_base()
    return [{"id": c["id"], "name": c["name"]} for c in _categories]
