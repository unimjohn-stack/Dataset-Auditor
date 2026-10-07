import hashlib
import re
import unicodedata

def fingerprint(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.casefold()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def validate(records: list[dict]) -> list[dict]:
    required_fields = {"id", "group", "text"}
    seen_ids = set()

    for record in records:
        if not required_fields.issubset(record):
            raise ValueError("Record is missing required fields")
        record_id = record["id"]
        if record_id in seen_ids:
            raise ValueError(f"Duplicate record_id: {record_id}")
        seen_ids.add(record_id)
    return records

def audit(train: list[dict], test: list[dict]) -> dict:
    validate(train)
    validate(test)
    train_fingerprints = {
        fingerprint(record["text"])
        for record in train
    }
    train_groups = {
        record["group"]
        for record in train
    }
    content_leakage = [
        record["id"]
        for record in test
        if fingerprint(record["text"]) in train_fingerprints
    ]
    group_leakage = [
        record["id"]
        for record in test
        if record["group"] in train_groups
    ]
    return {
        "content_leakage": content_leakage,
        "group_leakage": group_leakage,
        "content_leakage_count": len(content_leakage),
        "group_leakage_count": len(group_leakage)
    }