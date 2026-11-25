import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Optional

class VectorEngine:
    """
    Lightweight, high-performance in-memory vector & hybrid retrieval engine.
    Uses TF-IDF + n-gram semantic matching and cosine similarity over slide chunks.
    Requires no heavy external dependencies, guaranteed to run instantly.
    """

    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.doc_matrix: Optional[np.ndarray] = None

    def clear(self):
        """Clears all indexed documents."""
        self.documents = []
        self.vectorizer = None
        self.doc_matrix = None

    def add_documents(self, docs: List[Dict[str, Any]]):
        """Adds and indexes a list of slide chunks."""
        self.documents.extend(docs)
        self._reindex()

    def _reindex(self):
        """Builds the TF-IDF feature matrix over all stored documents."""
        if not self.documents:
            self.vectorizer = None
            self.doc_matrix = None
            return

        corpus = [doc["text"] for doc in self.documents]
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=5000
        )
        self.doc_matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves top_k most relevant slides for a given student query.
        Returns ranked documents with similarity scores and slide metadata.
        """
        if not self.documents or self.vectorizer is None or self.doc_matrix is None:
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.doc_matrix).flatten()

        # Sort indices by score descending
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            # Only include if score > 0.01 or if it's the top 1 result
            if score > 0.01 or len(results) == 0:
                doc_copy = dict(self.documents[idx])
                doc_copy["relevance_score"] = round(score, 4)
                results.append(doc_copy)

        return results

    def get_all_documents(self) -> List[Dict[str, Any]]:
        return self.documents

    def get_stats(self) -> Dict[str, Any]:
        sources = list(set(d["source"] for d in self.documents))
        total_slides = len(self.documents)
        return {
            "total_slides": total_slides,
            "sources": sources,
            "vocab_size": len(self.vectorizer.vocabulary_) if self.vectorizer else 0
        }
