"""
Calibration utilities for models.
"""
import numpy as np
from sklearn.calibration import calibration_curve

def compute_calibration_curve(y_true, y_prob, n_bins=10):
    """
    Computes calibration curve.
    Returns (prob_true, prob_pred).
    """
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")
    return prob_true, prob_pred

def select_thresholds(y_true, y_prob, target_precision_high=0.99, target_recall_low=0.99):
    """
    Selects two thresholds for a 3-way decision:
      - upper_thresh: confidence threshold for auto-accept (MATCH), optimizing for precision >= target_precision_high.
      - lower_thresh: confidence threshold below which it's auto-reject (NON-MATCH), optimizing for recall >= target_recall_low for the accepted+reviewed pool.
      - Between lower_thresh and upper_thresh is the REVIEW region.
    """
    thresholds = np.linspace(0.01, 0.99, 99)
    upper_thresh = 0.9
    lower_thresh = 0.1
    
    # Upper threshold: find lowest thresh that gives precision >= target_precision_high
    for t in sorted(thresholds):
        preds = (y_prob >= t).astype(int)
        tp = ((preds == 1) & (y_true == 1)).sum()
        fp = ((preds == 1) & (y_true == 0)).sum()
        if (tp + fp) == 0:
            continue
        prec = tp / (tp + fp)
        if prec >= target_precision_high:
            upper_thresh = t
            break
            
    # Lower threshold: find highest thresh that still catches almost all true matches
    # i.e., we don't want to throw away true matches into NON-MATCH.
    total_true = y_true.sum()
    for t in sorted(thresholds, reverse=True):
        preds = (y_prob >= t).astype(int)
        tp = ((preds == 1) & (y_true == 1)).sum()
        rec = tp / total_true if total_true > 0 else 0
        if rec >= target_recall_low:
            lower_thresh = t
            break
            
    # Ensure lower <= upper
    lower_thresh = min(lower_thresh, upper_thresh)
    
    return float(lower_thresh), float(upper_thresh)
