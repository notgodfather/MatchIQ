"""
CLI entry point for MatchIQ core.

Usage:
    python -m matchiq.cli baseline --dataset febrl4
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import pandas as pd

# Project root = parent of the `core/` directory where this package lives
_PACKAGE_ROOT = Path(__file__).resolve().parent          # core/matchiq/
_CORE_ROOT    = _PACKAGE_ROOT.parent                     # core/
PROJECT_ROOT  = _CORE_ROOT.parent                        # miniproject/
RESULTS_DIR   = PROJECT_ROOT / "experiments" / "results"
DATA_DIR      = PROJECT_ROOT / "data" / "raw"


def run_baseline(dataset: str, hard_mode: bool = False):
    """Load dataset, apply mapping, run B0/B1/B2 baselines, print and save results."""
    from matchiq.io.loader import load_csv
    from matchiq.mapping import apply_mapping
    from matchiq.baselines import baseline_b0, baseline_b1, baseline_b2

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if dataset == "febrl4":
        path_a     = DATA_DIR / "febrl4_A.csv"
        path_b     = DATA_DIR / "febrl4_B.csv"
        links_path = DATA_DIR / "febrl4_true_links.csv"

        print(f"Loading {path_a} …")
        df_a = load_csv(path_a).set_index("rec_id")
        df_b = load_csv(path_b).set_index("rec_id")

        true_links = pd.read_csv(links_path)
        true_pairs = set(zip(true_links["id_A"], true_links["id_B"]))

        # Febrl4 column mapping
        mapping = {
            "name":    {"a": ["given_name", "surname"], "b": ["given_name", "surname"]},
            "address": {"a": ["address_1", "address_2"], "b": ["address_1", "address_2"]},
            "city":    {"a": ["suburb"],  "b": ["suburb"]},
            "postcode":{"a": ["postcode"],"b": ["postcode"]},
            "dob":     {"a": ["date_of_birth"], "b": ["date_of_birth"]},
        }

    elif dataset == "synthetic-india":
        from matchiq.synthetic.generator import GeneratorConfig, generate

        syn_dir = DATA_DIR.parent / "synthetic" / "india"
        if not (syn_dir / "A.csv").exists():
            print("Generating synthetic-India dataset (n=2000, seed=42) …")
            cfg = GeneratorConfig(n_entities=2000, seed=42)
            summary = generate(cfg, out_dir=syn_dir)
            print(f"  Generated: {summary}")
        else:
            print(f"Using cached synthetic data in {syn_dir}")

        path_a     = syn_dir / "A.csv"
        path_b     = syn_dir / "B.csv"
        links_path = syn_dir / "truth.csv"

        df_a = load_csv(path_a).set_index("rec_id")
        df_b = load_csv(path_b).set_index("rec_id")

        true_links = pd.read_csv(links_path)
        true_pairs = set(zip(true_links["id_A"], true_links["id_B"]))

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
        raise ValueError(f"Unknown dataset: {dataset!r}. Supported: febrl4, synthetic-india")

    print("Applying column mapping …")
    df_a = apply_mapping(df_a, mapping, side="a")
    df_b = apply_mapping(df_b, mapping, side="b")

    print(f"Dataset A: {len(df_a)} rows | Dataset B: {len(df_b)} rows | True links: {len(true_pairs)}")
    print()

    results = []
    for fn, label in [(baseline_b0, "B0"), (baseline_b1, "B1"), (baseline_b2, "B2")]:
        print(f"Running {label} …")
        if label == "B0":
            r = fn(df_a, df_b, true_pairs)
        else:
            r = fn(df_a, df_b, true_pairs)
        results.append(r)
        print(
            f"  {r['baseline']:4s}  "
            f"P={r['precision']:.4f}  R={r['recall']:.4f}  F1={r['f1']:.4f}  "
            f"predicted={r['n_predicted']}  time={r['runtime_s']}s"
        )

    # Save CSV — union all keys so B0 (no threshold) and B1/B2 coexist cleanly
    all_keys: list[str] = []
    seen: set[str] = set()
    for r in results:
        for k in r.keys():
            if k not in seen:
                all_keys.append(k)
                seen.add(k)

    suffix = "_hard" if hard_mode else ""
    out_path = RESULTS_DIR / f"e00_baselines_{dataset.replace('-','_')}{suffix}.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore", restval="")
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to {out_path}")


def main():
    parser = argparse.ArgumentParser(prog="matchiq", description="MatchIQ CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    base_parser = sub.add_parser("baseline", help="Run baselines on a dataset")
    base_parser.add_argument("--dataset", required=True, help="Dataset name (e.g. febrl4, synthetic-india)")
    base_parser.add_argument("--hard-mode", action="store_true",
                             help="Drop phone/email fields (name+address only)")

    run_parser = sub.add_parser("run", help="Run the end-to-end matching pipeline")
    run_parser.add_argument("--dataset-a", required=True, help="Path to dataset A CSV")
    run_parser.add_argument("--dataset-b", required=True, help="Path to dataset B CSV")
    run_parser.add_argument("--mapping", required=True, help="Path to mapping JSON")
    run_parser.add_argument("--model", required=True, help="Path to trained model .pkl")
    run_parser.add_argument("--model-card", required=True, help="Path to model card JSON")
    run_parser.add_argument("--output", required=True, help="Path to output CSV")

    args = parser.parse_args()

    if args.command == "baseline":
        run_baseline(args.dataset, hard_mode=getattr(args, "hard_mode", False))
    elif args.command == "run":
        from matchiq.pipeline import run_pipeline
        import json
        with open(args.mapping, "r") as f:
            mapping = json.load(f)
        run_pipeline(
            df_a_path=args.dataset_a,
            df_b_path=args.dataset_b,
            mapping=mapping,
            model_path=args.model,
            model_card_path=args.model_card,
            output_path=args.output
        )

if __name__ == "__main__":
    main()
