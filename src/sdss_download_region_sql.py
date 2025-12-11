# src/sdss_download_region_sql.py
from astroquery.sdss import SDSS
import pandas as pd, os
from astropy.coordinates import SkyCoord
import astropy.units as u

os.makedirs("data/raw", exist_ok=True)

# center (degrees) and radius (degrees); you can use large radii here
RA_CENTER = 180.0
DEC_CENTER = 0.0
R_DEG = 0.5   # 0.5 deg = 30 arcmin

TOPN = 50000  # maximum number of rows to request (SkyServer may still limit), reduce if needed

# Build SQL using SpecObj or PhotoObj depending on what you want (specObj for spectra)
sql = f"""
SELECT TOP {TOPN}
  s.ra, s.dec, s.class, s.subclass, s.z, s.plate, s.mjd, s.fiberID, s.u, s.g, s.r, s.i, s.z AS zmag
FROM SpecObj AS s
WHERE s.class = 'STAR'
  AND dbo.fGetNearestObjEq({RA_CENTER}, {DEC_CENTER}, 0).distanceArcmin IS NOT NULL
  AND dbo.fGetNearestObjEq({RA_CENTER}, {DEC_CENTER}, 0).distanceArcmin <= {R_DEG * 60.0}
"""
# Note: Above uses dbo.fGetNearestObjEq as a helper to filter objects by distance from center (returns nearest object and distance).
# Alternatively we can use the geometric CIRCLE function in the WHERE clause:
sql_alt = f"""
SELECT TOP {TOPN}
  s.ra, s.dec, s.class, s.subclass, s.z, s.plate, s.mjd, s.fiberID, s.u, s.g, s.r, s.i, s.z AS zmag
FROM SpecObj AS s
WHERE s.class = 'STAR'
  AND POINT(s.ra, s.dec) IS NOT NULL
  AND CIRCLE({RA_CENTER}, {DEC_CENTER}, {R_DEG}) CONTAINS POINT(s.ra, s.dec) = 1
"""

print("Using SQL region query (CIRCLE) with radius (deg) =", R_DEG)
try:
    # Use the alternate SQL which uses CIRCLE - more portable
    table = SDSS.query_sql(sql_alt)
except Exception as e:
    print("SDSS query_sql failed:", e)
    table = None

if table is None or len(table) == 0:
    print("No SDSS results returned via SQL.")
else:
    df = table.to_pandas()
    out_csv = "data/raw/sdss_region_sql.csv"
    df.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv} ({len(df)} rows). Columns: {list(df.columns)[:20]}")

