"""
UrbanShield — Non-Destructive Live Data Update & Observation Manager
Provides in-memory validation, live observation simulation, CSV ingestion,
and seamless re-execution through the 6-layer intelligence pipeline.

STRICT SAFETY GUARANTEE:
This manager operates purely in-memory on pandas DataFrames and Streamlit session state.
It NEVER modifies, overwrites, or deletes records in 'data/urbanshield.db' or baseline CSV files.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from layers.predict import PredictLayer
from layers.prioritize import PrioritizeLayer
from layers.optimize import OptimizeLayer
from layers.recommend import RecommendLayer

logger = logging.getLogger("UrbanShield.UpdateManager")

# Known Monitored Zone IDs
VALID_ZONE_IDS = {
    "CHN-Z01", "CHN-Z02", "CHN-Z03", "CHN-Z04", "CHN-Z05",
    "CHN-Z06", "CHN-Z07", "CHN-Z08", "CHN-Z09", "CHN-Z10",
    "CHN-Z11", "CHN-Z12", "CHN-Z13", "CHN-Z14", "CHN-Z15",
    "CHN-REC-01"
}


class UpdateManager:
    def __init__(self):
        """Initializes the pipeline execution layers for in-memory re-evaluation."""
        self.predict_layer = PredictLayer()
        self.prioritize_layer = PrioritizeLayer()
        self.optimize_layer = OptimizeLayer()
        self.recommend_layer = RecommendLayer()

    def validate_csv_upload(self, df: pd.DataFrame) -> Tuple[bool, Optional[pd.DataFrame], List[str], List[str]]:
        """
        Validates an uploaded observation DataFrame.
        
        Supported Columns:
        - zone_id (Required)
        - rainfall_mm (Optional, >= 0.0)
        - inundation_depth_inches / water_depth_inches (Optional, >= 0.0)
        - hazard_category (Optional: VERY_HIGH, HIGH, MODERATE, LOW, VERY_LOW)
        
        Returns:
            Tuple: (is_valid, cleaned_df, errors_list, warnings_list)
        """
        errors = []
        warnings = []

        if df is None or df.empty:
            errors.append("Uploaded file is empty.")
            return False, None, errors, warnings

        # Standardize column names (lowercase and strip whitespace)
        col_map = {}
        for c in df.columns:
            cleaned = str(c).strip().lower()
            if cleaned in ["zone_id", "zoneid", "id", "zone"]:
                col_map[c] = "zone_id"
            elif cleaned in ["rainfall_mm", "rainfall", "rain_mm", "rain"]:
                col_map[c] = "rainfall_mm"
            elif cleaned in ["inundation_depth_inches", "water_depth_inches", "depth_inches", "depth", "inundation_depth", "water_depth"]:
                col_map[c] = "inundation_depth_inches"
            elif cleaned in ["hazard_category", "hazard", "hazard_tier"]:
                col_map[c] = "hazard_category"

        df_std = df.rename(columns=col_map)

        if "zone_id" not in df_std.columns:
            errors.append("Missing required column: 'zone_id' (or 'Zone_ID').")
            return False, None, errors, warnings

        if "rainfall_mm" not in df_std.columns and "inundation_depth_inches" not in df_std.columns:
            errors.append("Upload must contain at least one observation column: 'rainfall_mm' or 'inundation_depth_inches'.")
            return False, None, errors, warnings

        valid_rows = []
        seen_zones = set()

        for idx, row in df_std.iterrows():
            row_num = idx + 1
            zid = str(row["zone_id"]).strip().upper()

            # Handle common prefix variations (e.g. Z01 -> CHN-Z01)
            if not zid.startswith("CHN-") and zid.startswith("Z"):
                zid = f"CHN-{zid}"
            elif zid == "REC" or zid == "CHN-REC":
                zid = "CHN-REC-01"

            if zid not in VALID_ZONE_IDS:
                errors.append(f"Row {row_num}: Unknown Zone_ID '{row['zone_id']}'. Must be one of the 16 monitored zones (e.g. CHN-Z01 to CHN-Z15, CHN-REC-01).")
                continue

            if zid in seen_zones:
                warnings.append(f"Row {row_num}: Duplicate Zone_ID '{zid}' detected. The latest row entry will be used.")
            seen_zones.add(zid)

            cleaned_row = {"zone_id": zid}

            # Validate rainfall_mm
            if "rainfall_mm" in df_std.columns and pd.notna(row["rainfall_mm"]):
                try:
                    rf = float(row["rainfall_mm"])
                    if rf < 0.0:
                        errors.append(f"Row {row_num} [{zid}]: rainfall_mm cannot be negative ({rf} mm).")
                    elif rf > 600.0:
                        warnings.append(f"Row {row_num} [{zid}]: Exceptionally high rainfall ({rf} mm) detected.")
                        cleaned_row["rainfall_mm"] = rf
                    else:
                        cleaned_row["rainfall_mm"] = rf
                except (ValueError, TypeError):
                    errors.append(f"Row {row_num} [{zid}]: Invalid non-numeric rainfall value '{row['rainfall_mm']}'.")

            # Validate inundation_depth_inches
            if "inundation_depth_inches" in df_std.columns and pd.notna(row["inundation_depth_inches"]):
                try:
                    dp = float(row["inundation_depth_inches"])
                    if dp < 0.0:
                        errors.append(f"Row {row_num} [{zid}]: inundation_depth_inches cannot be negative ({dp} inches).")
                    elif dp > 120.0:
                        warnings.append(f"Row {row_num} [{zid}]: Extreme inundation depth ({dp} inches) detected.")
                        cleaned_row["inundation_depth_inches"] = dp
                    else:
                        cleaned_row["inundation_depth_inches"] = dp
                except (ValueError, TypeError):
                    errors.append(f"Row {row_num} [{zid}]: Invalid non-numeric depth value '{row['inundation_depth_inches']}'.")

            # Optional hazard_category
            if "hazard_category" in df_std.columns and pd.notna(row["hazard_category"]):
                haz = str(row["hazard_category"]).strip().upper()
                if haz in ["VERY_HIGH", "HIGH", "MODERATE", "LOW", "VERY_LOW"]:
                    cleaned_row["hazard_category"] = haz
                else:
                    warnings.append(f"Row {row_num} [{zid}]: Unrecognized hazard category '{haz}'. Baseline hazard tier retained.")

            valid_rows.append(cleaned_row)

        if errors:
            return False, None, errors, warnings

        cleaned_df = pd.DataFrame(valid_rows)
        # Drop duplicates, keeping the last row
        cleaned_df = cleaned_df.drop_duplicates(subset=["zone_id"], keep="last")

        return True, cleaned_df, errors, warnings

    def apply_overrides_to_baseline(
        self,
        baseline_df: pd.DataFrame,
        override_df: pd.DataFrame,
        source_label: str,
        provenance_type: str = "USER_UPLOAD"
    ) -> pd.DataFrame:
        """
        Creates an in-memory active working copy with applied overrides.
        Guarantees baseline_df is never modified in-place.
        """
        active_df = baseline_df.copy()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")

        for _, row in override_df.iterrows():
            zid = row["zone_id"]
            mask = active_df["zone_id"] == zid
            if not mask.any():
                continue

            if "rainfall_mm" in row and pd.notna(row["rainfall_mm"]):
                active_df.loc[mask, "rainfall_mm"] = float(row["rainfall_mm"])

            if "inundation_depth_inches" in row and pd.notna(row["inundation_depth_inches"]):
                active_df.loc[mask, "inundation_depth_inches"] = float(row["inundation_depth_inches"])

            if "hazard_category" in row and pd.notna(row["hazard_category"]):
                active_df.loc[mask, "hazard_category"] = str(row["hazard_category"])

            active_df.loc[mask, "data_source"] = f"{source_label} ({provenance_type})"
            active_df.loc[mask, "updated_at"] = current_time

        return active_df

    def re_evaluate_pipeline(self, active_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Re-executes the existing 6-layer intelligence pipeline top-to-bottom on active working state.
        Reuses 100% of the verified formulas and Google OR-Tools CP-SAT knapsack solver.
        """
        # Layer 2: PREDICT
        predictions_df = self.predict_layer.get_predictions(active_df)

        # Layer 3: PRIORITIZE
        ranked_df = self.prioritize_layer.prioritize_zones(predictions_df)

        # Layer 4: OPTIMIZE
        allocated_df, opt_summary = self.optimize_layer.optimize_allocation(ranked_df)

        # Layer 5: RECOMMEND
        final_df = self.recommend_layer.generate_recommendations(allocated_df)

        return final_df, opt_summary

    def compute_before_after_delta(
        self,
        baseline_final_df: pd.DataFrame,
        updated_final_df: pd.DataFrame
    ) -> Dict:
        """
        Computes an auditable BEFORE -> AFTER comparison between the baseline pipeline results
        and the updated pipeline results.
        """
        comparison = []
        alloc_changes = 0

        base_map = {r["zone_id"]: r for _, r in baseline_final_df.iterrows()}
        upd_map = {r["zone_id"]: r for _, r in updated_final_df.iterrows()}

        for zid, base_row in base_map.items():
            upd_row = upd_map.get(zid, base_row)

            b_risk = float(base_row.get("risk_score", 0.0))
            u_risk = float(upd_row.get("risk_score", 0.0))
            b_prio = float(base_row.get("priority_score", 0.0))
            u_prio = float(upd_row.get("priority_score", 0.0))
            b_alloc = str(base_row.get("allocation_status", "SKIPPED"))
            u_alloc = str(upd_row.get("allocation_status", "SKIPPED"))
            b_rain = float(base_row.get("rainfall_mm", 0.0))
            u_rain = float(upd_row.get("rainfall_mm", 0.0))
            b_depth = float(base_row.get("inundation_depth_inches", 0.0))
            u_depth = float(upd_row.get("inundation_depth_inches", 0.0))

            changed = (b_alloc != u_alloc) or (abs(b_risk - u_risk) > 0.001) or (abs(b_rain - u_rain) > 0.1) or (abs(b_depth - u_depth) > 0.1)
            if b_alloc != u_alloc:
                alloc_changes += 1

            comparison.append({
                "zone_id": zid,
                "zone_name": base_row.get("zone_name", zid),
                "rainfall_before": b_rain,
                "rainfall_after": u_rain,
                "depth_before": b_depth,
                "depth_after": u_depth,
                "risk_before": b_risk,
                "risk_after": u_risk,
                "risk_delta": u_risk - b_risk,
                "priority_before": b_prio,
                "priority_after": u_prio,
                "allocation_before": b_alloc,
                "allocation_after": u_alloc,
                "status_changed": b_alloc != u_alloc,
                "data_changed": changed
            })

        return {
            "plan_status": "RESOURCE PLAN UPDATED" if alloc_changes > 0 else "RESOURCE PLAN UNCHANGED",
            "allocation_changes_count": alloc_changes,
            "zone_deltas": comparison
        }
