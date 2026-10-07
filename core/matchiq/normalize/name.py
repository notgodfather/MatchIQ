import yaml
from pathlib import Path
from .utils import clean_string

TITLES_PATH = Path(__file__).parent / "resources" / "titles.yaml"

def _load_titles():
    if TITLES_PATH.exists():
        with open(TITLES_PATH, 'r') as f:
            return set(yaml.safe_load(f) or [])
    return set()

TITLES = _load_titles()

def normalize_name(name: str | None) -> str | None:
    s = clean_string(name)
    if not s:
        return None
        
    tokens = s.split()
    # Remove titles
    tokens = [t for t in tokens if t not in TITLES]
    
    if not tokens:
        return None
        
    return " ".join(tokens)

def sorted_name(name: str | None) -> str | None:
    norm = normalize_name(name)
    if not norm:
        return None
    return " ".join(sorted(norm.split()))
