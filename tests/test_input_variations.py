"""Normalization of input variations that must not create duplicates."""

from __future__ import annotations

import pytest

from server import validation
from server.repositories._search import like_pattern


def test_email_is_lowercased():
    assert validation.require_email("  Ada@Example.COM ") == "ada@example.com"


@pytest.mark.parametrize(
    "raw", ["978-0-13-468599-1", "9780134685991", "978 0 134 68599 1"]
)
def test_isbn_variants_normalize_identically(raw):
    assert validation.normalize_isbn(raw) == "9780134685991"


def test_isbn_check_digit_uppercased():
    assert validation.normalize_isbn("0-8044-2957-x") == "080442957X"


def test_search_collapses_inner_whitespace():
    assert validation.require_search("  ada    lovelace ") == "ada lovelace"


def test_like_pattern_escapes_wildcards():
    bs = chr(92)
    assert like_pattern("100%_x" + bs) == f"%100{bs}%{bs}_x{bs}{bs}%"
    assert like_pattern("") is None
