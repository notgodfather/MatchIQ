import pytest
import pandas as pd
from matchiq.io.loader import load_csv, ValidationError
from matchiq.io.profiler import profile_dataframe

def test_load_csv_utf8(tmp_path):
    p = tmp_path / "test.csv"
    p.write_text("name,age\nRahul,30\nPriya,25", encoding='utf-8')
    df = load_csv(p)
    assert len(df) == 2
    assert list(df.columns) == ['name', 'age']

def test_load_csv_latin1(tmp_path):
    p = tmp_path / "test.csv"
    p.write_bytes(b"name,city\nJos\xe9,S\xe3o Paulo") # latin-1 encoded
    df = load_csv(p)
    assert len(df) == 1
    assert df.iloc[0]['name'] == 'José'

def test_load_csv_bad_header(tmp_path):
    p = tmp_path / "test.csv"
    p.write_text("name,,age\nRahul,X,30", encoding='utf-8')
    with pytest.raises(ValidationError, match="unnamed headers"):
        load_csv(p)
        
def test_load_csv_duplicate_header(tmp_path):
    p = tmp_path / "test.csv"
    p.write_text("name,name\nRahul,Rahul", encoding='utf-8')
    with pytest.raises(ValidationError, match="duplicate headers"):
        load_csv(p)

def test_load_csv_empty(tmp_path):
    p = tmp_path / "empty.csv"
    p.write_text("")
    with pytest.raises(ValidationError, match="empty"):
        load_csv(p)

def test_profile_dataframe():
    df = pd.DataFrame({
        'name': ['A', 'B', None],
        'age': [20, 25, 30]
    })
    
    profile = profile_dataframe(df)
    assert profile['rows'] == 3
    assert profile['cols'] == 2
    assert profile['missing_pct']['name'] == pytest.approx(33.33)
    assert profile['missing_pct']['age'] == 0.0
    assert len(profile['samples']) == 3
    assert profile['samples'][2]['name'] is None
