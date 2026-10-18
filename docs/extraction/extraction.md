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

### Table: oil_product

| Column | Expected Data Type | Key | Purpose
| -------- | -------- | -------- |-------- |
| id  | int  | Primary Key  | Uniquely identifies each oil product. |
| brand  | text  | -  | Identifies the product brand. |
| name  | text  | -  | Stores the oil product name. |
| cost  | numeric  | -  | Stores the product cost used in the current cost-based calculations. |

### Table: fuel_sale_batch

| Column | Expected Data Type | Key | Purpose
| -------- | -------- | -------- |-------- |
| sale_id  | int  | Foreign Key  | Identifies the fuel sale associated with a batch allocation. |
| batch_id  | int  |  Foreign Key | Identifies the fuel inventory batch used for the sale. |
| liters_consumed  | numeric  | -  | Records the number of liters taken from the corresponding batch. |

### Table: fuel_batch

| Column | Expected Data Type | Key | Purpose
| -------- | -------- | -------- |-------- |
| id  | int  | Primary Key  | Uniquely identifies each fuel inventory batch. |
| fuel_id  | int  |  Foreign Key | Identifies the fuel product associated with the batch. |
| cost_per_liter  | numeric  | -  | Records the cost per liter for the batch. |
| liters_initial  | numeric  | -  | Records the initial volume of fuel in the batch. |

### Table: expense

# Extraction Validation Checks

The extraction validation stage verifies that the required data has been successfully retrieved from the Supabase PostgreSQL database before it proceeds to the Transformation Stage. The checks focus on source accessibility, table and column availability, identifier validity, primary key uniqueness, record counts, extraction completeness, and errors during data retrieval.

## Validation Checks

| Check Name | Target | Purpose | Validation Criteria |
|---|---|---|---|
| **Source Connection and Accessibility** | Supabase PostgreSQL connection | Ensures that the pipeline can connect to the source database and retrieve data. | **Pass:** The database connection succeeds and the pipeline can execute a test query. **Fail:** Connection errors, authentication failures, or access restrictions prevent retrieval. |
| **Required Tables Exist** | `sale`, `oil_sale`, `fuel`, `oil_product`, `fuel_sale_batch`, `fuel_batch` | Confirms that all tables required for the planned analytics are available. | **Pass:** Every required table exists and is accessible. **Fail:** A required table is missing or inaccessible. |
| **Required Columns Exist** | Selected columns in each source table | Ensures that the fields required for extraction are available before the queries execute. | **Pass:** All configured columns exist and can be queried. **Fail:** A required column is missing or causes a query error. |
| **Required Identifiers Are Present** | Primary and foreign key columns in the extracted records | Ensures that extracted records contain the identifiers needed to distinguish transactions and relate products, sales, and fuel batches. | **Pass:** Required identifier fields are not NULL in the extracted records. **Fail:** A required identifier is missing. Optional fields, such as `attendant_name`, are assessed separately according to their use in the analytics. |
| **Primary Key Uniqueness** | Primary keys or defined unique identifiers in the extracted tables | Prevents duplicate records from being treated as separate transactions or products. | **Pass:** No duplicate values exist for a table's declared primary key or unique identifier. **Fail:** Duplicate key values are detected. For tables with composite keys, the complete key combination must be checked. |
| **Record Count Verification** | Source query results and extracted datasets | Confirms that the number of extracted records matches the number of records expected from the source query. | **Pass:** The source query count and the extracted record count match for each table and extraction period. **Fail:** The counts differ without an explained or documented reason. |
| **Extraction Period Validation** | `sale.sold_at` and `oil_sale.sold_at` | Ensures that sales records fall within the configured extraction period. | **Pass:** All extracted sales records fall within the specified start and end timestamps. **Fail:** Records outside the extraction period are included or expected records within the period are missing. |
| **Relationship Identifier Validation** | Foreign key fields in `sale`, `oil_sale`, `fuel_sale_batch`, and `fuel_batch` | Checks whether the extracted identifiers can be matched to their corresponding referenced records. | **Pass:** Each non-NULL foreign key in the extracted relationship records matches an existing referenced record. **Fail:** A reference points to a nonexistent record. |
| **Extraction Error and Interruption Check** | Extraction queries, data retrieval operations, and output files or datasets | Detects incomplete extraction caused by query failures, connection interruptions, or file-writing errors. | **Pass:** All required extraction operations complete successfully, and the extracted datasets are available for the next stage. **Fail:** A required operation fails or produces an incomplete dataset. The affected extraction must be retried or marked as failed before transformation begins. |

