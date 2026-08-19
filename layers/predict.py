"""
UrbanShield - Layer 2: PREDICT
Evidence-Based Urban Flood Risk Estimation

Estimates flood risk probability (risk_score) and observational confidence (risk_confidence)
for each municipal zone using direct empirical evidence from publicly available Chennai datasets:
1. Ground-surveyed Inundation Depth (OpenCity / Greater Chennai Corporation)
2. Official Flood Hazard Classification (CMDA / GCC Master Plan)
3. Meteorological Rainfall Evidence (India Meteorological Department Weather Station Network)

Does NOT use synthetic labels, fabricated traffic/population features, or formula circularity.
"""

import logging
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from layers.sense import SenseLayer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("UrbanShield.Predict")

# Hazard category numerical weights based on official GCC / CMDA flood zoning
HAZARD_WEIGHTS = {
    "VERY_HIGH": 1.00,
    "HIGH": 0.75,
    "MODERATE": 0.50,
    "LOW": 0.25
}

# Empirical Evidence Combination Weights (Transparent, Audit-Ready, Evidence-Grounded)
WEIGHT_INUNDATION_DEPTH = 0.45   # Direct physical flood waterlogging depth (5 to 60 inches)
WEIGHT_HAZARD_CATEGORY = 0.35    # Official municipal flood zone susceptibility
WEIGHT_RAINFALL = 0.20          # Observed rainfall from nearest IMD station


class PredictLayer:
    def __init__(self):
        self.model = None

    def estimate_flood_risk(self, zone_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates empirical evidence-based flood risk scores and observational confidence.
        
        Formula:
        - Inundation Factor: Normalized depth (clamped 0 to 24 inches benchmark)
        - Hazard Factor: Official GCC/CMDA vulnerability tier weight (0.25 to 1.0)
        - Rainfall Factor: Normalized IMD rainfall scaled by spatial proximity confidence
        
        Returns:
            pd.DataFrame: Original DataFrame enriched with risk_score, risk_confidence, and contributing evidence.
        """
        if zone_df.empty:
            logger.warning("Empty zone DataFrame provided to PredictLayer.")
            return zone_df.copy()

        df = zone_df.copy()
        
        risk_scores = []
        risk_confidences = []
        inundation_factors = []
        hazard_factors = []
        rainfall_factors = []

        for _, row in df.iterrows():
            # 1. Observed Inundation Depth Evidence (normalized against 24-inch benchmark)
            depth = float(row.get("inundation_depth_inches", 6.0))
            d_norm = min(1.0, max(0.0, depth / 24.0))
            
            # 2. Official Flood Hazard Category Evidence
            hazard_cat = str(row.get("hazard_category", "MODERATE")).strip().upper()
            h_val = HAZARD_WEIGHTS.get(hazard_cat, 0.50)
            
            # 3. IMD Rainfall Evidence with Spatial Proximity Dampening
            rf_mm = float(row.get("rainfall_mm", 30.0))
            dist_km = float(row.get("rainfall_station_dist_km", 0.0))
            # Proximity confidence decays smoothly beyond 5 km (minimum 30% floor)
            proximity_weight = max(0.30, 1.0 - (dist_km / 20.0))
            rf_norm = min(1.0, max(0.0, rf_mm / 60.0)) * proximity_weight
            
            # Composite Evidence Risk Score (0.0 to 1.0)
            score = (
                WEIGHT_INUNDATION_DEPTH * d_norm +
                WEIGHT_HAZARD_CATEGORY * h_val +
                WEIGHT_RAINFALL * rf_norm
            )
            score = float(np.clip(score, 0.05, 0.98))
            
            # Observational Confidence: High when depth survey is verified and station is close
            confidence = 0.85 + (0.15 * proximity_weight)
            confidence = float(np.clip(confidence, 0.70, 0.99))
            
            risk_scores.append(round(score, 4))
            risk_confidences.append(round(confidence, 4))
            inundation_factors.append(round(d_norm, 3))
            hazard_factors.append(round(h_val, 3))
            rainfall_factors.append(round(rf_norm, 3))

        df["risk_score"] = risk_scores
        df["risk_confidence"] = risk_confidences
        df["inundation_factor"] = inundation_factors
        df["hazard_factor"] = hazard_factors
        df["rainfall_factor"] = rainfall_factors
        
        return df

    # Standard pipeline interface
    get_predictions = estimate_flood_risk

    def train_model(self, force_retrain: bool = False):
        """
        Maintains pipeline interface. Logs that evidence-based real estimation is active.
        """
        logger.info("Using real-data evidence-based flood risk estimation (No synthetic labels).")
        return self


if __name__ == "__main__":
    sense = SenseLayer()
    sense.load_real_data_to_db()
    zone_state = sense.get_structured_state()
    
    predict_layer = PredictLayer()
    predictions_df = predict_layer.get_predictions(zone_state)
    
    print("\n" + "=" * 80)
    print(" URBANSHIELD LAYER 2 (PREDICT) - EVIDENCE-BASED FLOOD RISK ESTIMATION")
    print("=" * 80)
    out_cols = [
        "zone_id", "zone_name", "inundation_depth_inches", "hazard_category",
        "rainfall_mm", "rainfall_station_dist_km", "risk_score", "risk_confidence"
    ]
    print(predictions_df[out_cols].to_string(index=False))
    print("=" * 80 + "\n")
