# src/inspect_inputs.py
import pandas as pd
import os

def quick_head(path, n=5):
    if not os.path.exists(path):
        print(f"MISSING: {path}")
        return None
    df = pd.read_csv(path)
    print(f"\n{path} -> {len(df):,} rows")
    print("columns:", list(df.columns))
    print("first rows:")
    print(df.head(n))
    return df

if __name__ == "__main__":
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    gaia = quick_head("data/raw/gaia_sample.csv")
    sdss = quick_head("data/raw/sdss_stars.csv")
    # show summary stats if available
    for (name, df) in (("Gaia",gaia),("SDSS",sdss)):
        if df is None:
            continue
        for col in ["ra","dec"]:
            if col in df.columns:
                print(f"{name} {col} range: {df[col].min()} -> {df[col].max()}")
            else:
                print(f"{name} missing {col} column")

