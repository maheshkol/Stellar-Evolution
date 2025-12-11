# src/crossmatch_gaia_sdss.py
"""
Cross-match Gaia CSV and SDSS CSV by sky position (cone match) using astropy.
Produces a joined CSV with Gaia+SDSS columns for matched sources.
"""

import pandas as pd
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
import os

os.makedirs("data/processed", exist_ok=True)

def crossmatch(gaia_csv="data/raw/gaia_sample.csv", sdss_csv="data/raw/sdss_stars.csv",
               out_csv="data/processed/gaia_sdss_crossmatch.csv", radius_arcsec=1.0):
    gaia = pd.read_csv(gaia_csv)
    sdss = pd.read_csv(sdss_csv)

    # Require RA/DEC columns exist
    for df_name, df in (("Gaia", gaia), ("SDSS", sdss)):
        if not set(['ra','dec']).issubset(df.columns):
            raise ValueError(f"{df_name} table is missing ra/dec columns: found {list(df.columns)}")

    print("Building SkyCoord objects...")
    c_gaia = SkyCoord(ra=gaia['ra'].values*u.deg, dec=gaia['dec'].values*u.deg)
    c_sdss = SkyCoord(ra=sdss['ra'].values*u.deg, dec=sdss['dec'].values*u.deg)

    print("Performing cross-match (nearest neighbour)...")
    idx, sep2d, _ = c_gaia.match_to_catalog_sky(c_sdss)  # returns index in sdss for each gaia
    sep_arcsec = sep2d.arcsecond
    match_mask = sep_arcsec <= radius_arcsec

    matched_gaia = gaia[match_mask].reset_index(drop=True)
    matched_sdss = sdss.iloc[idx[match_mask]].reset_index(drop=True)
    # Combine (prefix columns to avoid collision)
    matched = pd.concat([matched_gaia.add_prefix('gaia_'), matched_sdss.add_prefix('sdss_')], axis=1)
    matched.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv} ({len(matched)} matches, within {radius_arcsec} arcsec)")
    return matched

if __name__ == "__main__":
    crossmatch()

