import os
import time
import uuid
from datetime import datetime, timedelta, timezone
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler

RAW_STAGING_DIR = "raw_data"
TRANSFORMED_DIR = "transformed"
ANALYTICS_DIR = "analytics_output"
LOGS_DIR = "logs"
LOG_FILE_PATH = os.path.join(LOGS_DIR, "transformation.log")

REQUIRED_SCHEMA = {
    "sale": ["id", "fuel_id", "sold_at", "liters_sold", "total_amount", "attendant_name"],
    "oil_sale": ["id", "oil_product_id", "sold_at", "quantity", "total_amount", "attendant_name"],
    "expense": ["id", "amount", "category", "expense_date"]
}

def prepare_transformed_files():
    """Reads raw CSVs, verifies schema, drops null IDs, and outputs clean CSVs."""
    os.makedirs(TRANSFORMED_DIR, exist_ok=True)
    
    for table_name, cols in REQUIRED_SCHEMA.items():
        raw_csv_path = os.path.join(RAW_STAGING_DIR, f"{table_name}.csv")
        
        if not os.path.exists(raw_csv_path):
            print(f"  [!] Missing raw file: '{raw_csv_path}'. Ensure extraction stage ran!")
            return False
            
        df_raw = pd.read_csv(raw_csv_path)
        
        missing_cols = [c for c in cols if c not in df_raw.columns]
        if missing_cols:
            print(f"  [!] Missing columns in '{table_name}': {missing_cols}")
            return False

        df_clean = df_raw[cols].dropna(subset=["id"]).copy()
        output_csv_path = os.path.join(TRANSFORMED_DIR, f"{table_name}.csv")
        df_clean.to_csv(output_csv_path, index=False)
        print(f"  --> Prepared '{output_csv_path}' ({len(df_clean)} rows)")

    return True

