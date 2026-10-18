import time
from apscheduler.schedulers.background import BackgroundScheduler

def run_pipeline():
    print("Pipeline running...")

scheduler = BackgroundScheduler()

scheduler.add_job(
    run_pipeline, 
    trigger='cron', 
    day_of_week='mon', 
    hour=0, 
    minute=0
)
scheduler.start()

print("Scheduler started. Press Ctrl+C to exit.")

try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
    print("Scheduler stopped.")