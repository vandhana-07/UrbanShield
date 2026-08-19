"""
UrbanShield - Layer 5: RECOMMEND
Translates optimization results into deterministic, auditable emergency action directives
and clean executive summaries for city authorities.
"""

import logging
import sys
from pathlib import Path
import pandas as pd

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from layers.sense import SenseLayer
from layers.predict import PredictLayer
from layers.prioritize import PrioritizeLayer
from layers.optimize import OptimizeLayer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("UrbanShield.Recommend")

# High Risk Threshold Constant for Action Urgency Calibration
HIGH_RISK_THRESHOLD = 0.80
CRITICAL_PRIORITY_THRESHOLD = 0.70
HIGH_PRIORITY_THRESHOLD = 0.45


class RecommendLayer:
    def __init__(self):
        pass

    def _determine_action(self, status: str, priority_score: float, risk_score: float) -> str:
        """
        Determines the exact, auditable action directive based on allocation status,
        priority tier, and risk score threshold.
        """
        if status == "ALLOCATED":
            # If risk is severe (>= 0.80) or priority is critical (>= 0.70), issue urgent immediate repair
            if risk_score >= HIGH_RISK_THRESHOLD or priority_score >= CRITICAL_PRIORITY_THRESHOLD:
                return "REPAIR & DISPATCH IMMEDIATELY"
            else:
                return "ACTIVE RESPONSE DISPATCHED"
        else:  # SKIPPED
            if priority_score >= CRITICAL_PRIORITY_THRESHOLD:
                # High priority unserved zone - requires escalation to command
                return "ESCALATE FOR REINFORCEMENTS"
            elif priority_score >= HIGH_PRIORITY_THRESHOLD:
                return "INSPECT & MONITOR HIGH RISK"
            else:
                return "ROUTINE MONITORING"

    def _get_risk_desc(self, risk_score: float) -> str:
        """Helper to return accurate risk level description based on risk_score."""
        if risk_score >= 0.80:
            return "severe flood hazard"
        elif risk_score >= 0.40:
            return "moderate flood risk"
        elif risk_score >= 0.15:
            return "low flood risk"
        else:
            return "minimal flood impact"

    def _generate_executive_summary(self, row: pd.Series, action: str) -> str:
        """
        Generates a 1-2 sentence deterministic natural language executive briefing per zone.
        Uses structured template synthesis for 100% offline hackathon judging reliability.
        """
        zone_name = row.get("zone_name", "Unknown Zone")
        risk_score = row.get("risk_score", 0.0)
        depth = row.get("inundation_depth_inches", "N/A")
        hazard = row.get("hazard_category", "N/A")
        status = row.get("allocation_status", "SKIPPED")
        pumps = int(row.get("allocated_pumps", 0))
        crews = int(row.get("allocated_crews", 0))
        cost = float(row.get("allocated_cost", 0.0))
        reason = row.get("allocation_reason", "")
        risk_desc = self._get_risk_desc(risk_score)

        if status == "ALLOCATED":
            if action == "REPAIR & DISPATCH IMMEDIATELY":
                return (
                    f"{zone_name} presents {risk_desc} (risk: {risk_score:.2f}, inundation: {depth}\", hazard: {hazard}). "
                    f"ALLOCATED {pumps} heavy pumps and {crews} emergency crews (₹{cost:,.0f}) for immediate deployment."
                )
            else:
                return (
                    f"{zone_name} presents {risk_desc} (risk: {risk_score:.2f}, inundation: {depth}\", hazard: {hazard}). "
                    f"ALLOCATED {pumps} heavy pumps and {crews} emergency crews (₹{cost:,.0f}) for active mitigation support."
                )
        else:  # SKIPPED
            if action == "ESCALATE FOR REINFORCEMENTS":
                return (
                    f"{zone_name} presents {risk_desc} (risk: {risk_score:.2f}, inundation: {depth}\", hazard: {hazard}) but was SKIPPED due to resource limits ({reason}). "
                    f"IMMEDIATE ESCALATION to Chennai city command required for emergency reinforcement crews/pumps."
                )
            elif action == "INSPECT & MONITOR HIGH RISK":
                return (
                    f"{zone_name} presents {risk_desc} (risk: {risk_score:.2f}, inundation: {depth}\", hazard: {hazard}) but remained unserviced due to constraint bounds. "
                    f"Dispatched mobile inspection units for roving field monitoring."
                )
            else:
                return (
                    f"{zone_name} presents {risk_desc} (risk: {risk_score:.2f}, inundation: {depth}\", hazard: {hazard}). "
                    f"Retained on routine automated telemetry sensor monitoring with zero immediate intervention required."
                )

    def generate_recommendations(self, allocated_df: pd.DataFrame) -> pd.DataFrame:
        """
        Translates optimization results into recommended actions and executive summaries.
        
        Args:
            allocated_df (pd.DataFrame): Output DataFrame from OptimizeLayer.optimize_allocation()
            
        Returns:
            pd.DataFrame: Original DataFrame enriched with recommended_action and executive_summary.
        """
        if allocated_df.empty:
            logger.warning("Empty DataFrame provided to RecommendLayer.")
            return allocated_df.copy()

        df = allocated_df.copy()
        actions = []
        summaries = []

        for _, row in df.iterrows():
            status = row.get("allocation_status", "SKIPPED")
            priority_score = row.get("priority_score", 0.0)
            risk_score = row.get("risk_score", 0.0)

            action = self._determine_action(status, priority_score, risk_score)
            summary = self._generate_executive_summary(row, action)

            actions.append(action)
            summaries.append(summary)

        df["recommended_action"] = actions
        df["executive_summary"] = summaries

        return df


if __name__ == "__main__":
    # Standalone verification runner chaining SENSE -> PREDICT -> PRIORITIZE -> OPTIMIZE -> RECOMMEND
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

    logger.info("Running Layer 4 (OPTIMIZE)...")
    optimize_layer = OptimizeLayer()
    allocated_df, _ = optimize_layer.optimize_allocation(ranked_df)

    logger.info("Running Layer 5 (RECOMMEND)...")
    recommend_layer = RecommendLayer()
    recommended_df = recommend_layer.generate_recommendations(allocated_df)

    print("\n" + "=" * 100)
    print(" URBANSHIELD LAYER 5 (RECOMMEND) - ACTIONABLE EMERGENCY DIRECTIVES & EXECUTIVE BRIEFING")
    print("=" * 100)

    output_cols = ["priority_rank", "zone_id", "zone_name", "risk_score", "allocation_status", "recommended_action", "executive_summary"]
    for _, row in recommended_df.iterrows():
        print(f"Rank {row['priority_rank']:2d} | [{row['zone_id']}] {row['zone_name']:<22} | Status: {row['allocation_status']:<9} | Action: {row['recommended_action']}")
        print(f"        Briefing: {row['executive_summary']}")
        print("-" * 100)
    print("=" * 100 + "\n")
