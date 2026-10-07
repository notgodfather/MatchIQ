"""
Column mapping: defines which raw columns map to each canonical field,
and applies the mapping (with multi-column concat) to a DataFrame.

Mapping format:
{
    "name":    {"a": ["given_name", "surname"], "b": ["customer_name"]},
    "phone":   {"a": ["mobile"],               "b": ["contact_no"]},
    ...
}
"""
from __future__ import annotations

import pandas as pd
from matchiq.normalize import (
    normalize_name, normalize_phone, normalize_email,
    normalize_city, normalize_postcode, normalize_address,
)

CANONICAL_FIELDS = ("name", "phone", "email", "address", "city", "state", "postcode",
                    "company", "dob", "other_text")

NORMALIZERS: dict[str, callable] = {
    "name":       normalize_name,
    "phone":      normalize_phone,
    "email":      normalize_email,
    "address":    normalize_address,
    "city":       normalize_city,
    "state":      normalize_city,   # reuse city normalizer (alias lookup)
    "postcode":   normalize_postcode,
    "company":    normalize_name,   # reuse: strip titles/punct; TODO: add suffix removal
    "dob":        lambda x: x,      # passthrough; full date normalizer in later milestone
    "other_text": lambda x: x,      # passthrough
}


def apply_mapping(df: pd.DataFrame, mapping: dict, side: str) -> pd.DataFrame:
    """
    Apply the column mapping to a DataFrame for one side ('a' or 'b').

    For each canonical field, concatenate the raw columns listed in
    mapping[field][side] (with a single space), then normalize.

    Returns a copy of df with additional columns:
      - `_raw_<field>`: concatenated raw value
      - `_norm_<field>`: normalized value (may be None)
    """
    result = df.copy()

    for field, sides in mapping.items():
        cols = sides.get(side, [])
        if not cols:
            continue

        # Concatenate columns (treat NaN as empty string for concat, then replace "" → None)
        def concat_row(row):
            parts = [str(row[c]).strip() for c in cols if c in row.index and not pd.isna(row[c])]
            return " ".join(parts) if parts else None

        raw_col = f"_raw_{field}"
        norm_col = f"_norm_{field}"

        result[raw_col] = result.apply(concat_row, axis=1)

        normalizer = NORMALIZERS.get(field, lambda x: x)
        result[norm_col] = result[raw_col].apply(
            lambda v: normalizer(v) if v is not None else None
        )

    return result
