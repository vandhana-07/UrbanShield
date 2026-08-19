"""
UrbanShield - Layer 2: PREDICT
Estimates flood risk probability (risk_score) and prediction uncertainty/confidence (risk_confidence)
for each zone using a scikit-learn RandomForestClassifier.

Trained on a calibrated synthetic dataset whose parameter ranges are anchored to documented
Indian monsoon and urban flood statistics (IMD, CWC, MCGM, KSNDMC, OpenCity.in).
"""

import logging
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

from layers.sense import SenseLayer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("UrbanShield.Predict")

DEFAULT_MODEL_PATH = BASE_DIR / "models" / "flood_rf_model.joblib"
DATASET_PATH = BASE_DIR / "data" / "indian_flood_dataset.csv"
RANDOM_STATE = 42

# Calibrated parameter ranges anchored to documented real-world Indian flood events (see data/SOURCES.md)
CALIBRATION_ANCHORS = {
    "Mumbai": {
        "zones": ["Mithi River Basin", "Kurla West", "Dadar-Hindmata", "Sion Lowlands"],
        # Anchor: Aug 2017 flood recorded 468mm in 12h (MCGM/IMD); baseline IMD monsoon 15-60mm
        "rainfall_min": 15.0,
        "rainfall_max": 468.0,
        "drainage_min": 15.0,  # Constrained outfalls along Mithi River with tidal lock
        "drainage_max": 65.0,
        "pop_density_min": 25000,
        "pop_density_max": 120000,
        "traffic_min": 50.0,
        "traffic_max": 98.0,
        "road_cond_min": 2.0,
        "road_cond_max": 7.0,
        "infra_min": 3,
        "infra_max": 9
    },
    "Chennai": {
        "zones": ["Velachery", "Adyar Basin", "T. Nagar Market", "Tambaram Outfall"],
        # Anchor: Dec 2015 flood recorded 494mm in 24h (OpenCity.in / IMD); baseline 15-70mm
        "rainfall_min": 15.0,
        "rainfall_max": 494.0,
        "drainage_min": 20.0,  # Encroached marshland & canal bottlenecks
        "drainage_max": 70.0,
        "pop_density_min": 20000,
        "pop_density_max": 95000,
        "traffic_min": 40.0,
        "traffic_max": 95.0,
        "road_cond_min": 2.5,
        "road_cond_max": 8.0,
        "infra_min": 2,
        "infra_max": 8
    },
    "Bengaluru": {
        "zones": ["Silk Board", "Bellandur Catchment", "Mahadevapura", "HSR Layout Sector 6"],
        # Anchor: Sept 2022 Bengaluru floods (131.6mm single-day rain, KSNDMC report)
        "rainfall_min": 10.0,
        "rainfall_max": 131.6,
        "drainage_min": 25.0,  # Stormwater drain capacity bottlenecks
        "drainage_max": 80.0,
        "pop_density_min": 15000,
        "pop_density_max": 85000,
        "traffic_min": 60.0,   # Silk Board high congestion baseline
        "traffic_max": 99.0,
        "road_cond_min": 3.0,
        "road_cond_max": 8.5,
        "infra_min": 2,
        "infra_max": 7
    },
    "Kolkata": {
        "zones": ["MG Road", "Central Avenue", "Ultadanga Subway", "Park Street Canal"],
        # Anchor: Sept 2021 Kolkata convective deluge (142mm in 6h, KMC/IMD Alipore)
        "rainfall_min": 15.0,
        "rainfall_max": 142.0,
        "drainage_min": 15.0,  # Heritage lock gate & Hooghly river tidal lock
        "drainage_max": 60.0,
        "pop_density_min": 30000,
        "pop_density_max": 110000,
        "traffic_min": 45.0,
        "traffic_max": 92.0,
        "road_cond_min": 2.0,
        "road_cond_max": 7.5,
        "infra_min": 3,
        "infra_max": 8
    },
    "Delhi": {
        "zones": ["Yamuna Floodplain", "ITO Lowlands", "Minto Bridge Underpass", "Nizamuddin Drain"],
        # Anchor: July 2023 Yamuna inundation (153mm in 24h, CWC Yamuna breach)
        "rainfall_min": 10.0,
        "rainfall_max": 153.0,
        "drainage_min": 20.0,  # Yamuna backflow into city stormwater drains
        "drainage_max": 75.0,
        "pop_density_min": 20000,
        "pop_density_max": 100000,
        "traffic_min": 50.0,
        "traffic_max": 96.0,
        "road_cond_min": 3.0,
        "road_cond_max": 8.0,
        "infra_min": 3,
        "infra_max": 9
    },
    "Hyderabad": {
        "zones": ["Musi River Basin", "Begumpet Nala", "Khairatabad", "Madhapur Catchment"],
        # Anchor: Oct 2020 Musi River flash flood (241mm in 24h, TSDPS/IMD report)
        "rainfall_min": 10.0,
        "rainfall_max": 241.0,
        "drainage_min": 25.0,  # Nala constriction
        "drainage_max": 75.0,
        "pop_density_min": 18000,
        "pop_density_max": 90000,
        "traffic_min": 45.0,
        "traffic_max": 92.0,
        "road_cond_min": 3.5,
        "road_cond_max": 8.0,
        "infra_min": 2,
        "infra_max": 7
    },
    "Kochi": {
        "zones": ["Aluva Periyar Bank", "Kochi MG Road", "Kalamassery Lowlands", "Edappally Canal"],
        # Anchor: Aug 2018/2019 Kerala deluge (Periyar catchment >310mm, KSDMA report)
        "rainfall_min": 25.0,
        "rainfall_max": 310.0,
        "drainage_min": 20.0,  # Coastal lowlands & canal overflow
        "drainage_max": 70.0,
        "pop_density_min": 12000,
        "pop_density_max": 70000,
        "traffic_min": 35.0,
        "traffic_max": 88.0,
        "road_cond_min": 3.0,
        "road_cond_max": 7.5,
        "infra_min": 2,
        "infra_max": 6
    }
}


