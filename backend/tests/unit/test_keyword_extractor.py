"""Unit tests for keyword_extractor service."""

from app.services.keyword_extractor import extract_keywords


def test_returns_list():
    result = extract_keywords("The quick brown fox jumps over the lazy dog")
    assert isinstance(result, list)


def test_top_n_respected():
    text = "machine learning deep learning neural network training data model"
    result = extract_keywords(text, top_n=3)
    assert len(result) <= 3


def test_stopwords_excluded():
    text = "this that these those with from into through before after"
    result = extract_keywords(text, top_n=10)
    # All tokens are stopwords or < 4 chars — expect empty list
    assert result == []


def test_short_words_excluded():
    text = "the and or but is are was be it do"
    result = extract_keywords(text, top_n=10)
    assert result == []


def test_returns_lowercase():
    text = "Python Python Python programming language language"
    result = extract_keywords(text, top_n=5)
    for kw in result:
        assert kw == kw.lower()


def test_most_frequent_first():
    text = "learning " * 10 + "python " * 5 + "language " * 2
    result = extract_keywords(text, top_n=3)
    assert result[0] == "learning"


def test_empty_text_returns_empty():
    assert extract_keywords("", top_n=5) == []


def test_numeric_text_returns_empty():
    assert extract_keywords("123 456 789", top_n=5) == []


def test_default_top_n_is_eight():
    # 20 distinct long words: result should be at most 8
    words = [f"wordnumber{i:02d}" for i in range(20)]
    result = extract_keywords(" ".join(words))
    assert len(result) <= 8