def log_transformation_audit(report_data: dict):
    """Appends a structured 12-field audit report to logs/transformation.log."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    log_entry = (
        f"--------------------------------------------------\n"
        f"Pipeline Run ID      : {report_data['run_id']}\n"
        f"Metric Target        : {report_data['metric_target']}\n"
        f"Start Timestamp      : {report_data['start_time']}\n"
        f"End Timestamp        : {report_data['end_time']}\n"
        f"Status               : {report_data['status']}\n"
        f"Records Processed    : {report_data['records_processed']}\n"
        f"Summaries Generated  : {report_data['summaries_generated']}\n"
        f"Records Rejected     : {report_data['rejected_records']}\n"
        f"Output Destination   : {report_data['target_dest']}\n"
        f"Validation Results   : {report_data['validation_results']}\n"
        f"Error Message        : {report_data['error_message']}\n"
        f"Duration (sec)       : {report_data['duration_seconds']:.2f}\n"
        f"--------------------------------------------------\n\n"
    )
    
    with open(LOG_FILE_PATH, "a") as f:
        f.write(log_entry)

def compute_analytics():
    """Calculates weekly analytical aggregates and saves results as CSV files."""
    os.makedirs(ANALYTICS_DIR, exist_ok=True)
    run_id = f"ANLYT-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=7)

    print(f"\n==================================================")
    print(f"[{now.isoformat()}] STARTING ANALYTICS COMPUTATION: {run_id}")
    print(f"==================================================")

    if not prepare_transformed_files():
        print("  [!] Aborting computation due to missing raw staging files.")
        return

    sales_df = pd.read_csv(os.path.join(TRANSFORMED_DIR, "sale.csv"))
    oil_sales_df = pd.read_csv(os.path.join(TRANSFORMED_DIR, "oil_sale.csv"))
    expenses_df = pd.read_csv(os.path.join(TRANSFORMED_DIR, "expense.csv"))

    sales_df["sold_at"] = pd.to_datetime(sales_df["sold_at"], utc=True)
    oil_sales_df["sold_at"] = pd.to_datetime(oil_sales_df["sold_at"], utc=True)
    expenses_df["expense_date"] = pd.to_datetime(expenses_df["expense_date"], utc=True)

    recent_sales = sales_df[sales_df["sold_at"] >= week_start]
    recent_oil = oil_sales_df[oil_sales_df["sold_at"] >= week_start]
    recent_expenses = expenses_df[expenses_df["expense_date"] >= week_start]

    start_dt = datetime.now(timezone.utc)
    profit_csv_path = os.path.join(ANALYTICS_DIR, "weekly_net_profit_summary.csv")
    report = {
        "run_id": run_id,
        "metric_target": "weekly_net_profit_summary",
        "start_time": start_dt.isoformat(),
        "end_time": "",
        "status": "FAILED",
        "records_processed": len(recent_sales) + len(recent_oil) + len(recent_expenses),
        "summaries_generated": 0,
        "rejected_records": 0,
        "target_dest": profit_csv_path,
        "validation_results": "PENDING",
        "error_message": "None",
        "duration_seconds": 0.0
    }

    try:
        fuel_rev = float(recent_sales["total_amount"].sum()) if not recent_sales.empty else 0.0
        oil_rev = float(recent_oil["total_amount"].sum()) if not recent_oil.empty else 0.0
        total_rev = fuel_rev + oil_rev

        total_expenses = float(recent_expenses["amount"].sum()) if not recent_expenses.empty else 0.0
        net_profit = total_rev - total_expenses
        net_margin = (net_profit / total_rev * 100) if total_rev > 0 else 0.0

        profit_summary_df = pd.DataFrame([{
            "summary_date": str(now.date()),
            "fuel_revenue": round(fuel_rev, 2),
            "oil_revenue": round(oil_rev, 2),
            "total_revenue": round(total_rev, 2),
            "total_expenses": round(total_expenses, 2),
            "net_profit": round(net_profit, 2),
            "net_margin_percent": round(net_margin, 2),
            "total_transactions": len(recent_sales) + len(recent_oil)
        }])

        profit_summary_df.to_csv(profit_csv_path, index=False)
        print(f"  --> Successfully saved '{profit_csv_path}'")

        report["summaries_generated"] = len(profit_summary_df)
        report["status"] = "SUCCESS"
        report["validation_results"] = "PASS"

    except Exception as e:
        report["status"] = "FAILED"
        report["validation_results"] = "FAIL"
        report["error_message"] = str(e)
        print(f"  [!] Failed net profit analytics computation: {e}")

    finally:
        end_dt = datetime.now(timezone.utc)
        report["end_time"] = end_dt.isoformat()
        report["duration_seconds"] = (end_dt - start_dt).total_seconds()
        log_transformation_audit(report)

    start_dt = datetime.now(timezone.utc)
    attendant_csv_path = os.path.join(ANALYTICS_DIR, "weekly_attendant_rankings.csv")
    report = {
        "run_id": run_id,
        "metric_target": "weekly_attendant_rankings",
        "start_time": start_dt.isoformat(),
        "end_time": "",
        "status": "FAILED",
        "records_processed": len(recent_sales) + len(recent_oil),
        "summaries_generated": 0,
        "rejected_records": 0,
        "target_dest": attendant_csv_path,
        "validation_results": "PENDING",
        "error_message": "None",
        "duration_seconds": 0.0
    }

    try:
        fuel_att = recent_sales.groupby("attendant_name").agg(
            fuel_revenue=("total_amount", "sum"),
            fuel_transactions=("id", "count"),
            liters_sold=("liters_sold", "sum")
        ).reset_index() if not recent_sales.empty else pd.DataFrame(columns=["attendant_name", "fuel_revenue", "fuel_transactions", "liters_sold"])

        oil_att = recent_oil.groupby("attendant_name").agg(
            oil_revenue=("total_amount", "sum"),
            oil_transactions=("id", "count"),
            oil_quantity=("quantity", "sum")
        ).reset_index() if not recent_oil.empty else pd.DataFrame(columns=["attendant_name", "oil_revenue", "oil_transactions", "oil_quantity"])

        att_merged = pd.merge(fuel_att, oil_att, on="attendant_name", how="outer").fillna(0)
        
        if not att_merged.empty:
            att_merged["total_revenue"] = att_merged["fuel_revenue"] + att_merged["oil_revenue"]
            att_merged["total_transactions"] = att_merged["fuel_transactions"] + att_merged["oil_transactions"]
            att_merged.sort_values(by="total_revenue", ascending=False, inplace=True)
            att_merged["rank"] = range(1, len(att_merged) + 1)
            att_merged["summary_date"] = str(now.date())

            # Save to CSV
            att_merged.to_csv(attendant_csv_path, index=False)
            print(f"  --> Successfully saved '{attendant_csv_path}'")

            report["summaries_generated"] = len(att_merged)
            report["status"] = "SUCCESS"
            report["validation_results"] = "PASS"

    except Exception as e:
        report["status"] = "FAILED"
        report["validation_results"] = "FAIL"
        report["error_message"] = str(e)
        print(f"  [!] Failed attendant analytics computation: {e}")

    finally:
        end_dt = datetime.now(timezone.utc)
        report["end_time"] = end_dt.isoformat()
        report["duration_seconds"] = (end_dt - start_dt).total_seconds()
        log_transformation_audit(report)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        compute_analytics, 
        trigger='cron', 
        day_of_week='sun', 
        hour=0, 
        minute=0
    )

    scheduler.start()
    print("Analytics Transformation Service started.")
    print("Scheduled to run every Sunday at 12:00 AM. Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Transformation Service stopped.")