class PredictLayer:
    def __init__(self, model_path: str = None):
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self.model = None

    def generate_calibrated_flood_data(self, num_samples: int = 1000, random_state: int = RANDOM_STATE) -> pd.DataFrame:
        """
        Generates a synthetic historical flood dataset calibrated against real documented
        Indian monsoon and flood statistics across 7 Indian metropolitan areas.
        """
        np.random.seed(random_state)
        cities = list(CALIBRATION_ANCHORS.keys())
        samples_per_city = int(np.ceil(num_samples / len(cities)))
        
        rows = []
        for city in cities:
            cfg = CALIBRATION_ANCHORS[city]
            for _ in range(samples_per_city):
                zone = np.random.choice(cfg["zones"])
                rainfall = np.random.uniform(cfg["rainfall_min"], cfg["rainfall_max"])
                drainage = np.random.uniform(cfg["drainage_min"], cfg["drainage_max"])
                pop = np.random.randint(cfg["pop_density_min"], cfg["pop_density_max"])
                traffic = np.random.uniform(cfg["traffic_min"], cfg["traffic_max"])
                road_cond = np.random.uniform(cfg["road_cond_min"], cfg["road_cond_max"])
                infra = np.random.randint(cfg["infra_min"], cfg["infra_max"] + 1)
                
                overflow_ratio = rainfall / (drainage + 1e-5)
                road_vulnerability = (10.0 - road_cond) / 10.0
                traffic_norm = traffic / 100.0
                infra_norm = infra / 10.0
                pop_norm = pop / 120000.0
                
                # Physical risk composite score with sensor noise
                noise = np.random.normal(0.0, 0.04)
                raw_score = (
                    0.45 * overflow_ratio +
                    0.20 * road_vulnerability +
                    0.15 * traffic_norm +
                    0.10 * pop_norm +
                    0.10 * infra_norm +
                    noise
                )
                
                # Target classification: 1 if high flood hazard (raw_score >= 0.55), else 0
                target = int(raw_score >= 0.55)
                continuous_risk = float(np.clip(raw_score, 0.05, 0.98))
                
                rows.append({
                    "city": city,
                    "zone": zone,
                    "rainfall_mm": round(rainfall, 2),
                    "drainage_capacity": round(drainage, 2),
                    "population_density": pop,
                    "traffic_index": round(traffic, 2),
                    "road_condition_rating": round(road_cond, 2),
                    "critical_infrastructure_count": infra,
                    "rainfall": round(rainfall, 2),
                    "drainage_capacity_pct": round(drainage, 2),
                    "population": pop,
                    "traffic": round(traffic, 2),
                    "road_condition": round(road_cond, 2),
                    "critical_infrastructure": infra,
                    "drainage_overflow_ratio": round(overflow_ratio, 4),
                    "road_vulnerability": round(road_vulnerability, 4),
                    "flood_risk_score": round(continuous_risk, 4),
                    "flood_risk_target": target,
                    "target": target
                })
                
        df = pd.DataFrame(rows).iloc[:num_samples]
        return df

    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineers required numerical features for model input."""
        features_df = df.copy()
        
        # Standardize column naming if variations exist
        if "rainfall" not in features_df.columns and "rainfall_mm" in features_df.columns:
            features_df["rainfall"] = features_df["rainfall_mm"]
        if "drainage_capacity" not in features_df.columns and "drainage_capacity_pct" in features_df.columns:
            features_df["drainage_capacity"] = features_df["drainage_capacity_pct"]
        if "population" not in features_df.columns and "population_density" in features_df.columns:
            features_df["population"] = features_df["population_density"]
        if "traffic" not in features_df.columns and "traffic_index" in features_df.columns:
            features_df["traffic"] = features_df["traffic_index"]
        if "road_condition" not in features_df.columns and "road_condition_rating" in features_df.columns:
            features_df["road_condition"] = features_df["road_condition_rating"]
        if "critical_infrastructure" not in features_df.columns and "critical_infrastructure_count" in features_df.columns:
            features_df["critical_infrastructure"] = features_df["critical_infrastructure_count"]
            
        features_df["drainage_overflow_ratio"] = features_df["rainfall"] / (features_df["drainage_capacity"] + 1e-5)
        features_df["road_vulnerability"] = (10.0 - features_df["road_condition"]) / 10.0
        
        feature_cols = [
            "rainfall", "drainage_capacity", "population", "traffic",
            "road_condition", "critical_infrastructure",
            "drainage_overflow_ratio", "road_vulnerability"
        ]
        return features_df[feature_cols]

    def train_model(self, num_samples: int = 1000, force_retrain: bool = False) -> RandomForestClassifier:
        """
        Trains and evaluates RandomForestClassifier on calibrated synthetic flood dataset.
        Saves model artifact to self.model_path.
        """
        if self.model_path.exists() and not force_retrain:
            logger.info(f"Loading pre-trained model from {self.model_path}")
            self.model = joblib.load(self.model_path)
            return self.model

        logger.info("Loading/generating calibrated synthetic training dataset and training model...")
        
        # Load from CSV if available, else generate calibrated dataset
        if DATASET_PATH.exists():
            dataset = pd.read_csv(DATASET_PATH)
        else:
            dataset = self.generate_calibrated_flood_data(num_samples=num_samples, random_state=RANDOM_STATE)
            DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
            dataset.to_csv(DATASET_PATH, index=False)
            logger.info(f"Saved calibrated synthetic dataset to: {DATASET_PATH}")
        
        X = self.extract_features(dataset)
        y = dataset["target"] if "target" in dataset.columns else dataset["flood_risk_target"]
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
        )
        
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
        rf.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = rf.predict(X_test)
        y_prob = rf.predict_proba(X_test)[:, 1]
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_prob)
        
        print("\n" + "=" * 60)
        print(" URBANSHIELD LAYER 2 (PREDICT) - MODEL EVALUATION")
        print("=" * 60)
        print(" Model Type       : RandomForestClassifier (n_estimators=100)")
        print(f" Dataset Type     : Calibrated Synthetic Indian Flood Dataset ({len(dataset)} rows)")
        print(f" Random State     : {RANDOM_STATE} (fixed seed)")
        print(f" Train/Test Split : {len(X_train)} train / {len(X_test)} test samples")
        print(f" Accuracy         : {acc:.4f}")
        print(f" Precision        : {prec:.4f}")
        print(f" Recall           : {rec:.4f}")
        print(f" F1-Score         : {f1:.4f}")
        print(f" ROC-AUC          : {roc_auc:.4f}")
        print("=" * 60 + "\n")
        
        # Save model
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(rf, self.model_path)
        logger.info(f"Saved trained Random Forest model to: {self.model_path}")
        self.model = rf
        return self.model

    # Backward compatibility alias
    train_synthetic_model = train_model

    def get_predictions(self, zone_df: pd.DataFrame) -> pd.DataFrame:
        """
        Takes clean zone state DataFrame from Layer 1 (SENSE),
        predicts risk_score (probability of severe flood risk) and risk_confidence.
        
        Returns:
            pd.DataFrame: Original DataFrame enriched with risk_score and risk_confidence.
        """
        if self.model is None:
            if self.model_path.exists():
                self.model = joblib.load(self.model_path)
            else:
                self.train_model(force_retrain=False)
                
        X_infer = self.extract_features(zone_df)
        
        # Probability of high risk class (class 1)
        risk_scores = self.model.predict_proba(X_infer)[:, 1]
        
        # Estimate prediction confidence across decision trees in ensemble
        tree_predictions = np.array([tree.predict_proba(X_infer.values)[:, 1] for tree in self.model.estimators_])
        tree_std_devs = np.std(tree_predictions, axis=0)
        
        # risk_confidence = 1.0 - (2 * std_dev), clamped between 0.0 and 1.0
        risk_confidences = np.clip(1.0 - (2.0 * tree_std_devs), 0.0, 1.0)
        
        res_df = zone_df.copy()
        res_df["risk_score"] = np.round(risk_scores, 4)
        res_df["risk_confidence"] = np.round(risk_confidences, 4)
        
        return res_df


if __name__ == "__main__":
    # Standalone verification runner
    sense = SenseLayer()
    sense.load_csv_to_db()
    zone_state = sense.get_structured_state()
    
    predict_layer = PredictLayer()
    predict_layer.train_model(force_retrain=True)
    
    predictions_df = predict_layer.get_predictions(zone_state)
    
    print("Layer 2 (PREDICT) - Risk Predictions Output:")
    print(predictions_df[["zone_id", "zone_name", "rainfall", "drainage_capacity", "road_condition", "risk_score", "risk_confidence"]].to_string(index=False))
