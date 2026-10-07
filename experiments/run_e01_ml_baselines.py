"""
Experiment E1: Does ML beat baselines? 
Compares B0, B1, B2, LR, RF, GBM on identical splits of Febrl4 and Synthetic-India.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score

from matchiq.io.loader import load_csv
from matchiq.mapping import apply_mapping
from matchiq.blocking.rules import block_exact, block_name_key, block_token, block_tfidf_knn, combine_blocks
from matchiq.features.builder import build_features
from matchiq.features.training import make_entity_splits, apply_field_dropout
from matchiq.models.train import train_model
from matchiq.baselines import baseline_b1, baseline_b2


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"

def evaluate_models(dataset_name: str, hard_mode: bool = False):
    print(f"\n{'='*50}\nEvaluating E1 on {dataset_name} (hard_mode={hard_mode})\n{'='*50}")
    
    # 1. Load data
    if dataset_name == "febrl4":
        df_a = load_csv(DATA_DIR / "febrl4_A.csv").set_index("rec_id")
        df_b = load_csv(DATA_DIR / "febrl4_B.csv").set_index("rec_id")
        true_links_df = pd.read_csv(DATA_DIR / "febrl4_true_links.csv")
        mapping = {
            "name":    {"a": ["given_name", "surname"], "b": ["given_name", "surname"]},
            "address": {"a": ["address_1", "address_2"], "b": ["address_1", "address_2"]},
            "city":    {"a": ["suburb"],  "b": ["suburb"]},
            "postcode":{"a": ["postcode"],"b": ["postcode"]},
            "dob":     {"a": ["date_of_birth"], "b": ["date_of_birth"]},
        }
    elif dataset_name == "synthetic-india":
        syn_dir = PROJECT_ROOT / "data" / "synthetic" / "india"
        df_a = load_csv(syn_dir / "A.csv").set_index("rec_id")
        df_b = load_csv(syn_dir / "B.csv").set_index("rec_id")
        true_links_df = pd.read_csv(syn_dir / "truth.csv")
        mapping = {
            "name":    {"a": ["name"],    "b": ["name"]},
            "address": {"a": ["address"], "b": ["address"]},
            "city":    {"a": ["city"],    "b": ["city"]},
            "postcode":{"a": ["postcode"],"b": ["postcode"]},
        }
        if not hard_mode:
            mapping["phone"] = {"a": ["phone"], "b": ["phone"]}
            mapping["email"] = {"a": ["email"], "b": ["email"]}
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")

    true_pairs = set(zip(true_links_df["id_A"], true_links_df["id_B"]))
    
    # 2. Apply Mapping
    df_a_mapped = apply_mapping(df_a, mapping, side="a")
    df_b_mapped = apply_mapping(df_b, mapping, side="b")

    # 3. Blocking (Union)
    print("Running blockers...")
    blocks = []
    if not hard_mode and dataset_name != "febrl4":
        blocks.append(block_exact(df_a_mapped, df_b_mapped, "_norm_phone"))
        blocks.append(block_exact(df_a_mapped, df_b_mapped, "_norm_email"))
    
    blocks.append(block_name_key(df_a_mapped, df_b_mapped, "_norm_name", "_norm_city"))
    blocks.append(block_token(df_a_mapped, df_b_mapped, ["_norm_name", "_norm_address"], max_block_size=1000))
    blocks.append(block_tfidf_knn(df_a_mapped, df_b_mapped, ["_norm_name", "_norm_address", "_norm_city"], k=50))
    
    candidate_pairs = combine_blocks(*blocks)
    print(f"Total candidate pairs: {len(candidate_pairs)}")

    # 4. Split Train/Test by Entity
    # Since dataset A is clean (no duplicates within A), we can safely partition id_A.
    rng = np.random.default_rng(42)
    a_ids_shuffled = df_a_mapped.index.to_list()
    rng.shuffle(a_ids_shuffled)
    train_end = int(len(a_ids_shuffled) * 0.6)
    
    train_a_ids = set(a_ids_shuffled[:train_end])
    test_a_ids_set = set(a_ids_shuffled[train_end:])
    
    train_pairs = set(p for p in candidate_pairs if p[0] in train_a_ids)
    test_pairs = set(p for p in candidate_pairs if p[0] in test_a_ids_set)
    print(f"Train pairs: {len(train_pairs)}, Test pairs: {len(test_pairs)}")

    # Total true links that fell into the test split (for strict recall calculation)
    test_true_pairs = set(p for p in true_pairs if p[0] in test_a_ids_set)
    
    print(f"True matches in test split: {len(test_true_pairs)}")

    # 5. Build features
    print("Building features for train...")
    train_features = build_features(df_a_mapped, df_b_mapped, train_pairs)
    train_features["label"] = [1 if p in true_pairs else 0 for p in train_features.index]
    
    # Optional field dropout on train
    train_features = apply_field_dropout(train_features, dropout_rate=0.2, seed=42)

    print("Building features for test...")
    test_features = build_features(df_a_mapped, df_b_mapped, test_pairs)
    y_test_true = np.array([1 if p in true_pairs else 0 for p in test_features.index])
    X_test = test_features.copy()

    results = []

    # 6. ML Models
    for model_type in ["lr", "rf", "lgbm"]:
        print(f"Training {model_type}...")
        t0 = time.time()
        model = train_model(train_features, model_type=model_type)
        t_train = time.time() - t0
        
        t0 = time.time()
        y_pred = model.predict(X_test)
        t_pred = time.time() - t0
        
        # Calculate metrics
        p = precision_score(y_test_true, y_pred, zero_division=0)
        
        # End-to-end recall: correctly predicted / ALL true matches in test set
        # y_pred is for candidates only.
        correct_predictions = sum((y_test_true == 1) & (y_pred == 1))
        r = correct_predictions / len(test_true_pairs) if len(test_true_pairs) > 0 else 0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
        
        results.append({
            "model": model_type,
            "precision": p,
            "recall": r,
            "f1": f1,
            "train_time_s": t_train,
            "pred_time_s": t_pred
        })

    # 7. Baselines on Test pairs
    print("Running baselines on test set...")
    # Get df subset for test pairs
    test_a_ids = list(set([p[0] for p in test_pairs]))
    test_b_ids = list(set([p[1] for p in test_pairs]))
    df_a_test = df_a_mapped.loc[test_a_ids]
    df_b_test = df_b_mapped.loc[test_b_ids]
    
    for fn, label in [(baseline_b1, "B1"), (baseline_b2, "B2")]:
        r = fn(df_a_test, df_b_test, test_true_pairs)
        results.append({
            "model": label,
            "precision": r["precision"],
            "recall": r["recall"],
            "f1": r["f1"],
            "train_time_s": 0.0,
            "pred_time_s": r["runtime_s"]
        })

    # Print and save
    df_res = pd.DataFrame(results)
    print("\nResults:")
    print(df_res.to_string(index=False))
    
    suffix = "_hard" if hard_mode else ""
    out_file = RESULTS_DIR / f"e01_ml_baselines_{dataset_name.replace('-', '_')}{suffix}.csv"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df_res.to_csv(out_file, index=False)
    print(f"\nSaved to {out_file}\n")


def main():
    evaluate_models("febrl4")
    evaluate_models("synthetic-india")
    evaluate_models("synthetic-india", hard_mode=True)

if __name__ == "__main__":
    main()
