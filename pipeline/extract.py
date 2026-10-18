import os, time, uuid
from datetime import datetime, timezone
import pandas as pd
from sqlmodel import create_engine, text
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set in .env file.")

engine = create_engine(DATABASE_URL, echo=False)

STAGING_DIR = "raw_data"
LOGS_DIR = "logs"
LOG_FILE_PATH = os.path.join(LOGS_DIR, "extraction.log")

SOURCE_TABLES = [
    "sale",
    "oil_sale",
    "fuel",
    "oil_product",
    "fuel_sale_batch",
    "fuel_batch",
    "expense",
    "restockLog",
    "oil_restock_log"
]

TIMESTAMP_COLUMNS = {
    "sale": "sold_at",
    "oil_sale": "sold_at",
    "expenses": "created_at"
}

def log_audit_report(report_data: dict):
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    log_entry = (
        f"--------------------------------------------------\n"
        f"Pipeline Run ID : {report_data['run_id']}\n"
        f"Table Name      : {report_data['table_name']}\n"
        f"Start Timestamp : {report_data['start_time']}\n"
        f"End Timestamp   : {report_data['end_time']}\n"
        f"Status          : {report_data['status']}\n"
        f"Records Read    : {report_data['records_read']}\n"
        f"Records Extracted: {report_data['records_extracted']}\n"
        f"Records Rejected: {report_data['records_rejected']}\n"
        f"Extraction Window: {report_data['extraction_window']}\n"
        f"Validation Results: {report_data['validation_results']}\n"
        f"Error Message   : {report_data['error_message']}\n"
        f"Duration (sec)  : {report_data['duration_seconds']:.2f}\n"
        f"--------------------------------------------------\n\n"
    )
    
    with open(LOG_FILE_PATH, "a") as f:
        f.write(log_entry)

def extract_to_csv():
    """Extracts complete, unfiltered tables from database to CSV staging files

    and appends a 12-field audit report for both successful and failed runs.

    """
    os.makedirs(STAGING_DIR, exist_ok=True)
    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
    print(f"\n==================================================")
    print(f"[{datetime.now(timezone.utc).isoformat()}] STARTING EXTRACTION RUN: {run_id}")
    print(f"==================================================")

    for table_name in SOURCE_TABLES:
        start_dt = datetime.now(timezone.utc)
        start_time_iso = start_dt.isoformat()
        
        report = {
            "run_id": run_id,
            "table_name": table_name,
            "start_time": start_time_iso,
            "end_time": "",
            "status": "FAILED",
            "records_read": 0,
            "records_extracted": 0,
            "records_rejected": 0,
            "extraction_window": "N/A",
            "validation_results": "PENDING",
            "error_message": "None",
            "duration_seconds": 0.0
        }

        try:
            print(f"Extracting table: '{table_name}'...")
            
            with engine.connect() as connection:
                query = text(f"SELECT * FROM {table_name}")
                df = pd.read_sql(query, connection)

            records_count = len(df)
            report["records_read"] = records_count
            report["records_extracted"] = records_count

            ts_col = TIMESTAMP_COLUMNS.get(table_name)
            if ts_col and ts_col in df.columns and not df.empty:
                min_ts = pd.to_datetime(df[ts_col]).min()
                max_ts = pd.to_datetime(df[ts_col]).max()
                report["extraction_window"] = f"{min_ts} to {max_ts}"
            else:
                report["extraction_window"] = "FULL_TABLE_DUMP"

            csv_path = os.path.join(STAGING_DIR, f"{table_name}.csv")
            df.to_csv(csv_path, index=False)
            
            report["status"] = "SUCCESS"
            report["validation_results"] = "PASS"
            print(f"  --> Successfully saved {records_count} rows to '{csv_path}'")

        except Exception as e:
            report["status"] = "FAILED"
            report["validation_results"] = "FAIL"
            report["error_message"] = str(e)
            print(f"  [!] Failed to extract table '{table_name}': {e}")
            
        finally:
            end_dt = datetime.now(timezone.utc)
            report["end_time"] = end_dt.isoformat()
            report["duration_seconds"] = (end_dt - start_dt).total_seconds()

            log_audit_report(report)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()


    scheduler.add_job(
        extract_to_csv, 
        trigger='cron', 
        day_of_week='sun', 
        hour=0, 
        minute=0
    )

    scheduler.start()
    print("Extraction Service started.")
    print("Scheduled to run every Sunday at 12:00 AM. Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Extraction Service stopped.")