"""
Synthetic Indian customer record generator (T2.2).

Produces:
  - A.csv  : "clean" dataset (light noise)
  - B.csv  : "dirty" dataset (heavier noise + missing fields)
  - truth.csv: ground-truth matching pairs

Config:
  n_entities    : number of base entities
  overlap_frac  : fraction of A entities that also appear in B
  noise_level   : float 0-1 controlling how many noise ops are applied to B
  hard_neg_frac : fraction of B size to add as hard negatives
  seed          : for full reproducibility

Hard negatives:
  - Same surname + same city → easily confused with matches
  - Family: share address/phone but different first names

Usage:
    from matchiq.synthetic.generator import GeneratorConfig, generate
    cfg = GeneratorConfig(n_entities=1000, seed=42)
    generate(cfg, out_dir=Path("data/synthetic/"))
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from faker import Faker

from matchiq.synthetic.noise import (
    random_string_typo, initials, name_order_swap, add_title,
    city_alias, phone_format, phone_typo, missing,
)

fake = Faker("en_IN")


def _make_uuid(rng: np.random.Generator) -> str:
    """Generate a deterministic UUID from the seeded rng."""
    ints = rng.integers(0, 256, size=16, dtype=np.uint8)
    # Set version 4 and variant bits
    ints[6] = (ints[6] & 0x0F) | 0x40
    ints[8] = (ints[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(ints)))

# Canonical Indian cities for the generator
_CITIES = [
    "Bengaluru", "Mumbai", "Chennai", "Kolkata", "Delhi",
    "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "Kochi", "Gurugram", "Chandigarh", "Bhopal", "Nagpur",
]

_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "rediffmail.com", "ymail.com"]


@dataclass
class GeneratorConfig:
    n_entities:    int   = 2000
    overlap_frac:  float = 0.70   # 70% of A entities appear in B
    noise_level:   float = 0.30   # probability of applying each noise op to B
    hard_neg_frac: float = 0.10   # hard negatives as fraction of B size
    seed:          int   = 42


def _make_entity(rng: np.random.Generator) -> dict:
    """Generate one clean base entity."""
    first = fake.first_name()
    last  = fake.last_name()
    city  = _CITIES[rng.integers(0, len(_CITIES))]
    pin   = str(rng.integers(100000, 999999))
    phone_digits = "".join([str(d) for d in rng.integers(6, 10, size=1)] +
                           [str(d) for d in rng.integers(0, 10, size=9)])
    phone = phone_digits[:10]

    local = (first[0] + last).lower().replace(" ", "")
    domain = _DOMAINS[rng.integers(0, len(_DOMAINS))]
    email  = f"{local}@{domain}"

    address = f"{rng.integers(1, 500)} {fake.street_name()}"

    return {
        "entity_id": _make_uuid(rng),
        "name":      f"{first} {last}",
        "phone":     phone,
        "email":     email,
        "address":   address,
        "city":      city,
        "postcode":  pin,
    }


def _apply_noise(entity: dict, rng: np.random.Generator, noise_level: float) -> dict:
    """
    Return a noisy copy of entity for Dataset B.
    Each field independently has noise_level chance of being perturbed.
    """
    noisy = entity.copy()

    # Name: pick one of several name-noise ops
    if rng.random() < noise_level:
        name_ops: list[Callable] = [
            random_string_typo,
            initials,
            name_order_swap,
            add_title,
        ]
        op = name_ops[rng.integers(0, len(name_ops))]
        noisy["name"] = op(noisy["name"], rng)

    # Phone: format change or digit typo
    if rng.random() < noise_level:
        phone_ops: list[Callable] = [phone_format, phone_typo]
        op = phone_ops[rng.integers(0, len(phone_ops))]
        noisy["phone"] = op(noisy["phone"], rng)

    # Email: small string typo or drop
    if rng.random() < noise_level:
        if rng.random() < 0.3:
            noisy["email"] = None   # missing email
        else:
            noisy["email"] = random_string_typo(noisy["email"], rng)

    # Address: string typo
    if rng.random() < noise_level:
        noisy["address"] = random_string_typo(noisy["address"], rng)

    # City: alias substitution
    if rng.random() < noise_level:
        noisy["city"] = city_alias(noisy["city"], rng)

    # Postcode: occasionally drop
    if rng.random() < noise_level * 0.5:
        noisy["postcode"] = None

    return noisy


def _make_hard_negatives(
    entities: list[dict],
    n: int,
    rng: np.random.Generator,
) -> list[dict]:
    """
    Build hard-negative records that look similar but are NOT matches:
    - Same surname + same city, but different first name
    - Share address/phone (family members) with a different name
    """
    hard_negs: list[dict] = []
    idxs = rng.choice(len(entities), size=min(n * 2, len(entities)), replace=False)

    for idx in idxs[:n]:
        base = entities[idx]
        # Different first name, same surname, same city
        neg = base.copy()
        neg["entity_id"] = "HN_" + _make_uuid(rng)  # mark so we exclude from truth
        neg["name"] = fake.first_name() + " " + base["name"].split()[-1]
        # Occasionally share phone (family)
        if rng.random() < 0.3:
            pass  # keep phone — looks like family sharing a number
        else:
            # Fresh phone
            phone_digits = "".join([str(d) for d in rng.integers(6, 10, size=1)] +
                                   [str(d) for d in rng.integers(0, 10, size=9)])
            neg["phone"] = phone_digits[:10]
        neg["email"] = None
        hard_negs.append(neg)

    return hard_negs


def generate(cfg: GeneratorConfig, out_dir: Path) -> dict:
    """
    Generate A.csv, B.csv, truth.csv in out_dir.

    Returns a summary dict:
        {n_A, n_B, n_true_links, n_hard_negatives, seed}
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(cfg.seed)
    Faker.seed(cfg.seed)

    # 1. Generate base entities
    entities = [_make_entity(rng) for _ in range(cfg.n_entities)]

    # 2. Dataset A — light noise (noise_level / 3)
    a_noise = cfg.noise_level / 3.0
    df_a_records = []
    for i, e in enumerate(entities):
        rec = _apply_noise(e, rng, a_noise)
        rec["rec_id"] = f"a-{i}"
        df_a_records.append(rec)

    # 3. Dataset B — overlapping subset gets heavier noise + non-overlap gets fresh entities
    n_overlap = int(cfg.n_entities * cfg.overlap_frac)
    overlap_idxs = set(rng.choice(cfg.n_entities, size=n_overlap, replace=False).tolist())

    true_links: list[tuple[str, str]] = []
    df_b_records = []
    b_idx = 0

    for i, e in enumerate(entities):
        if i in overlap_idxs:
            rec = _apply_noise(e, rng, cfg.noise_level)
            rec["rec_id"] = f"b-{b_idx}"
            df_b_records.append(rec)
            true_links.append((f"a-{i}", f"b-{b_idx}"))
            b_idx += 1

    # Non-overlapping B records (fresh entities, noise applied)
    n_non_overlap = cfg.n_entities - n_overlap
    for j in range(n_non_overlap):
        fresh = _make_entity(rng)
        rec = _apply_noise(fresh, rng, cfg.noise_level)
        rec["rec_id"] = f"b-{b_idx}"
        df_b_records.append(rec)
        b_idx += 1

    # 4. Hard negatives appended to B (not in truth)
    n_hard = int(len(df_b_records) * cfg.hard_neg_frac)
    hard_negs = _make_hard_negatives(entities, n_hard, rng)
    for hn in hard_negs:
        hn["rec_id"] = f"b-{b_idx}"
        df_b_records.append(hn)
        b_idx += 1

    # 5. Build DataFrames
    cols = ["rec_id", "entity_id", "name", "phone", "email", "address", "city", "postcode"]
    df_a = pd.DataFrame(df_a_records)[cols].set_index("rec_id")
    df_b = pd.DataFrame(df_b_records)[cols].set_index("rec_id")

    truth = pd.DataFrame(true_links, columns=["id_A", "id_B"])

    # 6. Save
    df_a.to_csv(out_dir / "A.csv")
    df_b.to_csv(out_dir / "B.csv")
    truth.to_csv(out_dir / "truth.csv", index=False)

    return {
        "n_A":             len(df_a),
        "n_B":             len(df_b),
        "n_true_links":    len(truth),
        "n_hard_negatives": n_hard,
        "seed":            cfg.seed,
        "noise_level":     cfg.noise_level,
        "overlap_frac":    cfg.overlap_frac,
    }
