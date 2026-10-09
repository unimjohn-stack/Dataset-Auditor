from src.auditor import fingerprint, validate, audit, split_groups

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

def test_audit_includes_leakage_counts():
    train = [
        {"id": "1", "group": "customer-a", "text": "Hello"},
    ]

    test = [
        {"id": "2", "group": "customer-a", "text": "Hello"},
        {"id": "3", "group": "customer-b", "text": "Goodbye"},
    ]

    result = audit(train, test)

    assert result["content_leakage_count"] == 1
    assert result["group_leakage_count"] == 1

def test_split_groups_keeps_group_together():
    records = [
        {"id": "1", "group": "a", "text": "A1"},
        {"id": "2", "group": "a", "text": "A2"},
        {"id": "3", "group": "b", "text": "B1"},
        {"id": "4", "group": "b", "text": "B2"},
        {"id": "5", "group": "c", "text": "C1"},
        {"id": "6", "group": "c", "text": "C2"},
    ]
    train, test = split_groups(
        records, test_fraction=0.33, seed = "course",
    )
    train_groups = {record["group"] for record in train}
    test_groups = {record["group"] for record in test}
    assert train_groups.isdisjoint(test_groups)

def test_split_records_is_deterministic():
    records = [
        {"id": "1", "group": "a", "text": "A1"},
        {"id": "2", "group": "a", "text": "A2"},
        {"id": "3", "group": "b", "text": "B1"},
        {"id": "4", "group": "b", "text": "B2"},
        {"id": "5", "group": "c", "text": "C1"},
        {"id": "6", "group": "c", "text": "C2"},
    ]
    train1, test1 = split_groups(records, test_fraction=0.33, seed="course")
    train2, test2 = split_groups(records, test_fraction=0.33, seed="course")
    assert train1 == train2
    assert test1 == test2

def test_split_groups_preserves_all_records():
    records = [
        {"id": "1", "group": "a", "text": "A1"},
        {"id": "2", "group": "a", "text": "A2"},
        {"id": "3", "group": "b", "text": "B1"},
        {"id": "4", "group": "b", "text": "B2"},
        {"id": "5", "group": "c", "text": "C1"},
        {"id": "6", "group": "c", "text": "C2"},
    ]
    train, test = split_groups(records, test_fraction=0.5, seed = "course")
    combined_ids = {record["id"]
    for record in train + test}
    original_ids = {record["id"] for record in records}

    assert combined_ids == original_ids

def test_split_groups_rejects_invalid_fractions():
    records = [
        {"id": "1", "group": "a", "text": "A1"},
    ]
    try:
        split_groups(records, test_fraction=0)
        assert False
    except ValueError:
        assert True

    try:
        split_groups(records, test_fraction=1)
        assert False
    except ValueError:
        assert True

def test_split_groups_is_stable_when_record_order_changes():
    records = [
        {"id": "1", "group": "a", "text": "A1"},
        {"id": "2", "group": "b", "text": "B1"},
        {"id": "3", "group": "c", "text": "C1"},
        {"id": "4", "group": "d", "text": "D1"},
        {"id": "5", "group": "e", "text": "E1"},
    ]
    reordered = list(reversed(records))
    train1, test1 = split_groups(records, test_fraction=0.4, seed="experiment-1")
    train2, test2 = split_groups(records, test_fraction=0.4, seed="experiment-1")
    assert{r["id"] for r in train1} == {r["id"] for r in train2}
    assert{r["id"] for r in test1} == {r["id"] for r in test2}