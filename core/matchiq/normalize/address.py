import yaml
from pathlib import Path
from .utils import clean_string

ADDRESS_ABBREV_PATH = Path(__file__).parent / "resources" / "address_abbrev.yaml"

def _load_abbrev():
    if ADDRESS_ABBREV_PATH.exists():
        with open(ADDRESS_ABBREV_PATH, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

ABBREVS = _load_abbrev()

def normalize_address(address: str | None) -> str | None:
    s = clean_string(address)
    if not s:
        return None
        
    tokens = s.split()
    tokens = [ABBREVS.get(t, t) for t in tokens]
    
    return " ".join(tokens)
