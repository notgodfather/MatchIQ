import pandas as pd
import numpy as np

def profile_dataframe(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "rows": 0,
            "cols": len(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_pct": {col: 0.0 for col in df.columns},
            "samples": []
        }
        
    missing_pct = (df.isna().sum() / len(df) * 100).round(2).to_dict()
    dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
    
    # Get up to 5 sample rows, dropping NaNs to standard Python None for JSON serialization
    sample_df = df.head(5).replace({np.nan: None})
    samples = sample_df.to_dict(orient='records')
    
    return {
        "rows": len(df),
        "cols": len(df.columns),
        "dtypes": dtypes,
        "missing_pct": missing_pct,
        "samples": samples
    }
