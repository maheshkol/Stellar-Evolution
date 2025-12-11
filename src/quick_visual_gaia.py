# src/quick_visual_gaia.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

os.makedirs('visualizations', exist_ok=True)

# Load processed Gaia data
df = pd.read_csv('data/processed/gaia_processed.csv')

# Ensure required columns exist
required = ['mass_est', 'teff', 'star_class']
for col in required:
    if col not in df.columns:
        raise ValueError(f"Required column '{col}' missing from gaia_processed.csv")

# Remove missing rows
df = df.dropna(subset=required)

# ---- Visualization 1: Mass vs Teff ----
plt.figure(figsize=(10,6))
sns.scatterplot(
    data=df,
    x='mass_est',
    y='teff',
    hue='star_class',
    alpha=0.7,
    palette='viridis'
)

plt.xscale('log')
plt.yscale('log')

plt.xlabel('Estimated Mass (solar masses)')
plt.ylabel('Effective Temperature (K)')
plt.title('Mass vs Temperature (Gaia Processed Data)')
plt.gca().invert_yaxis()  # optional for HR-diagram style orientation
plt.tight_layout()

output1 = 'visualizations/mass_vs_teff.png'
plt.savefig(output1)
print(f"Saved {output1}")

# ---- Visualization 2: HR Diagram style (Teff vs abs_mag_g) ----
if 'abs_mag_g' in df.columns:
    plt.figure(figsize=(10,6))

    sns.scatterplot(
        data=df,
        x='teff',
        y='abs_mag_g',
        hue='star_class',
        alpha=0.6,
        palette='Spectral'
    )

    plt.xscale('log')
    plt.gca().invert_xaxis()  # HR diagram convention: hot stars on the left
    plt.gca().invert_yaxis()  # brighter at the top

    plt.xlabel('Effective Temperature (K)')
    plt.ylabel('Absolute G Magnitude')
    plt.title('H–R Diagram (Gaia Processed Data)')
    plt.tight_layout()

    output2 = 'visualizations/hr_diagram.png'
    plt.savefig(output2)
    print(f"Saved {output2}")
else:
    print("abs_mag_g not available — skipping HR diagram.")

