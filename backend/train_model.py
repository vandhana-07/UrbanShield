"""
UrbanShield Machine Learning Model Trainer
Trains a Scikit-Learn RandomForestRegressor for SENSE-stage Flood Risk Prediction.
Saves the trained model to models/flood_risk_rf.pkl using joblib.
"""

import os
from pathlib import Path
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import joblib

def generate_synthetic_dataset(n_samples=600, random_state=42):
    """
    Generates a realistic synthetic meteorological and hydrological dataset.
    Features: [rainfall_mm, drainage_capacity_pct, population, traffic_index]
    Target: flood_risk_score (0.0 to 1.0) with physical non-linear interactions.
    """
    np.random.seed(random_state)
    
    # Feature distributions
    rainfall_mm = np.random.uniform(0.0, 150.0, size=n_samples)
    drainage_capacity_pct = np.random.uniform(10.0, 100.0, size=n_samples)
    population = np.random.uniform(5000.0, 300000.0, size=n_samples)
    traffic_index = np.random.uniform(0.0, 1.0, size=n_samples)
    
    # Non-linear physical interactions
    rainfall_factor = (rainfall_mm / 120.0) ** 1.15
    drainage_deficit = ((100.0 - drainage_capacity_pct) / 100.0) ** 1.10
    storm_surge_interaction = rainfall_factor * drainage_deficit * 0.25
    population_exposure = (population / 200000.0) ** 0.85 * 0.15
    traffic_factor = traffic_index * 0.10
    
    # Gaussian noise modeling sensor variance
    noise = np.random.normal(0.0, 0.025, size=n_samples)
    
    raw_target = (
        (rainfall_factor * 0.38) +
        (drainage_deficit * 0.25) +
        storm_surge_interaction +
        population_exposure +
        traffic_factor +
        noise
    )
    
    # Clamp target to realistic bounds [0.05, 0.98]
    flood_risk_score = np.clip(raw_target, 0.05, 0.98)
    
    X = np.column_stack([rainfall_mm, drainage_capacity_pct, population, traffic_index])
    y = flood_risk_score
    return X, y


def train_and_save_model():
    print("=" * 60)
    print("  URBANSHIELD RANDOM FOREST FLOOD RISK MODEL TRAINING")
    print("=" * 60)
    
    # 1. Generate Dataset
    print("[1/4] Generating 600 synthetic training observations...")
    X, y = generate_synthetic_dataset(n_samples=600, random_state=42)
    
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
    
    print(f"      Validation R² Score : {r2:.4f} (Target > 0.95)")
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
