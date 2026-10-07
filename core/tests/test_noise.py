"""
Tests for T2.1: noise operators — deterministic and table-driven.
"""
import numpy as np
import pytest
from matchiq.synthetic.noise import (
    typo_insert, typo_delete, typo_swap, typo_substitute,
    initials, name_order_swap, add_title,
    city_alias, phone_format, phone_typo, missing,
    random_string_typo,
)

SEED = 42

def rng():
    return np.random.default_rng(SEED)


# ── Determinism: same seed → same output ─────────────────────────────────

@pytest.mark.parametrize("op", [
    typo_insert, typo_delete, typo_swap, typo_substitute,
    random_string_typo,
])
def test_deterministic_string_ops(op):
    r1, r2 = np.random.default_rng(SEED), np.random.default_rng(SEED)
    assert op("rahul kumar", r1) == op("rahul kumar", r2)


@pytest.mark.parametrize("op", [initials, name_order_swap, add_title])
def test_deterministic_name_ops(op):
    r1, r2 = np.random.default_rng(SEED), np.random.default_rng(SEED)
    assert op("Rahul Kumar", r1) == op("Rahul Kumar", r2)


# ── Structural correctness ────────────────────────────────────────────────

def test_typo_insert_length():
    s = "kumar"
    result = typo_insert(s, rng())
    assert len(result) == len(s) + 1

def test_typo_delete_length():
    s = "kumar"
    result = typo_delete(s, rng())
    assert len(result) == len(s) - 1

def test_typo_swap_length():
    s = "kumar"
    result = typo_swap(s, rng())
    assert len(result) == len(s)
    assert sorted(result) == sorted(s)   # same chars, different order

def test_typo_substitute_length():
    s = "kumar"
    result = typo_substitute(s, rng())
    assert len(result) == len(s)

def test_initials_format():
    result = initials("Rahul Kumar", rng())
    assert result == "R. Kumar"

def test_initials_single_token_unchanged():
    result = initials("Rahul", rng())
    assert result == "Rahul"

def test_name_order_swap():
    result = name_order_swap("Rahul Kumar", rng())
    assert result == "Kumar Rahul"

def test_name_order_swap_three_tokens():
    result = name_order_swap("Rahul Mohan Kumar", rng())
    assert result == "Kumar Rahul Mohan"

def test_add_title_prefix():
    result = add_title("Rahul Kumar", rng())
    assert result.endswith("Rahul Kumar")
    assert len(result) > len("Rahul Kumar")

def test_city_alias_bengaluru():
    # "bengaluru" maps to one of ["Bangalore", "Bglr", "BLR"]
    result = city_alias("bengaluru", rng())
    assert result in ["Bangalore", "Bglr", "BLR"]

def test_city_alias_unknown_unchanged():
    result = city_alias("Nagpur", rng())
    assert result == "Nagpur"

def test_phone_format_digits_preserved():
    phone = "9876543210"
    result = phone_format(phone, rng())
    digits = "".join(c for c in result if c.isdigit())
    # Either last 10 or last 11 (with leading 91) digits match
    assert phone in digits or digits.endswith(phone)

def test_phone_format_invalid_passthrough():
    bad = "12345"
    assert phone_format(bad, rng()) == bad

def test_phone_typo_length():
    phone = "9876543210"
    result = phone_typo(phone, rng())
    assert len(result) == 10

def test_phone_typo_one_digit_differs():
    """At most 1 digit should change."""
    phone = "9876543210"
    result = phone_typo(phone, rng())
    diffs = sum(a != b for a, b in zip(phone, result))
    assert diffs == 1

def test_missing_always_none():
    for s in ["hello", "", "9876543210", "rahul"]:
        assert missing(s, rng()) is None

# ── Edge cases ────────────────────────────────────────────────────────────

def test_typo_delete_single_char():
    assert typo_delete("a", rng()) == "a"   # can't delete from length-1

def test_typo_swap_single_char():
    assert typo_swap("a", rng()) == "a"     # nothing to swap

def test_typo_insert_empty():
    result = typo_insert("", rng())
    assert isinstance(result, str)
