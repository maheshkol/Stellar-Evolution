# src/sdss_download_region_small.py
from astroquery.sdss import SDSS
from astropy.coordinates import SkyCoord
import astropy.units as u
import pandas as pd, os

os.makedirs("data/raw", exist_ok=True)

# Center and radius (use arcminutes <= 3.0)
RA_CENTER = 180.0   # degrees
DEC_CENTER = 0.0    # degrees
R_ARCMIN = 2.5      # must be <= 3.0

coord = SkyCoord(RA_CENTER, DEC_CENTER, unit=(u.deg, u.deg), frame='icrs')
print(f"Querying SDSS around {coord.to_string('hmsdms')} radius={R_ARCMIN} arcmin")

try:
    # astroquery.sdss wants radius as an astropy Quantity
    table = SDSS.query_region(coord, radius=R_ARCMIN * u.arcmin, spectro=True)
except Exception as e:
    print("SDSS query_region failed:", e)
    table = None

if table is None:
    print("No SDSS results returned for region.")
else:
    df = table.to_pandas()
    out_csv = "data/raw/sdss_region_small.csv"
    df.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv} ({len(df)} rows). Columns: {list(df.columns)[:20]}")

