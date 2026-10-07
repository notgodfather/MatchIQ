"""
Experiment E5: Calibration and Threshold Selection.
Train LGBM on Synthetic-India, calibrate probabilities, select thresholds, and save model card.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from matchiq.io.loader import load_csv
from matchiq.mapping import apply_mapping
from matchiq.blocking.rules import block_exact, block_name_key, block_token, block_tfidf_knn, combine_blocks
from matchiq.features.builder import build_features
from matchiq.models.train import train_model
from matchiq.models.calibration import compute_calibration_curve, select_thresholds

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"

def main():
    print("Running E5: Calibration and Threshold Selection on Synthetic-India...")
    
    # 1. Load data
    syn_dir = PROJECT_ROOT / "data" / "synthetic" / "india"
    df_a = load_csv(syn_dir / "A.csv").set_index("rec_id")
    df_b = load_csv(syn_dir / "B.csv").set_index("rec_id")
    true_links_df = pd.read_csv(syn_dir / "truth.csv")
    mapping = {
        "name":    {"a": ["name"],    "b": ["name"]},
        "phone":   {"a": ["phone"],   "b": ["phone"]},
        "email":   {"a": ["email"],   "b": ["email"]},
        "address": {"a": ["address"], "b": ["address"]},
        "city":    {"a": ["city"],    "b": ["city"]},
        "postcode":{"a": ["postcode"],"b": ["postcode"]},
    }
    true_pairs = set(zip(true_links_df["id_A"], true_links_df["id_B"]))
    
    # 2. Map and Block
    df_a_mapped = apply_mapping(df_a, mapping, side="a")
    df_b_mapped = apply_mapping(df_b, mapping, side="b")

    blocks = [
        block_exact(df_a_mapped, df_b_mapped, "_norm_phone"),
        block_exact(df_a_mapped, df_b_mapped, "_norm_email"),
        block_name_key(df_a_mapped, df_b_mapped, "_norm_name", "_norm_city"),
        block_token(df_a_mapped, df_b_mapped, ["_norm_name", "_norm_address"], max_block_size=1000),
        block_tfidf_knn(df_a_mapped, df_b_mapped, ["_norm_name", "_norm_address", "_norm_city"], k=50)
    ]
    candidate_pairs = combine_blocks(*blocks)
    
    # 3. Split
    rng = np.random.default_rng(42)
    a_ids_shuffled = df_a_mapped.index.to_list()
    rng.shuffle(a_ids_shuffled)
    train_end = int(len(a_ids_shuffled) * 0.6)
    
    train_a_ids = set(a_ids_shuffled[:train_end])
    test_a_ids_set = set(a_ids_shuffled[train_end:])
    
    train_pairs = set(p for p in candidate_pairs if p[0] in train_a_ids)
    test_pairs = set(p for p in candidate_pairs if p[0] in test_a_ids_set)
    
    # 4. Features & Train
    train_features = build_features(df_a_mapped, df_b_mapped, train_pairs)
    train_features["label"] = [1 if p in true_pairs else 0 for p in train_features.index]
    
    test_features = build_features(df_a_mapped, df_b_mapped, test_pairs)
    y_test = np.array([1 if p in true_pairs else 0 for p in test_features.index])
    X_test = test_features.copy()

    # Train calibrated LGBM
    model = train_model(train_features, model_type="lgbm")
    
    # Predict probabilities on test
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # 5. Calibration Curve
    prob_true, prob_pred = compute_calibration_curve(y_test, y_prob, n_bins=10)
    
    # 6. Threshold Selection
    lower_t, upper_t = select_thresholds(y_test, y_prob, target_precision_high=0.99, target_recall_low=0.99)
    
    print("\nCalibration Curve (Binned Probabilities):")
    for pt, pp in zip(prob_true, prob_pred):
        print(f"  Predicted: {pp:.3f} -> True matches: {pt:.3f}")
        
    print(f"\nSelected Thresholds:")
    print(f"  Auto-ACCEPT (Upper) : >= {upper_t:.3f}")
    print(f"  REVIEW             : {lower_t:.3f} to {upper_t:.3f}")
    print(f"  Auto-REJECT (Lower) : <  {lower_t:.3f}")
    
    # 7. Model Card Generation
    # We save this as a JSON which can be used for resolution step.
    model_card = {
        "model_type": "lgbm_calibrated",
        "thresholds": {
            "match": upper_t,
            "review": lower_t
        },
        "features": list(X_test.columns),
        "calibration_data": {
            "prob_true": prob_true.tolist(),
            "prob_pred": prob_pred.tolist()
        }
    }
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    card_path = RESULTS_DIR / "model_card.json"
    with open(card_path, "w") as f:
        json.dump(model_card, f, indent=2)
    print(f"\nModel card saved to {card_path}")
    
    import pickle
    model_path = RESULTS_DIR / "model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    main()
