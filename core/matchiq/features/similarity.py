"""
Similarity functions for feature engineering.
All functions handle missing values by returning np.nan.
Results are typically in the range [0.0, 1.0].
"""
from __future__ import annotations

import re
import numpy as np
import pandas as pd
import jellyfish
from rapidfuzz import fuzz, distance


def _is_missing(val) -> bool:
    return pd.isna(val) or val is None or str(val).strip() == ""


# --- Generic String Similarities ---

def exact_equal(s1: str | None, s2: str | None) -> float:
    if _is_missing(s1) or _is_missing(s2):
        return np.nan
    return 1.0 if str(s1).strip() == str(s2).strip() else 0.0


def jaro_winkler(s1: str | None, s2: str | None) -> float:
    if _is_missing(s1) or _is_missing(s2):
        return np.nan
    return distance.JaroWinkler.similarity(str(s1), str(s2))


def norm_levenshtein(s1: str | None, s2: str | None) -> float:
    if _is_missing(s1) or _is_missing(s2):
        return np.nan
    return fuzz.ratio(str(s1), str(s2)) / 100.0


def token_sort_ratio(s1: str | None, s2: str | None) -> float:
    if _is_missing(s1) or _is_missing(s2):
        return np.nan
    return fuzz.token_sort_ratio(str(s1), str(s2)) / 100.0


def token_set_ratio(s1: str | None, s2: str | None) -> float:
    if _is_missing(s1) or _is_missing(s2):
        return np.nan
    return fuzz.token_set_ratio(str(s1), str(s2)) / 100.0


def token_jaccard(s1: str | None, s2: str | None) -> float:
    if _is_missing(s1) or _is_missing(s2):
        return np.nan
    tokens1 = set(str(s1).lower().split())
    tokens2 = set(str(s2).lower().split())
    if not tokens1 or not tokens2:
        return 0.0
    return len(tokens1 & tokens2) / len(tokens1 | tokens2)


def phonetic_equal(s1: str | None, s2: str | None) -> float:
    if _is_missing(s1) or _is_missing(s2):
        return np.nan
    return 1.0 if jellyfish.metaphone(str(s1)) == jellyfish.metaphone(str(s2)) else 0.0


def length_diff(s1: str | None, s2: str | None) -> float:
    if _is_missing(s1) or _is_missing(s2):
        return np.nan
    return abs(len(str(s1)) - len(str(s2)))


# --- Name Specific ---

def initial_compatible(s1: str | None, s2: str | None) -> float:
    """
    Checks if initials match, e.g. "r kumar" ~ "rahul kumar".
    We check if one is a prefix initial of the other.
    Returns 1.0 if compatible, 0.0 otherwise.
    """
    if _is_missing(s1) or _is_missing(s2):
        return np.nan
    
    t1 = str(s1).lower().split()
    t2 = str(s2).lower().split()
    
    if len(t1) != len(t2):
        return 0.0
        
    for w1, w2 in zip(t1, t2):
        if w1 == w2:
            continue
        # If one is a single letter, check if it matches the first letter of the other
        if (len(w1) == 1 and w2.startswith(w1)) or (len(w2) == 1 and w1.startswith(w2)):
            continue
        return 0.0
        
    return 1.0


# --- Phone Specific ---

def phone_edit_dist_le_1(s1: str | None, s2: str | None) -> float:
    if _is_missing(s1) or _is_missing(s2):
        return np.nan
    dist = distance.Levenshtein.distance(str(s1), str(s2))
    return 1.0 if dist <= 1 else 0.0


def phone_last_7_equal(s1: str | None, s2: str | None) -> float:
    if _is_missing(s1) or _is_missing(s2):
        return np.nan
    v1 = str(s1).strip()
    v2 = str(s2).strip()
    if len(v1) >= 7 and len(v2) >= 7 and v1[-7:] == v2[-7:]:
        return 1.0
    return 0.0


# --- Email Specific ---

def email_local_jaro(s1: str | None, s2: str | None) -> float:
    if _is_missing(s1) or _is_missing(s2):
        return np.nan
    local1 = str(s1).split('@')[0] if '@' in str(s1) else str(s1)
    local2 = str(s2).split('@')[0] if '@' in str(s2) else str(s2)
    return distance.JaroWinkler.similarity(local1, local2)


def email_domain_equal(s1: str | None, s2: str | None) -> float:
    if _is_missing(s1) or _is_missing(s2):
        return np.nan
    dom1 = str(s1).split('@')[1] if '@' in str(s1) else ""
    dom2 = str(s2).split('@')[1] if '@' in str(s2) else ""
    if not dom1 or not dom2:
        return 0.0
    return 1.0 if dom1 == dom2 else 0.0


# --- Address / Postcode Specific ---

def house_number_equal(s1: str | None, s2: str | None) -> float:
    """Extract first digits from address and compare."""
    if _is_missing(s1) or _is_missing(s2):
        return np.nan
    
    m1 = re.search(r'\d+', str(s1))
    m2 = re.search(r'\d+', str(s2))
    
    if m1 and m2:
        return 1.0 if m1.group() == m2.group() else 0.0
    return 0.0


def pincode_first_3_equal(s1: str | None, s2: str | None) -> float:
    if _is_missing(s1) or _is_missing(s2):
        return np.nan
    v1, v2 = str(s1).strip(), str(s2).strip()
    if len(v1) >= 3 and len(v2) >= 3 and v1[:3] == v2[:3]:
        return 1.0
    return 0.0
