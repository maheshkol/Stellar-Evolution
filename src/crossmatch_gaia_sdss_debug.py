# src/crossmatch_gaia_sdss_debug.py
"""
Robust cross-match Gaia <-> SDSS with diagnostics.

- Tries to auto-detect RA/DEC column names.
- Runs search_around_sky for radii 1", 2", 5", 10".
- Writes `data/processed/gaia_sdss_crossmatch.csv` for best radius (largest match count)
  and `data/processed/gaia_unmatched.csv` for Gaia rows without any SDSS match.
- Prints diagnostics to help you understand why matches may be zero.
"""

import pandas as pd
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
import os
from collections import defaultdict

os.makedirs("data/processed", exist_ok=True)

# common ra/dec column name variants to try
RA_CANDIDATES = ["ra", "RA", "RAJ2000", "ra_deg", "ra_deg"]
DEC_CANDIDATES = ["dec", "DEC", "DEJ2000", "dec_deg", "dec_deg"]

def find_ra_dec_cols(df):
    cols = set(df.columns)
    ra_col = next((c for c in RA_CANDIDATES if c in cols), None)
    dec_col = next((c for c in DEC_CANDIDATES if c in cols), None)
    return ra_col, dec_col

def load_table(path, which):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{which} file not found: {path}")
    df = pd.read_csv(path)
    print(f"\nLoaded {which}: {path} -> {len(df):,} rows")
    print("Columns:", list(df.columns)[:40])
    ra_col, dec_col = find_ra_dec_cols(df)
    if ra_col is None or dec_col is None:
        raise ValueError(f"Could not find RA/DEC columns in {which}. Tried {RA_CANDIDATES} & {DEC_CANDIDATES}.")
    print(f"Using RA/DEC columns for {which}: {ra_col}, {dec_col}")
    # check for non-finite values in RA/DEC
    mask_good = pd.to_numeric(df[ra_col], errors='coerce').notnull() & pd.to_numeric(df[dec_col], errors='coerce').notnull()
    bad_count = (~mask_good).sum()
    if bad_count > 0:
        print(f"  WARNING: {bad_count} rows in {which} have invalid RA/DEC and will be dropped.")
        df = df[mask_good].copy()
    # convert to float
    df[ra_col] = df[ra_col].astype(float)
    df[dec_col] = df[dec_col].astype(float)
    return df, ra_col, dec_col

