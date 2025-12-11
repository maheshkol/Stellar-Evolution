from astroquery.vizier import Vizier
import pandas as pd
import os

os.makedirs('data/raw', exist_ok=True)

def fetch_gaia_sample(limit=500):
    Vizier.ROW_LIMIT = limit
    catalog = "I/345/gaia2"
    v = Vizier(columns=['Source','RAJ2000','DEJ2000','TeffVal','Plx','phot_g_mean_mag'], catalog=catalog)
    try:
        result = v.query_constraints()
    except Exception as e:
        print("Query failed:", e)
        return
    if len(result) == 0:
        print("No results.")
        return
    tab = result[0].to_pandas()
    tab.rename(columns={'Source':'source_id','TeffVal':'teff'}, inplace=True)
    tab.to_csv('data/raw/gaia_sample.csv', index=False)
    print('Saved data/raw/gaia_sample.csv')

if __name__ == '__main__':
    fetch_gaia_sample(200)
