# src/advanced_visuals_gaia.py
"""
Advanced visualization suite for Gaia-processed data.

Creates:
 - visualizations/mass_vs_teff.png
 - visualizations/hr_diagram.png         (if abs_mag_g present)
 - visualizations/mass_hist.png
 - visualizations/teff_hist.png
 - visualizations/mass_teff_abs3d.png   (if abs_mag_g present)
 - visualizations/confusion_matrix.png  (if models exist)
 - visualizations/pairplot.png

Requires:
 - data/processed/gaia_processed.csv
 - optional: models/scaler.joblib, models/label_encoder.joblib, models/endpoint_predictor.keras
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# for 3D plot
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# for confusion matrix
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

import joblib

# tensorflow imports only if model exists
try:
    import tensorflow as tf
    TF_AVAILABLE = True
except Exception:
    TF_AVAILABLE = False

VIS_DIR = "visualizations"
os.makedirs(VIS_DIR, exist_ok=True)

CSV_PATH = "data/processed/gaia_processed.csv"
MODEL_PATH = "models/endpoint_predictor.keras"
SCALER_PATH = "models/scaler.joblib"
LE_PATH = "models/label_encoder.joblib"

# load data
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"Processed Gaia CSV not found: {CSV_PATH}")

df = pd.read_csv(CSV_PATH)
print("Loaded", CSV_PATH, "shape:", df.shape)

# Ensure minimal columns exist
if 'mass_est' not in df.columns or 'teff' not in df.columns:
    raise ValueError("Input CSV must contain at least 'mass_est' and 'teff' columns.")

# drop invalid values for plotting (but keep original df intact)
plot_df = df.dropna(subset=['mass_est','teff']).copy()

# Helper to save and close plots
def save_and_close(fig, path):
    fig.savefig(path, bbox_inches='tight', dpi=150)
    plt.close(fig)
    print("Saved", path)

# 1) Mass vs Teff scatter (log-log) colored by star_class (if exists)
fig = plt.figure(figsize=(10,6))
ax = fig.add_subplot(111)
hue_col = 'star_class' if 'star_class' in plot_df.columns else None
if hue_col:
    sns.scatterplot(data=plot_df, x='mass_est', y='teff', hue=hue_col, alpha=0.7, ax=ax, palette='viridis')
else:
    sns.scatterplot(data=plot_df, x='mass_est', y='teff', alpha=0.7, ax=ax)
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('Estimated Mass (M_sun)')
ax.set_ylabel('Effective Temperature (K)')
ax.set_title('Mass vs Teff')
# For HR-like appearance (optional) invert y-axis
ax.invert_yaxis()
out = os.path.join(VIS_DIR, 'mass_vs_teff.png')
save_and_close(fig, out)

# 2) HR Diagram (Teff vs abs_mag_g) if available
if 'abs_mag_g' in plot_df.columns and not plot_df['abs_mag_g'].isna().all():
    fig = plt.figure(figsize=(10,6))
    ax = fig.add_subplot(111)
    if hue_col:
        sns.scatterplot(data=plot_df, x='teff', y='abs_mag_g', hue=hue_col, alpha=0.6, ax=ax, palette='Spectral')
    else:
        sns.scatterplot(data=plot_df, x='teff', y='abs_mag_g', alpha=0.6, ax=ax)
    ax.set_xscale('log')
    ax.invert_xaxis()  # HR diagram: hot stars on left
    ax.invert_yaxis()  # brighter (smaller mag) at top
    ax.set_xlabel('Effective Temperature (K)')
    ax.set_ylabel('Absolute G Magnitude')
    ax.set_title('H-R Diagram (Teff vs Abs G)')
    out = os.path.join(VIS_DIR, 'hr_diagram.png')
    save_and_close(fig, out)
else:
    print("Skipping HR diagram — 'abs_mag_g' not present or all NaN in data.")

# 3) Mass distribution histogram
fig = plt.figure(figsize=(8,5))
ax = fig.add_subplot(111)
sns.histplot(plot_df['mass_est'], bins=50, kde=True, ax=ax)
ax.set_xscale('log')
ax.set_xlabel('Estimated Mass (M_sun)')
ax.set_title('Mass Distribution')
out = os.path.join(VIS_DIR, 'mass_hist.png')
save_and_close(fig, out)

# 4) Teff distribution histogram
fig = plt.figure(figsize=(8,5))
ax = fig.add_subplot(111)
sns.histplot(plot_df['teff'], bins=60, kde=True, ax=ax)
ax.set_xscale('log')
ax.set_xlabel('Effective Temperature (K)')
ax.set_title('Teff Distribution')
out = os.path.join(VIS_DIR, 'teff_hist.png')
save_and_close(fig, out)

# 5) 3D scatter: mass vs teff vs abs_mag_g (if abs_mag_g exists)
if 'abs_mag_g' in plot_df.columns and not plot_df['abs_mag_g'].isna().all():
    sample_df = plot_df.dropna(subset=['abs_mag_g','mass_est','teff']).copy()
    # sample if too many points
    if len(sample_df) > 5000:
        sample_df = sample_df.sample(5000, random_state=1)
    fig = plt.figure(figsize=(10,8))
    ax = fig.add_subplot(111, projection='3d')
    sc = ax.scatter(sample_df['mass_est'], sample_df['teff'], sample_df['abs_mag_g'],
                    c=sample_df['teff'], cmap='viridis', s=8, alpha=0.7)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Mass (M_sun)')
    ax.set_ylabel('Teff (K)')
    ax.set_zlabel('Abs G Mag')
    ax.set_title('3D: Mass vs Teff vs AbsMagG')
    fig.colorbar(sc, ax=ax, label='Teff (K)')
    out = os.path.join(VIS_DIR, 'mass_teff_abs3d.png')
    save_and_close(fig, out)
else:
    print("Skipping 3D scatter — 'abs_mag_g' not present or all NaN.")

# 6) Confusion matrix using trained model if available
if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH) and os.path.exists(LE_PATH) and TF_AVAILABLE:
    try:
        print("Loading model and scaler for predictions...")
        model = tf.keras.models.load_model(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        le = joblib.load(LE_PATH)
        # Prepare X for prediction using same features as used in training scaler
        # We will try to infer feature columns from scaler input size by using a heuristic:
        # If scaler contains a feature_names_in_ attribute (sklearn >=1.0), use it.
        feature_cols = None
        if hasattr(scaler, 'feature_names_in_'):
            feature_cols = list(scaler.feature_names_in_)
        else:
            # fallback: choose common features in order
            candidate_cols = ['mass_est','teff','abs_mag_g','mh_gspphot','metallicity','log_mass','log_teff']
            feature_cols = [c for c in candidate_cols if c in plot_df.columns]
            # limit to scaler.n_features_in_ if available
            if hasattr(scaler, 'n_features_in_'):
                feature_cols = feature_cols[:scaler.n_features_in_]

        if len(feature_cols) == 0:
            raise RuntimeError("Could not determine feature columns to use with scaler/model.")

        print("Using feature columns for prediction:", feature_cols)
        pred_df = plot_df.dropna(subset=feature_cols).copy()
        X = pred_df[feature_cols].apply(pd.to_numeric, errors='coerce').fillna(method='ffill').fillna(0).values
        Xs = scaler.transform(X)
        y_proba = model.predict(Xs, batch_size=256)
        y_pred = np.argmax(y_proba, axis=1)
        y_true = None
        if 'label' in pred_df.columns:
            # if label column exists, use it (string labels)
            y_true = pred_df['label'].values
            # transform to numeric
            try:
                y_true_num = le.transform(y_true)
            except Exception:
                # if label encoding fails, create fallback numeric mapping
                uniq = np.unique(y_true)
                mapping = {v:i for i,v in enumerate(uniq)}
                y_true_num = np.array([mapping[v] for v in y_true])
        else:
            print("No 'label' column present in processed CSV — confusion matrix will use model predictions only.")
            y_true_num = None

        # Plot confusion matrix if we have y_true
        if y_true is not None:
            cm = confusion_matrix(y_true_num, y_pred, labels=np.arange(len(le.classes_)))
            disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=le.inverse_transform(np.arange(len(le.classes_))))
            fig = plt.figure(figsize=(8,6))
            disp.plot(cmap='Blues', ax=fig.gca(), xticks_rotation='45')
            plt.title('Confusion Matrix (model predictions vs labels)')
            out = os.path.join(VIS_DIR, 'confusion_matrix.png')
            fig.savefig(out, bbox_inches='tight', dpi=150)
            plt.close(fig)
            print("Saved", out)
        else:
            print("Skipping confusion matrix — no true labels ('label' column) available in CSV.")

    except Exception as e:
        print("Error while computing confusion matrix:", e)
else:
    print("Skipping confusion matrix — model/scaler/label encoder not found or TF not available.")
    print(f"Expected: {MODEL_PATH}, {SCALER_PATH}, {LE_PATH}")

# 7) Pairplot of main numeric features (sampled if large)
# Select numeric columns of interest
candidate_cols = ['mass_est','teff','abs_mag_g','log_mass','log_teff','phot_g_mean_mag']
numeric_cols = [c for c in candidate_cols if c in plot_df.columns]

if len(numeric_cols) >= 2:
    # sample if too many rows
    pair_df = plot_df[numeric_cols].dropna().copy()
    if len(pair_df) > 2000:
        pair_df = pair_df.sample(2000, random_state=1)

    sns.set(style="ticks")
    pairplot = sns.pairplot(pair_df, diag_kind='kde', plot_kws={'s':10, 'alpha':0.6})
    out = os.path.join(VIS_DIR, 'pairplot.png')
    pairplot.savefig(out, dpi=150)
    plt.close('all')
    print("Saved", out)
else:
    print("Skipping pairplot — not enough numeric columns available.")

print("All visualizations complete.")

