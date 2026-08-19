import datetime
from database import db

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.String(64), primary_key=True)  # e.g., AST-BRG-001
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(64), nullable=False, index=True)  # bridge, road, drainage, water, power, public_building
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    zone = db.Column(db.String(128), nullable=False, index=True)
    year_built = db.Column(db.Integer, nullable=False)
    health_index = db.Column(db.Float, nullable=False, default=100.0)  # 0.0 to 100.0
    criticality_score = db.Column(db.Float, nullable=False, default=5.0)  # 1.0 to 10.0
    status = db.Column(db.String(32), nullable=False, default="healthy", index=True)  # healthy, degraded, critical
    sensor_data = db.Column(db.JSON, nullable=True, default=dict)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    risks = db.relationship("RiskAssessment", backref="asset", cascade="all, delete-orphan", lazy="dynamic")
    priorities = db.relationship("PriorityRanking", backref="asset", cascade="all, delete-orphan", lazy="dynamic")
    recommendations = db.relationship("Recommendation", backref="asset", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self, include_relations=False):
        data = {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "zone": self.zone,
            "year_built": self.year_built,
            "health_index": round(self.health_index, 1),
            "criticality_score": round(self.criticality_score, 1),
            "status": self.status,
            "sensor_data": self.sensor_data or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_relations:
            latest_risk = self.risks.order_by(RiskAssessment.assessed_at.desc()).first()
            data["latest_risk"] = latest_risk.to_dict() if latest_risk else None
            data["recommendations"] = [r.to_dict() for r in self.recommendations.all()]
        return data


class RiskAssessment(db.Model):
    __tablename__ = "risk_assessments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_id = db.Column(db.String(64), db.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_score = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    failure_probability = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    consequence_level = db.Column(db.String(32), nullable=False)  # low, medium, high, catastrophic
    primary_hazard = db.Column(db.String(128), nullable=False)
    predicted_days_to_failure = db.Column(db.Integer, nullable=False)
    confidence_score = db.Column(db.Float, nullable=False, default=0.85)
    source = db.Column(db.String(32), nullable=False, default="mock")  # mock, agent, mock_fallback
    assessed_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "asset_name": self.asset.name if self.asset else None,
            "asset_category": self.asset.category if self.asset else None,
            "risk_score": round(self.risk_score, 3),
            "failure_probability": round(self.failure_probability, 3),
            "consequence_level": self.consequence_level,
            "primary_hazard": self.primary_hazard,
            "predicted_days_to_failure": self.predicted_days_to_failure,
            "confidence_score": round(self.confidence_score, 2),
            "source": self.source,
            "assessed_at": self.assessed_at.isoformat() if self.assessed_at else None,
        }


class PriorityRanking(db.Model):
    __tablename__ = "priority_rankings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_id = db.Column(db.String(64), db.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    rank = db.Column(db.Integer, nullable=False)
    priority_tier = db.Column(db.String(32), nullable=False)  # P1_URGENT, P2_HIGH, P3_MEDIUM, P4_LOW
    composite_urgency_score = db.Column(db.Float, nullable=False)  # 0.0 to 100.0
    estimated_population_impact = db.Column(db.Integer, nullable=False)
    estimated_economic_exposure = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(32), nullable=False, default="mock")
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        score_val = round(self.composite_urgency_score, 1)
        # 0-1 scale priority_score for UI
        norm_score = round(self.composite_urgency_score / 100.0, 4) if self.composite_urgency_score > 1.0 else round(self.composite_urgency_score, 4)
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "asset_name": self.asset.name if self.asset else None,
            "asset_category": self.asset.category if self.asset else None,
            "rank": self.rank,
            "priority_tier": self.priority_tier,
            "composite_urgency_score": score_val,
            "priority_score": norm_score,
            "primary_reason": f"MCDA Rank #{self.rank} ({self.priority_tier})",
            "estimated_population_impact": self.estimated_population_impact,
            "estimated_economic_exposure": round(self.estimated_economic_exposure, 2),
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Recommendation(db.Model):
    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_id = db.Column(db.String(64), db.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = db.Column(db.String(64), nullable=False)  # structural_retrofit, emergency_closure, sensor_audit, power_rerouting
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    estimated_cost = db.Column(db.Float, nullable=False)
    expected_risk_reduction_pct = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(32), nullable=False, default="pending", index=True)  # pending, approved, rejected, in_progress
    tradeoff_analysis = db.Column(db.JSON, nullable=True, default=dict)
    source = db.Column(db.String(32), nullable=False, default="mock")
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "asset_name": self.asset.name if self.asset else None,
            "action_type": self.action_type,
            "action": self.action_type,
            "title": self.title,
            "description": self.description,
            "executive_summary": self.description,
            "estimated_cost": round(self.estimated_cost, 2),
            "expected_risk_reduction_pct": round(self.expected_risk_reduction_pct, 1),
            "status": self.status,
            "tradeoff_analysis": self.tradeoff_analysis or {},
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Simulation(db.Model):
    __tablename__ = "simulations"

    id = db.Column(db.String(64), primary_key=True)  # e.g., SIM-2026-9041
    name = db.Column(db.String(255), nullable=False)
    hazard_type = db.Column(db.String(64), nullable=False)  # flood, earthquake, power_outage, extreme_heat
    input_parameters = db.Column(db.JSON, nullable=False, default=dict)
    selected_interventions = db.Column(db.JSON, nullable=False, default=list)
    budget_limit = db.Column(db.Float, nullable=False, default=0.0)
    baseline_metrics = db.Column(db.JSON, nullable=False, default=dict)
    simulated_metrics = db.Column(db.JSON, nullable=False, default=dict)
    net_benefit = db.Column(db.JSON, nullable=False, default=dict)
    cascade_analysis = db.Column(db.JSON, nullable=False, default=list)
    status = db.Column(db.String(32), nullable=False, default="completed")
    source = db.Column(db.String(32), nullable=False, default="mock")
    executed_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "simulation_id": self.id,
            "name": self.name,
            "hazard_type": self.hazard_type,
            "input_parameters": self.input_parameters or {},
            "selected_interventions": self.selected_interventions or [],
            "budget_limit": round(self.budget_limit, 2),
            "baseline_metrics": self.baseline_metrics or {},
            "simulated_metrics": self.simulated_metrics or {},
            "net_benefit": self.net_benefit or {},
            "cascade_analysis": self.cascade_analysis or [],
            "status": self.status,
            "source": self.source,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


class Resource(db.Model):
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resource_type = db.Column(db.String(64), nullable=False, unique=True)  # e.g., "pump", "crew", "budget_usd"
    total_quantity = db.Column(db.Float, nullable=False, default=0.0)
    allocated_quantity = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "resource_type": self.resource_type,
            "total_quantity": round(self.total_quantity, 2),
            "allocated_quantity": round(self.allocated_quantity, 2),
            "available_quantity": round(max(0.0, self.total_quantity - self.allocated_quantity), 2),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