## Validation Outcome

After completing the validation checks, the pipeline determines whether the extracted data is ready for the Transformation Stage. If all required checks pass, the extracted datasets are accepted for further processing. If a required check fails, the pipeline records the failure and prevents incomplete or unreliable extraction results from being treated as valid input.

The validation stage focuses only on the availability, integrity, and completeness of the extracted data. Tasks such as correcting invalid values, standardizing formats, handling outliers, and performing business calculations are handled during the Transformation Stage.

# Extraction Metadata and Log Specification

The batch data pipeline will maintain extraction metadata and logs to monitor each extraction run and track the data retrieved from the Supabase PostgreSQL database. The metadata will record the pipeline execution identifier, source table, extraction timestamps, record counts, extraction status, validation results, and any errors encountered during data retrieval.

The logs will be maintained in a dedicated logging table in Supabase PostgreSQL. Each extraction run will have a unique run ID, and each source table processed during that run will have its own extraction record. This allows the pipeline to track the results of individual table extractions and determine whether the complete extraction process was successful.

## Extraction Metadata Fields

| Field Name | Purpose | Example Value or Format |
|---|---|---|
| run_id | Uniquely identifies a pipeline execution and connects the extraction records belonging to the same run. | RUN-20261017-001 |
| table_name | Identifies the source table from which the data was extracted. | sale |
| extraction_start_time | Records the date and time when extraction of a particular table begins. | 2026-10-17T01:00:00+08:00 |
| extraction_end_time | Records the date and time when extraction of that table finishes. | 2026-10-17T01:00:03+08:00 |
| extraction_status | Indicates whether the extraction operation completed successfully, failed, or completed with a partial result. | SUCCESS, FAILED, or PARTIAL |
| records_read | Records the number of rows returned by the source database query. | 250 |
| records_extracted | Records the number of rows successfully retrieved and made available to the extraction output or staging process. | 250 |
| records_rejected | Records the number of retrieved rows rejected by extraction-level validation, where applicable. | 0 |
| extraction_window_start | Identifies the beginning of the date and time range used to retrieve records. | 2026-10-10T00:00:00+08:00 |
| extraction_window_end | Identifies the end of the date and time range used to retrieve records. | 2026-10-16T23:59:59+08:00 |
| validation_results | Stores the outcome of extraction checks, including table availability, required columns, identifier checks, uniqueness, and record-count verification. | {"connection":"PASS","columns":"PASS","count_match":"PASS"} |
| error_code | Stores a code identifying an extraction error, if one occurs. | DB_CONNECTION_ERROR |
| error_message | Describes the error encountered during extraction. Remains empty when no error occurs. | Database connection timed out. |
| extraction_duration_seconds | Records the time taken to complete the extraction operation, in seconds. | 3.25 |

*Note:* All example values are illustrative. The exact formats and values will depend on the pipeline implementation. records_read and records_extracted may be equal when all returned records are retrieved successfully. Any difference should be investigated. Rejected records should be counted only when an extraction-level validation rule explicitly excludes them; data-cleaning decisions belong to the Transformation Stage.

## Use of Metadata and Logs

*Monitoring:* The logs allow the pipeline operator to check whether each source table was extracted successfully, how many records were retrieved, and how long each extraction took. They can also help identify changes in extraction volume or unusually long execution times.

*Troubleshooting:* When an extraction fails, the status, error code, error message, and validation results help identify the cause. For example, a missing table or database connection failure can be identified from the corresponding log entry.

*Auditing and Traceability:* Each run ID links the extraction records produced during one pipeline execution. The source table name, extraction window, timestamps, and record counts provide a record of which data was requested and retrieved and when the operation occurred.

