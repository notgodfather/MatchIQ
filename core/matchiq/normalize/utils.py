import pandas as pd
import unicodedata
import re

# Placeholders checked BEFORE stripping punctuation (lowercased raw)
PLACEHOLDERS_RAW = {"", "na", "n/a", "null", "none", "-", "unknown", "0000000000", "n.a.", "n.a", "nan"}

def clean_string(s: str | None, keep_punct: str = "") -> str | None:
    if pd.isna(s) or s is None:
        return None
    s = str(s).strip()
    if not s:
        return None

    # Check placeholder before punctuation removal (compare lowercased raw value)
    if s.lower() in PLACEHOLDERS_RAW:
        return None

    # NFKD and strip accents
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
    s = s.lower()

    # Strip punctuation except what's in keep_punct
    if keep_punct:
        escaped = re.escape(keep_punct)
        s = re.sub(f'[^a-z0-9{escaped}\\s]', ' ', s)
    else:
        s = re.sub(r'[^a-z0-9\s]', ' ', s)

    # Collapse whitespace
    s = re.sub(r'\s+', ' ', s).strip()

    # Check placeholder again after stripping (catches "n a" style)
    if s in {"", "na", "null", "none", "unknown", "0000000000"}:
        return None

    return s if s else None
