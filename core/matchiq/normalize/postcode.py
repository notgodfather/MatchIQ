from .utils import clean_string

def normalize_postcode(postcode: str | None) -> str | None:
    s = clean_string(postcode)
    if not s:
        return None
        
    # Keep only digits
    digits = "".join(c for c in s if c.isdigit())
    if len(digits) == 6:
        return digits
    return None
