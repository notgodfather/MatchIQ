import pytest
import pandas as pd
from matchiq.mapping import apply_mapping
from matchiq.evaluation import evaluate


# ──────────────────────── T1.4: Column Mapping ────────────────────────

def test_apply_mapping_single_column():
    df = pd.DataFrame({"customer_name": ["Mr. Rahul Kumar", "Priya Nair"], "city": ["Bangalore", "Pune"]})
    mapping = {
        "name": {"a": ["customer_name"]},
        "city": {"a": ["city"]},
    }
    result = apply_mapping(df, mapping, side="a")
    assert result["_norm_name"].tolist() == ["rahul kumar", "priya nair"]
    assert result["_norm_city"].tolist() == ["bengaluru", "pune"]


def test_apply_mapping_multi_column_concat():
    """Febrl-style: given_name + surname → name field."""
    df = pd.DataFrame({
        "given_name": ["Rahul", "Priya"],
        "surname":    ["Kumar", "Nair"],
    })
    mapping = {"name": {"a": ["given_name", "surname"]}}
    result = apply_mapping(df, mapping, side="a")
    assert result["_raw_name"].tolist() == ["Rahul Kumar", "Priya Nair"]
    assert result["_norm_name"].tolist() == ["rahul kumar", "priya nair"]


def test_apply_mapping_missing_column_produces_none():
    df = pd.DataFrame({"name": ["Rahul", pd.NA]})
    mapping = {"name": {"a": ["name"]}}
    result = apply_mapping(df, mapping, side="a")
    assert result["_norm_name"].iloc[0] == "rahul"
    assert pd.isna(result["_norm_name"].iloc[1])


def test_apply_mapping_side_not_in_mapping_skipped():
    df = pd.DataFrame({"name": ["Rahul"]})
    mapping = {"name": {"b": ["name"]}}   # side='a' not listed
    result = apply_mapping(df, mapping, side="a")
    assert "_norm_name" not in result.columns


def test_apply_mapping_phone_normalized():
    df = pd.DataFrame({"mobile": ["+91 98765 43210", "invalid"]})
    mapping = {"phone": {"a": ["mobile"]}}
    result = apply_mapping(df, mapping, side="a")
    assert result["_norm_phone"].iloc[0] == "9876543210"
    assert pd.isna(result["_norm_phone"].iloc[1])


# ──────────────────────── T1.5: Evaluation ────────────────────────

@pytest.mark.parametrize("predicted, true, expected", [
    # Perfect
    ({(1, 1), (2, 2)}, {(1, 1), (2, 2)}, {"tp": 2, "fp": 0, "fn": 0, "precision": 1.0, "recall": 1.0, "f1": 1.0}),
    # No predictions
    (set(), {(1, 1)},                    {"tp": 0, "fp": 0, "fn": 1, "precision": 0.0, "recall": 0.0, "f1": 0.0}),
    # All wrong
    ({(1, 2)}, {(1, 1)},                {"tp": 0, "fp": 1, "fn": 1, "precision": 0.0, "recall": 0.0, "f1": 0.0}),
    # Partial match
    ({(1, 1), (2, 2), (3, 4)}, {(1, 1), (2, 2), (3, 3)},
     {"tp": 2, "fp": 1, "fn": 1, "precision": round(2/3,4), "recall": round(2/3,4), "f1": round(2/3,4)}),
    # Empty both
    (set(), set(), {"tp": 0, "fp": 0, "fn": 0, "precision": 0.0, "recall": 0.0, "f1": 0.0}),
])
def test_evaluate(predicted, true, expected):
    result = evaluate(predicted, true)
    assert result == expected
