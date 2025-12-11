# src/sdss_download_region.py
from astroquery.sdss import SDSS
from astropy.coordinates import SkyCoord
import astropy.units as u
import pandas as pd, os

os.makedirs("data/raw", exist_ok=True)

RA_CENTER = 180.0
DEC_CENTER = 0.0
R_DEG = 0.5

coord = SkyCoord(RA_CENTER, DEC_CENTER, unit=(u.deg, u.deg), frame='icrs')
print("Querying SDSS around", coord.to_string('hmsdms'), f"radius={R_DEG} deg")
# query_region returns an astropy Table
try:
    table = SDSS.query_region(coord, radius=R_DEG*u.deg, spectro=True)  # spectro=True to request spectra objects
except Exception as e:
    print("SDSS query_region failed:", e)
    table = None

if table is None:
    print("No SDSS results returned for region.")
else:
    df = table.to_pandas()
    out_csv = "data/raw/sdss_region.csv"
    df.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv} ({len(df)} rows). Columns: {list(df.columns)[:20]}")

