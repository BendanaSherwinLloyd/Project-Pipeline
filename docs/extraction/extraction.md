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
The batch data pipeline will extract transaction and inventory-related data from the sale, oil_sale, and restock_log tables in the Supabase PostgreSQL database. The extracted data will provide the information required to generate the analytics dashboard, including peak hours, product demand, profit margins, revenue, top-selling products, and attendant performance.

The main fields included in the extraction are:
-fuel_id – identifies the fuel product involved in a fuel transaction.
-pump_id – identifies the pump used for the transaction.
-attendant_name – identifies the attendant responsible for the transaction.
-created_at – records the date and time when the transaction or record was created and is used to determine the extraction date range.
-oil_product_id – identifies the oil product involved in an oil transaction.
-quantity – records the number of units sold for an oil product.
-liters_sold – records the amount of fuel sold in liters.

The sale table will primarily provide fuel transaction information, including the fuel product, pump, attendant, transaction timestamp, and liters sold. The oil_sale table will provide oil product sales information, including the oil product, quantity sold, attendant, and transaction timestamp. The restock_log table will provide relevant inventory and restocking information needed for product demand and profit-related analysis.

The extraction will focus on records within the seven-day processing period for each scheduled batch execution. Only the required rows and fields will be extracted rather than retrieving the entire contents of the tables. The extracted data will then be temporarily stored as CSV staging files before being passed to the transformation phase.

### 5. Source Limitations