import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib, os

os.makedirs('models', exist_ok=True)

def train_rf(csv='data/processed/processed_stars.csv'):
    df = pd.read_csv(csv)
    df = df.dropna(subset=['mass_solar','teff','metallicity'])
    def label_for(m):
        if m < 8: return 'white_dwarf'
        if m < 20: return 'neutron_star'
        return 'black_hole'
    df['label'] = df['mass_solar'].apply(label_for)
    X = df[['mass_solar','teff','metallicity']]; y = df['label']
    X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X_train, y_train)
    acc = clf.score(X_test, y_test)
    joblib.dump(clf, 'models/rf_endpoint.joblib')
    print('RF accuracy:', acc)
    print('Feature importances:', dict(zip(X.columns, clf.feature_importances_)))
    return clf

if __name__ == '__main__':
    train_rf()
