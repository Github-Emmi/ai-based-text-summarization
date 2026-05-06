"""Keyword extraction — simple regex-based fallback (no ML deps required).

KeyBERT/sentence-transformers are not available on Python 3.14 in this env.
We use a TF-IDF-style approach with stopword filtering as a lightweight alternative.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Sequence

# Common English stopwords
_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "this", "that",
    "these", "those", "it", "its", "as", "if", "so", "we", "you", "he",
    "she", "they", "them", "their", "our", "your", "my", "his", "her",
    "not", "no", "nor", "very", "also", "just", "than", "then", "about",
    "into", "through", "during", "before", "after", "above", "below",
    "between", "each", "more", "most", "other", "some", "such", "only",
    "own", "same", "too", "any", "both", "few", "more", "all", "when",
    "which", "who", "what", "how", "where", "why", "i", "s", "t",
})


def extract_keywords(text: str, top_n: int = 8) -> list[str]:
    """Extract top keywords from *text* using word frequency + stopword filter."""
    # Tokenise — keep only alphabetic tokens of length >= 4
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    filtered = [w for w in words if w not in _STOPWORDS]
    if not filtered:
        return []
    counter = Counter(filtered)
    top = counter.most_common(top_n)
    return [word for word, _ in top]
