import pandas as pd
import csv
from pathlib import Path

class ValidationError(Exception):
    pass

def load_csv(filepath: Path | str) -> pd.DataFrame:
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    if filepath.stat().st_size == 0:
        raise ValidationError("File is empty.")
    
    # Try reading first few bytes for encoding detection
    encodings_to_try = ['utf-8', 'latin-1']
    content = None
    used_encoding = None
    
    for enc in encodings_to_try:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read(4096)
                used_encoding = enc
                break
        except UnicodeDecodeError:
            continue
            
    if content is None:
        raise ValidationError("Could not decode file with standard encodings (utf-8, latin-1).")
        
    if not content.strip():
        raise ValidationError("File contains only whitespace.")

    # Detect delimiter
    try:
        dialect = csv.Sniffer().sniff(content)
        delimiter = dialect.delimiter
    except csv.Error:
        # Fallback to comma if sniffing fails
        delimiter = ','

    # Check for duplicate headers
    try:
        first_line = content.splitlines()[0]
        parsed_headers = next(csv.reader([first_line], delimiter=delimiter))
        if len(parsed_headers) != len(set(parsed_headers)):
            raise ValidationError("File contains duplicate headers.")
    except StopIteration:
        pass
    except ValidationError:
        raise
        
    # Load with pandas
    try:
        df = pd.read_csv(filepath, sep=delimiter, encoding=used_encoding)
    except Exception as e:
        raise ValidationError(f"Failed to parse CSV: {e}")
        
    if df.empty and df.columns.empty:
        raise ValidationError("File contains no data and no headers.")
        
    # Check headers
    headers = list(df.columns)
    if any(pd.isna(c) or str(c).strip() == "" or "Unnamed:" in str(c) for c in headers):
        raise ValidationError("File contains empty or unnamed headers.")
        
    return df
