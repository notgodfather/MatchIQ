import phonenumbers
from .utils import clean_string

def normalize_phone(phone: str | None) -> str | None:
    # Keep + for E.164 parsing
    s = clean_string(phone, keep_punct="+")
    if not s:
        return None
    
    try:
        # Default to IN region as specified
        parsed = phonenumbers.parse(s, "IN")
        if phonenumbers.is_possible_number(parsed):
            # Use E.164 then take the last 10 digits (the subscriber number)
            # This avoids NATIONAL format's leading 0 issue
            e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            digits = "".join(c for c in e164 if c.isdigit())
            return digits[-10:] if len(digits) >= 10 else None
    except phonenumbers.NumberParseException:
        pass
    
    return None
