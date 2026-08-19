"""
UrbanShield Database Seeder
Populates SQLite database with 25 realistic, interconnected urban infrastructure assets,
associated risk assessments, composite priority rankings, and actionable AI recommendations.
"""

from app import create_app
from database import db
from models import Asset, RiskAssessment, PriorityRanking, Recommendation, Simulation, Resource
from services import mock_engine

SAMPLE_ASSETS = [
    # --- BRIDGES ---
    {
        "id": "AST-BRG-001",
        "name": "Harbor Bay Suspension Bridge",
        "category": "bridge",
        "latitude": 37.7983,
        "longitude": -122.3778,
        "zone": "District 1 - Waterfront",
        "year_built": 1974,
        "health_index": 38.5,
        "criticality_score": 9.8,
        "status": "critical",
        "sensor_data": {"vibration_hz": 16.4, "strain_microstrain": 1420, "load_pct": 91.0, "crack_width_mm": 4.2}
    },
    {
        "id": "AST-BRG-002",
        "name": "East River Viaduct Connector",
        "category": "bridge",
        "latitude": 37.7845,
        "longitude": -122.3921,
        "zone": "District 2 - Industrial East",
        "year_built": 1988,
        "health_index": 62.0,
        "criticality_score": 7.5,
        "status": "degraded",
        "sensor_data": {"vibration_hz": 8.2, "strain_microstrain": 780, "load_pct": 74.0}
    },
    {
        "id": "AST-BRG-003",
        "name": "Metro Transit Arch Overpass",
        "category": "bridge",
        "latitude": 37.7692,
        "longitude": -122.4180,
        "zone": "District 3 - Central Corridor",
        "year_built": 2004,
        "health_index": 88.0,
        "criticality_score": 6.8,
        "status": "healthy",
        "sensor_data": {"vibration_hz": 3.1, "strain_microstrain": 310, "load_pct": 52.0}
    },
    {
        "id": "AST-BRG-004",
        "name": "Port Logistics Heavy Rail Bridge",
        "category": "bridge",
        "latitude": 37.7511,
        "longitude": -122.3855,
        "zone": "District 5 - Port & Freight",
        "year_built": 1969,
        "health_index": 44.0,
        "criticality_score": 8.9,
        "status": "critical",
        "sensor_data": {"vibration_hz": 14.8, "strain_microstrain": 1280, "load_pct": 88.5}
    },

    # --- POWER GRID ---
    {
        "id": "AST-PWR-001",
        "name": "Midtown 230kV Main Transmission Substation",
        "category": "power",
        "latitude": 37.7761,
        "longitude": -122.4152,
        "zone": "District 3 - Central Corridor",
        "year_built": 1982,
        "health_index": 41.0,
        "criticality_score": 9.6,
        "status": "critical",
        "sensor_data": {"temp_celsius": 84.5, "load_pct": 94.2, "oil_pressure_psi": 42.0, "harmonic_distortion_pct": 6.4}
    },
    {
        "id": "AST-PWR-002",
        "name": "Bayside Industrial Substation 4B",
        "category": "power",
        "latitude": 37.7588,
        "longitude": -122.3890,
        "zone": "District 5 - Port & Freight",
        "year_built": 1995,
        "health_index": 67.5,
        "criticality_score": 8.0,
        "status": "degraded",
        "sensor_data": {"temp_celsius": 61.0, "load_pct": 76.0, "oil_pressure_psi": 52.0}
    },
    {
        "id": "AST-PWR-003",
        "name": "North Hills Renewable Solar Intertie Hub",
        "category": "power",
        "latitude": 37.8020,
        "longitude": -122.4285,
        "zone": "District 4 - North Hills",
        "year_built": 2016,
        "health_index": 92.5,
        "criticality_score": 6.0,
        "status": "healthy",
        "sensor_data": {"temp_celsius": 39.0, "load_pct": 48.0, "oil_pressure_psi": 58.0}
    },
    {
        "id": "AST-PWR-004",
        "name": "Civic Center Auxiliary Power Bank",
        "category": "power",
        "latitude": 37.7810,
        "longitude": -122.4160,
        "zone": "District 3 - Central Corridor",
        "year_built": 2001,
        "health_index": 73.0,
        "criticality_score": 7.8,
        "status": "degraded",
        "sensor_data": {"temp_celsius": 55.0, "load_pct": 68.0}
    },

    # --- DRAINAGE & FLOOD CONTROL ---
    {
        "id": "AST-DRN-001",
        "name": "Lower River Levee & Sea Dike 7",
        "category": "drainage",
        "latitude": 37.7915,
        "longitude": -122.3810,
        "zone": "District 1 - Waterfront",
        "year_built": 1965,
        "health_index": 35.0,
        "criticality_score": 9.5,
        "status": "critical",
        "sensor_data": {"water_level_pct": 89.0, "seepage_flow_lps": 34.5, "tilt_degrees": 1.8}
    },
    {
        "id": "AST-DRN-002",
        "name": "Downtown Stormwater Siphon 4",
        "category": "drainage",
        "latitude": 37.7880,
        "longitude": -122.4010,
        "zone": "District 1 - Waterfront",
        "year_built": 1978,
        "health_index": 52.0,
        "criticality_score": 8.7,
        "status": "degraded",
        "sensor_data": {"silt_blockage_pct": 68.0, "flow_capacity_pct": 45.0}
    },
    {
        "id": "AST-DRN-003",
        "name": "North Basin Dual Spillway & Sluice Gate",
        "category": "drainage",
        "latitude": 37.8060,
        "longitude": -122.4350,
        "zone": "District 4 - North Hills",
        "year_built": 2011,
        "health_index": 86.0,
        "criticality_score": 7.2,
        "status": "healthy",
        "sensor_data": {"water_level_pct": 34.0, "gate_actuator_health": "nominal"}
    },
    {
        "id": "AST-DRN-004",
        "name": "South Bay Regional Retention Lagoon",
        "category": "drainage",
        "latitude": 37.7420,
        "longitude": -122.3950,
        "zone": "District 5 - Port & Freight",
        "year_built": 1999,
        "health_index": 71.0,
        "criticality_score": 8.1,
        "status": "degraded",
        "sensor_data": {"sediment_depth_m": 2.4, "capacity_available_pct": 58.0}
    },

    # --- WATER INFRASTRUCTURE ---
    {
        "id": "AST-WTR-001",
        "name": "Central Metro Water Treatment Plant Alpha",
        "category": "water",
        "latitude": 37.7650,
        "longitude": -122.4300,
        "zone": "District 3 - Central Corridor",
        "year_built": 1985,
        "health_index": 48.0,
        "criticality_score": 9.7,
        "status": "critical",
        "sensor_data": {"turbidity_ntu": 4.8, "pressure_psi": 142.0, "chlorine_residual_ppm": 1.2}
    },
    {
        "id": "AST-WTR-002",
        "name": "High-Elevation Twin Reservoirs & Booster Station",
        "category": "water",
        "latitude": 37.7550,
        "longitude": -122.4450,
        "zone": "District 4 - North Hills",
        "year_built": 1992,
        "health_index": 68.0,
        "criticality_score": 8.4,
        "status": "degraded",
        "sensor_data": {"pump_vibration_hz": 7.4, "storage_level_pct": 82.0}
    },
    {
        "id": "AST-WTR-003",
        "name": "Harbor Water Main 48-Inch Feeder Line",
        "category": "water",
        "latitude": 37.7940,
        "longitude": -122.3960,
        "zone": "District 1 - Waterfront",
        "year_built": 1971,
        "health_index": 40.5,
        "criticality_score": 9.1,
        "status": "critical",
        "sensor_data": {"acoustic_leak_db": 68.0, "flow_rate_gpm": 18400, "corrosion_rate_mpy": 8.2}
    },
    {
        "id": "AST-WTR-004",
        "name": "Sunset District Automated Desalination Auxiliary",
        "category": "water",
        "latitude": 37.7620,
        "longitude": -122.4810,
        "zone": "District 6 - West End",
        "year_built": 2018,
        "health_index": 94.0,
        "criticality_score": 6.5,
        "status": "healthy",
        "sensor_data": {"membrane_diff_pressure_psi": 12.0, "salinity_ppm": 180}
    },

    # --- ROAD NETWORK ---
    {
        "id": "AST-RD-001",
        "name": "Coastal Highway 101 Causeway Segment",
        "category": "road",
        "latitude": 37.8010,
        "longitude": -122.4080,
        "zone": "District 1 - Waterfront",
        "year_built": 1980,
        "health_index": 56.0,
        "criticality_score": 8.8,
        "status": "degraded",
        "sensor_data": {"rutting_depth_mm": 24.0, "traffic_volume_vph": 4800, "subgrade_moisture_pct": 28.0}
    },
    {
        "id": "AST-RD-002",
        "name": "Metro Expressway Tunnel & Ventilation Shafts",
        "category": "road",
        "latitude": 37.7720,
        "longitude": -122.4220,
        "zone": "District 3 - Central Corridor",
        "year_built": 1994,
        "health_index": 64.0,
        "criticality_score": 8.5,
        "status": "degraded",
        "sensor_data": {"co2_ppm": 640, "structural_seepage_lpm": 8.2, "fan_vibration_hz": 5.8}
    },
    {
        "id": "AST-RD-003",
        "name": "Grand Boulevard Rapid Bus Dedicated Way",
        "category": "road",
        "latitude": 37.7850,
        "longitude": -122.4120,
        "zone": "District 3 - Central Corridor",
        "year_built": 2014,
        "health_index": 89.0,
        "criticality_score": 6.2,
        "status": "healthy",
        "sensor_data": {"surface_friction_sn": 62, "daily_transit_trips": 42000}
    },
    {
        "id": "AST-RD-004",
        "name": "Industrial Port Heavy Haul Access Highway",
        "category": "road",
        "latitude": 37.7470,
        "longitude": -122.3890,
        "zone": "District 5 - Port & Freight",
        "year_built": 1983,
        "health_index": 45.0,
        "criticality_score": 7.9,
        "status": "degraded",
        "sensor_data": {"axle_load_violations": 142, "pothole_density_sqm": 8.5}
    },

    # --- PUBLIC BUILDINGS & CRITICAL FACILITIES ---
    {
        "id": "AST-BLD-001",
        "name": "Metro City Emergency Operations Center (EOC)",
        "category": "public_building",
        "latitude": 37.7780,
        "longitude": -122.4190,
        "zone": "District 3 - Central Corridor",
        "year_built": 2008,
        "health_index": 91.0,
        "criticality_score": 9.9,
        "status": "healthy",
        "sensor_data": {"seismic_drift_ratio": 0.002, "backup_generator_fuel_hrs": 72}
    },
    {
        "id": "AST-BLD-002",
        "name": "General Trauma & Regional Medical Center",
        "category": "public_building",
        "latitude": 37.7570,
        "longitude": -122.4050,
        "zone": "District 2 - Industrial East",
        "year_built": 1976,
        "health_index": 54.0,
        "criticality_score": 9.7,
        "status": "degraded",
        "sensor_data": {"structural_settlement_mm": 18.2, "hvac_differential_pa": 45}
    },
    {
        "id": "AST-BLD-003",
        "name": "Central Railway Union Terminal & Dispatch",
        "category": "public_building",
        "latitude": 37.7750,
        "longitude": -122.3980,
        "zone": "District 1 - Waterfront",
        "year_built": 1968,
        "health_index": 42.0,
        "criticality_score": 8.9,
        "status": "critical",
        "sensor_data": {"roof_truss_deflection_mm": 32.0, "passenger_throughput_daily": 85000}
    },
    {
        "id": "AST-BLD-004",
        "name": "Coastal Marine Fire & Rescue Station 1",
        "category": "public_building",
        "latitude": 37.8040,
        "longitude": -122.4110,
        "zone": "District 1 - Waterfront",
        "year_built": 1996,
        "health_index": 78.0,
        "criticality_score": 8.2,
        "status": "healthy",
        "sensor_data": {"pier_pile_corrosion_pct": 14.0, "boat_slip_depth_m": 5.4}
    },
    {
        "id": "AST-BLD-005",
        "name": "West District Secondary Telecom Switching Center",
        "category": "public_building",
        "latitude": 37.7680,
        "longitude": -122.4650,
        "zone": "District 6 - West End",
        "year_built": 2002,
        "health_index": 82.0,
        "criticality_score": 7.6,
        "status": "healthy",
        "sensor_data": {"optical_signal_dbm": -12.4, "battery_backup_capacity_pct": 98.0}
    }
]


