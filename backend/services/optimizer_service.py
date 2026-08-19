"""
UrbanShield Constrained Optimization Service
Provides mathematical optimization solvers powered by Google OR-Tools (Mixed-Integer Linear Programming).
Includes automated fallback to greedy heuristics if the solver is unavailable.
"""

import logging
from ortools.linear_solver import pywraplp
from models import Recommendation, Asset

logger = logging.getLogger("urbanshield.optimizer")

class ConstrainedOptimizerService:
    def __init__(self):
        self.solver_name = "SCIP"

    def solve_budget_knapsack(self, candidate_recs, budget_limit):
        """
        Solves the 0-1 Knapsack problem for capital intervention recommendations using Google OR-Tools.
        Maximizes total risk reduction percentage subject to total cost <= budget_limit.
        """
        budget_limit = float(budget_limit)
        if not candidate_recs or budget_limit <= 0:
            return {
                "budget_limit": round(budget_limit, 2),
                "total_cost": 0.0,
                "remaining_budget": round(budget_limit, 2),
                "total_risk_reduction_achieved_pct": 0.0,
                "recommendations_considered": len(candidate_recs),
                "recommendations_selected": 0,
                "selected_recommendations": [],
                "optimization_method": "or_tools"
            }

        try:
            solver = pywraplp.Solver.CreateSolver(self.solver_name)
            if not solver:
                solver = pywraplp.Solver.CreateSolver("CBC")
            
            if not solver:
                logger.warning("OR-Tools solver creation failed. Using greedy fallback.")
                return self._greedy_knapsack_fallback(candidate_recs, budget_limit)

            # Decision variables: x[i] = 1 if recommendation i is selected, 0 otherwise
            x = {}
            for i, rec in enumerate(candidate_recs):
                x[i] = solver.BoolVar(f"rec_{i}")

            # Budget Constraint: sum(cost[i] * x[i]) <= budget_limit
            constraint = solver.Constraint(0, budget_limit, "BudgetConstraint")
            for i, rec in enumerate(candidate_recs):
                constraint.SetCoefficient(x[i], float(rec.estimated_cost))

            # Objective: Maximize sum(risk_reduction[i] * x[i])
            objective = solver.Objective()
            for i, rec in enumerate(candidate_recs):
                objective.SetCoefficient(x[i], float(rec.expected_risk_reduction_pct))
            objective.SetMaximization()

            status = solver.Solve()

            if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
                selected = []
                total_cost = 0.0
                total_risk_reduction = 0.0

                for i, rec in enumerate(candidate_recs):
                    if x[i].solution_value() > 0.5:
                        selected.append(rec.to_dict())
                        total_cost += rec.estimated_cost
                        total_risk_reduction += rec.expected_risk_reduction_pct

                return {
                    "budget_limit": round(budget_limit, 2),
                    "total_cost": round(total_cost, 2),
                    "remaining_budget": round(max(0.0, budget_limit - total_cost), 2),
                    "total_risk_reduction_achieved_pct": round(total_risk_reduction, 1),
                    "recommendations_considered": len(candidate_recs),
                    "recommendations_selected": len(selected),
                    "selected_recommendations": selected,
                    "optimization_method": "or_tools"
                }
            else:
                logger.warning("OR-Tools solver returned non-optimal status %s. Using greedy fallback.", status)
                return self._greedy_knapsack_fallback(candidate_recs, budget_limit)

        except Exception as exc:
            logger.error("OR-Tools optimization exception: %s. Using greedy fallback.", str(exc))
            return self._greedy_knapsack_fallback(candidate_recs, budget_limit)

    def _greedy_knapsack_fallback(self, candidate_recs, budget_limit):
        """
        Greedy cost-efficiency fallback algorithm.
        """
        scored = []
        for rec in candidate_recs:
            cost = max(1.0, rec.estimated_cost)
            ratio = rec.expected_risk_reduction_pct / cost
            scored.append((rec, ratio))
        scored.sort(key=lambda x: x[1], reverse=True)

        selected = []
        remaining = budget_limit
        total_cost = 0.0
        total_risk = 0.0

        for rec, _ in scored:
            if rec.estimated_cost <= remaining:
                selected.append(rec.to_dict())
                remaining -= rec.estimated_cost
                total_cost += rec.estimated_cost
                total_risk += rec.expected_risk_reduction_pct

        return {
            "budget_limit": round(budget_limit, 2),
            "total_cost": round(total_cost, 2),
            "remaining_budget": round(remaining, 2),
            "total_risk_reduction_achieved_pct": round(total_risk, 1),
            "recommendations_considered": len(candidate_recs),
            "recommendations_selected": len(selected),
            "selected_recommendations": selected,
            "optimization_method": "greedy_fallback"
        }

    def solve_multi_resource_allocation(self, zones_list, pumps_avail, crews_avail, budget_avail):
        """
        Allocates countable resources (pumps, crews) and financial budget across zones using OR-Tools.
        """
        pumps_avail = float(pumps_avail)
        crews_avail = float(crews_avail)
        budget_avail = float(budget_avail)

        if not zones_list:
            return {
                "allocations": [],
                "total_pumps_allocated": 0,
                "total_crews_allocated": 0,
                "total_budget_allocated": 0.0,
                "unallocated_pumps": int(pumps_avail),
                "unallocated_crews": int(crews_avail),
                "unallocated_budget": round(budget_avail, 2),
                "optimization_method": "or_tools"
            }

        try:
            solver = pywraplp.Solver.CreateSolver(self.solver_name) or pywraplp.Solver.CreateSolver("CBC")
            if not solver:
                return self._greedy_multi_resource_fallback(zones_list, pumps_avail, crews_avail, budget_avail)

            n_zones = len(zones_list)
            p = {}
            c = {}

            # Decision variables: integer pumps and crews for each zone
            for z_idx, z in enumerate(zones_list):
                p[z_idx] = solver.IntVar(0, int(pumps_avail), f"pumps_z{z_idx}")
                c[z_idx] = solver.IntVar(0, int(crews_avail), f"crews_z{z_idx}")

            # Constraints: sum(pumps) <= pumps_avail, sum(crews) <= crews_avail
            pump_constr = solver.Constraint(0, int(pumps_avail), "TotalPumpsLimit")
            crew_constr = solver.Constraint(0, int(crews_avail), "TotalCrewsLimit")
            for z_idx in range(n_zones):
                pump_constr.SetCoefficient(p[z_idx], 1)
                crew_constr.SetCoefficient(c[z_idx], 1)

            # Objective: Maximize urgency-weighted protection
            objective = solver.Objective()
            for z_idx, z in enumerate(zones_list):
                urgency_weight = float(z.get("priority_weight", 1))
                critical_count = float(z.get("critical_asset_count", 0))
                coeff = urgency_weight * (1.0 + critical_count * 0.5)
                objective.SetCoefficient(p[z_idx], coeff * 1.5)
                objective.SetCoefficient(c[z_idx], coeff * 1.0)
            objective.SetMaximization()

            status = solver.Solve()

            allocations = []
            remaining_budget = budget_avail
            total_pumps_used = 0
            total_crews_used = 0
            total_budget_used = 0.0

            for z_idx, z in enumerate(zones_list):
                if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
                    pumps_assigned = int(p[z_idx].solution_value())
                    crews_assigned = int(c[z_idx].solution_value())
                else:
                    pumps_assigned = min(int(pumps_avail - total_pumps_used), z["critical_asset_count"])
                    crews_assigned = min(int(crews_avail - total_crews_used), z["critical_asset_count"])

                total_pumps_used += pumps_assigned
                total_crews_used += crews_assigned

                # Budget knapsack for zone
                zone_recs = Recommendation.query.filter(
                    Recommendation.status == "pending"
                ).join(Asset).filter(Asset.zone == z["zone"]).all()

                zone_knapsack = self.solve_budget_knapsack(zone_recs, remaining_budget)
                zone_budget_spent = zone_knapsack["total_cost"]
                funded_recs = zone_knapsack["selected_recommendations"]

                remaining_budget -= zone_budget_spent
                total_budget_used += zone_budget_spent

                allocations.append({
                    "zone": z["zone"],
                    "priority_tier": z["highest_priority_tier"],
                    "critical_asset_count": z["critical_asset_count"],
                    "avg_risk_score": z["avg_risk_score"],
                    "pumps_allocated": pumps_assigned,
                    "crews_allocated": crews_assigned,
                    "budget_allocated": round(zone_budget_spent, 2),
                    "recommendations_funded": funded_recs
                })

            return {
                "allocations": allocations,
                "total_pumps_allocated": total_pumps_used,
                "total_crews_allocated": total_crews_used,
                "total_budget_allocated": round(total_budget_used, 2),
                "unallocated_pumps": int(max(0, pumps_avail - total_pumps_used)),
                "unallocated_crews": int(max(0, crews_avail - total_crews_used)),
                "unallocated_budget": round(max(0.0, budget_avail - total_budget_used), 2),
                "optimization_method": "or_tools"
            }

        except Exception as exc:
            logger.error("OR-Tools multi-resource allocation error: %s. Using greedy fallback.", str(exc))
            return self._greedy_multi_resource_fallback(zones_list, pumps_avail, crews_avail, budget_avail)

    def _greedy_multi_resource_fallback(self, zones_list, pumps_avail, crews_avail, budget_avail):
        """
        Greedy multi-resource fallback allocation.
        """
        remaining_pumps = int(pumps_avail)
        remaining_crews = int(crews_avail)
        remaining_budget = float(budget_avail)
        total_critical = sum(z["critical_asset_count"] for z in zones_list) or 1

        allocations = []
        for z in zones_list:
            zone_crit = z["critical_asset_count"]
            zone_risk = z["avg_risk_score"]

            if zone_crit > 0 or zone_risk >= 0.5:
                p_share = int(round((zone_crit / total_critical) * pumps_avail)) if total_critical > 0 else 1
                c_share = int(round((zone_crit / total_critical) * crews_avail)) if total_critical > 0 else 1
                p_to_assign = min(remaining_pumps, max(1, p_share)) if remaining_pumps > 0 else 0
                c_to_assign = min(remaining_crews, max(1, c_share)) if remaining_crews > 0 else 0
            else:
                p_to_assign = 0
                c_to_assign = 0

            remaining_pumps -= p_to_assign
            remaining_crews -= c_to_assign

            zone_recs = Recommendation.query.filter(
                Recommendation.status == "pending"
            ).join(Asset).filter(Asset.zone == z["zone"]).all()

            knapsack = self._greedy_knapsack_fallback(zone_recs, remaining_budget)
            zone_budget_spent = knapsack["total_cost"]
            remaining_budget -= zone_budget_spent

            allocations.append({
                "zone": z["zone"],
                "priority_tier": z["highest_priority_tier"],
                "critical_asset_count": z["critical_asset_count"],
                "avg_risk_score": z["avg_risk_score"],
                "pumps_allocated": p_to_assign,
                "crews_allocated": c_to_assign,
                "budget_allocated": round(zone_budget_spent, 2),
                "recommendations_funded": knapsack["selected_recommendations"]
            })

        return {
            "allocations": allocations,
            "total_pumps_allocated": int(pumps_avail - remaining_pumps),
            "total_crews_allocated": int(crews_avail - remaining_crews),
            "total_budget_allocated": round(budget_avail - remaining_budget, 2),
            "unallocated_pumps": int(remaining_pumps),
            "unallocated_crews": int(remaining_crews),
            "unallocated_budget": round(remaining_budget, 2),
            "optimization_method": "greedy_fallback"
        }


# Global singleton instance
optimizer_service = ConstrainedOptimizerService()
