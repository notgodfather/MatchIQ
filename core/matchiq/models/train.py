"""
Model training and wrapper functions.
"""
from __future__ import annotations

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from lightgbm import LGBMClassifier


def get_estimator(model_type: str = "lgbm", calibrate: bool = True, cv: int | str = "prefit"):
    """
    Returns an instantiated scikit-learn compatible estimator.
    
    Supported types: 'lr' (Logistic Regression), 'rf' (Random Forest), 'lgbm' (LightGBM).
    If calibrate is True, wraps the estimator in CalibratedClassifierCV.
    """
    if model_type == "lr":
        # Logistic Regression needs imputation for NaNs
        clf = Pipeline([
            ("imputer", SimpleImputer(strategy="constant", fill_value=0.0)),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))
        ])
    elif model_type == "rf":
        # Random Forest in scikit-learn also doesn't handle NaNs out of the box in older versions, 
        # but does in newer. We impute to be safe.
        clf = Pipeline([
            ("imputer", SimpleImputer(strategy="constant", fill_value=-1.0)),
            ("clf", RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=42, n_jobs=-1))
        ])
    elif model_type == "lgbm":
        # LightGBM handles NaNs natively
        clf = LGBMClassifier(n_estimators=100, class_weight="balanced", random_state=42, n_jobs=-1, verbose=-1)
    else:
        raise ValueError(f"Unknown model_type {model_type}")
        
    if calibrate:
        # We use isotonic calibration if cv is given as cross-validation splits, 
        # or platt scaling if it's 'prefit'. By default we use isotonic.
        method = "isotonic"
        return CalibratedClassifierCV(estimator=clf, method=method, cv=cv)
    return clf


def train_model(features_df: pd.DataFrame, model_type: str = "lgbm") -> any:
    """
    Trains a model on the provided features DataFrame (which must include 'label' column).
    Returns the trained scikit-learn compatible model.
    """
    if "label" not in features_df.columns:
        raise ValueError("features_df must contain a 'label' column.")
        
    X = features_df.drop(columns=["label"])
    y = features_df["label"]
    
    # We calibrate using CV so we don't need a separate calibration set for training.
    # It does cross-validation internally to calibrate.
    model = get_estimator(model_type=model_type, calibrate=True, cv=5)
    model.fit(X, y)
    
    return model
