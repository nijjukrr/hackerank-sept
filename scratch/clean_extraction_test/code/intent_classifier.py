"""Intent classification for deletion request authorization."""

from __future__ import annotations

import re


class IntentClassifier:
    """Determines whether a user request text authorizes personal data / account deletion."""

    # Explicit non-deletion patterns that request retention, correction, access, or marketing opt-out
    NON_DELETION_PATTERNS = [
        re.compile(r"leave (?:the|my) account active", re.IGNORECASE),
        re.compile(r"keep (?:the|my) account", re.IGNORECASE),
        re.compile(r"leave my (?:profile|purchase|history)", re.IGNORECASE),
        re.compile(r"(?:want to )?continue using (?:the|this) service", re.IGNORECASE),
        re.compile(r"do not (?:delete|close|erase|remove|change)", re.IGNORECASE),
        re.compile(r"don['’]t (?:delete|close|erase|remove|change)", re.IGNORECASE),
        re.compile(r"not (?:asking for |a request to |requesting )(?:deletion|delete|erase|erasure|closing|close|removal|remove)", re.IGNORECASE),
        re.compile(r"without (?:removing|deleting|erasing|closing)", re.IGNORECASE),
        re.compile(r"marketing lists? only", re.IGNORECASE),
        re.compile(r"stop (?:the )?promotional emails", re.IGNORECASE),
        re.compile(r"information request", re.IGNORECASE),
        re.compile(r"still (?:use|need) (?:it|the account|my order)", re.IGNORECASE),
    ]

    # Multilingual deletion action terms
    DELETION_TERMS = [
        r"delet", r"eras", r"remov", r"clos", r"suppress", r"purg", r"wip",
        r"supprim", r"effac", r"cl[oô]tur", r"fermer",
        r"elimin", r"borr", r"cancel", r"cerr",
        r"exclu", r"apag", r"fech",
        r"l[oö]sch", r"entfern", r"schlie[sß]",
        r"cancell", r"audit", r"gone",
        r"削除", r"消去", r"삭제"
    ]
    DELETION_REGEX = re.compile("|".join(DELETION_TERMS), re.IGNORECASE)

    @classmethod
    def authorizes_deletion(cls, request_text: str) -> bool:
        """Returns True if the request authorizes deletion, False if NOT_APPLICABLE."""
        if not request_text:
            return False

        text = request_text.strip()

        # Check explicit non-deletion retention phrases first
        for pat in cls.NON_DELETION_PATTERNS:
            if pat.search(text):
                return False

        # Must contain an affirmative deletion term
        if cls.DELETION_REGEX.search(text):
            return True

        return False
