from .utils import clean_string

def normalize_email(email: str | None) -> str | None:
    # We keep @ and . and + for email structure
    s = clean_string(email, keep_punct="@.+")
    if not s or "@" not in s:
        return None
        
    local, domain = s.split("@", 1)
    if not local or not domain:
        return None
        
    # Optional Gmail dot/plus-tag handling can go here later if configured
    return f"{local}@{domain}"
