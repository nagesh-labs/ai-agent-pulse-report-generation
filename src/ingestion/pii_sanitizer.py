"""PII Sanitization & Text Normalization Engine for mobile store reviews.

Provides multi-pass redaction for phone numbers, email addresses,
UPI VPAs, Indian PAN cards, and bank/Demat account numbers,
as well as emoji stripping and English language detection.
"""

import re
import unicodedata
from typing import Tuple, Optional
from langdetect import detect, DetectorFactory

# Enforce deterministic language detection across threads
DetectorFactory.seed = 0


class PIISanitizer:
    """Sanitizes text by stripping personally identifiable information (PII) and emojis."""

    # Emojis regex matching all standard Unicode emoji blocks
    _EMOJI_PATTERN = re.compile(
        r"["
        r"\U00010000-\U0010ffff"  # All 4-byte astral characters / emojis
        r"\u200d"                  # Zero-width joiner
        r"\u2600-\u27bf"           # Miscellaneous symbols, dingbats
        r"\ufe0f"                  # Variation selector 16
        r"\u2300-\u23ff"           # Miscellaneous technical
        r"\u2b50"                  # Star
        r"\u20e3"                  # Enclosing keycap
        r"]+",
        flags=re.UNICODE
    )

    # Obfuscated spaced digits pattern (e.g. "9 8 7 6 5 4 3 2 1 0")
    _SPACED_DIGIT_PATTERN = re.compile(r'(?<=\b\d)\s+(?=\d\b)')

    # Obfuscated email syntax: e.g. " [at] ", " (at) ", " [dot] ", " (dot) "
    _OBFUSCATED_AT_PATTERN = re.compile(r'\s*[\[\(]at[\]\)]\s*', re.IGNORECASE)
    _OBFUSCATED_DOT_PATTERN = re.compile(r'\s*[\[\(]dot[\]\)]\s*', re.IGNORECASE)

    # Standard and spaced email regex
    _EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')

    # Indian Mobile numbers: 10 digits starting with 6, 7, 8, or 9 (with optional +91 or 0 prefix)
    _PHONE_PATTERN = re.compile(r'(?:\b0|\+91[\s\-]?)?[6-9]\d{9}\b|\b[6-9]\d{9}\b')

    # UPI Virtual Payment Address (VPA)
    _UPI_PATTERN = re.compile(
        r'\b[a-zA-Z0-9.\-_]{2,256}@(okaxis|okhdfcbank|okicici|paytm|ybl|apl|upi|axl|ibl|sbi|kotak|federal|idfc)\b',
        re.IGNORECASE
    )

    # Permanent Account Number (PAN) used in Indian taxation & demat KYC: 5 letters, 4 digits, 1 letter
    _PAN_PATTERN = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b')

    # 16-digit Demat Account number (CDSL/NSDL) or 12-16 digit bank account number
    _ACCOUNT_PATTERN = re.compile(r'\b(?:IN\d{14}|\d{16})\b')

    # Indic Scripts (Devanagari, Bengali, Gurmukhi, Gujarati, Odia, Tamil, Telugu, Kannada, Malayalam, Urdu)
    _INDIC_SCRIPT_PATTERN = re.compile(r'[\u0900-\u0DFF\u0600-\u06FF]')

    # Unambiguous Hindi / Hinglish vocabulary (does not overlap with standard English words)
    _UNAMBIGUOUS_HINGLISH = {
        'hai', 'hain', 'karna', 'karke', 'nahi', 'nahin', 'bekar', 'karo', 'mujhe',
        'mera', 'meri', 'mere', 'bahut', 'bohot', 'hote', 'hota', 'hoti', 'gaya',
        'gayi', 'gaye', 'paise', 'paisa', 'accha', 'achha', 'kyun', 'kyu', 'chahiye',
        'dhokha', 'chindi', 'tarikh', 'lekin', 'magar', 'kaun', 'kisko', 'apna', 'apni'
    }

    def __init__(self, strip_emojis: bool = True) -> None:
        self.strip_emojis = strip_emojis
        self._user_counter = 0
        self._user_id_map: dict[str, str] = {}

    def anonymize_user(self, original_name: str) -> str:
        """Map a real user name or identifier to a persistent anonymous pseudonym."""
        clean_name = (original_name or "").strip()
        if not clean_name or clean_name.lower() in ("anonymous", "google user", "a google user"):
            return "Anonymous User"

        if clean_name not in self._user_id_map:
            self._user_counter += 1
            self._user_id_map[clean_name] = f"Reviewer #{self._user_counter:04d}"

        return self._user_id_map[clean_name]

    def remove_emojis(self, text: str) -> str:
        """Strip all emoji characters from text."""
        return self._EMOJI_PATTERN.sub('', text)

    def normalize_text(self, text: str) -> str:
        """Normalize Unicode characters, strip emojis, and collapse non-printable characters."""
        if not text:
            return ""
        # Normalize to NFKC form (standardizes compatibility characters)
        normalized = unicodedata.normalize("NFKC", text)

        # Strip emojis if configured
        if self.strip_emojis:
            normalized = self.remove_emojis(normalized)

        # Remove non-printable control characters except newline and tab
        cleaned = "".join(ch for ch in normalized if ch == '\n' or ch == '\t' or unicodedata.category(ch)[0] != 'C')
        # Collapse multiple spaces on the same line
        cleaned = re.sub(r'[^\S\r\n]+', ' ', cleaned)
        return cleaned.strip()

    def sanitize_text(self, text: str) -> Tuple[str, int]:
        """Strip all detected PII and emojis from review text.

        Returns:
            Tuple[str, int]: The sanitized text and count of PII entities redacted.
        """
        if not text:
            return "", 0

        redaction_count = 0
        normalized = self.normalize_text(text)

        # 1. De-obfuscate masked emails
        deobfuscated = self._OBFUSCATED_AT_PATTERN.sub('@', normalized)
        deobfuscated = self._OBFUSCATED_DOT_PATTERN.sub('.', deobfuscated)

        # 2. De-obfuscate spaced digits for phone matching (only if 10 consecutive digits separated by single spaces)
        def collapse_phone_spaces(match: re.Match) -> str:
            return match.group(0).replace(" ", "")

        spaced_phone_regex = re.compile(r'\b[6-9](?:\s+\d){9}\b')
        deobfuscated = spaced_phone_regex.sub(collapse_phone_spaces, deobfuscated)

        # 3. Mask UPI VPAs
        sanitized, count = self._UPI_PATTERN.subn('[REDACTED_UPI]', deobfuscated)
        redaction_count += count

        # 4. Mask Email Addresses
        sanitized, count = self._EMAIL_PATTERN.subn('[REDACTED_EMAIL]', sanitized)
        redaction_count += count

        # 5. Mask Indian Phone Numbers
        sanitized, count = self._PHONE_PATTERN.subn('[REDACTED_PHONE]', sanitized)
        redaction_count += count

        # 6. Mask PAN Numbers
        sanitized, count = self._PAN_PATTERN.subn('[REDACTED_PAN]', sanitized)
        redaction_count += count

        # 7. Mask Demat / Account Numbers
        sanitized, count = self._ACCOUNT_PATTERN.subn('[REDACTED_ACCOUNT]', sanitized)
        redaction_count += count

        return sanitized, redaction_count

    def is_english(self, text: str) -> bool:
        """Determine whether text is genuine English, filtering out Hindi, Hinglish, and other languages."""
        if not text or not text.strip():
            return False

        # Reject any review containing Indic scripts (Devanagari, Tamil, Telugu, Kannada, etc.)
        if self._INDIC_SCRIPT_PATTERN.search(text):
            return False

        # Extract words for vocabulary check
        words = re.findall(r'[a-zA-Z]+', text.lower())
        if not words:
            return False

        # Reject if multiple unambiguous Hinglish marker words appear
        hinglish_matches = [w for w in words if w in self._UNAMBIGUOUS_HINGLISH]
        if len(hinglish_matches) >= 2 or (len(words) > 0 and len(hinglish_matches) / len(words) > 0.08):
            return False

        # Run statistical language detection
        try:
            detected = detect(text)
            return detected == 'en'
        except Exception:
            # Fallback: check if most characters are standard ASCII
            ascii_chars = sum(1 for ch in text if ord(ch) < 128)
            return (ascii_chars / len(text)) > 0.85
