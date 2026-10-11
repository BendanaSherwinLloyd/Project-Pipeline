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
-oil_product_id – identifies the oil product involved in an oil transaction.
-attendant_name – identifies the attendant responsible for the transaction.
-sold_at – records the date and time when the transaction occurred and is used to determine the extraction date range.
-oil_product_id – identifies the oil product involved in an oil transaction.
-quantity – records the number of units sold for an oil product.
-liters_sold – records the amount of fuel sold in liters.
-total_amount – records the total transaction amount and supports revenue and profit-related calculations.

The sale table primarily provides fuel transaction information, including the fuel product, transaction timestamp, liters sold, revenue, and attendant details. The oil_sale table provides oil product sales information, including the product identifier, quantity sold, transaction timestamp, revenue, and attendant details. Related product and fuel batch tables provide the additional information required for product identification and cost calculations.

The extraction will focus on records within the configured processing period for each scheduled batch execution. Only the required rows and fields will be retrieved rather than extracting the entire database. The extracted data will then be passed to the transformation phase for validation, cleaning, aggregation, and analysis. The resulting analytical outputs will be stored in dedicated tables for reporting and further use.

### 5. Source Limitations

The extraction process depends on the availability and consistency of the Supabase PostgreSQL database. The pipeline assumes that the relevant tables, including sale, oil_sale, and restock_log, are accessible and contain complete and properly formatted records during each extraction period.

One limitation is that changes to the database schema may affect the extraction process. Changes to table names, column names, data types, or relationships may require modifications to the extraction queries and Python script. The pipeline also assumes that the required transaction data is available and that the created_at field is properly recorded, as this field is used to determine the seven-day extraction window.

The extraction process also depends on database connectivity and access permissions. If the Supabase database is temporarily unavailable or the pipeline does not have the required credentials or permissions, the scheduled extraction may fail. The pipeline therefore assumes that the database credentials stored in GitHub Actions Secrets remain valid and that the required database access is maintained.

Another limitation is that the accuracy of the analytics depends on the quality and completeness of the source data. Missing, duplicated, or incorrectly entered transaction records may affect the resulting dashboard metrics. The pipeline assumes that transactions and restocking records are properly recorded by the operational system before the scheduled batch execution.

Historical data is also assumed to be available within the database for the required analytical calculations. If historical records are missing or incomplete, the pipeline may have limited ability to generate accurate trends or comparisons for the analytics dashboard.

# Source Tables and Column Specification

### Table: sale

| Column | Data Type | Key | Purpose
| -------- | -------- | -------- |-------- |
| fuel_id  | int  | Foreign Key  | Identifies the fuel product sold. |
| attendant_name  | Text  | -  | Identifies the attendant responsible for the sale. |
| liters_sold  | Numeric  |  - | Records the volume of fuel sold in liters. |
| total_ammount  | Numeric  | -  | Records the total amount collected for the transaction. |
| sold_at  | Timestamp  | - | Records the date and time of the transaction. |


### Table: oil_sale

| Column | Data Type | Key | Purpose
| -------- | -------- | -------- |-------- |
| oil_product_id  | int  | Foreign Key  | Identifies the oil product sold. |
| quantity  | int  | -  | Records the number of units sold. |
| total_amount  | int  | -  | Records the total amount collected for the transaction. |
| attendant_name  | text  | -  | Identifies the attendant responsible for the sale. |
| sold_at  | int  | timestmap  | Records the date and time of the transaction. |

### Table: fuel

| Column | Data Type | Key | Purpose
| -------- | -------- | -------- |-------- |
| id  | int  | Primary Key  | Uniquely identifies each fuel product. |
| name  | text  | -  | Stores the name of the fuel product. |