"""
UrbanShield Machine Learning Model Trainer
Trains a Scikit-Learn RandomForestRegressor for SENSE-stage Flood Risk Prediction.
Trained on a calibrated synthetic dataset whose parameter ranges are anchored to documented
Indian monsoon and urban flood statistics (see data/SOURCES.md).
Saves the trained model to models/flood_risk_rf.pkl using joblib.
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import joblib

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "data" / "indian_flood_dataset.csv"


def load_calibrated_dataset():
    """
    Loads the calibrated synthetic dataset anchored to documented Indian monsoon
    and flood statistics (IMD, CWC, MCGM, KSNDMC, OpenCity.in).
    Features: [rainfall_mm, drainage_capacity_pct, population, traffic_index]
    Target: flood_risk_score (continuous index from 0.05 to 0.98)
    """
    if not DATASET_PATH.exists():
        # Fallback to importing generator if CSV is missing
        from layers.predict import PredictLayer
        generator = PredictLayer()
        df = generator.generate_calibrated_flood_data(num_samples=1000, random_state=42)
        DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(DATASET_PATH, index=False)
    else:
        df = pd.read_csv(DATASET_PATH)

    rainfall = df["rainfall_mm"] if "rainfall_mm" in df.columns else df["rainfall"]
    drainage = df["drainage_capacity"] if "drainage_capacity" in df.columns else df["drainage_capacity_pct"]
    population = df["population_density"] if "population_density" in df.columns else df["population"]
    traffic = df["traffic_index"] if "traffic_index" in df.columns else df["traffic"]

    # Scale traffic index to 0.0 - 1.0 range if expressed in 0 - 100 percentage
    traffic_scaled = traffic.apply(lambda t: t / 100.0 if t > 1.0 else t)

    X = np.column_stack([rainfall.values, drainage.values, population.values, traffic_scaled.values])
    y = df["flood_risk_score"].values
    return X, y


def train_and_save_model():
    print("=" * 60)
    print("  URBANSHIELD RANDOM FOREST FLOOD RISK MODEL TRAINING")
    print("=" * 60)
    
    # 1. Load Calibrated Dataset
    print("[1/4] Loading calibrated synthetic Indian flood observations...")
    X, y = load_calibrated_dataset()
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )
    print(f"      Training set size: {len(X_train)} rows, Test set size: {len(X_test)} rows")
    
    # 2. Train Random Forest Model
    print("[2/4] Fitting Scikit-Learn RandomForestRegressor (n_estimators=100)...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # 3. Evaluate Performance
    print("[3/4] Evaluating model performance on holdout test split...")
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    print(f"      Validation R² Score : {r2:.4f} (Target > 0.90)")
    print(f"      Mean Absolute Error : {mae:.4f}")
    
    # 4. Save Model Artifact
    backend_dir = Path(__file__).resolve().parent
    model_dir = backend_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = model_dir / "flood_risk_rf.pkl"
    print(f"[4/4] Serializing trained model to {output_path} via joblib...")
    joblib.dump(model, output_path)
    
    print("=" * 60)
    print(f"  MODEL TRAINING COMPLETE! R²={r2:.4f} -> Saved to {output_path.name}")
    print("=" * 60)
    return r2, mae


if __name__ == "__main__":
    train_and_save_model()
