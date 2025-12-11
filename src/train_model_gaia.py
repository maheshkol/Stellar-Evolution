#src/train_model_gaia.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import tensorflow as tf
import joblib
import os

os.makedirs('models', exist_ok=True)

CSV_PATH = 'data/processed/gaia_processed.csv'

def choose_feature_columns(df):
    # Prioritized list of useful features — use those that exist in the processed CSV
    candidates = ['mass_est', 'teff', 'abs_mag_g', 'mh_gspphot', 'metallicity']
    features = [c for c in candidates if c in df.columns]
    if len(features) < 2:
        # fallback: try 'log_mass', 'log_teff' if present
        fallback = [c for c in ['log_mass','log_teff'] if c in df.columns]
        features += fallback
    return features

def label_for_mass(m):
    """Map estimated mass to endpoint label."""
    if m < 8:
        return 'white_dwarf'
    if m < 20:
        return 'neutron_star'
    return 'black_hole'

def prepare_data(csv=CSV_PATH):
    print("Loading processed Gaia CSV:", csv)
    df = pd.read_csv(csv)
    print("Initial shape:", df.shape)

    if 'mass_est' not in df.columns:
        raise ValueError("Input CSV must contain 'mass_est' column (estimated mass).")

    # make label column from mass_est
    df['label'] = df['mass_est'].apply(label_for_mass)

    # choose features automatically (use only numeric features)
    feature_cols = choose_feature_columns(df)
    if not feature_cols:
        raise ValueError("No suitable feature columns found in CSV. Expected one of mass_est, teff, abs_mag_g, mh_gspphot, metallicity, log_mass, log_teff.")

    print("Using feature columns:", feature_cols)

    # Keep only rows with non-null features and label
    needed = feature_cols + ['label']
    df_clean = df.dropna(subset=feature_cols + ['label']).copy()
    print("After dropping rows with missing features:", df_clean.shape)

    # Convert features to numeric, fill NaN with column median
    X = df_clean[feature_cols].apply(pd.to_numeric, errors='coerce')
    for col in feature_cols:
        if X[col].isna().any():
            med = X[col].median()
            X[col].fillna(med, inplace=True)

    # labels -> integers
    le = LabelEncoder()
    y = le.fit_transform(df_clean['label'])
    joblib.dump(le, 'models/label_encoder.joblib')
    print("Saved label encoder -> models/label_encoder.joblib")
    
    # scale features
    scaler = StandardScaler().fit(X.values)
    joblib.dump(scaler, 'models/scaler.joblib')
    print("Saved scaler -> models/scaler.joblib")
    Xs = scaler.transform(X.values)

    print("Feature matrix shape:", Xs.shape, "Labels shape:", y.shape)
    # class distribution
    unique, counts = np.unique(y, return_counts=True)
    dist = dict(zip(le.inverse_transform(unique), counts))
    print("Label distribution:", dist)

    return Xs, y, len(le.classes_), feature_cols

def build_model(input_dim, n_classes):
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(input_dim,)),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(n_classes, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model

def train(epochs=10, batch_size=32):
    X, y, n_classes, feature_cols = prepare_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = build_model(X_train.shape[1], n_classes)
    print("Training model with input dim =", X_train.shape[1], "classes =", n_classes)
    history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=epochs, batch_size=batch_size)
    # save model
    model.save('models/endpoint_predictor.keras')
    print("Saved model -> models/endpoint_predictor.keras")
    return model, history

if __name__ == '__main__':
    # small default for quick runs — raise epochs for serious training
    train(epochs=10)