def run_crossmatch(gaia_csv="data/raw/gaia_sample.csv", sdss_csv="data/raw/sdss_stars.csv",
                   out_csv="data/processed/gaia_sdss_crossmatch.csv", radius_list_arcsec=[1.0,2.0,5.0,10.0]):
    gaia, gra, gdec = load_table(gaia_csv, "Gaia")
    sdss, sra, sdec = load_table(sdss_csv, "SDSS")

    # quick sky coverage check
    print("\nGaia RA range: {:.4f} - {:.4f}, Dec range: {:.4f} - {:.4f}".format(
        gaia[gra].min(), gaia[gra].max(), gaia[gdec].min(), gaia[gdec].max()))
    print("SDSS RA range: {:.4f} - {:.4f}, Dec range: {:.4f} - {:.4f}".format(
        sdss[sra].min(), sdss[sra].max(), sdss[sdec].min(), sdss[sdec].max()))

    # Build SkyCoord objects
    c_gaia = SkyCoord(ra=gaia[gra].values * u.deg, dec=gaia[gdec].values * u.deg)
    c_sdss = SkyCoord(ra=sdss[sra].values * u.deg, dec=sdss[sdec].values * u.deg)

    best_matches = None
    best_radius = None
    best_count = 0
    result_details = {}

    # try multiple radii (arcsec)
    for r_arcsec in radius_list_arcsec:
        r = r_arcsec * u.arcsec
        print(f"\nSearching with radius = {r_arcsec:.1f} arcsec ...")
        # search_around_sky returns indices and separations for all pairs within radius
        idx_gaia, idx_sdss, sep2d, _ = c_gaia.search_around_sky(c_sdss, r)
        # Note: idx_gaia are indices into c_sdss? astropy's search_around_sky returns:
        #   idx1, idx2, sep2d, _ where idx1 are indices into first coord array passed,
        # but because we passed (c_sdss, c_gaia) the ordering matters. To avoid confusion, we can re-run with (c_gaia, c_sdss).
        # Let's do correct call:
        idx_gaia, idx_sdss, sep2d, _ = c_gaia.search_around_sky(c_sdss, r)

        # The documentation: search_around_sky(cat1, cat2, seplimit) returns idxcat1, idxcat2...
        # idx_gaia -> indices in c_gaia; idx_sdss -> indices in c_sdss
        match_count = len(idx_gaia)
        print(f"  raw pair matches found: {match_count:,}")

        # Build DataFrame of matches (we'll prefix columns)
        if match_count == 0:
            result_details[r_arcsec] = {'count': 0}
            continue

        df_matches = pd.DataFrame({
            'idx_gaia': idx_gaia,
            'idx_sdss': idx_sdss,
            'sep_arcsec': sep2d.arcsecond
        })
        # join Gaia and SDSS rows (allow many-to-many)
        df_matches = df_matches.merge(gaia.reset_index().rename(columns={'index':'idx_gaia'}), on='idx_gaia', how='left') \
                               .merge(sdss.reset_index().rename(columns={'index':'idx_sdss'}), on='idx_sdss', how='left', suffixes=('_gaia','_sdss'))
        # count unique Gaia matches
        unique_gaia = df_matches['idx_gaia'].nunique()
        unique_sdss = df_matches['idx_sdss'].nunique()
        print(f"  unique Gaia matched: {unique_gaia:,}, unique SDSS matched: {unique_sdss:,}")

        result_details[r_arcsec] = {
            'count_pairs': match_count,
            'unique_gaia': unique_gaia,
            'unique_sdss': unique_sdss,
            'matches_df': df_matches
        }

        # pick the radius with the largest number of unique Gaia matches
        if unique_gaia > best_count:
            best_count = unique_gaia
            best_matches = df_matches.copy()
            best_radius = r_arcsec

    if best_matches is None or best_count == 0:
        print("\nNo matches found for any radius tried. Summary:")
        for r, info in result_details.items():
            print(f" radius {r} arcsec -> {info.get('count_pairs',0)} pair matches, unique_gaia={info.get('unique_gaia',0)}")
        raise RuntimeError("No matches found between Gaia and SDSS. Check inputs, coordinate ranges and column names.")

    # Save best results (flatten columns: prefix original columns)
    print(f"\nBest radius chosen: {best_radius} arcsec with {best_count} unique Gaia matches (pairs: {len(best_matches):,})")

    # Select and rename columns to avoid duplicates
    # Prefix original gaia columns with 'gaia_' and SDSS columns with 'sdss_'
    gaia_cols = [c for c in gaia.columns]
    sdss_cols = [c for c in sdss.columns]
    # prepare prefixed dataframe (we already have both sets from merges; just rename explicitly)
    # We'll keep only one copy of idx and sep
    out_df = best_matches.copy()
    # rename GAIA columns (they have names without suffix)
    out_df = out_df.rename(columns={col: f"gaia_{col}" for col in gaia_cols})
    # rename SDSS columns (they may have suffix _sdss already)
    out_df = out_df.rename(columns={col: f"sdss_{col}" for col in sdss_cols})
    # Some columns now duplicate (because pandas merge added columns with suffixes). To be safe, select by prefix:
    out_df = out_df[[c for c in out_df.columns if c.startswith('gaia_') or c.startswith('sdss_') or c in ('sep_arcsec','idx_gaia','idx_sdss')]]

    out_df.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv} ({len(out_df):,} pair rows).")

    # also write unmatched Gaia rows (those idx in gaia not in matched idx_gaia)
    matched_gaia_idxs = set(out_df['idx_gaia'].unique())
    all_gaia_idxs = set(range(len(gaia)))
    unmatched_idxs = sorted(list(all_gaia_idxs - matched_gaia_idxs))
    gaia_unmatched = gaia.reset_index().loc[unmatched_idxs].drop(columns=['index'])
    gaia_unmatched.to_csv("data/processed/gaia_unmatched.csv", index=False)
    print(f"Wrote data/processed/gaia_unmatched.csv ({len(gaia_unmatched):,} rows)")

    return out_df

if __name__ == "__main__":
    try:
        df = run_crossmatch()
    except Exception as e:
        print("CROSSMATCH ERROR:", e)

