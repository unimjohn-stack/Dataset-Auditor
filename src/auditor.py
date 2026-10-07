import hashlib
import re
import unicodedata

def fingerprint(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.casefold()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()