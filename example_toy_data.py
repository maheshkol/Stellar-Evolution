import numpy as np, pandas as pd, os
os.makedirs('data/raw', exist_ok=True)

np.random.seed(42)
n = 500
df = pd.DataFrame({
    'source_id': np.arange(n),
    'mass_solar': np.random.uniform(0.1, 80.0, n),
    'teff': np.random.uniform(2500, 50000, n),
    'metallicity': np.random.uniform(-2.5, 0.5, n),
})
df.to_csv('data/raw/toy_gaia.csv', index=False)
print('Wrote data/raw/toy_gaia.csv')
