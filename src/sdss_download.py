# src/sdss_download.py
"""
Download SDSS spectroscopic stellar entries using astroquery.sdss.
This fetches a sample with ra, dec, class/subclass, plate/mjd/fiber (for spectra access).
"""

from astroquery.sdss import SDSS
from astropy.table import Table
import pandas as pd
import os

os.makedirs("data/raw", exist_ok=True)

def download_sdss_stars(out_csv="data/raw/sdss_stars.csv", topn=5000):
    # Simple SQL: use specObj (specObjAll) to get spectroscopic classifications.
    # 'class' typically stores 'STAR', 'GALAXY', 'QSO' etc. 'subclass' stores spectral subtype.
    sql = f"""
    SELECT TOP {topn}
      s.ra, s.dec, s.class, s.subclass, s.z, s.plate, s.mjd, s.fiberID
    FROM SpecObj AS s
    WHERE s.class = 'STAR'
    """
    print("Querying SDSS SkyServer...")
    try:
        table = SDSS.query_sql(sql)
    except Exception as e:
        print("SDSS query failed:", e)
        return None
    if table is None:
        print("No results returned.")
        return None
    df = table.to_pandas()
    df.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv} ({len(df)} rows)")
    return df

if __name__ == "__main__":
    download_sdss_stars(topn=3000)

