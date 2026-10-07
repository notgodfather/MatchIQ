import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from pathlib import Path

RESULTS_DIR = Path("results")

def plot_ml_baselines():
    # Plot synthetic-india results
    csv_file = RESULTS_DIR / "e01_ml_baselines_synthetic_india.csv"
    if not csv_file.exists():
        print(f"Skipping baselines plot: {csv_file} not found.")
        return
        
    df = pd.read_csv(csv_file)
    
    # We want to plot precision, recall, and F1 for each model
    df_melted = df.melt(id_vars=["model"], value_vars=["precision", "recall", "f1"], 
                        var_name="Metric", value_name="Score")
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df_melted, x="model", y="Score", hue="Metric", palette="viridis")
    plt.title("Model Performance Comparison (Synthetic India)")
    plt.ylim(0, 1.1)
    plt.legend(loc='lower right')
    plt.tight_layout()
    
    out_path = RESULTS_DIR / "ml_baselines_f1.png"
    plt.savefig(out_path, dpi=300)
    print(f"Saved {out_path}")
    plt.close()

def plot_calibration():
    card_file = RESULTS_DIR / "model_card.json"
    if not card_file.exists():
        print(f"Skipping calibration plot: {card_file} not found.")
        return
        
    with open(card_file, "r") as f:
        data = json.load(f)
        
    calib = data.get("calibration_data", {})
    prob_true = calib.get("prob_true", [])
    prob_pred = calib.get("prob_pred", [])
    
    plt.figure(figsize=(8, 8))
    plt.plot(prob_pred, prob_true, marker='o', linewidth=2, label="LGBM")
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label="Perfectly Calibrated")
    plt.xlabel("Mean Predicted Probability")
    plt.ylabel("Fraction of True Matches")
    plt.title("Calibration Curve (Reliability Diagram)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    out_path = RESULTS_DIR / "calibration_curve.png"
    plt.savefig(out_path, dpi=300)
    print(f"Saved {out_path}")
    plt.close()

if __name__ == "__main__":
    # Set style
    try:
        sns.set_theme(style="whitegrid")
    except Exception:
        pass
        
    plot_ml_baselines()
    plot_calibration()
