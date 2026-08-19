"""
UrbanShield Machine Learning Model Trainer
Trains a Scikit-Learn RandomForestRegressor for SENSE-stage Flood Risk Estimation.
Trained on real historical Chennai urban flood observations (OpenCity / GCC / IMD).
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
ZONES_PATH = BASE_DIR / "data" / "zones.csv"


def load_real_chennai_dataset():
    """
    Loads real Chennai observational records derived from OpenCity, GCC, and IMD.
    Features: [rainfall_mm, inundation_depth_inches, rainfall_station_dist_km]
    Target: risk_score (empirical evidence flood risk score)
    """
    if not ZONES_PATH.exists():
        from layers.sense import SenseLayer
        sense = SenseLayer()
        sense.load_real_data_to_db()

    df = pd.read_csv(ZONES_PATH)
    
    # Calculate evidence risk score
    depth_factor = df["inundation_depth_inches"].apply(lambda d: min(1.0, max(0.0, float(d) / 24.0)))
    hazard_map = {"VERY_HIGH": 1.0, "HIGH": 0.75, "MODERATE": 0.50, "LOW": 0.25}
    hazard_factor = df["hazard_category"].apply(lambda h: hazard_map.get(str(h).upper(), 0.5))
    rf_factor = df["rainfall_mm"].apply(lambda r: min(1.0, max(0.0, float(r) / 60.0)))

    risk_scores = (0.45 * depth_factor + 0.35 * hazard_factor + 0.20 * rf_factor).clip(0.05, 0.98)

    # Multi-feature array
    rainfall = df["rainfall_mm"].values
    depth = df["inundation_depth_inches"].values
    dist = df["rainfall_station_dist_km"].values
    hazard_num = hazard_factor.values

    X = np.column_stack([rainfall, depth, dist, hazard_num])
    y = risk_scores.values
    return X, y


def train_and_save_model():
    print("=" * 60)
    print("  URBANSHIELD CHENNAI FLOOD RISK MODEL TRAINING")
    print("=" * 60)
    
    # 1. Load Real Chennai Dataset
    print("[1/4] Loading real Chennai flood observations...")
    X, y = load_real_chennai_dataset()
    
    # 2. Fit Random Forest Model
    print("[2/4] Fitting Scikit-Learn RandomForestRegressor (n_estimators=100)...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        min_samples_split=2,
        random_state=42,
        n_jobs=1
    )
    model.fit(X, y)
    
    # 3. Evaluate Performance
    print("[3/4] Evaluating model performance...")
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    print(f"      Fit R² Score        : {r2:.4f}")
    print(f"      Mean Absolute Error : {mae:.4f}")
    
    # 4. Save Model Artifact
    backend_dir = Path(__file__).resolve().parent
    model_dir = backend_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = model_dir / "flood_risk_rf.pkl"
    print(f"[4/4] Serializing trained model to {output_path} via joblib...")
    joblib.dump(model, output_path)
    
    print("=" * 60)
    print(f"  MODEL TRAINING COMPLETE! -> Saved to {output_path.name}")
    print("=" * 60)
    return r2, mae


if __name__ == "__main__":
    train_and_save_model()
