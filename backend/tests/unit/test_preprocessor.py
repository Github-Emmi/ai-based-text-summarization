"""Unit tests for preprocessor service."""

from app.services.preprocessor import count_words, detect_language


class TestCountWords:
    def test_simple_sentence(self):
        assert count_words("hello world foo bar") == 4

    def test_single_word(self):
        assert count_words("hello") == 1

    def test_empty_string(self):
        assert count_words("") == 0

    def test_extra_whitespace(self):
        # str.split() collapses whitespace
        assert count_words("  hello   world  ") == 2

    def test_multiline(self):
        assert count_words("line one\nline two\nline three") == 6


class TestDetectLanguage:
    def test_returns_string(self):
        result = detect_language("Hello world this is a test sentence")
        assert isinstance(result, str)
        assert len(result) >= 2  # ISO 639-1 codes are 2 chars

    def test_falls_back_on_short_text(self):
        # Very short or ambiguous text — must still return a string
        result = detect_language("hi")
        assert isinstance(result, str)

    def test_english_text(self):
        text = "The quick brown fox jumps over the lazy dog"
        result = detect_language(text)
        # Either detected as 'en' or fell back to 'en'
        assert result == "en"

    def test_empty_text_returns_en(self):
        result = detect_language("")
        assert result == "en"
