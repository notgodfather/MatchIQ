"""
Noise operators — pure functions, all take a string and an rng (numpy.random.Generator).

Each operator returns a string (possibly identical if nothing to perturb).
Returning the original string is always safe; callers must handle the None case
before calling these.

Operators:
  - typo_insert    : insert a random keyboard-adjacent char
  - typo_delete    : delete one random char
  - typo_swap      : swap two adjacent chars
  - typo_substitute: replace a char with a keyboard-adjacent one
  - initials       : first token → first character (e.g. "Rahul Kumar" → "R. Kumar")
  - name_order_swap: swap first and last token ("Rahul Kumar" → "Kumar Rahul")
  - add_title      : prepend a random Indian title
  - city_alias      : replace a city with a known alias
  - phone_format   : reformat a 10-digit phone number
  - phone_typo     : one digit substitution in a 10-digit phone number
  - missing        : always returns None (field dropout)
"""
from __future__ import annotations

import numpy as np

# ── Keyboard adjacency (QWERTY) for ASCII chars ────────────────────────────

_KEYBOARD: dict[str, str] = {
    'a': 'sqzw', 'b': 'vghn', 'c': 'xdfv', 'd': 'serfcx', 'e': 'wrsdf',
    'f': 'drtgvc', 'g': 'ftyhbv', 'h': 'gyujnb', 'i': 'ujko', 'j': 'huikmn',
    'k': 'jiolm', 'l': 'kop', 'm': 'njk', 'n': 'bhjm', 'o': 'iklp',
    'p': 'ol', 'q': 'wa', 'r': 'edft', 's': 'awedxz', 't': 'rfgy',
    'u': 'yhji', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc', 'y': 'tghu',
    'z': 'asx',
    '0': '9', '1': '2', '2': '13', '3': '24', '4': '35',
    '5': '46', '6': '57', '7': '68', '8': '79', '9': '80',
}


def _adjacent(char: str, rng: np.random.Generator) -> str:
    neighbors = _KEYBOARD.get(char.lower(), "")
    if not neighbors:
        return char
    return rng.choice(list(neighbors))


# ── String-level noise ─────────────────────────────────────────────────────

def typo_insert(s: str, rng: np.random.Generator) -> str:
    if not s:
        return s
    pos = rng.integers(0, len(s) + 1)
    ch = _adjacent(s[min(pos, len(s) - 1)], rng)
    return s[:pos] + ch + s[pos:]


def typo_delete(s: str, rng: np.random.Generator) -> str:
    if len(s) <= 1:
        return s
    pos = rng.integers(0, len(s))
    return s[:pos] + s[pos + 1:]


def typo_swap(s: str, rng: np.random.Generator) -> str:
    if len(s) < 2:
        return s
    pos = rng.integers(0, len(s) - 1)
    lst = list(s)
    lst[pos], lst[pos + 1] = lst[pos + 1], lst[pos]
    return "".join(lst)


def typo_substitute(s: str, rng: np.random.Generator) -> str:
    if not s:
        return s
    pos = rng.integers(0, len(s))
    lst = list(s)
    lst[pos] = _adjacent(lst[pos], rng)
    return "".join(lst)


# ── Name-level noise ───────────────────────────────────────────────────────

_TITLES = ["Mr.", "Mrs.", "Ms.", "Dr.", "Shri", "Smt.", "Prof.", "Er."]


def initials(name: str, rng: np.random.Generator) -> str:
    """Replace the first token with its initial: 'Rahul Kumar' → 'R. Kumar'."""
    tokens = name.strip().split()
    if len(tokens) < 2:
        return name
    return tokens[0][0].upper() + ". " + " ".join(tokens[1:])


def name_order_swap(name: str, rng: np.random.Generator) -> str:
    """Swap first and last tokens: 'Rahul Kumar' → 'Kumar Rahul'."""
    tokens = name.strip().split()
    if len(tokens) < 2:
        return name
    return tokens[-1] + " " + " ".join(tokens[:-1])


def add_title(name: str, rng: np.random.Generator) -> str:
    """Prepend a random title."""
    title = _TITLES[rng.integers(0, len(_TITLES))]
    return f"{title} {name}"


# ── City-level noise ───────────────────────────────────────────────────────

_CITY_ALIASES: dict[str, list[str]] = {
    "bengaluru": ["Bangalore", "Bglr", "BLR"],
    "mumbai":    ["Bombay"],
    "chennai":   ["Madras"],
    "kolkata":   ["Calcutta"],
    "gurugram":  ["Gurgaon"],
    "kochi":     ["Cochin"],
}
# Build reverse map: canonical → list of aliases
_CITY_NOISE: dict[str, list[str]] = {k: v for k, v in _CITY_ALIASES.items()}


def city_alias(city: str, rng: np.random.Generator) -> str:
    """Replace city with an alias if available."""
    key = city.strip().lower()
    options = _CITY_NOISE.get(key)
    if options:
        return options[rng.integers(0, len(options))]
    return city


# ── Phone-level noise ──────────────────────────────────────────────────────

def phone_format(phone: str, rng: np.random.Generator) -> str:
    """
    Reformat a 10-digit national phone number into one of several formats:
    - +91 XXXXX XXXXX
    - 0XXXXXXXXXX
    - XXXXX-XXXXX
    - +91-XXXXX-XXXXX
    """
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) != 10:
        return phone
    fmt = rng.integers(0, 4)
    if fmt == 0:
        return f"+91 {digits[:5]} {digits[5:]}"
    elif fmt == 1:
        return f"0{digits}"
    elif fmt == 2:
        return f"{digits[:5]}-{digits[5:]}"
    else:
        return f"+91-{digits[:5]}-{digits[5:]}"


def phone_typo(phone: str, rng: np.random.Generator) -> str:
    """Replace one random digit in a 10-digit phone with an adjacent digit."""
    digits = list("".join(c for c in phone if c.isdigit()))
    if len(digits) != 10:
        return phone
    pos = rng.integers(0, 10)
    digits[pos] = _adjacent(digits[pos], rng)
    return "".join(digits)


# ── Field dropout ──────────────────────────────────────────────────────────

def missing(s: str, rng: np.random.Generator) -> None:  # noqa: ARG001
    """Always returns None — used for field dropout."""
    return None


# ── Convenience: apply one operator chosen at random ──────────────────────

_STRING_OPS = [typo_insert, typo_delete, typo_swap, typo_substitute]


def random_string_typo(s: str, rng: np.random.Generator) -> str:
    op = _STRING_OPS[rng.integers(0, len(_STRING_OPS))]
    return op(s, rng)
