# Data Source and Extraction Specification

### 1. Source System
Name: GAStoKITA: An Integrated Point-of-Sale and Business Intelligence System for U-Fuel Station Operations 
Purpose: GAStoKITA is a cashier POS system and admin business intelligence system to help improve the operations of the U-Fuel Gas station in Real, Calatagan, Batangas. 

### 2. Source Database
Database Management System: Supabase PostgreSQL
Source: GAStoKITA Operational Database
File format: CSV

### 3. Extraction Method
The GAStoKITA batch data pipeline will use incremental extraction from the Supabase PostgreSQL database. The pipeline will retrieve only the records required to generate and update the analytics dashboard. The dashboard will provide insights on peak operating hours, product demand, profit margins, revenue, top-selling products, and attendant performance.

The pipeline will run every 7 days, each batch execution will extract the relevant transaction records from the previous seven-day period. This allows the pipeline to process recent operational data without repeatedly extracting the entire transaction history. Where historical data is required for comparison or trend analysis, the extraction logic may retrieve the additional records needed by the specific analytical calculation.

Data will be extracted by a Python-based extraction script that connects directly to the Supabase PostgreSQL database. SQL queries will be used to retrieve only the required rows and columns from relevant tables, such as sales, fuel batches, oil sales, expenses, and attendant records. The extracted records will then be temporarily converted into CSV files, which will serve as staging datasets for the transformation phase.

The extraction process will use Python with the PostgreSQL database adapter (psycopg2) to establish the database connection and execute the required SQL queries. The extraction script and batch pipeline will be executed through GitHub Actions, which will provide the scheduled cloud-based execution environment.
The extraction method will be incremental rather than full extraction. Only records within the defined seven-day extraction window will normally be retrieved, reducing unnecessary database reads and allowing the pipeline to focus on recently completed transactions.

The extraction method will be incremental rather than full extraction. Only records within the defined seven-day extraction window will normally be retrieved, reducing unnecessary database reads and allowing the pipeline to focus on recently completed transactions.

The pipeline will be scheduled to run once every 7 days. After extraction, the CSV staging files will be passed to the transformation phase, where the data will be processed to calculate the metrics required by the analytics dashboard, including peak hours, product demand, profit margins, revenue, top-selling products, and attendant performance.

### 4. Extraction Scope

### 5. Source Limitations

The extraction process depends on the availability and consistency of the Supabase PostgreSQL database. The pipeline assumes that the relevant tables, including sale, oil_sale, and restock_log, are accessible and contain complete and properly formatted records during each extraction period.

One limitation is that changes to the database schema may affect the extraction process. Changes to table names, column names, data types, or relationships may require modifications to the extraction queries and Python script. The pipeline also assumes that the required transaction data is available and that the created_at field is properly recorded, as this field is used to determine the seven-day extraction window.

The extraction process also depends on database connectivity and access permissions. If the Supabase database is temporarily unavailable or the pipeline does not have the required credentials or permissions, the scheduled extraction may fail. The pipeline therefore assumes that the database credentials stored in GitHub Actions Secrets remain valid and that the required database access is maintained.

Another limitation is that the accuracy of the analytics depends on the quality and completeness of the source data. Missing, duplicated, or incorrectly entered transaction records may affect the resulting dashboard metrics. The pipeline assumes that transactions and restocking records are properly recorded by the operational system before the scheduled batch execution.

Historical data is also assumed to be available within the database for the required analytical calculations. If historical records are missing or incomplete, the pipeline may have limited ability to generate accurate trends or comparisons for the analytics dashboard.
