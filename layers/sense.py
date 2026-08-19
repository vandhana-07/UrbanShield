"""
UrbanShield - Layer 1: SENSE
Loads zone data from CSV, validates schema and value ranges, handles missing data explicitly,
persists valid records to SQLite (data/urbanshield.db), and outputs clean structured zone state.
"""

from datetime import datetime
import logging
import sqlite3
from pathlib import Path
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("UrbanShield.Sense")

# Default relative paths anchored to the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CSV_PATH = BASE_DIR / "data" / "zones.csv"
DEFAULT_DB_PATH = BASE_DIR / "data" / "urbanshield.db"


class SenseLayer:
    def __init__(self, csv_path: str = None, db_path: str = None):
        self.csv_path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH

    def _init_db(self, conn: sqlite3.Connection):
        """Creates the zones table if it does not exist."""
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zones (
                zone_id TEXT PRIMARY KEY,
                zone_name TEXT NOT NULL,
                rainfall REAL NOT NULL,
                drainage_capacity REAL NOT NULL,
                population INTEGER NOT NULL,
                traffic REAL NOT NULL,
                road_condition REAL NOT NULL,
                critical_infrastructure INTEGER NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

    def load_csv_to_db(self) -> pd.DataFrame:
        """
        Idempotently loads and validates CSV zone data into SQLite database.
        Clears existing records before inserting to guarantee clean state.
        
        Returns:
            pd.DataFrame: Validated records that were successfully loaded into SQLite.
        """
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Source CSV not found at: {self.csv_path}")

        # Ensure target database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Read raw CSV
        raw_df = pd.read_csv(self.csv_path)
        total_rows = len(raw_df)

        valid_rows = []
        dropped_summary = []

        # Required columns check
        required_cols = [
            "zone_id", "zone_name", "rainfall", "drainage_capacity",
            "population", "traffic", "road_condition",
            "critical_infrastructure", "latitude", "longitude"
        ]

        for col in required_cols:
            if col not in raw_df.columns:
                raise ValueError(f"Missing required column in CSV: {col}")

        # Validate row by row
        for idx, row in raw_df.iterrows():
            zone_id = str(row["zone_id"]).strip() if pd.notna(row["zone_id"]) else f"ROW_{idx}"
            reasons = []

            # 1. Check required non-null fields
            for key_field in ["rainfall", "drainage_capacity", "population", "road_condition", "latitude", "longitude"]:
                if pd.isna(row[key_field]) or str(row[key_field]).strip() == "":
                    reasons.append(f"Missing or null value in required field '{key_field}'")

            # Skip range checks if crucial values are missing
            if reasons:
                logger.warning(f"[Zone {zone_id}] REJECTED -> {'; '.join(reasons)}")
                dropped_summary.append((zone_id, "; ".join(reasons)))
                continue

            # 2. Convert and validate data types & numerical ranges
            try:
                rainfall = float(row["rainfall"])
                drainage_capacity = float(row["drainage_capacity"])
                population = int(float(row["population"]))
                traffic = float(row["traffic"]) if pd.notna(row["traffic"]) else 0.0
                road_condition = float(row["road_condition"])
                critical_infra = int(float(row["critical_infrastructure"])) if pd.notna(row["critical_infrastructure"]) else 0
                lat = float(row["latitude"])
                lon = float(row["longitude"])
            except (ValueError, TypeError) as e:
                reasons.append(f"Data type conversion error: {str(e)}")
                logger.warning(f"[Zone {zone_id}] REJECTED -> {'; '.join(reasons)}")
                dropped_summary.append((zone_id, "; ".join(reasons)))
                continue

            # Range Checks
            if rainfall < 0:
                reasons.append(f"Invalid rainfall: {rainfall} (must be >= 0)")
            if drainage_capacity <= 0:
                reasons.append(f"Invalid drainage_capacity: {drainage_capacity} (must be > 0)")
            if population < 0:
                reasons.append(f"Invalid population: {population} (must be >= 0)")
            if not (0.0 <= traffic <= 100.0):
                reasons.append(f"Invalid traffic index: {traffic} (must be between 0 and 100)")
            if not (1.0 <= road_condition <= 10.0):
                reasons.append(f"Invalid road_condition: {road_condition} (must be between 1.0 and 10.0)")

            if reasons:
                logger.warning(f"[Zone {zone_id}] REJECTED -> {'; '.join(reasons)}")
                dropped_summary.append((zone_id, "; ".join(reasons)))
                continue

            # Row is valid
            valid_rows.append({
                "zone_id": zone_id,
                "zone_name": str(row["zone_name"]).strip(),
                "rainfall": rainfall,
                "drainage_capacity": drainage_capacity,
                "population": population,
                "traffic": traffic,
                "road_condition": road_condition,
                "critical_infrastructure": critical_infra,
                "latitude": lat,
                "longitude": lon
            })

        valid_df = pd.DataFrame(valid_rows)

        # Idempotently update SQLite database
        with sqlite3.connect(self.db_path) as conn:
            self._init_db(conn)
            cursor = conn.cursor()
            
            # 1. Clear existing table to guarantee zero duplicate or stale rows on re-runs
            cursor.execute("DELETE FROM zones;")
            
            # 2. Insert fresh valid records with explicit current timestamp
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for item in valid_rows:
                cursor.execute("""
                    INSERT INTO zones (
                        zone_id, zone_name, rainfall, drainage_capacity, population,
                        traffic, road_condition, critical_infrastructure, latitude, longitude, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    item["zone_id"], item["zone_name"], item["rainfall"],
                    item["drainage_capacity"], item["population"], item["traffic"],
                    item["road_condition"], item["critical_infrastructure"],
                    item["latitude"], item["longitude"], current_time
                ))
            conn.commit()

        # Print execution summary
        print("\n" + "=" * 60)
        print(" URBANSHIELD LAYER 1 (SENSE) - INGESTION SUMMARY")
        print("=" * 60)
        print(f" Source CSV         : {self.csv_path}")
        print(f" Target Database    : {self.db_path}")
        print(f" Total Rows Read    : {total_rows}")
        print(f" Valid Rows Loaded  : {len(valid_rows)}")
        print(f" Rows Dropped       : {len(dropped_summary)}")

        if dropped_summary:
            print("\nDropped Rows Details:")
            for zid, reason in dropped_summary:
                print(f" - Zone [{zid}]: {reason}")
        print("=" * 60 + "\n")

        return valid_df

    def get_structured_state(self) -> pd.DataFrame:
        """
        Queries SQLite database and returns the clean active zone state.
        
        Returns:
            pd.DataFrame: Active zone records stored in SQLite.
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file does not exist: {self.db_path}. Run load_csv_to_db() first.")

        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT zone_id, zone_name, rainfall, drainage_capacity, population,
                       traffic, road_condition, critical_infrastructure, latitude, longitude, updated_at
                FROM zones
                ORDER BY zone_id ASC;
            """
            df = pd.read_sql_query(query, conn)

        return df


if __name__ == "__main__":
    # Standalone verification runner
    sense = SenseLayer()
    sense.load_csv_to_db()
    structured_state = sense.get_structured_state()
    print("Structured Zone State Output:")
    print(structured_state.to_string(index=False))
