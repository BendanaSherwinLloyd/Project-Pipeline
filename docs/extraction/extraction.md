# GAStoKITA Data Extraction Documentation

# 1. Data Source and Extraction Specification

## 1. Source System

**Source system:** GAStoKITA Point-of-Sale and Business Intelligence System for U-Fuel

**Purpose:** GAStoKITA supports fuel station cashier operations and provides operational data used for business analytics. The extraction process retrieves data from the operational database so it can be prepared for analytics in a later pipeline stage.

### 2. Source Database
Database Management System: Supabase PostgreSQL
Source: GAStoKITA Operational Database
File format: CSV

## 3. Extraction Method

The current extraction method is **full-table extraction**.

For every configured source table, the script executes a query equivalent to:

```sql
SELECT * FROM table_name;
```

The result is loaded into a Pandas DataFrame and exported as a CSV file. The script does not currently apply a date filter, select only a subset of columns, or perform incremental extraction.

The extraction process uses the following technologies:

- Python
- SQLModel / SQLAlchemy for database connectivity
- Pandas for loading query results and writing CSV files
- `python-dotenv` for environment configuration
- APScheduler for scheduled execution

### Extraction Schedule

The script configures APScheduler to run the extraction every **Sunday at 12:00 AM**.

The scheduler runs inside the Python process. Therefore, the machine or environment running `extract.py` must remain active and the script must remain running for the scheduled extraction to occur.

## 4. Extraction Scope

The current `SOURCE_TABLES` list contains the following tables:

| Source table | General purpose in the pipeline |
|---|---|
| `sale` | Fuel sales transaction records |
| `oil_sale` | Oil and non-fuel product sales records |
| `fuel` | Fuel product reference information |
| `oil_product` | Oil product reference information |
| `fuel_sale_batch` | Links fuel sales to the inventory batches consumed |
| `fuel_batch` | Fuel inventory batch information, including cost-related data |
| `expense` | Operational expense records |
| `restockLog` | Fuel or inventory restocking records, depending on the source schema |
| `oil_restock_log` | Oil product restocking records |

It extracts all columns and all records returned by each source table query. The timestamp fields in `sale` and `oil_sale` are used to report the minimum and maximum timestamps found in the extracted data when those fields are present.

## 5. Source Limitations and Assumptions

The current implementation has the following limitations and assumptions:

1. The configured database URL is valid and has permission to read the listed tables.
2. Each configured table exists and can be queried.
3. The extraction uses `SELECT *`, so it retrieves the complete table schema and contents. Changes to source schemas may affect the resulting CSV structure.
4. No incremental timestamp filtering is applied. Large source tables may therefore take longer to extract and produce larger CSV files.
5. The extraction process depends on the Python process remaining active for the scheduled run.
6. The CSV files use fixed names and are overwritten when the script runs again. The output files are not currently separated by run ID.
7. The script does not currently implement automatic retries, incremental checkpoints, or a separate quarantine location for failed data.

---

# Source Tables and Column Specification

The extraction script retrieves every column from each configured table using `SELECT *`. The following tables identify the source entities and the fields relevant to understanding the analytics pipeline. Actual column names and data types are inherited from the source database schema; they are not explicitly projected or converted by the extraction script.

The column examples below describe relevant source data based on the pipeline's intended use. They should be verified against the current Supabase schema. The extraction code itself does not enforce these column definitions.

## 1. `sale`

| Relevant column | Purpose |
|---|---|
| `id` | Identifies a fuel sale record |
| `fuel_id` | Identifies the fuel product sold |
| `pump_id` | Identifies the pump associated with the transaction, if present |
| `attendant_name` | Identifies the attendant associated with the sale, if present |
| `sold_at` | Records the sale date and time |
| `liters_sold` | Records the fuel volume sold |
| `total_amount` | Records the sale amount |

**Reason for inclusion:** Provides fuel transaction information for sales, demand, peak-hour, and attendant-related analysis.

## 2. `oil_sale`

| Relevant column | Purpose |
|---|---|
| `id` | Identifies an oil sale record |
| `oil_product_id` | Identifies the oil product sold |
| `sold_at` | Records the transaction date and time |
| `quantity` | Records the quantity sold |
| `total_amount` | Records the transaction amount |
| `attendant_name` | Identifies the attendant, if present |

