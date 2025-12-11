import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import tensorflow as tf
import joblib, os

os.makedirs('models', exist_ok=True)

def prepare_data(csv='data/processed/gaia_processed.csv'):
    df = pd.read_csv(csv)
    df = df.dropna(subset=['mass_solar','teff','metallicity'])
    def label_for(m):
        if m < 8: return 'white_dwarf'
        if m < 20: return 'neutron_star'
        return 'black_hole'
    df['label'] = df['mass_solar'].apply(label_for)
    X = df[['mass_solar','teff','metallicity']].values
    le = LabelEncoder(); y = le.fit_transform(df['label'])
    joblib.dump(le, 'models/label_encoder.joblib')
    scaler = StandardScaler().fit(X); joblib.dump(scaler, 'models/scaler.joblib')
    Xs = scaler.transform(X)
    return Xs, y

def train(epochs=10):
    X, y = prepare_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(X_train.shape[1],)),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(len(set(y)), activation='softmax')
    ])
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=epochs, batch_size=32)
    model.save('models/endpoint_predictor.keras')
    print('Saved model to models/endpoint_predictor.keras')

if __name__ == '__main__':
    train(epochs=5)
