"""
UrbanShield - Layer 3: PRIORITIZE
Ranks urban zones using a transparent Multi-Criteria Decision Analysis (MCDA) formula
combining flood risk probability, population impact, critical infrastructure exposure,
and prediction confidence.
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
WEIGHT_RISK = 0.50             # Core hazard signal (flood probability)
WEIGHT_POPULATION = 0.30       # Human life safety (affected population count)
WEIGHT_INFRASTRUCTURE = 0.20   # Systemic asset exposure (hospitals, power, shelters)

# Confidence Dampening Multiplier Constants
CONFIDENCE_BASE_FLOOR = 0.85    # Minimum multiplier for low-confidence predictions
CONFIDENCE_SCALE_FACTOR = 0.15  # Additional weight for high-confidence predictions

# Tier Threshold Constants for Priority Categorization
TIER_CRITICAL_THRESHOLD = 0.70  # CRITICAL PRIORITY: Urgent emergency resource deployment
TIER_HIGH_THRESHOLD = 0.45      # HIGH PRIORITY: Heightened alert & crew pre-positioning
TIER_MODERATE_THRESHOLD = 0.25  # MODERATE PRIORITY: Standard inspection & monitoring
# Scores below 0.25 are categorized as LOW PRIORITY


class PrioritizeLayer:
    def __init__(self, weight_risk: float = WEIGHT_RISK,
                 weight_pop: float = WEIGHT_POPULATION,
                 weight_infra: float = WEIGHT_INFRASTRUCTURE):
        self.weight_risk = weight_risk
        self.weight_pop = weight_pop
        self.weight_infra = weight_infra
        
        # Verify weights sum to 1.0
        total_weight = self.weight_risk + self.weight_pop + self.weight_infra
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
        Ranks zones using a deterministic Multi-Criteria Decision Analysis (MCDA) formula.
        
        Args:
            predictions_df (pd.DataFrame): DataFrame output from PredictLayer.get_predictions()
            
        Returns:
            pd.DataFrame: DataFrame sorted by priority_score descending with priority_rank and priority_reason.
        """
        if predictions_df.empty:
            logger.warning("Empty predictions DataFrame provided to PrioritizeLayer.")
            return predictions_df.copy()

        required_cols = ["zone_id", "population", "critical_infrastructure", "risk_score", "risk_confidence"]
        for col in required_cols:
            if col not in predictions_df.columns:
                raise ValueError(f"Missing required column in predictions DataFrame: {col}")

        df = predictions_df.copy()

        # Min-Max Normalization of Population and Infrastructure
        max_pop = df["population"].max() if df["population"].max() > 0 else 1.0
        max_infra = df["critical_infrastructure"].max() if df["critical_infrastructure"].max() > 0 else 1.0

        norm_pop = df["population"] / max_pop
        norm_infra = df["critical_infrastructure"] / max_infra

        # Core Weighted Score (0.0 to 1.0)
        raw_priority = (
            self.weight_risk * df["risk_score"] +
            self.weight_pop * norm_pop +
            self.weight_infra * norm_infra
        )

        # Bounded Confidence Multiplier (0.85 to 1.00)
        confidence_factor = CONFIDENCE_BASE_FLOOR + (CONFIDENCE_SCALE_FACTOR * df["risk_confidence"])
        
        # Final Priority Score
        priority_scores = raw_priority * confidence_factor
        df["priority_score"] = np.round(priority_scores, 4)

        # Sort descending by priority_score
        df = df.sort_values(by="priority_score", ascending=False).reset_index(drop=True)

        # Assign 1-indexed priority_rank
        df["priority_rank"] = df.index + 1

        # Construct human-readable priority_reason string
        reasons = []
        for idx, row in df.iterrows():
            tier = self._get_tier_label(row["priority_score"])
            reason = (
                f"{tier} (Score: {row['priority_score']:.4f}) -> "
                f"Risk: {row['risk_score']:.2f} | "
                f"Pop: {int(row['population']):,} | "
                f"Infra: {int(row['critical_infrastructure'])} facilities | "
                f"Conf: {row['risk_confidence'] * 100:.1f}%"
            )
            reasons.append(reason)

        df["priority_reason"] = reasons
        return df


if __name__ == "__main__":
    # Standalone verification runner chaining SENSE -> PREDICT -> PRIORITIZE
    logger.info("Running Layer 1 (SENSE)...")
    sense = SenseLayer()
    sense.load_csv_to_db()
    zone_state = sense.get_structured_state()

    logger.info("Running Layer 2 (PREDICT)...")
    predict_layer = PredictLayer()
    predictions_df = predict_layer.get_predictions(zone_state)

    logger.info("Running Layer 3 (PRIORITIZE)...")
    prioritize_layer = PrioritizeLayer()
    ranked_df = prioritize_layer.prioritize_zones(predictions_df)

    print("\n" + "=" * 80)
    print(" URBANSHIELD LAYER 3 (PRIORITIZE) - RANKED ZONE EMERGENCY LIST")
    print("=" * 80)
    output_cols = ["priority_rank", "zone_id", "zone_name", "risk_score", "risk_confidence", "priority_score", "priority_reason"]
    print(ranked_df[output_cols].to_string(index=False))
    print("=" * 80 + "\n")