**Reason for inclusion:** Provides non-fuel product transaction information for product demand, revenue, and attendant-related analysis.

## 3. `fuel`

| Relevant column | Purpose |
|---|---|
| `id` | Identifies a fuel product |
| `name` | Stores the fuel product name |

**Reason for inclusion:** Provides fuel product reference information used to interpret fuel sales.

## 4. `oil_product`

| Relevant column | Purpose |
|---|---|
| `id` | Identifies an oil product |
| `name` | Stores the product name |
| `brand` | Stores the product brand, if present |
| `cost` | Stores product cost information, if present |

**Reason for inclusion:** Provides product reference and cost information for oil product analysis.

## 5. `fuel_sale_batch`

| Relevant column | Purpose |
|---|---|
| `sale_id` | Identifies the related fuel sale |
| `batch_id` | Identifies the fuel batch used |
| `liters_consumed` | Records the volume consumed from the batch |

**Reason for inclusion:** Connects fuel sales to inventory batches and supports cost-related calculations in later stages.

## 6. `fuel_batch`

| Relevant column | Purpose |
|---|---|
| `id` | Identifies a fuel inventory batch |
| `fuel_id` | Identifies the associated fuel product |
| `cost_per_liter` | Records the batch cost per liter |
| `liters_initial` | Records the initial volume in the batch |

**Reason for inclusion:** Provides batch-level fuel cost and inventory information.

## 7. `expense`

The script extracts all columns from `expense`. The exact fields and their data types are inherited from the source schema.

**Reason for inclusion:** Provides operational expense information that may be used in later financial analytics.

## 8. `restockLog`

The script extracts all columns from `restockLog`. The exact fields and their data types are inherited from the source schema.

**Reason for inclusion:** Provides records of inventory restocking activity.

## 9. `oil_restock_log`

The script extracts all columns from `oil_restock_log`. The exact fields and their data types are inherited from the source schema.

**Reason for inclusion:** Provides oil product restocking activity and supports later inventory-related analysis.

---

# Extraction Validation and Data Quality Checks

It performs basic extraction-level checks through successful database querying and CSV writing. It does not yet implement the full set of data-quality checks listed below. The documented checks distinguish between checks currently performed by the code and checks that are recommended for a more complete extraction implementation.

| Check name | Target | Purpose | Current implementation / criteria |
|---|---|---|---|
| Database connection and query execution | Database connection and each source query | Confirms that the database can be accessed and the query can run | **Implemented indirectly.** A query that raises an exception is recorded as `FAILED`; successful query execution continues to CSV output. |
| Source table accessibility | Every table in `SOURCE_TABLES` | Confirms that each configured table can be queried | **Implemented indirectly.** A missing or inaccessible table raises an exception and is logged as failed. |
| CSV output creation | CSV file for each source table | Confirms that the query result can be written to staging | **Implemented.** A successful `to_csv` operation results in a `SUCCESS` status. A file-writing exception is recorded as `FAILED`. |
| Record count tracking | Query result and CSV output | Records how many rows were returned and extracted | **Implemented as count tracking.** `records_read` and `records_extracted` are both set to the DataFrame row count. A separate source-to-file reconciliation check is not performed. |
| Timestamp range reporting | `sale.sold_at`, `oil_sale.sold_at` | Reports the observed timestamp range in the extracted records | **Implemented when the mapped timestamp column exists and the DataFrame is not empty.** The range is metadata only; it does not validate a configured date window. |
| Primary key uniqueness | Source table identifiers | Detects duplicate primary keys | **Not implemented.** The current script does not check uniqueness. |
| Required identifier completeness | Primary and foreign key columns | Detects missing identifiers | **Not implemented.** The current script does not check null identifiers. |
| Foreign key relationship validation | Sales, products, and batch relationship tables | Detects unmatched references | **Not implemented.** The current script does not compare foreign key values between tables. |
| Required column validation | Source schemas | Detects missing or changed fields | **Not implemented as a separate check.** A query using `SELECT *` can succeed even if an expected analytics field is absent. |
| Extraction interruption / error tracking | Query and CSV operations | Records failures during extraction | **Implemented.** Exceptions are captured in the report, the status becomes `FAILED`, and the validation result becomes `FAIL`. |

### Validation Outcome

