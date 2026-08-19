"""
UrbanShield - Layer 3: PRIORITIZE
Ranks urban zones using a transparent Multi-Criteria Decision Analysis (MCDA) formula
grounded in real observed flood evidence:
1. Evidence-based flood risk score (60%)
2. Observed inundation depth severity (25%)
3. Official municipal hazard tier weight (15%)
Adjusted by observational confidence.
"""

import logging
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from layers.sense import SenseLayer
from layers.predict import PredictLayer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("UrbanShield.Prioritize")

# Multi-Criteria Decision Analysis (MCDA) Weights
WEIGHT_RISK = 0.60              # Core hazard signal (evidence risk score)
WEIGHT_INUNDATION = 0.25        # Physical water depth severity
WEIGHT_HAZARD = 0.15            # Official municipal vulnerability designation

# Confidence Dampening Multiplier Constants
CONFIDENCE_BASE_FLOOR = 0.85    # Minimum multiplier for lower confidence
CONFIDENCE_SCALE_FACTOR = 0.15  # Scale factor for high observational confidence

# Tier Threshold Constants for Priority Categorization
TIER_CRITICAL_THRESHOLD = 0.65  # CRITICAL PRIORITY: Urgent emergency resource deployment
TIER_HIGH_THRESHOLD = 0.45      # HIGH PRIORITY: Heightened alert & crew pre-positioning
TIER_MODERATE_THRESHOLD = 0.30  # MODERATE PRIORITY: Standard inspection & monitoring
# Scores below 0.30 are categorized as LOW PRIORITY


class PrioritizeLayer:
    def __init__(self, weight_risk: float = WEIGHT_RISK,
                 weight_inundation: float = WEIGHT_INUNDATION,
                 weight_hazard: float = WEIGHT_HAZARD):
        self.weight_risk = weight_risk
        self.weight_inundation = weight_inundation
        self.weight_hazard = weight_hazard
        
        total_weight = self.weight_risk + self.weight_inundation + self.weight_hazard
        if not np.isclose(total_weight, 1.0):
            raise ValueError(f"MCDA weights must sum to 1.0, got {total_weight}")

    def _get_tier_label(self, score: float) -> str:
        """Determines the named priority tier label based on score thresholds."""
        if score >= TIER_CRITICAL_THRESHOLD:
            return "CRITICAL PRIORITY"
        elif score >= TIER_HIGH_THRESHOLD:
            return "HIGH PRIORITY"
        elif score >= TIER_MODERATE_THRESHOLD:
            return "MODERATE PRIORITY"
        else:
            return "LOW PRIORITY"

    def prioritize_zones(self, predictions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Ranks zones using deterministic Multi-Criteria Decision Analysis on real evidence.
        
        Args:
            predictions_df (pd.DataFrame): Output from PredictLayer.estimate_flood_risk()
            
        Returns:
            pd.DataFrame: DataFrame sorted by priority_score descending with priority_rank and priority_reason.
        """
        if predictions_df.empty:
            logger.warning("Empty predictions DataFrame provided to PrioritizeLayer.")
            return predictions_df.copy()

        required_cols = ["zone_id", "zone_name", "risk_score", "risk_confidence"]
        for col in required_cols:
            if col not in predictions_df.columns:
                raise ValueError(f"Missing required column in predictions DataFrame: {col}")

        df = predictions_df.copy()

        # Normalized physical inundation depth factor
        depth_series = df.get("inundation_depth_inches", pd.Series([6.0] * len(df)))
        norm_depth = depth_series.apply(lambda d: min(1.0, max(0.0, float(d) / 24.0)))

        # Hazard category factor
        hazard_map = {"VERY_HIGH": 1.0, "HIGH": 0.75, "MODERATE": 0.50, "LOW": 0.25}
        norm_hazard = df.get("hazard_category", pd.Series(["MODERATE"] * len(df))).apply(lambda h: hazard_map.get(str(h).upper(), 0.5))

        # Core Weighted Score (0.0 to 1.0)
        raw_priority = (
            self.weight_risk * df["risk_score"] +
            self.weight_inundation * norm_depth +
            self.weight_hazard * norm_hazard
        )

        # Bounded Confidence Multiplier (0.85 to 1.00)
        confidence_factor = CONFIDENCE_BASE_FLOOR + (CONFIDENCE_SCALE_FACTOR * df["risk_confidence"])
        
        # Final Priority Score
        priority_scores = raw_priority * confidence_factor
        df["priority_score"] = np.round(priority_scores, 4)

        # Sort descending by priority_score
        df = df.sort_values(by="priority_score", ascending=False).reset_index(drop=True)
        df["priority_rank"] = df.index + 1

        # Construct explainable priority_reason
        reasons = []
        for _, row in df.iterrows():
            tier = self._get_tier_label(row["priority_score"])
            depth_val = row.get("inundation_depth_inches", "N/A")
            hazard_val = row.get("hazard_category", "N/A")
            rf_val = row.get("rainfall_mm", "N/A")
            st_val = row.get("nearest_rainfall_station", "IMD")
            dist_val = row.get("rainfall_station_dist_km", 0.0)
            
            reason = (
                f"{tier} (Score: {row['priority_score']:.4f}) -> "
                f"Inundation: {depth_val}\" | Hazard: {hazard_val} | "
                f"Rain: {rf_val}mm ({st_val}, {dist_val}km) | "
                f"Conf: {row['risk_confidence'] * 100:.1f}%"
            )
            reasons.append(reason)

        df["priority_reason"] = reasons
        return df


if __name__ == "__main__":
    sense = SenseLayer()
    sense.load_real_data_to_db()
    zone_state = sense.get_structured_state()

    predict_layer = PredictLayer()
    predictions_df = predict_layer.get_predictions(zone_state)

    prioritize_layer = PrioritizeLayer()
    ranked_df = prioritize_layer.prioritize_zones(predictions_df)

    print("\n" + "=" * 90)
    print(" URBANSHIELD LAYER 3 (PRIORITIZE) - REAL CHENNAI ZONE EMERGENCY RANKINGS")
    print("=" * 90)
    output_cols = ["priority_rank", "zone_id", "zone_name", "risk_score", "risk_confidence", "priority_score", "priority_reason"]
    print(ranked_df[output_cols].to_string(index=False))
    print("=" * 90 + "\n")
