import pandas as pd
import numpy as np
import os

os.makedirs('data/processed', exist_ok=True)

def classify_simple(mass):
    if mass < 0.5: return 'low_mass'
    if mass < 1.5: return 'sun_like'
    if mass < 8: return 'intermediate'
    return 'high_mass'

def load_and_process(input_csv='data/raw/toy_gaia.csv'):
    df = pd.read_csv(input_csv)
    df = df.dropna(subset=['mass_solar','teff'])
    df['log_mass'] = np.log10(df['mass_solar'].clip(lower=1e-3))
    df['log_teff'] = np.log10(df['teff'].clip(lower=1))
    df['class_simple'] = df['mass_solar'].apply(classify_simple)
    def end_prob(m):
        if m < 8: return {'wd':0.99,'ns':0.01,'bh':0.0}
        if m < 20: return {'wd':0.02,'ns':0.7,'bh':0.28}
        return {'wd':0.0,'ns':0.1,'bh':0.9}
    probs = df['mass_solar'].apply(end_prob)
    df['p_wd'] = probs.apply(lambda d: d['wd'])
    df['p_ns'] = probs.apply(lambda d: d['ns'])
    df['p_bh'] = probs.apply(lambda d: d['bh'])
    df.to_csv('data/processed/processed_stars.csv', index=False)
    print('Wrote data/processed/processed_stars.csv')
    return df

if __name__ == '__main__':
    load_and_process()
