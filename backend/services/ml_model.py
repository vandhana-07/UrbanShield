"""
UrbanShield Machine Learning Inference Service
Provides real-time Random Forest predictions for SENSE-stage Flood Risk Prediction.
Includes automatic, graceful fallback to the mathematical formula if the model file is unavailable.
"""

import logging
from pathlib import Path
import joblib

logger = logging.getLogger("urbanshield.ml_model")

class FloodRiskMLService:
    def __init__(self):
        self.model = None
        self.is_loaded = False
        self.model_path = Path(__file__).resolve().parent.parent / "models" / "flood_risk_rf.pkl"
        self._load_model()

    def _load_model(self):
        """
        Loads the serialized Random Forest model from disk once at startup.
        """
        try:
            if self.model_path.exists():
                self.model = joblib.load(self.model_path)
                self.is_loaded = True
                logger.info("Successfully loaded Scikit-Learn Flood Risk Random Forest from %s", self.model_path)
            else:
                logger.warning("ML model file not found at %s. Will use formula fallback until trained.", self.model_path)
        except Exception as exc:
            logger.error("Failed to load ML model from %s: %s. Using formula fallback.", self.model_path, str(exc))
            self.model = None
            self.is_loaded = False

    def predict_flood_risk(self, zone_name, rainfall_mm, drainage_capacity_pct, population, traffic_index):
        """
        Computes flood risk score using the trained Scikit-Learn Random Forest model.
        Falls back to mathematical calculation if the ML model is not loaded.
        """
        rainfall_mm = float(rainfall_mm)
        drainage_capacity_pct = float(drainage_capacity_pct)
        population = float(population)
        traffic_index = float(traffic_index)

        # Factor calculations for explainable AI breakdown
        rainfall_factor = round(min(1.0, max(0.0, rainfall_mm / 120.0)), 2)
        drainage_deficit_factor = round(min(1.0, max(0.0, (100.0 - drainage_capacity_pct) / 100.0)), 2)
        population_factor = round(min(1.0, max(0.0, population / 200000.0)), 2)
        traffic_factor = round(min(1.0, max(0.0, traffic_index)), 2)

        contributing_factors = {
            "rainfall_factor": rainfall_factor,
            "drainage_deficit_factor": drainage_deficit_factor,
            "population_exposure_factor": population_factor,
            "traffic_factor": traffic_factor
        }

        # Try ML inference
        if self.is_loaded and self.model is not None:
            try:
                features = [[rainfall_mm, drainage_capacity_pct, population, traffic_index]]
                raw_pred = float(self.model.predict(features)[0])
                flood_risk_score = round(min(0.98, max(0.05, raw_pred)), 2)
                source = "ml_model"
            except Exception as exc:
                logger.warning("ML inference exception: %s. Falling back to formula.", str(exc))
                flood_risk_score = self._compute_formula_score(rainfall_factor, drainage_deficit_factor, population_factor, traffic_factor)
                source = "mock"
        else:
            flood_risk_score = self._compute_formula_score(rainfall_factor, drainage_deficit_factor, population_factor, traffic_factor)
            source = "mock"

        # Determine qualitative risk level
        if flood_risk_score >= 0.82:
            risk_level = "catastrophic"
        elif flood_risk_score >= 0.62:
            risk_level = "high"
        elif flood_risk_score >= 0.38:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "zone": zone_name,
            "flood_risk_score": flood_risk_score,
            "risk_level": risk_level,
            "contributing_factors": contributing_factors,
            "source": source
        }

    def _compute_formula_score(self, rf_factor, dd_factor, pop_factor, tr_factor):
        raw = (rf_factor * 0.45) + (dd_factor * 0.30) + (pop_factor * 0.15) + (tr_factor * 0.10)
        return round(min(0.98, max(0.05, raw)), 2)


# Global singleton instance
ml_service = FloodRiskMLService()