*Recovery and Re-execution:* If an extraction fails or returns incomplete results, the logs help identify the affected table and extraction window. The pipeline can retry the failed extraction after the underlying problem is resolved. A failed or incomplete extraction must not be marked as successful simply because other tables were extracted successfully.

The metadata and logs are used strictly to monitor and trace the extraction process. They do not replace the data-validation checks or the data-cleaning and transformation operations performed in later pipeline stages.

# Extraction Metadata and Log Specification

The batch data pipeline will maintain extraction metadata and logs to monitor each extraction run and track the data retrieved from the Supabase PostgreSQL database. The metadata will record the pipeline execution identifier, source table, extraction timestamps, record counts, extraction status, validation results, and any errors encountered during data retrieval.

The logs will be maintained in a dedicated logging table in Supabase PostgreSQL. Each extraction run will have a unique run ID, and each source table processed during that run will have its own extraction record. This allows the pipeline to track the results of individual table extractions and determine whether the complete extraction process was successful.

## Extraction Metadata Fields

| Field Name | Purpose | Example Value or Format |
|---|---|---|
| run_id | Uniquely identifies a pipeline execution and connects the extraction records belonging to the same run. | RUN-20261017-001 |
| table_name | Identifies the source table from which the data was extracted. | sale |
| extraction_start_time | Records the date and time when extraction of a particular table begins. | 2026-10-17T01:00:00+08:00 |
| extraction_end_time | Records the date and time when extraction of that table finishes. | 2026-10-17T01:00:03+08:00 |
| extraction_status | Indicates whether the extraction operation completed successfully, failed, or completed with a partial result. | SUCCESS, FAILED, or PARTIAL |
| records_read | Records the number of rows returned by the source database query. | 250 |
| records_extracted | Records the number of rows successfully retrieved and made available to the extraction output or staging process. | 250 |
| records_rejected | Records the number of retrieved rows rejected by extraction-level validation, where applicable. | 0 |
| extraction_window_start | Identifies the beginning of the date and time range used to retrieve records. | 2026-10-10T00:00:00+08:00 |
| extraction_window_end | Identifies the end of the date and time range used to retrieve records. | 2026-10-16T23:59:59+08:00 |
| validation_results | Stores the outcome of extraction checks, including table availability, required columns, identifier checks, uniqueness, and record-count verification. | {"connection":"PASS","columns":"PASS","count_match":"PASS"} |
| error_code | Stores a code identifying an extraction error, if one occurs. | DB_CONNECTION_ERROR |
| error_message | Describes the error encountered during extraction. Remains empty when no error occurs. | Database connection timed out. |
| extraction_duration_seconds | Records the time taken to complete the extraction operation, in seconds. | 3.25 |

*Note:* All example values are illustrative. The exact formats and values will depend on the pipeline implementation. records_read and records_extracted may be equal when all returned records are retrieved successfully. Any difference should be investigated. Rejected records should be counted only when an extraction-level validation rule explicitly excludes them; data-cleaning decisions belong to the Transformation Stage.

## Use of Metadata and Logs

*Monitoring:* The logs allow the pipeline operator to check whether each source table was extracted successfully, how many records were retrieved, and how long each extraction took. They can also help identify changes in extraction volume or unusually long execution times.

*Troubleshooting:* When an extraction fails, the status, error code, error message, and validation results help identify the cause. For example, a missing table or database connection failure can be identified from the corresponding log entry.

*Auditing and Traceability:* Each run ID links the extraction records produced during one pipeline execution. The source table name, extraction window, timestamps, and record counts provide a record of which data was requested and retrieved and when the operation occurred.

*Recovery and Re-execution:* If an extraction fails or returns incomplete results, the logs help identify the affected table and extraction window. The pipeline can retry the failed extraction after the underlying problem is resolved. A failed or incomplete extraction must not be marked as successful simply because other tables were extracted successfully.

The metadata and logs are used strictly to monitor and trace the extraction process. They do not replace the data-validation checks or the data-cleaning and transformation operations performed in later pipeline stages.
