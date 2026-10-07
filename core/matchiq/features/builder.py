"""
Feature builder. Given candidate pairs and DataFrames A & B, computes features.
"""
from __future__ import annotations

import pandas as pd
import numpy as np

from matchiq.features.similarity import (
    exact_equal, jaro_winkler, norm_levenshtein, token_sort_ratio,
    token_set_ratio, token_jaccard, phonetic_equal, length_diff,
    initial_compatible, phone_edit_dist_le_1, phone_last_7_equal,
    email_local_jaro, email_domain_equal, house_number_equal,
    pincode_first_3_equal
)


def build_features(df_a: pd.DataFrame, df_b: pd.DataFrame, candidate_pairs: set[tuple[str, str]]) -> pd.DataFrame:
    """
    Compute features for candidate pairs. 
    df_a and df_b must have `_norm_<field>` columns for fields they map.
    Returns a DataFrame with MultiIndex (id_A, id_B) and one column per feature.
    """
    pairs_list = list(candidate_pairs)
    if not pairs_list:
        return pd.DataFrame()
        
    ids_a = [p[0] for p in pairs_list]
    ids_b = [p[1] for p in pairs_list]
    
    # We slice out the records in order
    a_records = df_a.loc[ids_a].reset_index(drop=True)
    b_records = df_b.loc[ids_b].reset_index(drop=True)
    
    feature_dict = {}
    
    # --- NAME ---
    if "_norm_name" in df_a.columns and "_norm_name" in df_b.columns:
        a_name = a_records["_norm_name"]
        b_name = b_records["_norm_name"]
        
        feature_dict["name_jaro"] = [jaro_winkler(a, b) for a, b in zip(a_name, b_name)]
        feature_dict["name_levenshtein"] = [norm_levenshtein(a, b) for a, b in zip(a_name, b_name)]
        feature_dict["name_token_sort"] = [token_sort_ratio(a, b) for a, b in zip(a_name, b_name)]
        feature_dict["name_token_set"] = [token_set_ratio(a, b) for a, b in zip(a_name, b_name)]
        feature_dict["name_token_jaccard"] = [token_jaccard(a, b) for a, b in zip(a_name, b_name)]
        feature_dict["name_exact"] = [exact_equal(a, b) for a, b in zip(a_name, b_name)]
        feature_dict["name_initial_comp"] = [initial_compatible(a, b) for a, b in zip(a_name, b_name)]
        feature_dict["name_phonetic"] = [phonetic_equal(a, b) for a, b in zip(a_name, b_name)]
        feature_dict["name_len_diff"] = [length_diff(a, b) for a, b in zip(a_name, b_name)]
        feature_dict["name_missing"] = [1 if pd.isna(a) or pd.isna(b) else 0 for a, b in zip(a_name, b_name)]
        
    # --- ADDRESS ---
    if "_norm_address" in df_a.columns and "_norm_address" in df_b.columns:
        a_addr = a_records["_norm_address"]
        b_addr = b_records["_norm_address"]
        
        feature_dict["address_token_set"] = [token_set_ratio(a, b) for a, b in zip(a_addr, b_addr)]
        feature_dict["address_token_jaccard"] = [token_jaccard(a, b) for a, b in zip(a_addr, b_addr)]
        feature_dict["address_house_num"] = [house_number_equal(a, b) for a, b in zip(a_addr, b_addr)]
        feature_dict["address_missing"] = [1 if pd.isna(a) or pd.isna(b) else 0 for a, b in zip(a_addr, b_addr)]
        
    # --- PHONE ---
    if "_norm_phone" in df_a.columns and "_norm_phone" in df_b.columns:
        a_phone = a_records["_norm_phone"]
        b_phone = b_records["_norm_phone"]
        
        feature_dict["phone_exact"] = [exact_equal(a, b) for a, b in zip(a_phone, b_phone)]
        feature_dict["phone_edit_dist_le_1"] = [phone_edit_dist_le_1(a, b) for a, b in zip(a_phone, b_phone)]
        feature_dict["phone_last_7"] = [phone_last_7_equal(a, b) for a, b in zip(a_phone, b_phone)]
        feature_dict["phone_missing"] = [1 if pd.isna(a) or pd.isna(b) else 0 for a, b in zip(a_phone, b_phone)]

    # --- EMAIL ---
    if "_norm_email" in df_a.columns and "_norm_email" in df_b.columns:
        a_email = a_records["_norm_email"]
        b_email = b_records["_norm_email"]
        
        feature_dict["email_exact"] = [exact_equal(a, b) for a, b in zip(a_email, b_email)]
        feature_dict["email_local_jaro"] = [email_local_jaro(a, b) for a, b in zip(a_email, b_email)]
        feature_dict["email_domain"] = [email_domain_equal(a, b) for a, b in zip(a_email, b_email)]
        feature_dict["email_missing"] = [1 if pd.isna(a) or pd.isna(b) else 0 for a, b in zip(a_email, b_email)]

    # --- CITY ---
    if "_norm_city" in df_a.columns and "_norm_city" in df_b.columns:
        a_city = a_records["_norm_city"]
        b_city = b_records["_norm_city"]
        
        feature_dict["city_exact"] = [exact_equal(a, b) for a, b in zip(a_city, b_city)]
        feature_dict["city_jaro"] = [jaro_winkler(a, b) for a, b in zip(a_city, b_city)]
        feature_dict["city_missing"] = [1 if pd.isna(a) or pd.isna(b) else 0 for a, b in zip(a_city, b_city)]

    # --- POSTCODE ---
    if "_norm_postcode" in df_a.columns and "_norm_postcode" in df_b.columns:
        a_post = a_records["_norm_postcode"]
        b_post = b_records["_norm_postcode"]
        
        feature_dict["postcode_exact"] = [exact_equal(a, b) for a, b in zip(a_post, b_post)]
        feature_dict["postcode_first_3"] = [pincode_first_3_equal(a, b) for a, b in zip(a_post, b_post)]
        feature_dict["postcode_missing"] = [1 if pd.isna(a) or pd.isna(b) else 0 for a, b in zip(a_post, b_post)]

    # Build DataFrame
    features_df = pd.DataFrame(feature_dict)
    
    # Set multi-index
    features_df.index = pd.MultiIndex.from_arrays([ids_a, ids_b], names=["id_A", "id_B"])
    
    return features_df
