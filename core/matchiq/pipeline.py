"""
End-to-end pipeline execution (T4.6).
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import numpy as np

from matchiq.io.loader import load_csv
from matchiq.mapping import apply_mapping
from matchiq.blocking.rules import block_exact, block_name_key, block_token, block_tfidf_knn, combine_blocks
from matchiq.features.builder import build_features
from matchiq.resolution import resolve_one_to_one


def run_pipeline(
    df_a_path: Path | str, 
    df_b_path: Path | str, 
    mapping: Dict[str, Any],
    model_path: Path | str,
    model_card_path: Path | str,
    output_path: Path | str
) -> pd.DataFrame:
    """
    Runs the end-to-end matching pipeline.
    1. Loads datasets
    2. Maps columns
    3. Blocks
    4. Builds Features
    5. Predicts (using loaded model)
    6. Resolves to 1-to-1 matches
    7. Saves results
    """
    print("1. Loading data...")
    df_a = load_csv(df_a_path).set_index("rec_id")
    df_b = load_csv(df_b_path).set_index("rec_id")
    
    print("2. Applying mapping...")
    df_a_mapped = apply_mapping(df_a, mapping, side="a")
    df_b_mapped = apply_mapping(df_b, mapping, side="b")
    
    print("3. Generating candidate pairs (Blocking)...")
    blocks = []
    if "_norm_phone" in df_a_mapped.columns:
        blocks.append(block_exact(df_a_mapped, df_b_mapped, "_norm_phone"))
    if "_norm_email" in df_a_mapped.columns:
        blocks.append(block_exact(df_a_mapped, df_b_mapped, "_norm_email"))
        
    blocks.append(block_name_key(df_a_mapped, df_b_mapped, "_norm_name", "_norm_city"))
    blocks.append(block_token(df_a_mapped, df_b_mapped, ["_norm_name", "_norm_address"], max_block_size=1000))
    blocks.append(block_tfidf_knn(df_a_mapped, df_b_mapped, ["_norm_name", "_norm_address", "_norm_city"], k=10))
    
    candidate_pairs = combine_blocks(*blocks)
    print(f"   Generated {len(candidate_pairs)} candidate pairs.")
    
    print("4. Building features...")
    features_df = build_features(df_a_mapped, df_b_mapped, candidate_pairs)
    
    # Ensure columns match training
    with open(model_card_path, "r") as f:
        model_card = json.load(f)
    feature_cols = model_card["features"]
    
    if features_df.empty:
        print("   No features to predict (0 candidate pairs).")
        out_cols = ["id_A", "id_B", "probability", "decision"] + feature_cols
        return pd.DataFrame(columns=out_cols)
        
    print("5. Predicting probabilities...")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
        
    # Reorder or fill missing feature columns with NaNs if any are missing
    for col in feature_cols:
        if col not in features_df.columns:
            features_df[col] = np.nan
    X = features_df[feature_cols].astype(float)
    
    probs = model.predict_proba(X)[:, 1]
    features_df["probability"] = probs
    
    # Thresholds
    t_match = model_card["thresholds"]["match"]
    t_review = model_card["thresholds"]["review"]
    
    print("6. Resolving 1-to-1 matches...")
    # Add index as columns for resolution
    features_df = features_df.reset_index()
    
    # We resolve everything above the review threshold
    resolved_df = resolve_one_to_one(features_df, id_col_a="id_A", id_col_b="id_B", prob_col="probability", lower_threshold=t_review)
    
    # Assign decisions
    resolved_df["decision"] = resolved_df["probability"].apply(
        lambda p: "MATCH" if p >= t_match else "REVIEW"
    )
    
    print(f"   Found {len(resolved_df[resolved_df['decision'] == 'MATCH'])} auto-matches.")
    print(f"   Found {len(resolved_df[resolved_df['decision'] == 'REVIEW'])} reviews.")
    
    print(f"7. Saving results to {output_path}...")
    out_cols = ["id_A", "id_B", "probability", "decision"] + feature_cols
    resolved_df[out_cols].to_csv(output_path, index=False)
    
    print("Pipeline complete!")
    return resolved_df[out_cols]
