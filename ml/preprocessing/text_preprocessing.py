"""Shared text cleaning used by both training and inference so they never drift apart."""
import re

_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9\s]")


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = _NON_ALNUM_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def combine_title_description(title: str, description: str) -> str:
    return clean_text(f"{title or ''} {description or ''}")
