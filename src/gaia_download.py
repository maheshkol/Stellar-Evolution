# src/gaia_download.py
"""
Download a Gaia sample (CSV) using astroquery.Gaia (ADQL / TAP).
Adjust ADQL (SELECT ...) to add/remove columns you need.
"""

from astroquery.gaia import Gaia
import pandas as pd
import os
from astropy.table import Table
from tqdm import tqdm

os.makedirs("data/raw", exist_ok=True)

def run_adql_and_save(adql, out_csv, row_limit=None):
    """
    Run ADQL job asynchronously (recommended for >2000 rows) and save CSV.
    If row_limit is set, the query is wrapped with a TOP clause for ADQL.
    """
    if row_limit:
        # Insert TOP <n> after SELECT
        adql = adql.replace("SELECT", f"SELECT TOP {row_limit}", 1)
    print("Launching ADQL job (async)...")
    job = Gaia.launch_job_async(adql)
    print("Job finished; fetching results...")
    table = job.get_results()
    # Convert to pandas.DataFrame then save
    df = table.to_pandas()
    df.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv} ({len(df)} rows)")
    return df

def download_gaia_sample(out_csv="data/raw/gaia_sample.csv", row_limit=20000):
    # Prefer astrophysical_parameters (has Teff, metallicity, etc.)
    adql_ap = """
    SELECT source_id, ra, dec, phot_g_mean_mag,
           teff_gspphot, a_gspphot, mh_gspphot, distance_gspphot
    FROM gaiadr3.astrophysical_parameters
    WHERE teff_gspphot IS NOT NULL
    """
    try:
        df = run_adql_and_save(adql_ap, out_csv, row_limit=row_limit)
        return df
    except Exception as e:
        print("astrophysical_parameters query failed:", e)
        print("Falling back to gaia_source table (basic columns)...")
        adql_basic = """
        SELECT source_id, ra, dec, phot_g_mean_mag, parallax, pmra, pmdec
        FROM gaiadr3.gaia_source
        WHERE phot_g_mean_mag IS NOT NULL
        """
        df = run_adql_and_save(adql_basic, out_csv, row_limit=row_limit)
        return df

if __name__ == "__main__":
    # small default sample — increase row_limit for bigger sets but be mindful of time/limits
    download_gaia_sample(row_limit=5000)

