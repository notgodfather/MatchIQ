"""
Resolution strategies to convert candidate pair probabilities into final match decisions.
"""
from __future__ import annotations

import pandas as pd


def resolve_one_to_one(
    predictions_df: pd.DataFrame, 
    id_col_a: str = "id_A", 
    id_col_b: str = "id_B", 
    prob_col: str = "probability",
    lower_threshold: float = 0.5
) -> pd.DataFrame:
    """
    Greedy one-to-one resolution.
    Sorts pairs by probability descending. Iterates and accepts a pair if
    neither record has been accepted yet.
    Only considers pairs with probability >= lower_threshold.
    
    Returns a DataFrame with the accepted pairs.
    """
    df = predictions_df[predictions_df[prob_col] >= lower_threshold].copy()
    if df.empty:
        return df

    # Sort descending by probability
    df = df.sort_values(by=prob_col, ascending=False)
    
    seen_a = set()
    seen_b = set()
    accepted = []

    # Using iterrows or vectors? iterrows is okay since it's just candidates
    for row in df.itertuples(index=False):
        a = getattr(row, id_col_a)
        b = getattr(row, id_col_b)
        
        if a not in seen_a and b not in seen_b:
            accepted.append(row)
            seen_a.add(a)
            seen_b.add(b)

    return pd.DataFrame(accepted)
