"""Unit tests for QuoteVerifier substring assertion and extraction."""

from src.agent.quote_verifier import QuoteVerifier


def test_verify_quote_exact_substring():
    source = "This broker won't support you if there is any dispute on stop loss not triggered."
    valid_quote = "stop loss not triggered"
    assert QuoteVerifier.verify_quote_in_text(valid_quote, source) is True


def test_verify_quote_case_and_whitespace_insensitivity():
    source = "Charts   are NOT opening   even in a good network."
    candidate = "charts are not opening"
    assert QuoteVerifier.verify_quote_in_text(candidate, source) is True


def test_verify_quote_rejects_hallucination():
    source = "I lost money due to app crash when by option."
    # LLM attempted to correct grammar: "by option" -> "buying options"
    hallucinated = "I lost money due to app crash when buying options."
    assert QuoteVerifier.verify_quote_in_text(hallucinated, source) is False


def test_extract_verbatim_sentence_fallback():
    source = (
        "Groww is easy to use. "
        "However on 29/10/2026 sensex 73500pe i have lost 30000 due to my Stop loss not triggered. "
        "Please resolve immediately."
    )
    quote = QuoteVerifier.extract_verbatim_sentence(source, preferred_keywords=["stop loss"])
    assert "Stop loss not triggered" in quote
    assert QuoteVerifier.verify_quote_in_text(quote, source) is True
    assert 8 <= len(quote.split()) <= 35

