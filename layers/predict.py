"""
UrbanShield - Layer 2: PREDICT
Estimates flood risk probability (risk_score) and prediction uncertainty/confidence (risk_confidence)
for each zone using a scikit-learn RandomForestClassifier.
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

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = BASE_DIR / "models" / "flood_rf_model.joblib"
RANDOM_STATE = 42


class PredictLayer:
    def __init__(self, model_path: str = None):
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self.model = None

    def generate_synthetic_data(self, num_samples: int = 1000, random_state: int = RANDOM_STATE) -> pd.DataFrame:
        """
        Generates a synthetic historical flood dataset based on physical flood risk formulas
        and environmental noise for training and evaluating the Random Forest model.
        """
        np.random.seed(random_state)
        
        rainfall = np.random.uniform(10.0, 200.0, num_samples)
        drainage_capacity = np.random.uniform(20.0, 100.0, num_samples)
        population = np.random.randint(5000, 100000, num_samples)
        traffic = np.random.uniform(10.0, 100.0, num_samples)
        road_condition = np.random.uniform(1.0, 10.0, num_samples)
        critical_infra = np.random.randint(0, 10, num_samples)
        
        overflow_ratio = rainfall / (drainage_capacity + 1e-5)
        road_vulnerability = (10.0 - road_condition) / 10.0
        traffic_norm = traffic / 100.0
        infra_norm = critical_infra / 10.0
        
        # Physical formula + Gaussian noise
        noise = np.random.normal(0.0, 0.05, num_samples)
        raw_score = 0.50 * overflow_ratio + 0.20 * road_vulnerability + 0.15 * traffic_norm + 0.15 * infra_norm + noise
        
        # Target label: 1 if high risk (raw_score >= 0.55), else 0
        target = (raw_score >= 0.55).astype(int)
        
        df = pd.DataFrame({
            "rainfall": rainfall,
            "drainage_capacity": drainage_capacity,
            "population": population,
            "traffic": traffic,
            "road_condition": road_condition,
            "critical_infrastructure": critical_infra,
            "drainage_overflow_ratio": overflow_ratio,
            "road_vulnerability": road_vulnerability,
            "target": target
        })
        return df

    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineers required numerical features for model input."""
        features_df = df.copy()
        features_df["drainage_overflow_ratio"] = features_df["rainfall"] / (features_df["drainage_capacity"] + 1e-5)
        features_df["road_vulnerability"] = (10.0 - features_df["road_condition"]) / 10.0
        
        feature_cols = [
            "rainfall", "drainage_capacity", "population", "traffic",
            "road_condition", "critical_infrastructure",
            "drainage_overflow_ratio", "road_vulnerability"
        ]
        return features_df[feature_cols]

    def train_synthetic_model(self, num_samples: int = 1000, force_retrain: bool = False) -> RandomForestClassifier:
        """
        Trains and evaluates RandomForestClassifier on synthetic historical flood dataset.
        Saves model artifact to self.model_path.
        """
        if self.model_path.exists() and not force_retrain:
            logger.info("Loading pre-trained model from models/flood_rf_model.joblib")
            self.model = joblib.load(self.model_path)
            return self.model

        logger.info("Generating synthetic training dataset and training model...")
        dataset = self.generate_synthetic_data(num_samples=num_samples, random_state=RANDOM_STATE)
        
        feature_cols = [
            "rainfall", "drainage_capacity", "population", "traffic",
            "road_condition", "critical_infrastructure",
            "drainage_overflow_ratio", "road_vulnerability"
        ]
        X = dataset[feature_cols]
        y = dataset["target"]
        
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
        print(f" Model Type       : RandomForestClassifier (n_estimators=100)")
        print(f" Random State     : {RANDOM_STATE} (fixed seed)")
        print(f" Train/Test Split : 800 train / 200 test samples")
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
                self.train_synthetic_model(force_retrain=False)
                
        X_infer = self.extract_features(zone_df)
        
        # Probability of high risk class (class 1)
        risk_scores = self.model.predict_proba(X_infer)[:, 1]
        
        # Estimate prediction confidence across decision trees in ensemble
        # Calculate standard deviation of tree predictions for each zone sample
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
    # Checks if pre-trained model exists; loads cached artifact or trains if missing
    predict_layer.train_synthetic_model(force_retrain=False)
    
    predictions_df = predict_layer.get_predictions(zone_state)
    
    print("Layer 2 (PREDICT) - Risk Predictions Output:")
    print(predictions_df[["zone_id", "zone_name", "rainfall", "drainage_capacity", "road_condition", "risk_score", "risk_confidence"]].to_string(index=False))
