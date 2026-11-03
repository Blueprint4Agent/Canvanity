import unicodedata

import pytest
from pydantic import ValidationError

from app.models.tag import TagCreateForm, TagSearchQuery, normalize_tag_name


@pytest.mark.parametrize(
    "raw,name,key",
    [
        ("  한글  ", "한글", "한글"),
        (" C++ ", "C++", "c++"),
        ("C#", "C#", "c#"),
        ("Straße", "Straße", "strasse"),
        ("İ", "İ", "i\u0307"),
        ("ΐ", "ΐ", "ΐ"),
        ("ß" * 40, "ß" * 40, "ss" * 40),
        ("한" * 40, "한" * 40, "한" * 40),
        ("Ｃ＋＋", "Ｃ＋＋", "ｃ＋＋"),
    ],
)
def test_tag_normalization_preserves_symbols_and_composes_casefold_output(raw, name, key):
    form = TagCreateForm(name=raw)
    assert form.name == name
    assert normalize_tag_name(form.name) == (name, key)
    assert unicodedata.is_normalized("NFC", key)


@pytest.mark.parametrize(
    "raw",
    ["", "   ", "a" * 41, "ﬃ" * 40, "a\x00", "\ta", "a\n", "a\x7f", "a\u200b", "\ud800"],
)
def test_tag_names_reject_blank_lengths_non_utf8_and_control_characters(raw):
    with pytest.raises(ValidationError):
        TagCreateForm(name=raw)


def test_query_supports_empty_catalog_but_still_rejects_control_characters():
    assert TagSearchQuery(q="  ").q == ""
    with pytest.raises(ValidationError):
        TagSearchQuery(q="\n")
