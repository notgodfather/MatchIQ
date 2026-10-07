"""
Tests for T2.2: synthetic data generator.
"""
import pandas as pd
import pytest
from pathlib import Path
from matchiq.synthetic.generator import GeneratorConfig, generate


def test_generate_creates_files(tmp_path):
    cfg = GeneratorConfig(n_entities=100, seed=42)
    summary = generate(cfg, out_dir=tmp_path)

    assert (tmp_path / "A.csv").exists()
    assert (tmp_path / "B.csv").exists()
    assert (tmp_path / "truth.csv").exists()


def test_generate_summary_keys(tmp_path):
    cfg = GeneratorConfig(n_entities=100, seed=42)
    summary = generate(cfg, out_dir=tmp_path)

    for key in ("n_A", "n_B", "n_true_links", "n_hard_negatives", "seed"):
        assert key in summary


def test_generate_truth_consistent(tmp_path):
    """Every pair in truth.csv must appear as a valid (id_A, id_B) combo."""
    cfg = GeneratorConfig(n_entities=200, seed=7)
    generate(cfg, out_dir=tmp_path)

    df_a = pd.read_csv(tmp_path / "A.csv")
    df_b = pd.read_csv(tmp_path / "B.csv")
    truth = pd.read_csv(tmp_path / "truth.csv")

    a_ids = set(df_a["rec_id"])
    b_ids = set(df_b["rec_id"])

    assert all(truth["id_A"].isin(a_ids)), "Some truth id_A not in A.csv"
    assert all(truth["id_B"].isin(b_ids)), "Some truth id_B not in B.csv"


def test_generate_deterministic(tmp_path):
    """Same seed → identical A.csv, B.csv, truth.csv."""
    cfg = GeneratorConfig(n_entities=50, seed=99)
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    generate(cfg, out_dir=out1)
    generate(cfg, out_dir=out2)

    for fname in ("A.csv", "B.csv", "truth.csv"):
        df1 = pd.read_csv(out1 / fname)
        df2 = pd.read_csv(out2 / fname)
        pd.testing.assert_frame_equal(df1, df2)


def test_generate_overlap_fraction(tmp_path):
    cfg = GeneratorConfig(n_entities=200, overlap_frac=0.5, seed=1)
    summary = generate(cfg, out_dir=tmp_path)
    # True links should be ~50% of n_entities
    expected = int(200 * 0.5)
    assert abs(summary["n_true_links"] - expected) <= 2   # ±2 tolerance


def test_hard_negatives_not_in_truth(tmp_path):
    """Hard negatives have entity_id starting with 'HN_' and should NOT be in truth."""
    cfg = GeneratorConfig(n_entities=100, hard_neg_frac=0.1, seed=3)
    generate(cfg, out_dir=tmp_path)

    df_b = pd.read_csv(tmp_path / "B.csv")
    truth = pd.read_csv(tmp_path / "truth.csv")

    hn_b_ids = set(df_b[df_b["entity_id"].str.startswith("HN_")]["rec_id"])
    truth_b_ids = set(truth["id_B"])

    assert hn_b_ids.isdisjoint(truth_b_ids), "Hard negatives leaked into truth.csv"


def test_b_noisier_than_a(tmp_path):
    """B should have more missing fields than A on average."""
    cfg = GeneratorConfig(n_entities=500, noise_level=0.5, seed=42)
    generate(cfg, out_dir=tmp_path)

    df_a = pd.read_csv(tmp_path / "A.csv")
    df_b = pd.read_csv(tmp_path / "B.csv")

    fields = ["email", "postcode"]
    for f in fields:
        missing_a = df_a[f].isna().mean()
        missing_b = df_b[f].isna().mean()
        assert missing_b >= missing_a, f"Field '{f}' not noisier in B than A"
