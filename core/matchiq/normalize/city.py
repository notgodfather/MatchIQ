import yaml
from pathlib import Path
from .utils import clean_string

CITY_ALIASES_PATH = Path(__file__).parent / "resources" / "city_aliases.yaml"

def _load_aliases():
    if CITY_ALIASES_PATH.exists():
        with open(CITY_ALIASES_PATH, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

ALIASES = _load_aliases()

def normalize_city(city: str | None) -> str | None:
    s = clean_string(city)
    if not s:
        return None
        
    return ALIASES.get(s, s)