def seed_database():
    app = create_app()
    with app.app_context():
        print("Resetting and creating database tables...")
        db.drop_all()
        db.create_all()

        print(f"Seeding {len(SAMPLE_ASSETS)} infrastructure assets...")
        created_assets = []
        for raw in SAMPLE_ASSETS:
            asset = Asset(
                id=raw["id"],
                name=raw["name"],
                category=raw["category"],
                latitude=raw["latitude"],
                longitude=raw["longitude"],
                zone=raw["zone"],
                year_built=raw["year_built"],
                health_index=raw["health_index"],
                criticality_score=raw["criticality_score"],
                status=raw["status"],
                sensor_data=raw["sensor_data"]
            )
            db.session.add(asset)
            created_assets.append(asset)

        db.session.flush()

        print("Computing mock risk assessments and priority scores...")
        scored_items = []
        for asset in created_assets:
            risk_dict = mock_engine.calculate_risk_assessment(asset, source="mock")
            risk_obj = RiskAssessment(
                asset_id=asset.id,
                risk_score=risk_dict["risk_score"],
                failure_probability=risk_dict["failure_probability"],
                consequence_level=risk_dict["consequence_level"],
                primary_hazard=risk_dict["primary_hazard"],
                predicted_days_to_failure=risk_dict["predicted_days_to_failure"],
                confidence_score=risk_dict["confidence_score"],
                source="mock"
            )
            db.session.add(risk_obj)

            priority_dict = mock_engine.calculate_priority_ranking(asset, risk_dict, source="mock")
            scored_items.append((asset, risk_dict, priority_dict))

            # Recommendations
            recs = mock_engine.generate_recommendations_for_asset(asset, risk_dict, source="mock")
            for r in recs:
                rec_obj = Recommendation(
                    asset_id=asset.id,
                    action_type=r["action_type"],
                    title=r["title"],
                    description=r["description"],
                    estimated_cost=r["estimated_cost"],
                    expected_risk_reduction_pct=r["expected_risk_reduction_pct"],
                    status=r["status"],
                    tradeoff_analysis=r["tradeoff_analysis"],
                    source="mock"
                )
                db.session.add(rec_obj)

        # Sort priority rankings by urgency score descending to assign ranks 1..N
        scored_items.sort(key=lambda x: x[2]["composite_urgency_score"], reverse=True)
        for rank_idx, (asset, risk_dict, priority_dict) in enumerate(scored_items, start=1):
            p_obj = PriorityRanking(
                asset_id=asset.id,
                rank=rank_idx,
                priority_tier=priority_dict["priority_tier"],
                composite_urgency_score=priority_dict["composite_urgency_score"],
                estimated_population_impact=priority_dict["estimated_population_impact"],
                estimated_economic_exposure=priority_dict["estimated_economic_exposure"],
                source="mock"
            )
            db.session.add(p_obj)

        # Seed an initial sample simulation
        print("Seeding baseline simulation scenario...")
        sample_sim = mock_engine.simulate_scenario(
            name="100-Year Coastal Flood & Storm Surge",
            hazard_type="flood",
            intensity=0.85,
            selected_interventions=[
                {"asset_id": "AST-DRN-001", "action": "auxiliary_sluice_activation"},
                {"asset_id": "AST-BRG-001", "action": "emergency_pier_reinforcement"}
            ],
            budget_limit=1500000.0,
            assets=created_assets,
            source="mock"
        )
        sim_record = Simulation(
            id=sample_sim["simulation_id"],
            name=sample_sim["name"],
            hazard_type=sample_sim["hazard_type"],
            input_parameters={"intensity": 0.85, "hazard_type": "flood"},
            selected_interventions=sample_sim["selected_interventions"],
            budget_limit=1500000.0,
            baseline_metrics=sample_sim["baseline_metrics"],
            simulated_metrics=sample_sim["simulated_metrics"],
            net_benefit=sample_sim["net_benefit"],
            cascade_analysis=sample_sim["cascade_analysis"],
            status="completed",
            source="mock"
        )
        db.session.add(sim_record)

        # Seed emergency resource pools
        print("Seeding emergency resource pools...")
        resources = [
            Resource(resource_type="pump", total_quantity=25.0, allocated_quantity=0.0),
            Resource(resource_type="crew", total_quantity=18.0, allocated_quantity=0.0),
            Resource(resource_type="budget_usd", total_quantity=3500000.0, allocated_quantity=0.0)
        ]
        for r in resources:
            db.session.add(r)

        db.session.commit()
        print("Database seeded successfully with 25 assets, 25 risks, 25 priorities, 25 recommendations, 1 simulation, and 3 resource pools!")


if __name__ == "__main__":
    seed_database()
