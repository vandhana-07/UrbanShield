"""
UrbanShield - Layer 4: OPTIMIZE
Allocates a limited pool of emergency resources (pumps, crews, budget cap) across urban zones
using Google OR-Tools CP-SAT Constraint Programming solver to maximize total covered priority score.
"""

import logging
import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ortools.sat.python import cp_model
from layers.sense import SenseLayer
from layers.predict import PredictLayer
from layers.prioritize import PrioritizeLayer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("UrbanShield.Optimize")

# Default Global Emergency Resource Pool Capacities
DEFAULT_TOTAL_PUMPS = 6        # Total portable heavy pump units available
DEFAULT_TOTAL_CREWS = 4        # Total disaster response crew teams available
DEFAULT_TOTAL_BUDGET = 500000.0  # Total emergency operating budget cap ($)


class OptimizeLayer:
    def __init__(self, total_pumps: int = DEFAULT_TOTAL_PUMPS,
                 total_crews: int = DEFAULT_TOTAL_CREWS,
                 total_budget: float = DEFAULT_TOTAL_BUDGET):
        self.total_pumps = total_pumps
        self.total_crews = total_crews
        self.total_budget = total_budget

    def _calculate_zone_requirements(self, row: pd.Series) -> tuple:
        """
        Calculates required pumps, crews, and cost for a zone based on physical metrics.
        
        Rules:
        - Pumps: 2 pumps if rainfall > 100mm/h and drainage < 40mm/h, else 1 pump.
        - Crews: 2 crews if population > 50,000 or critical_infra >= 5, else 1 crew.
        - Cost: Base dispatch ($30,000) + (pumps * $40,000) + (crews * $35,000).
        """
        rainfall = row.get("rainfall", 0.0)
        drainage = row.get("drainage_capacity", 50.0)
        population = row.get("population", 0)
        infra = row.get("critical_infrastructure", 0)

        pumps_needed = 2 if (rainfall > 100.0 and drainage < 40.0) else 1
        crews_needed = 2 if (population > 50000 or infra >= 5) else 1
        cost_needed = 30000.0 + (pumps_needed * 40000.0) + (crews_needed * 35000.0)

        return pumps_needed, crews_needed, cost_needed

    def optimize_allocation(self, ranked_df: pd.DataFrame,
                            total_pumps: int = None,
                            total_crews: int = None,
                            total_budget: float = None) -> tuple:
        """
        Solves 0-1 Multi-Dimensional Knapsack problem using Google OR-Tools CP-SAT.
        
        Returns:
            tuple: (allocated_df, summary_metrics_dict)
        """
        pumps_cap = total_pumps if total_pumps is not None else self.total_pumps
        crews_cap = total_crews if total_crews is not None else self.total_crews
        budget_cap = total_budget if total_budget is not None else self.total_budget

        if ranked_df.empty:
            logger.warning("Empty ranked DataFrame provided to OptimizeLayer.")
            return ranked_df.copy(), {}

        df = ranked_df.copy()
        num_zones = len(df)

        # 1. Compute resource requirements per zone
        pumps_req = []
        crews_req = []
        cost_req = []

        for _, row in df.iterrows():
            p, c, cost = self._calculate_zone_requirements(row)
            pumps_req.append(p)
            crews_req.append(c)
            cost_req.append(cost)

        df["req_pumps"] = pumps_req
        df["req_crews"] = crews_req
        df["req_cost"] = cost_req

        # 2. Build CP-SAT Model
        model = cp_model.CpModel()

        # Binary decision variables x[z] \in {0, 1}
        x = {}
        for i in range(num_zones):
            x[i] = model.NewBoolVar(f"select_zone_{df.iloc[i]['zone_id']}")

        # Constraints
        model.Add(sum(pumps_req[i] * x[i] for i in range(num_zones)) <= pumps_cap)
        model.Add(sum(crews_req[i] * x[i] for i in range(num_zones)) <= crews_cap)
        model.Add(sum(int(cost_req[i]) * x[i] for i in range(num_zones)) <= int(budget_cap))

        # Objective Function: Maximize sum of priority_score (scaled to integer)
        model.Maximize(sum(int(df.iloc[i]["priority_score"] * 10000) * x[i] for i in range(num_zones)))

        # 3. Solve Model
        solver = cp_model.CpSolver()
        start_time = time.time()
        status = solver.Solve(model)
        solve_duration = time.time() - start_time
        status_name = solver.StatusName(status)

        logger.info(f"CP-SAT Solver Status: {status_name} (Solve Time: {solve_duration:.4f}s)")

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise RuntimeError(f"Optimization failed! CP-SAT Solver returned non-feasible status: {status_name}")

        # 4. Extract Solution
        allocated_indices = set()
        for i in range(num_zones):
            if solver.Value(x[i]) == 1:
                allocated_indices.add(i)

        # Compute consumed totals from allocated set
        used_pumps = sum(pumps_req[i] for i in allocated_indices)
        used_crews = sum(crews_req[i] for i in allocated_indices)
        used_cost = sum(cost_req[i] for i in allocated_indices)

        rem_pumps = pumps_cap - used_pumps
        rem_crews = crews_cap - used_crews
        rem_budget = budget_cap - used_cost

        # 5. Populate Allocation Columns with Honest Reason Determination
        allocated_pumps_col = []
        allocated_crews_col = []
        allocated_cost_col = []
        status_col = []
        reason_col = []

        for i in range(num_zones):
            p_req = pumps_req[i]
            c_req = crews_req[i]
            cost_r = cost_req[i]

            if i in allocated_indices:
                allocated_pumps_col.append(p_req)
                allocated_crews_col.append(c_req)
                allocated_cost_col.append(cost_r)
                status_col.append("ALLOCATED")
                reason_col.append(f"ALLOCATED: {p_req} pumps, {c_req} crews (${cost_r:,.0f})")
            else:
                allocated_pumps_col.append(0)
                allocated_crews_col.append(0)
                allocated_cost_col.append(0.0)
                status_col.append("SKIPPED")

                # Honest reason determination check:
                # Could this zone fit ALONE in the remaining unallocated pool?
                exceeded_constraints = []
                if p_req > rem_pumps:
                    exceeded_constraints.append(f"requires {p_req} pumps, {rem_pumps} available")
                if c_req > rem_crews:
                    exceeded_constraints.append(f"requires {c_req} crews, {rem_crews} available")
                if cost_r > rem_budget:
                    exceeded_constraints.append(f"requires ${cost_r:,.0f} budget, ${rem_budget:,.0f} available")

                if exceeded_constraints:
                    reason_col.append(f"SKIPPED: Infeasible alone — {'; '.join(exceeded_constraints)}")
                else:
                    reason_col.append("SKIPPED: Solved combination — resources allocated to a higher-value combination of other zones")

        df["allocated_pumps"] = allocated_pumps_col
        df["allocated_crews"] = allocated_crews_col
        df["allocated_cost"] = allocated_cost_col
        df["allocation_status"] = status_col
        df["allocation_reason"] = reason_col

        # Cleanup temporary requirement columns
        df.drop(columns=["req_pumps", "req_crews", "req_cost"], inplace=True)

        # 6. Global Summary Metrics
        total_possible_score = df["priority_score"].sum()
        total_covered_score = df[df["allocation_status"] == "ALLOCATED"]["priority_score"].sum()
        coverage_pct = (total_covered_score / total_possible_score * 100.0) if total_possible_score > 0 else 0.0

        summary = {
            "solver_status": status_name,
            "solve_time_seconds": round(solve_duration, 4),
            "total_pumps_capacity": pumps_cap,
            "pumps_deployed": used_pumps,
            "total_crews_capacity": crews_cap,
            "crews_deployed": used_crews,
            "total_budget_capacity": budget_cap,
            "budget_spent": used_cost,
            "zones_serviced": len(allocated_indices),
            "total_zones": num_zones,
            "total_covered_score": round(total_covered_score, 4),
            "total_possible_score": round(total_possible_score, 4),
            "score_coverage_percentage": round(coverage_pct, 2)
        }

        return df, summary


