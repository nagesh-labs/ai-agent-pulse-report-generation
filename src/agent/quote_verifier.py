"""Deterministic Verbatim Quote Verification & Extraction Engine.

Guarantees 100% factual fidelity by verifying that all quoted user feedback
is an exact substring of the original review text, eliminating LLM hallucinations.
"""

import re
from typing import List, Optional


class QuoteVerifier:
    """Validates and extracts verbatim quotes with zero hallucination."""

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Collapse consecutive whitespace and strip edges for comparison."""
        if not text:
            return ""
        return " ".join(text.strip().split())

    @classmethod
    def verify_quote_in_text(cls, candidate_quote: str, source_text: str) -> bool:
        """Verify that candidate_quote is an exact substring of source_text (case-insensitive)."""
        if not candidate_quote or not source_text:
            return False

        clean_candidate = cls.normalize_whitespace(candidate_quote).lower()
        clean_source = cls.normalize_whitespace(source_text).lower()

        return clean_candidate in clean_source

    @classmethod
    def verify_quote_in_corpus(cls, candidate_quote: str, corpus: List[str]) -> bool:
        """Verify that candidate_quote exists verbatim in at least one review in the corpus."""
        if not candidate_quote or not corpus:
            return False

        clean_candidate = cls.normalize_whitespace(candidate_quote).lower()
        for source in corpus:
            clean_source = cls.normalize_whitespace(source).lower()
            if clean_candidate in clean_source:
                return True

        return False

    @classmethod
    def extract_verbatim_sentence(
        cls,
        source_text: str,
        preferred_keywords: Optional[List[str]] = None,
        min_words: int = 8,
        max_words: int = 35,
    ) -> str:
        """Deterministically slice an authentic, self-contained sentence from review text.

        Used as an automated fallback if an LLM paraphrases or modifies quotes.
        """
        clean_text = cls.normalize_whitespace(source_text)
        if not clean_text:
            return ""

        # Split into sentences based on punctuation (. ! ? \n)
        raw_sentences = re.split(r'(?<=[.!?])\s+|\n+', clean_text)
        candidates = []

        for s in raw_sentences:
            s_clean = cls.normalize_whitespace(s)
            words = s_clean.split()
            if min_words <= len(words) <= max_words:
                candidates.append(s_clean)
            elif len(words) > max_words:
                # If a sentence is long, slice the first max_words words ending at word boundary
                truncated = " ".join(words[:max_words])
                candidates.append(truncated)

        if not candidates:
            # Fallback to bounded slice of full text
            words = clean_text.split()
            return " ".join(words[:min(max_words, len(words))])

        if preferred_keywords:
            keywords_lower = [k.lower() for k in preferred_keywords]
            for cand in candidates:
                cand_lower = cand.lower()
                if any(kw in cand_lower for kw in keywords_lower):
                    return cand

        # Return the most descriptive candidate (longest under limit)
        return max(candidates, key=lambda c: len(c.split()))

