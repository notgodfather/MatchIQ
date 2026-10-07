"""
Evaluate blocking strategies on datasets.
Computes pairs completeness, reduction ratio, and runtimes.
"""
from __future__ import annotations

import time
import pandas as pd
from typing import Callable, Sequence

from matchiq.blocking.rules import combine_blocks


def evaluate_blocking(
    df_a: pd.DataFrame, 
    df_b: pd.DataFrame, 
    true_pairs: set[tuple[str, str]], 
    blockers: list[tuple[str, Callable[[pd.DataFrame, pd.DataFrame], set[tuple[str, str]]]]]
) -> dict:
    """
    Run multiple blockers and measure their performance and union performance.
    
    Returns metrics dict.
    """
    n_a = len(df_a)
    n_b = len(df_b)
    total_possible = n_a * n_b
    total_true = len(true_pairs)
    
    results = {}
    
    all_candidate_pairs = set()
    total_time = 0.0
    
    for name, blocker_func in blockers:
        start_t = time.time()
        pairs = blocker_func(df_a, df_b)
        elapsed = time.time() - start_t
        
        all_candidate_pairs = combine_blocks(all_candidate_pairs, pairs)
        
        found_true = len(pairs & true_pairs)
        n_candidates = len(pairs)
        
        results[f"blocker_{name}"] = {
            "time_s": round(elapsed, 3),
            "candidates": n_candidates,
            "completeness": found_true / total_true if total_true > 0 else 0,
            "reduction_ratio": 1.0 - (n_candidates / total_possible) if total_possible > 0 else 0,
        }
        total_time += elapsed
        
    # Union metrics
    union_found_true = len(all_candidate_pairs & true_pairs)
    n_union_candidates = len(all_candidate_pairs)
    
    results["union"] = {
        "time_s": round(total_time, 3),
        "candidates": n_union_candidates,
        "completeness": union_found_true / total_true if total_true > 0 else 0,
        "reduction_ratio": 1.0 - (n_union_candidates / total_possible) if total_possible > 0 else 0,
        "quality": union_found_true / n_union_candidates if n_union_candidates > 0 else 0,
    }
    
    return results
