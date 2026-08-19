"""
UrbanShield - Layer 6: SIMULATE
Executes what-if scenario analyses by overriding zone environmental metrics or resource pool limits.
Selective re-executes downstream layers in-memory (without mutating SQLite database) and computes
a detailed BEFORE vs AFTER delta comparison.
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
from layers.prioritize import PrioritizeLayer
from layers.optimize import OptimizeLayer
from layers.recommend import RecommendLayer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("UrbanShield.Simulate")


class SimulateLayer:
    def __init__(self):
        self.sense_layer = SenseLayer()
        self.predict_layer = PredictLayer()
        self.prioritize_layer = PrioritizeLayer()
        self.optimize_layer = OptimizeLayer()
        self.recommend_layer = RecommendLayer()

    def run_baseline(self) -> tuple:
        """
        Executes full baseline pipeline (SENSE -> PREDICT -> PRIORITIZE -> OPTIMIZE -> RECOMMEND).
        
        Returns:
            tuple: (baseline_recommended_df, baseline_summary_dict, baseline_zone_state)
        """
        zone_state = self.sense_layer.get_structured_state()
        pred_df = self.predict_layer.get_predictions(zone_state)
        prio_df = self.prioritize_layer.prioritize_zones(pred_df)
        opt_df, opt_summary = self.optimize_layer.optimize_allocation(prio_df)
        rec_df = self.recommend_layer.generate_recommendations(opt_df)
        return rec_df, opt_summary, zone_state

    def run_simulation(self, zone_overrides: dict = None,
                       resource_overrides: dict = None,
                       baseline_tuple: tuple = None) -> tuple:
        """
        Executes scenario simulation with overrides.
        
        NO DATABASE MUTATION: zone_overrides are applied to an in-memory DataFrame copy only.
        MODEL REUSE: Re-invoking PredictLayer loads the cached models/flood_rf_model.joblib for inference.
        COMBINED OVERRIDES: Handles zone and resource overrides simultaneously if both passed.
        
        Args:
            zone_overrides (dict, optional): e.g. {"Z05": {"rainfall": 180.0}}
            resource_overrides (dict, optional): e.g. {"total_pumps": 8, "total_crews": 6, "total_budget": 650000.0}
            baseline_tuple (tuple, optional): (baseline_rec_df, baseline_summary, baseline_zone_state)
            
        Returns:
            tuple: (simulated_rec_df, simulated_summary_dict, comparison_delta_dict)
        """
        # Fetch baseline results if not provided
        if baseline_tuple is None:
            baseline_rec_df, baseline_summary, baseline_zone_state = self.run_baseline()
        else:
            baseline_rec_df, baseline_summary, baseline_zone_state = baseline_tuple

        # Determine selective layer execution path
        has_zone_overrides = bool(zone_overrides)
        has_resource_overrides = bool(resource_overrides)

        if not has_zone_overrides and not has_resource_overrides:
            logger.info("No overrides provided. Returning baseline results.")
            return baseline_rec_df, baseline_summary, {}

        # 1. Handle Zone Overrides (IN-MEMORY COPY ONLY - SQLite remains untouched)
        # Explicit DataFrame .copy() ensures zero database or disk mutation
        working_zone_state = baseline_zone_state.copy()

        if has_zone_overrides:
            for zid, override_fields in zone_overrides.items():
                mask = working_zone_state["zone_id"] == zid
                if not mask.any():
                    logger.warning(f"Zone override target '{zid}' not found in zone state. Skipping.")
                    continue
                for field, val in override_fields.items():
                    if field in working_zone_state.columns and field != "zone_id":
                        working_zone_state.loc[mask, field] = val
                        logger.info(f"[SIMULATION OVERRIDE] Zone {zid} -> {field} = {val} (in-memory)")
                    else:
                        logger.warning(f"Invalid field '{field}' for zone override. Skipping.")

        # 2. Determine downstream execution pipeline
        if has_zone_overrides:
            # Re-run PREDICT -> PRIORITIZE -> OPTIMIZE -> RECOMMEND
            # Note: PredictLayer().get_predictions() loads cached models/flood_rf_model.joblib
            logger.info("Re-running PREDICT -> PRIORITIZE -> OPTIMIZE -> RECOMMEND for zone metric overrides...")
            sim_pred_df = self.predict_layer.get_predictions(working_zone_state)
            sim_prio_df = self.prioritize_layer.prioritize_zones(sim_pred_df)
        else:
            # Reuse baseline prediction & priority scores if only resource caps changed
            logger.info("Reusing baseline PREDICT/PRIORITIZE scores (resource overrides only)...")
            sim_prio_df = baseline_rec_df.copy()

        # Parse resource overrides
        res_kwargs = {}
        if has_resource_overrides:
            if "total_pumps" in resource_overrides:
                res_kwargs["total_pumps"] = resource_overrides["total_pumps"]
            if "total_crews" in resource_overrides:
                res_kwargs["total_crews"] = resource_overrides["total_crews"]
            if "total_budget" in resource_overrides:
                res_kwargs["total_budget"] = resource_overrides["total_budget"]

        # Run OPTIMIZE -> RECOMMEND
        sim_opt_df, sim_summary = self.optimize_layer.optimize_allocation(sim_prio_df, **res_kwargs)
        sim_rec_df = self.recommend_layer.generate_recommendations(sim_opt_df)

        # 3. Compute BEFORE vs AFTER Comparison Delta
        comparison_delta = self._build_comparison_delta(baseline_rec_df, baseline_summary, sim_rec_df, sim_summary)

        return sim_rec_df, sim_summary, comparison_delta

    def _build_comparison_delta(self, base_df: pd.DataFrame, base_summary: dict,
                                sim_df: pd.DataFrame, sim_summary: dict) -> dict:
        """
        Computes detailed BEFORE vs AFTER delta comparison.
        """
        # Global Metrics Comparison
        global_delta = {
            "serviced_zones": {
                "before": base_summary.get("zones_serviced", 0),
                "after": sim_summary.get("zones_serviced", 0),
                "diff": sim_summary.get("zones_serviced", 0) - base_summary.get("zones_serviced", 0)
            },
            "score_coverage_pct": {
                "before": base_summary.get("score_coverage_percentage", 0.0),
                "after": sim_summary.get("score_coverage_percentage", 0.0),
                "diff": round(sim_summary.get("score_coverage_percentage", 0.0) - base_summary.get("score_coverage_percentage", 0.0), 2)
            },
            "total_covered_score": {
                "before": base_summary.get("total_covered_score", 0.0),
                "after": sim_summary.get("total_covered_score", 0.0),
                "diff": round(sim_summary.get("total_covered_score", 0.0) - base_summary.get("total_covered_score", 0.0), 4)
            },
            "pumps_deployed": {
                "before": f"{base_summary.get('pumps_deployed', 0)}/{base_summary.get('total_pumps_capacity', 0)}",
                "after": f"{sim_summary.get('pumps_deployed', 0)}/{sim_summary.get('total_pumps_capacity', 0)}"
            },
            "crews_deployed": {
                "before": f"{base_summary.get('crews_deployed', 0)}/{base_summary.get('total_crews_capacity', 0)}",
                "after": f"{sim_summary.get('crews_deployed', 0)}/{sim_summary.get('total_crews_capacity', 0)}"
            },
            "budget_spent": {
                "before": f"₹{base_summary.get('budget_spent', 0.0):,.0f} / ₹{base_summary.get('total_budget_capacity', 0.0):,.0f}",
                "after": f"₹{sim_summary.get('budget_spent', 0.0):,.0f} / ₹{sim_summary.get('total_budget_capacity', 0.0):,.0f}"
            }
        }

        # Zone-Level Comparisons & Flips
        rf_col = "rainfall_mm" if "rainfall_mm" in base_df.columns else "rainfall"
        depth_col = "inundation_depth_inches" if "inundation_depth_inches" in base_df.columns else "inundation_depth"
        
        merged = pd.merge(
            base_df[["zone_id", "zone_name", rf_col, depth_col, "risk_score", "risk_confidence", "priority_score", "allocation_status", "recommended_action"]],
            sim_df[["zone_id", rf_col, depth_col, "risk_score", "risk_confidence", "priority_score", "allocation_status", "recommended_action"]],
            on="zone_id",
            suffixes=("_before", "_after")
        )

        status_flips = []
        gained_zones = []
        lost_zones = []

        for _, row in merged.iterrows():
            zid = row["zone_id"]
            zname = row["zone_name"]
            b_stat = row["allocation_status_before"]
            a_stat = row["allocation_status_after"]

            if b_stat == "SKIPPED" and a_stat == "ALLOCATED":
                change = "GAINED_ALLOCATION"
                gained_zones.append(f"{zname} ({zid})")
            elif b_stat == "ALLOCATED" and a_stat == "SKIPPED":
                change = "LOST_ALLOCATION"
                lost_zones.append(f"{zname} ({zid})")
            elif a_stat == "ALLOCATED":
                change = "UNCHANGED_ALLOCATED"
            else:
                change = "UNCHANGED_SKIPPED"

            status_flips.append(change)

        merged["status_change"] = status_flips

        comparison_delta = {
            "global_metrics": global_delta,
            "gained_zones": gained_zones,
            "lost_zones": lost_zones,
            "zone_delta_df": merged
        }

        return comparison_delta


if __name__ == "__main__":
    # Standalone verification runner testing what-if simulation scenarios
    logger.info("Initializing SimulateLayer...")
    sim = SimulateLayer()

    logger.info("Running Baseline Pipeline...")
    base_rec_df, base_summary, base_zone_state = sim.run_baseline()
    base_tuple = (base_rec_df, base_summary, base_zone_state)

    # Scenario 1: Resource Pool Expansion (8 pumps, 6 crews, ₹650,000 budget)
    print("\n" + "=" * 90)
    print(" WHAT-IF SCENARIO A: RESOURCE EXPANSION (+2 Pumps, +2 Crews, +₹150k Budget)")
    print("=" * 90)
    sim_rec_a, sim_sum_a, delta_a = sim.run_simulation(
        resource_overrides={"total_pumps": 8, "total_crews": 6, "total_budget": 650000.0},
        baseline_tuple=base_tuple
    )

    g_a = delta_a["global_metrics"]
    print(f" Serviced Zones   : {g_a['serviced_zones']['before']} -> {g_a['serviced_zones']['after']} (Diff: {g_a['serviced_zones']['diff']:+d})")
    print(f" Priority Coverage: {g_a['score_coverage_pct']['before']}% -> {g_a['score_coverage_pct']['after']}% (Diff: {g_a['score_coverage_pct']['diff']:+.2f}%)")
    print(f" Pumps Deployed   : {g_a['pumps_deployed']['before']} -> {g_a['pumps_deployed']['after']}")
    print(f" Crews Deployed   : {g_a['crews_deployed']['before']} -> {g_a['crews_deployed']['after']}")
    print(f" Budget Spent     : {g_a['budget_spent']['before']} -> {g_a['budget_spent']['after']}")
    print(f" Gained Allocation: {', '.join(delta_a['gained_zones']) if delta_a['gained_zones'] else 'None'}")
    print(f" Lost Allocation  : {', '.join(delta_a['lost_zones']) if delta_a['lost_zones'] else 'None'}")

    # Scenario 2: Combined Overrides (Severe Rainfall Spike on CHN-Z03 T. Nagar + Resource Expansion)
    print("\n" + "=" * 90)
    print(" WHAT-IF SCENARIO B: DELUGE SPIKE (CHN-Z03 T. Nagar Rain 32->120mm + Resource Expansion)")
    print("=" * 90)
    sim_rec_b, sim_sum_b, delta_b = sim.run_simulation(
        zone_overrides={"CHN-Z03": {"rainfall_mm": 120.0, "inundation_depth_inches": 22.0}},
        resource_overrides={"total_pumps": 8, "total_crews": 6, "total_budget": 650000.0},
        baseline_tuple=base_tuple
    )

    g_b = delta_b["global_metrics"]
    print(f" Serviced Zones   : {g_b['serviced_zones']['before']} -> {g_b['serviced_zones']['after']} (Diff: {g_b['serviced_zones']['diff']:+d})")
    print(f" Priority Coverage: {g_b['score_coverage_pct']['before']}% -> {g_b['score_coverage_pct']['after']}% (Diff: {g_b['score_coverage_pct']['diff']:+.2f}%)")
    print(f" Gained Allocation: {', '.join(delta_b['gained_zones']) if delta_b['gained_zones'] else 'None'}")
    print(f" Lost Allocation  : {', '.join(delta_b['lost_zones']) if delta_b['lost_zones'] else 'None'}")
    print("=" * 90 + "\n")
    print("\nZone CHN-Z03 Specific Metrics Delta (Scenario B):")
    rf_col = "rainfall_mm" if "rainfall_mm_before" in delta_b["zone_delta_df"].columns else "rainfall"
    z3_matches = delta_b["zone_delta_df"][delta_b["zone_delta_df"]["zone_id"] == "CHN-Z03"]
    if not z3_matches.empty:
        z3_row = z3_matches.iloc[0]
        print(f" - Zone ID              : {z3_row['zone_id']} ({z3_row['zone_name']})")
        print(f" - Rainfall             : {z3_row[rf_col + '_before']} mm  ->  {z3_row[rf_col + '_after']} mm")
        print(f" - Risk Score           : {z3_row['risk_score_before']:.4f}     ->  {z3_row['risk_score_after']:.4f}")
        print(f" - Priority Score       : {z3_row['priority_score_before']:.4f} ->  {z3_row['priority_score_after']:.4f}")
        print(f" - Allocation Status    : {z3_row['allocation_status_before']} ->  {z3_row['allocation_status_after']}")

    # Scenario 3: Budget Cut What-If (-40% budget cut to $300,000)
    print("\n" + "=" * 90)
    print(" WHAT-IF SCENARIO C: MUNICIPAL BUDGET CUT (-40% Budget Cut to $300,000)")
    print("=" * 90)
    sim_rec_c, sim_sum_c, delta_c = sim.run_simulation(
        resource_overrides={"total_budget": 300000.0},
        baseline_tuple=base_tuple
    )

    g_c = delta_c["global_metrics"]
    print(f" Serviced Zones   : {g_c['serviced_zones']['before']} -> {g_c['serviced_zones']['after']} (Diff: {g_c['serviced_zones']['diff']:+d})")
    print(f" Priority Coverage: {g_c['score_coverage_pct']['before']}% -> {g_c['score_coverage_pct']['after']}% (Diff: {g_c['score_coverage_pct']['diff']:+.2f}%)")
    print(f" Budget Spent     : {g_c['budget_spent']['before']} -> {g_c['budget_spent']['after']}")
    print(f" Lost Allocation  : {', '.join(delta_c['lost_zones']) if delta_c['lost_zones'] else 'None'}")
    print("=" * 90 + "\n")
