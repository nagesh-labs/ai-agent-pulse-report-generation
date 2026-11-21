"""Unit tests for PII sanitization, emoji removal, and language detection."""

import pytest
from src.ingestion.pii_sanitizer import PIISanitizer


@pytest.fixture
def sanitizer():
    return PIISanitizer(strip_emojis=True)


def test_standard_email_redaction(sanitizer):
    text = "Please contact me at john.doe@example.com for my refund."
    sanitized, count = sanitizer.sanitize_text(text)
    assert "[REDACTED_EMAIL]" in sanitized
    assert "john.doe@example.com" not in sanitized
    assert count == 1


def test_obfuscated_email_redaction(sanitizer):
    text = "Send statement to ramesh.kumar [at] gmail [dot] com immediately."
    sanitized, count = sanitizer.sanitize_text(text)
    assert "[REDACTED_EMAIL]" in sanitized
    assert "ramesh.kumar" not in sanitized
    assert count == 1


def test_phone_number_redaction(sanitizer):
    cases = [
        "Call me at 9876543210 regarding the failed deposit.",
        "My mobile is +91 9876543210 please check.",
        "Contact 09123456789 for KYC help.",
    ]
    for text in cases:
        sanitized, count = sanitizer.sanitize_text(text)
        assert "[REDACTED_PHONE]" in sanitized
        assert "9876543210" not in sanitized
        assert "9123456789" not in sanitized
        assert count == 1


def test_spaced_obfuscated_phone_redaction(sanitizer):
    text = "Do not ignore call on 9 8 7 6 5 4 3 2 1 0 right now."
    sanitized, count = sanitizer.sanitize_text(text)
    assert "[REDACTED_PHONE]" in sanitized
    assert "9 8 7 6 5 4 3 2 1 0" not in sanitized
    assert count == 1


def test_upi_vpa_redaction(sanitizer):
    cases = [
        "Transferred funds from suresh@okaxis but wallet balance is zero.",
        "My vpa is rahul.kumar@paytm why was order rejected?",
        "Deducted via trader123@ybl please refund.",
    ]
    for text in cases:
        sanitized, count = sanitizer.sanitize_text(text)
        assert "[REDACTED_UPI]" in sanitized
        assert "@okaxis" not in sanitized
        assert "@paytm" not in sanitized
        assert "@ybl" not in sanitized
        assert count == 1


def test_pan_number_redaction(sanitizer):
    text = "KYC rejected even though PAN ABCDE1234F is verified with Aadhaar."
    sanitized, count = sanitizer.sanitize_text(text)
    assert "[REDACTED_PAN]" in sanitized
    assert "ABCDE1234F" not in sanitized
    assert count == 1


def test_demat_account_redaction(sanitizer):
    text = "Check holdings in Demat 1208160012345678 shares not showing."
    sanitized, count = sanitizer.sanitize_text(text)
    assert "[REDACTED_ACCOUNT]" in sanitized
    assert "1208160012345678" not in sanitized
    assert count == 1


def test_financial_amounts_not_falsely_redacted(sanitizer):
    """Ensure legitimate trading figures are NOT falsely masked as phone numbers or accounts."""
    text = "I invested Rs. 50000 in Nifty and lost 1500 on option contract with error 500."
    sanitized, count = sanitizer.sanitize_text(text)
    assert "50000" in sanitized
    assert "1500" in sanitized
    assert "500" in sanitized
    assert "[REDACTED_PHONE]" not in sanitized
    assert count == 0


def test_user_anonymization(sanitizer):
    u1 = sanitizer.anonymize_user("Aarav Sharma")
    u2 = sanitizer.anonymize_user("Pooja Patel")
    u1_again = sanitizer.anonymize_user("Aarav Sharma")
    anon = sanitizer.anonymize_user("Google User")

    assert u1 == "Reviewer #0001"
    assert u2 == "Reviewer #0002"
    assert u1_again == "Reviewer #0001"
    assert anon == "Anonymous User"


def test_emoji_removal_and_currency_preservation(sanitizer):
    """Assert that emojis are completely stripped while currency and punctuation remain intact."""
    text = "Great app! ❤️ ₹500 cashback received 👍👏 very nice 💯"
    sanitized, count = sanitizer.sanitize_text(text)
    assert "❤️" not in sanitized
    assert "👍" not in sanitized
    assert "👏" not in sanitized
    assert "💯" not in sanitized
    assert "₹500" in sanitized
    assert "Great app!" in sanitized
    assert "cashback received very nice" in sanitized


def test_english_language_detection(sanitizer):
    """Verify that English text passes and Hindi/Hinglish/regional scripts are rejected."""
    # Valid English
    assert sanitizer.is_english("Charts are not opening even in a good network connection. Showing error.")
    assert sanitizer.is_english("This broker will not support you if there is any dispute on stop loss.")

    # Devanagari Hindi
    assert not sanitizer.is_english("भाई पी डालने के बाद वेरीफाई के टाइम पर ओटीपी नहीं आ रहा है")

    # Kannada
    assert not sanitizer.is_english("ಉತ್ತಮ ವಾದ app")

    # Hinglish
    assert not sanitizer.is_english("bahut hi bekar Hai cal 30 tarikh ko Friday ko iske baad bleach hua")
    assert not sanitizer.is_english("abhi groww aap me bahut kuch new update karna baki he")
