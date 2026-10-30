import os
import time
import uuid
from datetime import datetime, timezone
import pandas as pd

STAGING_DIR = "raw_data"
TRANSFORMED_DIR = "transformed"
LOGS_DIR = "logs"
LOG_FILE_PATH = os.path.join(LOGS_DIR, "transformation.log")

REQUIRED_SCHEMA = {
    "sale": ["id", "fuel_id", "sold_at", "liters_sold", "total_amount", "attendant_name"],
    "oil_sale": ["id", "oil_product_id", "sold_at", "quantity", "total_amount", "attendant_name"],
    "fuel": ["id", "name"],
    "oil_product": ["id", "brand", "name", "cost"],
    "fuel_sale_batch": ["sale_id", "batch_id", "liters_consumed"],
    "fuel_batch": ["id", "fuel_id", "cost_per_liter"],
    "expense": ["id", "amount", "category", "expense_date"]
}

PRIMARY_KEYS = {
    "sale": "id",
    "oil_sale": "id",
    "fuel": "id",
    "oil_product": "id",
    "fuel_sale_batch": "sale_id",
    "fuel_batch": "id",
    "expense": "id"
}

def log_transformation_audit(report_data: dict):
    """Appends a structured 12-field transformation audit report to logs/transformation.log."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    log_entry = (
        f"--------------------------------------------------\n"
        f"Pipeline Run ID      : {report_data['run_id']}\n"
        f"File Name            : {report_data['file_name']}\n"
        f"Start Timestamp      : {report_data['start_time']}\n"
        f"End Timestamp        : {report_data['end_time']}\n"
        f"Status               : {report_data['status']}\n"
        f"Raw Staged Records   : {report_data['raw_records']}\n"
        f"Filtered Records     : {report_data['filtered_records']}\n"
        f"Rejected/Null Rows   : {report_data['rejected_records']}\n"
        f"Columns Fetched      : {report_data['columns_fetched']}\n"
        f"Validation Results   : {report_data['validation_results']}\n"
        f"Error Message        : {report_data['error_message']}\n"
        f"Duration (sec)       : {report_data['duration_seconds']:.2f}\n"
        f"--------------------------------------------------\n\n"
    )
    
    with open(LOG_FILE_PATH, "a") as f:
        f.write(log_entry)

def transform_fetch_and_filter():
    """Reads staged CSVs, verifies schema completeness, retains required columns,

    cleans null identifier rows, and exports staged data for aggregate logic.

    """
    os.makedirs(TRANSFORMED_DIR, exist_ok=True)
    run_id = f"TRNS-{uuid.uuid4().hex[:8].upper()}"
    
    print(f"\n==================================================")
    print(f"[{datetime.now(timezone.utc).isoformat()}] STARTING TRANSFORMATION FETCH RUN: {run_id}")
    print(f"==================================================")

    for table_name, target_columns in REQUIRED_SCHEMA.items():
        start_dt = datetime.now(timezone.utc)
        file_name = f"{table_name}.csv"
        csv_path = os.path.join(STAGING_DIR, file_name)
        
        report = {
            "run_id": run_id,
            "file_name": file_name,
            "start_time": start_dt.isoformat(),
            "end_time": "",
            "status": "FAILED",
            "raw_records": 0,
            "filtered_records": 0,
            "rejected_records": 0,
            "columns_fetched": "None",
            "validation_results": "PENDING",
            "error_message": "None",
            "duration_seconds": 0.0
        }

        try:
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"Staged file '{csv_path}' not found. Run extraction step first.")
            
            df_raw = pd.read_csv(csv_path)
            raw_count = len(df_raw)
            report["raw_records"] = raw_count

            missing_cols = [col for col in target_columns if col not in df_raw.columns]
            if missing_cols:
                raise KeyError(f"Missing required columns in '{file_name}': {missing_cols}")

            df_filtered = df_raw[target_columns].copy()

            pk_col = PRIMARY_KEYS.get(table_name)
            if pk_col and pk_col in df_filtered.columns:
                df_clean = df_filtered.dropna(subset=[pk_col]).copy()
            else:
                df_clean = df_filtered

            clean_count = len(df_clean)
            rejected_count = raw_count - clean_count

            report["filtered_records"] = clean_count
            report["rejected_records"] = rejected_count
            report["columns_fetched"] = ", ".join(target_columns)

            output_path = os.path.join(TRANSFORMED_DIR, file_name)
            df_clean.to_csv(output_path, index=False)

            report["status"] = "SUCCESS"
            report["validation_results"] = "PASS"
            print(f"  --> Successfully transformed '{file_name}': Fetched {len(target_columns)} columns, {clean_count} valid rows.")

        except Exception as e:
            report["status"] = "FAILED"
            report["validation_results"] = "FAIL"
            report["error_message"] = str(e)
            print(f"  [!] Failed transformation for '{file_name}': {e}")

        finally:
            end_dt = datetime.now(timezone.utc)
            report["end_time"] = end_dt.isoformat()
            report["duration_seconds"] = (end_dt - start_dt).total_seconds()
            log_transformation_audit(report)

if __name__ == "__main__":
    transform_fetch_and_filter()