For each table, the script initially sets the status to `FAILED` and the validation result to `PENDING`. If the query and CSV export complete without raising an exception, the script sets the status to `SUCCESS` and the validation result to `PASS`.

This `PASS` means the current extraction operation completed successfully. It does not mean that the extracted records have passed uniqueness, completeness, relationship, or business-rule validation.

The current script processes the configured tables one at a time. A failure for one table is recorded, and the loop continues to the next configured table.

Data cleaning, standardization, and business calculations are outside the scope of this extraction stage.

---

# Extraction Metadata and Log Specification

The extraction script creates one run ID for each execution of `extract_to_csv()` and records one audit entry for each configured source table.

The audit entries are appended to the local file:

```text
logs/extraction.log
```

The log directory is created automatically if it does not exist.

## 1. Metadata Fields

| Field | Purpose | Example / format |
|---|---|---|
| `run_id` | Identifies the extraction execution | `RUN-A1B2C3D4` |
| `table_name` | Identifies the source table being extracted | `sale` |
| `start_time` | Records when extraction of the table begins | UTC ISO 8601 timestamp |
| `end_time` | Records when extraction of the table finishes | UTC ISO 8601 timestamp |
| `status` | Indicates whether the table extraction succeeded or failed | `SUCCESS` / `FAILED` |
| `records_read` | Number of rows returned by the query | Integer |
| `records_extracted` | Number of rows written to the CSV output | Integer |
| `records_rejected` | Number of rows rejected during extraction | `0` in the current implementation |
| `extraction_window` | Reports the observed timestamp range or indicates a full-table extraction | Timestamp range or `FULL_TABLE_DUMP` |
| `validation_results` | Records the basic extraction outcome | `PASS` / `FAIL` / `PENDING` |
| `error_message` | Stores the exception text when an extraction fails | Error text or `None` |
| `duration_seconds` | Records the time taken for the table extraction | Decimal seconds |

The timestamps used for the start and end times are generated in UTC. The `extraction_window` field is not a configured start/end filter. It reports the minimum and maximum timestamps found for mapped timestamp fields; otherwise, it reports `FULL_TABLE_DUMP`.

## 2. Use of Metadata and Logs

The local audit log supports:

- **Monitoring:** Reviewing which tables completed and how many rows were extracted.
- **Troubleshooting:** Reviewing the exception message for a failed table.
- **Auditing:** Identifying the run and table associated with an extraction result.
- **Performance review:** Comparing the recorded extraction durations.

The log is currently a text file on the machine running the extraction script. The script does not currently write extraction logs to a Supabase logging table.

---

# Log Retention and Access

| Requirement | Current specification |
|---|---|
| Log storage location | Local `logs/extraction.log` file |
| Retention period | No automatic retention or deletion policy is implemented in the current script |
| Access | Access is controlled by permissions on the machine and directory where the script runs |
| Archiving | Not implemented |
| Deletion | Logs are appended to the file; the script does not automatically delete old entries |

The log file should be retained while it is needed for monitoring, troubleshooting, or auditing. A retention period and archiving process may be defined when the extraction service is deployed in its intended environment.

The current code does not implement automatic log rotation or deletion.

---

# Extraction Data Contract and Naming Convention

## 1. Output Structure

The extraction output consists of one CSV file per configured source table. The CSV file contains the columns returned by the source table's `SELECT *` query.

| Source table | Output file |
|---|---|
| `sale` | `raw_data/sale.csv` |
| `oil_sale` | `raw_data/oil_sale.csv` |
| `fuel` | `raw_data/fuel.csv` |
| `oil_product` | `raw_data/oil_product.csv` |
| `fuel_sale_batch` | `raw_data/fuel_sale_batch.csv` |
| `fuel_batch` | `raw_data/fuel_batch.csv` |
| `expense` | `raw_data/expense.csv` |
| `restockLog` | `raw_data/restockLog.csv` |
| `oil_restock_log` | `raw_data/oil_restock_log.csv` |

The output directory is `raw_data`. It is created automatically if it does not exist.

## 2. Naming Convention

- Output files use the source table name with the `.csv` extension.
- Source column names are preserved as returned by the database.
- The current extraction script does not rename columns or convert source data types.
- Each extraction run writes to the same table-specific file path. A subsequent run overwrites the previous CSV file for that table.
- The run ID is recorded in the audit log but is not currently included in the CSV filename.

