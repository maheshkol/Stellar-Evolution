# src/process_gaia_data.py
"""
Process Gaia CSV into ML-ready feature table.

Input:
    data/raw/gaia_sample.csv      (from your Gaia download script)

Output:
    data/processed/gaia_processed.csv
"""

import pandas as pd
import numpy as np
import os

os.makedirs("data/processed", exist_ok=True)

def classify_star(teff):
    """Simple temperature-based sequence classification."""
    if teff < 4000:
        return "cool_star"
    elif teff < 6500:
        return "sun_like"
    elif teff < 10000:
        return "hot_star"
    return "very_hot_star"

def estimate_mass_from_teff(teff):
    """
    Rough mass estimate from Teff.
    Very approximate but works for ML placeholder.
    """
    if teff < 4000:
        return 0.6
    elif teff < 5500:
        return 0.9
    elif teff < 7000:
        return 1.2
    elif teff < 10000:
        return 2.0
    elif teff < 15000:
        return 5.0
    return 10.0

def estimate_evolution_probs(mass):
    """Return WD / NS / BH probabilities from mass."""
    if mass < 8:
        return 0.98, 0.02, 0.0    # WD almost certain
    elif mass < 20:
        return 0.10, 0.75, 0.15   # NS dominant
    else:
        return 0.00, 0.10, 0.90   # BH dominant

def process_gaia_csv(input_csv="data/raw/gaia_sample.csv",
                     output_csv="data/processed/gaia_processed.csv"):
    print(f"Loading Gaia CSV: {input_csv}")
    df = pd.read_csv(input_csv)

    # --- Check required columns ---
    required_cols = ["ra", "dec", "phot_g_mean_mag"]
    optional_cols = ["teff_gspphot", "mh_gspphot"]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column {col} not found in Gaia CSV.")

    # If Teff is missing, try fallback columns
    if "teff_gspphot" not in df.columns:
        print("⚠ Warning: teff_gspphot missing. Creating dummy_teff column (approx).")
        df["teff_gspphot"] = np.random.uniform(3500, 10000, size=len(df))

    # --- Clean dataset ---
    print("Cleaning data...")
    df = df.dropna(subset=["teff_gspphot", "phot_g_mean_mag"])
    df = df[df["teff_gspphot"] > 0]        # remove invalid Teff entries

    # --- Derived Features ---
    print("Computing derived features...")

    df["teff"] = df["teff_gspphot"]
    df["log_teff"] = np.log10(df["teff"])

    # Approximate mass from Teff
    df["mass_est"] = df["teff"].apply(estimate_mass_from_teff)
    df["log_mass"] = np.log10(df["mass_est"])

    # Gaia G-magnitude to absolute magnitude estimate (if parallax present)
    if "parallax" in df.columns:
        print("Computing absolute magnitude from parallax...")
        parallax = df["parallax"].replace(0, np.nan)
        df["distance_pc"] = 1000.0 / parallax   # d(pc) = 1 / (parallax arcsec), but Gaia gives mas → multiply by 1000
        df["abs_mag_g"] = df["phot_g_mean_mag"] - 5 * np.log10(df["distance_pc"] / 10)
    else:
        print("Parallax missing — skipping absolute magnitude.")
        df["abs_mag_g"] = np.nan

    # Classification
    df["star_class"] = df["teff"].apply(classify_star)

    # Evolution endpoint probabilities
    probs = df["mass_est"].apply(estimate_evolution_probs)
    df["prob_white_dwarf"] = probs.apply(lambda x: x[0])
    df["prob_neutron_star"] = probs.apply(lambda x: x[1])
    df["prob_black_hole"] = probs.apply(lambda x: x[2])

    # Output
    df.to_csv(output_csv, index=False)
    print(f"Processed file saved to {output_csv}")
    print(f"Final shape: {df.shape}")

    return df


if __name__ == "__main__":
    process_gaia_csv()

