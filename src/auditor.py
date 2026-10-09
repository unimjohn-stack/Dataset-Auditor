import hashlib
import re
import unicodedata
# import random

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

def split_groups(records: list[dict], test_fraction: float = 0.2, seed: str = "course",) -> dict:
    validate(records)
    if not isinstance(test_fraction, (int, float)) or not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")
    if not isinstance(test_fraction, (int, float)) or not __import__("math").isfinite(test_fraction):
        raise ValueError("test_fraction must be finite")
    groups = {}
    for record in records:
        groups.setdefault(record["group"], []).append(record)
    # ranked_groups = sorted(groups, key=lambda group_name: 
    # group_names = list(groups)
    # rng = random.Random(seed)
    # rng.shuffle(group_names)

    # test_group_count = max(1, round(len(ranked_groups) * test_fraction))
    # test_groups = set(ranked_groups[:test_group_count])
    train = []
    test = []

    for group_name, group_records in groups.items():
        digest = hashlib.sha256(f"{seed}:{group_name}".encode("utf-8")).digest()
        fraction = int.from_bytes(digest, "big") / (2 ** 256)
        if fraction < test_fraction:
            test.extend(group_records)
        else:
            train.extend(group_records)
    return {"train":train, "test":test}

def summarize(train: list[dict], test: list[dict]) -> dict:
    result = audit(train, test)

    train_groups = {record["group"] for record in train}
    test_groups = {record["group"] for record in test}

    train_rows = len(train)
    test_rows = len(test)

    usable = (
        train_rows > 0
        and test_rows> 0
        and result["content_leakage_count"] == 0
        and result["group_leakage_count"] == 0
    )
    return {
        "train_rows": train_rows,
        "test_rows": test_rows,
        "train_groups": len(train_groups),
        "test_groups": len(test_groups),
        "content_leakage": result["content_leakage"],
        "content_leakage_count": result["content_leakage_count"],
        "group_leakage": result["group_leakage"],
        "group_leakage_count": result["group_leakage_count"],
        "usable": usable
    }