import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
os.makedirs('visualizations', exist_ok=True)

df = pd.read_csv('data/processed/gaia_processed.csv')
plt.figure(figsize=(10,6))
sns.scatterplot(data=df, x='mass_solar', y='teff', hue='class_simple', alpha=0.7)
plt.xscale('log'); plt.yscale('log')
plt.xlabel('Mass (solar masses)'); plt.ylabel('Effective Temperature (K)')
plt.title('Mass vs Teff colored by simple class')
plt.tight_layout()
plt.savefig('visualizations/mass_teff.png')
print('Saved visualizations/mass_teff.png')
