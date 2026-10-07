from src.auditor import fingerprint

def test_fingerprint_is_deterministic():
    assert fingerprint("Hello World") == fingerprint("Hello World")

def test_fingerprint_normalize_case():
    assert fingerprint("Hello World") == fingerprint("HELLO WORLD")

def test_fingerprint_normalize_whitespace():
    assert fingerprint("Hello World") == fingerprint("  Hello   World   ")

def test_fingerprint_text_has_different_fingerprint():
    assert fingerprint("Hello Baby") != fingerprint("Hello Babe")

def test_fingerprint_returns_sha256_hex():
    result = fingerprint("Hello World")

    assert len(result) == 64
    assert all(
        character in "0123456789abcdef"
        for character in result
    )