## 3. Schema Consistency

Because the extraction uses `SELECT *`, the output schema follows the current source table schema. If a source column is added, removed, or renamed, the CSV structure may change.

The current script does not compare the source schema against a predefined data contract. Unexpected schema changes should therefore be identified during review or in a later validation enhancement before the data is used for transformation.

No source-to-standardized column mapping is applied during extraction. Standardization and field mapping belong to the Transformation Stage unless explicitly required by the extraction process.

---

# Extraction Acceptance and Handover Rules

The current script records the extraction outcome for each source table. The following rules describe how the current output should be interpreted before it is handed to the Transformation Stage.

| Condition | Acceptance decision | Pipeline action |
|---|---|---|
| A table query succeeds and its CSV file is written | Extraction `SUCCESS` | The table's CSV file is available in `raw_data` for review and possible handover. |
| A table query fails | Extraction `FAILED` | The exception is recorded in the audit log. The script continues to the next table. The failed table must be re-extracted after the issue is resolved. |
| CSV writing fails | Extraction `FAILED` | The exception is recorded in the audit log. The affected output must be checked before it is used. |
| All configured tables complete successfully | All table extractions report `SUCCESS` | The extraction output may be handed to the Transformation Stage, subject to review of the run log. |
| One or more tables fail | Partial extraction run | Do not treat the full set of output files as a complete extraction package. Review the log and re-run the affected extraction after resolving the problem. |

### Handover Package

The extraction stage produces:

1. CSV files in the `raw_data` directory.
2. The local audit log in `logs/extraction.log`.
3. Per-table extraction status, record counts, timestamp range information when available, duration, and error information.

The current script does not implement automatic retries, quarantine handling, or a centralized overall approval status. These are not represented as implemented features in this documentation.

---

# Common Extraction Problems and Mitigation

| Problem | Possible cause | Impact on extraction | Mitigation |
|---|---|---|---|
| Database connection failure | Incorrect `DATABASE_URL`, unavailable database, network issue, or invalid credentials | The affected table cannot be extracted | Verify the environment variable, database availability, and credentials, then run the extraction again. |
| Source table not found | Table name mismatch or schema change | The query fails for the affected table | Confirm the exact table name in PostgreSQL and update `SOURCE_TABLES` if necessary. |
| Permission denied | Database role lacks read access to a source table | The affected table cannot be retrieved | Confirm that the database role has the required read permissions. |
| Source schema changes | A table's columns or types are modified | CSV structure may differ from what downstream processing expects | Review the source schema and update the pipeline or transformation mapping as required. |
| Large table extraction | Full-table extraction retrieves all available rows | Longer execution time and larger CSV files | Monitor file sizes and execution duration. Consider incremental extraction only after implementing and documenting the required timestamp filtering logic. |
| CSV output failure | Directory permissions, disk space, or interrupted file writing | A table's output may be missing or incomplete | Check the output directory, available disk space, and the recorded error; then rerun the extraction. |
| Scheduled run does not occur | The Python process or host is not running at the scheduled time | The weekly extraction is missed | Keep the host and extraction process running, or use an appropriate persistent scheduler environment. |
| Timestamp metadata is unavailable | A mapped timestamp column is absent or the table has no rows | The log reports `FULL_TABLE_DUMP` instead of a timestamp range | Confirm the source schema and mapping. The current metadata does not apply a date filter. |
| Timestamp mapping mismatch for expenses | `SOURCE_TABLES` contains `expense`, while `TIMESTAMP_COLUMNS` contains `expenses` | The `expense` table does not receive timestamp-range reporting from the current mapping | Align the mapping key with the actual table name after confirming the timestamp column in the source schema. |

---

## Summary

The current GAStoKITA extraction implementation performs full-table extraction from the configured PostgreSQL source tables. It writes each table's results to a CSV file in `raw_data` and appends a per-table audit report to `logs/extraction.log`.

The script schedules extraction every Sunday at 12:00 AM through APScheduler. A successful extraction status indicates that the query and CSV export completed without an exception. More advanced checks—such as primary key uniqueness, required-field completeness, foreign-key validation, and source-to-output count reconciliation—are not currently implemented.

The CSV files and audit log form the output of the Extraction Stage and provide the inputs and traceability information for the Transformation Stage.