if __name__ == "__main__":
    # Standalone verification runner chaining SENSE -> PREDICT -> PRIORITIZE -> OPTIMIZE
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
    allocated_df, summary = optimize_layer.optimize_allocation(ranked_df)

    print("\n" + "=" * 80)
    print(" URBANSHIELD LAYER 4 (OPTIMIZE) - OPTIMAL RESOURCE ALLOCATION PLAN")
    print("=" * 80)
    print(f" Solver Status    : {summary['solver_status']} (Solve Time: {summary['solve_time_seconds']}s)")
    print(f" Serviced Zones   : {summary['zones_serviced']} / {summary['total_zones']} zones")
    print(f" Priority Coverage: {summary['total_covered_score']:.4f} / {summary['total_possible_score']:.4f} ({summary['score_coverage_percentage']}%)")
    print(f" Pumps Deployed   : {summary['pumps_deployed']} / {summary['total_pumps_capacity']} units")
    print(f" Crews Deployed   : {summary['crews_deployed']} / {summary['total_crews_capacity']} teams")
    print(f" Budget Spent     : ${summary['budget_spent']:,.2f} / ${summary['total_budget_capacity']:,.2f}")
    print("=" * 80)

    output_cols = ["priority_rank", "zone_id", "zone_name", "priority_score", "allocation_status", "allocation_reason"]
    print(allocated_df[output_cols].to_string(index=False))
    print("=" * 80 + "\n")
