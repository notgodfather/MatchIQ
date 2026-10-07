import os
from pathlib import Path
import recordlinkage
from recordlinkage.datasets import load_febrl4

# Always resolve relative to the project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def main():
    data_dir = PROJECT_ROOT / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("Downloading Febrl4 dataset...")
    dfA, dfB, true_links = load_febrl4(return_links=True)
    
    dfA_path = data_dir / "febrl4_A.csv"
    dfB_path = data_dir / "febrl4_B.csv"
    links_path = data_dir / "febrl4_true_links.csv"
    
    if not dfA_path.exists():
        dfA.to_csv(dfA_path)
        print(f"Saved {dfA_path}")
    else:
        print(f"Cached {dfA_path} already exists")

    if not dfB_path.exists():
        dfB.to_csv(dfB_path)
        print(f"Saved {dfB_path}")
    else:
        print(f"Cached {dfB_path} already exists")

    if not links_path.exists():
        links_df = true_links.to_frame(index=False)
        links_df.columns = ["id_A", "id_B"]
        links_df.to_csv(links_path, index=False)
        print(f"Saved {links_path}")
    else:
        print(f"Cached {links_path} already exists")
        
    print(f"Dataset A: {len(dfA)} rows")
    print(f"Dataset B: {len(dfB)} rows")
    print(f"True links: {len(true_links)}")

if __name__ == "__main__":
    main()

