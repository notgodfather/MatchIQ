"""
Experiment E2: Evaluate blocking strategies on Febrl4 and Synthetic-India.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from matchiq.io.loader import load_csv
from matchiq.mapping import apply_mapping
from matchiq.blocking.rules import block_exact, block_name_key, block_token, block_tfidf_knn
from matchiq.blocking.evaluate import evaluate_blocking

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"

def evaluate_dataset(dataset_name: str, hard_mode: bool = False):
    print(f"--- Evaluating {dataset_name} (hard_mode={hard_mode}) ---")
    
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
    
    df_a_mapped = apply_mapping(df_a, mapping, side="a")
    df_b_mapped = apply_mapping(df_b, mapping, side="b")

    blockers = []
    if not hard_mode and dataset_name != "febrl4":
        blockers.append(("exact_phone", lambda a, b: block_exact(a, b, "_norm_phone")))
        blockers.append(("exact_email", lambda a, b: block_exact(a, b, "_norm_email")))
        
    blockers.extend([
        ("name_key", lambda a, b: block_name_key(a, b, "_norm_name", "_norm_city")),
        ("token_name_address", lambda a, b: block_token(a, b, ["_norm_name", "_norm_address"], max_block_size=1000)),
        ("tfidf_knn", lambda a, b: block_tfidf_knn(a, b, ["_norm_name", "_norm_address", "_norm_city"], k=50)),
    ])

    results = evaluate_blocking(df_a_mapped, df_b_mapped, true_pairs, blockers)
    
    print(json.dumps(results, indent=2))
    
    suffix = "_hard" if hard_mode else ""
    out_file = RESULTS_DIR / f"e02_blocking_{dataset_name.replace('-', '_')}{suffix}.json"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved to {out_file}\n")


def main():
    evaluate_dataset("febrl4")
    evaluate_dataset("synthetic-india")
    evaluate_dataset("synthetic-india", hard_mode=True)

if __name__ == "__main__":
    main()
