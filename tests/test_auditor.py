from src.auditor import fingerprint, validate

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

def test_validate_accepts_valid_records():
    records = [
        {"id": "1", "group": "a", "text": "Hello"},
        {"id": "2", "group": "b", "text": "World"},
    ]
    assert validate(records) == records

def test_validate_rejects_duplicate_ids():
    records = [
        {"id": "1", "group": "a", "text": "Hello"},
        {"id": "1", "group": "b", "text": "World"},
    ]
    try: 
        validate(records)
        assert False
    except ValueError:
        assert True

def test_validate_rejects_missing_fields():
    records = [
        {"id": "1", "group": "a"},
    ]
    try:
        validate(records)
        assert False
    except ValueError:
        assert True

def test_audit_detects_content_leakage():
    train = [
        {"id": "1", "group": "a", "text": "Hello World"},
    ]
    test = [
        {"id": "2", "group": "b", "text": "   hello  world"}
    ]

    result = audit(train, test)
    assert result["content_leakage"] == ["2"]

def test_audit_detects_group_leakage():
    train = [
        {"id": "1", "group":"customer-a", "text": "Hello"}
    ]
    test = [
        {"id": "2", "group": "customer-a", "text": "Goodbye"}
    ]
    result = audit(train, test)
    assert result["group_leakage"] == ["2"]

def test_audit_detects_both_leakage():
    train = [
        {"id": "1", "group": "customer-a", "text": "Hello"},
    ]
    test = [
        {"id": "2", "group": "customer-a", "text": "Hello"},
    ]
    result = audit(train, test)
    assert result["content_leakage"] == ["2"]
    assert result["group_leakage"] == ["2"]

def test_audit_returns_empty_leakage_lists_when_clean():
    train = [
        {"id": "1", "group": "customer-a", "text": "hello"},
    ]
    test = [
        {"id": "2", "group": "customer-b", "text": "Goodbye"},
    ]
    result = audit(train, test)
    assert result["content_leakage"] == []
    assert result["group_leakage"] == []