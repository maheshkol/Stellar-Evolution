# src/gaia_download_region.py
from astroquery.gaia import Gaia
import pandas as pd, os
from astropy.table import Table

os.makedirs("data/raw", exist_ok=True)

# pick a known sky center where SDSS has coverage (example: RA=180.0, Dec=0.0)
RA_CENTER = 180.0
DEC_CENTER = 0.0
R_DEG = 0.5  # radius in degrees (0.5 deg = 30 arcmin)

adql = f"""
SELECT source_id, ra, dec, phot_g_mean_mag, parallax,
       teff_gspphot, mh_gspphot
FROM gaiadr3.gaia_source
WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS',{RA_CENTER},{DEC_CENTER},{R_DEG}))=1
"""

out_csv = "data/raw/gaia_region.csv"
print("Launching Gaia TAP query around RA,Dec:", RA_CENTER, DEC_CENTER)
job = Gaia.launch_job_async(adql)
table = job.get_results()
df = table.to_pandas()
df.to_csv(out_csv, index=False)
print(f"Wrote {out_csv} ({len(df)} rows)")

