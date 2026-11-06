# GAStoKITA Data Transformation Documentation

# 1. Transformation Input and Processing Specification

## 1. Input Source

**Input staging area:** `raw_data`

**Input format:** CSV files produced by the Extraction Stage.

**Expected input files used by this transformation:**

| Input file | Purpose |
|---|---|
| `raw_data/sale.csv` | Fuel sales transactions |
| `raw_data/oil_sale.csv` | Oil/non-fuel sales transactions |
| `raw_data/expense.csv` | Operational expense records |

The Transformation Stage receives the CSV outputs produced by the Extraction Stage. It does **not** connect to or re-extract data from the PostgreSQL source system. The Extraction Stage documents that its output is written to `raw_data` and handed to the Transformation Stage. 

The transformation code does not receive or read an extraction `run_id` from the handover package. The analytics process creates its own transformation/analytics run ID in the form:

```text
ANLYT-XXXXXXXX
```

where `XXXXXXXX` is an uppercase eight-character UUID fragment.

### Batch Window

The transformation calculates a rolling seven-day analytical window:

```text
week_start = current UTC timestamp - 7 days
```

Records are included when their transaction/expense timestamp is greater than or equal to `week_start`.

The actual computation is scheduled every **Sunday at 12:00 AM** by APScheduler.

### Batch Processing Method

**Technology:**

- Python
- Pandas
- APScheduler
- CSV files

The process runs as a background scheduler inside the Python process. The host and Python process must remain active for the scheduled job to execute.

The scheduled job calls:

```text
compute_analytics()
```

The processing sequence is:

1. Verify that the required raw CSV files exist.
2. Verify that each required input file contains the expected columns.
3. Select only the columns required by the transformation.
4. Drop records whose `id` is null.
5. Write the prepared datasets to `transformed/`.
6. Read the prepared datasets.
7. Convert timestamp fields to UTC-aware datetime values.
8. Select records from the most recent seven-day window.
9. Calculate weekly net-profit analytics.
10. Calculate weekly attendant rankings.
11. Write the analytical summaries to `analytics_output/`.
12. Append an audit record to `logs/transformation.log` for each analytical output.

### Rerun and Idempotency

The output files are written using fixed filenames:

```text
analytics_output/weekly_net_profit_summary.csv
analytics_output/weekly_attendant_rankings.csv
```

Therefore, a successful rerun replaces the previous analytical CSV files rather than appending duplicate summary rows.

The transformed staging files are also written to fixed filenames:

```text
transformed/sale.csv
transformed/oil_sale.csv
transformed/expense.csv
```

The implementation is therefore **effectively idempotent for the same raw input files and current seven-day window** because the files are overwritten. However, the process does not store a batch ID in the output filenames and does not preserve historical output versions.

A failed computation is not automatically retried by the code. The scheduler will execute again at the next scheduled Sunday run, or the function can be invoked manually by the operator.

---

## 2. Transformation Scope

The transformation explicitly processes three source datasets:

| Dataset | Important input columns | Main use |
|---|---|---|
| `sale` | `id`, `fuel_id`, `sold_at`, `liters_sold`, `total_amount`, `attendant_name` | Fuel revenue and attendant performance |
| `oil_sale` | `id`, `oil_product_id`, `sold_at`, `quantity`, `total_amount`, `attendant_name` | Oil revenue and attendant performance |
| `expense` | `id`, `amount`, `category`, `expense_date` | Weekly operating expenses |

The transformation performs:

- Schema validation
- Required-column selection
- Null-ID removal
- Date/time standardization to UTC-aware datetimes
- Seven-day filtering
- Revenue aggregation
- Expense aggregation
- Net-profit calculation
- Net-margin calculation
- Attendant-level aggregation and ranking
- CSV output generation
- Transformation audit logging

No joins between the three source datasets are performed.

The `fuel_id` and `oil_product_id` fields are preserved in the transformed files but are not used in the current analytics calculations.

---

## 3. Dependencies and Assumptions

The transformation depends on the Extraction Stage having produced the following files:

```text
raw_data/sale.csv
raw_data/oil_sale.csv
raw_data/expense.csv
```

The implementation assumes:

1. The raw CSV files exist before `compute_analytics()` begins.
2. Each required CSV contains all columns declared in `REQUIRED_SCHEMA`.
3. The `id` column identifies a record and is required for the transformed staging file.
4. `sale.sold_at` and `oil_sale.sold_at` contain values that Pandas can convert to UTC-aware timestamps.
5. `expense.expense_date` contains values that Pandas can convert to UTC-aware timestamps.
6. `total_amount` and `amount` contain numeric values suitable for summation.
7. `attendant_name` can be used as the grouping key for attendant rankings.
8. The rolling seven-day window is the intended business reporting period.
9. The raw files represent the latest extraction handover available to the transformation process.

The current implementation does not implement lookup-table processing, foreign-key validation, late-arriving-data reconciliation, or quarantine storage.



# 2. Data Profiling and Issue Identification

The current implementation performs limited profiling as part of the transformation rather than maintaining a separate profiling report.

The code explicitly checks for:

- Missing raw files.
- Missing required columns.
- Null values in the `id` field.

The code does **not** calculate a separate percentage of affected records, duplicate counts, invalid numeric-value counts, or outlier statistics before transformation.

| Table/File | Column | Issue Type | Detection in Code | Treatment |
|---|---|---|---|---|
| `sale.csv` | Required columns | Missing schema fields | Checks `REQUIRED_SCHEMA["sale"]` | Stop transformation before analytics |
| `oil_sale.csv` | Required columns | Missing schema fields | Checks `REQUIRED_SCHEMA["oil_sale"]` | Stop transformation before analytics |
| `expense.csv` | Required columns | Missing schema fields | Checks `REQUIRED_SCHEMA["expense"]` | Stop transformation before analytics |
| `sale.csv` | `id` | Null identifier | `dropna(subset=["id"])` | Remove from transformed file |
| `oil_sale.csv` | `id` | Null identifier | `dropna(subset=["id"])` | Remove from transformed file |
| `expense.csv` | `id` | Null identifier | `dropna(subset=["id"])` | Remove from transformed file |
| Sales timestamps | `sold_at` | Date/time representation | `pd.to_datetime(..., utc=True)` | Convert to UTC-aware datetime |
| Expenses | `expense_date` | Date/time representation | `pd.to_datetime(..., utc=True)` | Convert to UTC-aware datetime |

### Important Implementation Limitation

The Lab 4 specification requires rejected records to be counted and logged. The current code removes null-ID records with `dropna()` but does not count those removed rows separately.

The audit report initializes:

```text
rejected_records = 0
```

and never updates this value when null-ID records are removed.

Therefore, the current implementation does **not yet provide complete rejection accounting** for null-ID records. This should be treated as a known documentation/code gap rather than claiming that rejected records are fully tracked.

The transformation also does not explicitly detect or remove duplicate IDs.



# 3. Data Cleaning Rules

## Cleaning Rule C-01 — Required Schema Validation

| Field | Specification |
|---|---|
| Rule ID | `C-01` |
| Target | `sale`, `oil_sale`, `expense` input files |
| Condition | One or more required columns are absent |
| Action | Print an error and abort the analytics computation |
| Justification | Analytics cannot safely proceed when required input fields are unavailable |

The required schemas are:

```text
sale:
id, fuel_id, sold_at, liters_sold, total_amount, attendant_name

oil_sale:
id, oil_product_id, sold_at, quantity, total_amount, attendant_name

expense:
id, amount, category, expense_date
```

## Cleaning Rule C-02 — Remove Records Without IDs

| Field | Specification |
|---|---|
| Rule ID | `C-02` |
| Target | `sale.id`, `oil_sale.id`, `expense.id` |
| Condition | `id` is null |
| Action | Drop the record from the transformed CSV |
| Justification | The transformation requires an identifiable transaction/expense record for traceability |

Implementation:

```python
df_raw[cols].dropna(subset=["id"]).copy()
```

**Current limitation:** the removed record count is not assigned to `rejected_records` in the audit report.

## Cleaning Rule C-03 — Select Only Required Columns

| Field | Specification |
|---|---|
| Rule ID | `C-03` |
| Target | All three input datasets |
| Condition | Raw extraction contains columns beyond the transformation contract |
| Action | Select only the columns declared in `REQUIRED_SCHEMA` |
| Justification | Produces a predictable transformed staging schema and removes fields not required by this stage |

## Cleaning Rule C-04 — Missing Raw File Handling

| Field | Specification |
|---|---|
| Rule ID | `C-04` |
| Target | Required raw CSV files |
| Condition | Expected file does not exist |
| Action | Print an error and return `False`; analytics computation stops |
| Justification | Prevents analytics from being calculated from an incomplete input handover |

### Duplicate Handling

The current code does **not** implement duplicate detection or duplicate removal.

Consequently, duplicate transaction IDs in the raw files can remain in the transformed files and can contribute to the analytics aggregates.



# 4. Standardization and Data Type Rules

## S-01 — UTC Timestamp Standardization

The transformation converts the relevant date/time columns using Pandas:

```python
pd.to_datetime(column, utc=True)
```

| Rule ID | Column | Standard | Failure Behavior |
|---|---|---|---|
| `S-01` | `sale.sold_at` | UTC-aware datetime | Exception causes analytics section to fail |
| `S-01` | `oil_sale.sold_at` | UTC-aware datetime | Exception causes analytics section to fail |
| `S-01` | `expense.expense_date` | UTC-aware datetime | Exception causes analytics section to fail |

The current process does not explicitly define a fallback value for an unparseable timestamp. Conversion errors are handled by the surrounding `try` block for the analytics computation and are recorded in the transformation audit log.

## S-02 — Numeric Aggregation

The code explicitly converts the final revenue/expense aggregate values to Python `float` values before writing the summary:

```python
float(...)
```

The summary monetary values are rounded to two decimal places:

```python
round(value, 2)
```

The output therefore uses two decimal places for:

- `fuel_revenue`
- `oil_revenue`
- `total_revenue`
- `total_expenses`
- `net_profit`
- `net_margin_percent`

The source numeric columns themselves are not explicitly cast to a fixed decimal type before aggregation.

## S-03 — Text Standardization

No text casing, trimming, or character normalization is implemented.

For example, `attendant_name` values are grouped using their values as supplied in the transformed CSV. Differences such as `"John"` and `"john"` are therefore treated as different grouping keys.

## S-04 — Conversion Failure Handling

A conversion or calculation exception causes the relevant analytics computation to be marked:

```text
status = FAILED
validation_results = FAIL
```

The exception text is stored in:

```text
error_message
```



# 5. Business Transformation Rules

## B-01 — Weekly Fuel Revenue

**Input:** `recent_sales.total_amount`

**Logic:**

```text
fuel_revenue = SUM(sale.total_amount)
```

Only fuel sales within the rolling seven-day window are included.

## B-02 — Weekly Oil Revenue

**Input:** `recent_oil.total_amount`

**Logic:**

```text
oil_revenue = SUM(oil_sale.total_amount)
```

Only oil sales within the rolling seven-day window are included.

## B-03 — Total Revenue

**Input:** `fuel_revenue`, `oil_revenue`

**Logic:**

```text
total_revenue = fuel_revenue + oil_revenue
```

## B-04 — Weekly Operating Expenses

**Input:** `recent_expenses.amount`

**Logic:**

```text
total_expenses = SUM(expense.amount)
```

Only expenses whose `expense_date` is within the rolling seven-day window are included.

## B-05 — Weekly Net Profit

**Input:** `total_revenue`, `total_expenses`

**Logic:**

```text
net_profit = total_revenue - total_expenses
```

## B-06 — Net Margin

**Input:** `net_profit`, `total_revenue`

**Logic:**

```text
net_margin_percent = (net_profit / total_revenue) * 100
```

If `total_revenue` is zero, the implementation sets `net_margin_percent` to `0.0` to avoid division by zero.

## B-07 — Weekly Transaction Count

**Input:** recent fuel and oil sales

**Logic:**

```text
total_transactions = len(recent_sales) + len(recent_oil)
```

## B-08 — Attendant Fuel Aggregation

Fuel sales are grouped by `attendant_name`.

The following measures are calculated:

```text
fuel_revenue      = SUM(total_amount)
fuel_transactions = COUNT(id)
liters_sold       = SUM(liters_sold)
```

## B-09 — Attendant Oil Aggregation

Oil sales are grouped by `attendant_name`.

The following measures are calculated:

```text
oil_revenue       = SUM(total_amount)
oil_transactions  = COUNT(id)
oil_quantity      = SUM(quantity)
```

## B-10 — Attendant Combined Revenue

Fuel and oil attendant summaries are merged using an outer join on:

```text
attendant_name
```

Missing values after the merge are filled with zero.

Then:

```text
total_revenue = fuel_revenue + oil_revenue
```

## B-11 — Attendant Transaction Count

```text
total_transactions = fuel_transactions + oil_transactions
```

## B-12 — Attendant Ranking

Attendants are sorted by `total_revenue` in descending order.

Ranks are then assigned sequentially:

```text
1, 2, 3, ...
```

The ranking is based on total revenue, not transaction count, liters, or oil quantity.

### Analytics Outputs

The transformation generates two business-ready CSV summaries:

1. `weekly_net_profit_summary.csv`
2. `weekly_attendant_rankings.csv`



# 6. Transformed Data Contract and Naming Convention

## 1. Transformed Staging Files

The transformation creates:

| Output file | Purpose |
|---|---|
| `transformed/sale.csv` | Cleaned fuel sales records |
| `transformed/oil_sale.csv` | Cleaned oil sales records |
| `transformed/expense.csv` | Cleaned expense records |

### `transformed/sale.csv`

| Column | Source | Purpose |
|---|---|---|
| `id` | `sale.id` | Fuel sale identifier |
| `fuel_id` | `sale.fuel_id` | Fuel product identifier |
| `sold_at` | `sale.sold_at` | Fuel sale timestamp |
| `liters_sold` | `sale.liters_sold` | Volume sold |
| `total_amount` | `sale.total_amount` | Fuel sale amount |
| `attendant_name` | `sale.attendant_name` | Attendant identifier/name |

### `transformed/oil_sale.csv`

| Column | Source | Purpose |
|---|---|---|
| `id` | `oil_sale.id` | Oil sale identifier |
| `oil_product_id` | `oil_sale.oil_product_id` | Oil product identifier |
| `sold_at` | `oil_sale.sold_at` | Oil sale timestamp |
| `quantity` | `oil_sale.quantity` | Quantity sold |
| `total_amount` | `oil_sale.total_amount` | Oil sale amount |
| `attendant_name` | `oil_sale.attendant_name` | Attendant identifier/name |

### `transformed/expense.csv`

| Column | Source | Purpose |
|---|---|---|
| `id` | `expense.id` | Expense identifier |
| `amount` | `expense.amount` | Expense amount |
| `category` | `expense.category` | Expense category |
| `expense_date` | `expense.expense_date` | Expense date |

## 2. Analytics Output Contract

### `weekly_net_profit_summary.csv`

The output contains one summary row for the current transformation run.

| Column | Description |
|---|---|
| `summary_date` | UTC current date at the start of the analytics run |
| `fuel_revenue` | Fuel revenue during the seven-day window |
| `oil_revenue` | Oil revenue during the seven-day window |
| `total_revenue` | Fuel revenue plus oil revenue |
| `total_expenses` | Expenses during the seven-day window |
| `net_profit` | Total revenue minus total expenses |
| `net_margin_percent` | Net profit as a percentage of total revenue |
| `total_transactions` | Fuel and oil transaction count |

### `weekly_attendant_rankings.csv`

The output contains one row per attendant represented in either fuel or oil sales.

| Column | Description |
|---|---|
| `attendant_name` | Attendant grouping key |
| `fuel_revenue` | Fuel revenue attributed to attendant |
| `fuel_transactions` | Fuel transaction count |
| `liters_sold` | Fuel volume sold |
| `oil_revenue` | Oil revenue attributed to attendant |
| `oil_transactions` | Oil transaction count |
| `oil_quantity` | Oil quantity sold |
| `total_revenue` | Combined fuel and oil revenue |
| `total_transactions` | Combined fuel and oil transactions |
| `rank` | Revenue ranking |
| `summary_date` | UTC current date at the start of the analytics run |

## 3. Naming Convention

- Directories use lowercase descriptive names with underscores where applicable.
- Transformed CSV filenames use the source dataset name.
- Analytics filenames use descriptive `snake_case`.
- Columns use `snake_case`.
- No surrogate keys are generated.
- No dimensional-model prefixes such as `dim_` or `fact_` are used.
- The output files do not contain the transformation `run_id`.

## 4. Schema Consistency

The transformation checks that all required input columns exist before creating the transformed files.

If one or more required columns are missing, the transformation stops before analytics computation.

Unexpected extra columns are ignored because the code selects only the columns listed in `REQUIRED_SCHEMA`.



# 7. Transformation Validation and Data Quality Checks

The current implementation performs validation primarily through schema checks and successful completion of the analytics computations.

| Check Name | Target | Purpose | Current Criteria | Severity |
|---|---|---|---|---|
| Required file check | `raw_data/*.csv` | Ensure all required inputs exist | All three files must exist | Critical |
| Required column check | Three raw datasets | Prevent missing fields from entering analytics | Every field in `REQUIRED_SCHEMA` must be present | Critical |
| ID completeness | Transformed staging files | Remove records without IDs | Null `id` records are dropped | Critical |
| Timestamp conversion | Sales and expense timestamps | Standardize date/time processing | `pd.to_datetime(..., utc=True)` must succeed | Critical |
| Net-profit computation | `weekly_net_profit_summary.csv` | Confirm analytical summary can be generated | Summary CSV successfully written | Critical |
| Attendant ranking computation | `weekly_attendant_rankings.csv` | Confirm ranking summary can be generated | Ranking CSV successfully written when data is available | Critical |
| Output schema | Analytics CSVs | Ensure expected output fields are generated | DataFrame is constructed with documented columns | Critical |
| Record reconciliation | Raw vs transformed | Detect silently lost records | **Not fully implemented**; null-ID removals are not counted in `rejected_records` | Critical |
| Duplicate detection | IDs | Prevent duplicate contributions | **Not implemented** | Critical |
| Referential integrity | Product/transaction relationships | Detect orphan records | **Not implemented** | Critical |
| Aggregate reconciliation | Input vs analytical totals | Detect incorrect aggregation | **Not implemented as a separate comparison** | Critical |
| Negative-value validation | Revenue/expenses | Detect invalid business values | **Not implemented** | Non-critical |

### Validation Status

For each analytics output, the report starts as:

```text
status = FAILED
validation_results = PENDING
```

If the computation and output writing complete successfully, the report becomes:

```text
status = SUCCESS
validation_results = PASS
```

If an exception occurs:

```text
status = FAILED
validation_results = FAIL
```

The current `PASS` status therefore means that the implemented computation and file-writing operations completed successfully. It does not mean that all Lab 4 data-quality requirements have been fully validated.

### Record Reconciliation Limitation

The Lab 4 specification requires a reconciliation relationship for row-level cleaning:

```text
records_in = records_output + records_rejected
```

The current code does not maintain the required counts for this equation. Specifically, records removed by `dropna(subset=["id"])` are not added to `rejected_records`.

This is a known implementation gap.



# 8. Transformation Metadata and Log Specification

The transformation creates one analytics run ID:

```text
ANLYT-XXXXXXXX
```

Audit records are appended to:

```text
logs/transformation.log
```

## Metadata Fields

| Field | Purpose | Example / format |
|---|---|---|
| `run_id` | Identifies the analytics/transformation execution | `ANLYT-7F3A91BC` |
| `metric_target` | Identifies the analytical output being generated | `weekly_net_profit_summary` |
| `start_time` | Start of the individual analytical computation | UTC ISO 8601 |
| `end_time` | End of the individual analytical computation | UTC ISO 8601 |
| `status` | Result of the computation | `SUCCESS` / `FAILED` |
| `records_processed` | Number of records included in the seven-day input datasets | Integer |
| `summaries_generated` | Number of rows generated in the analytical output | Integer |
| `rejected_records` | Intended count of rejected records | Currently remains `0` in the implementation |
| `target_dest` | Output CSV path | `analytics_output/weekly_net_profit_summary.csv` |
| `validation_results` | Analytics validation outcome | `PASS` / `FAIL` / `PENDING` |
| `error_message` | Exception information when applicable | Error text or `None` |
| `duration_seconds` | Computation duration | Decimal seconds |

Two audit entries are generated for each successful invocation of `compute_analytics()` under normal conditions:

1. `weekly_net_profit_summary`
2. `weekly_attendant_rankings`

The same `run_id` is used for both analytical outputs.

### Monitoring and Troubleshooting

The log supports:

- Identifying the transformation run.
- Identifying which analytical metric failed.
- Tracking processing duration.
- Recording output destinations.
- Recording validation status.
- Reviewing exception messages.
- Tracking the number of source records included in the analytical window.

The log is a local text file and is appended to over time.

### Parent Extraction Run

The Lab 4 specification calls for a linked `parent_run_id`. The current code does **not** receive or record the Extraction Stage run ID.

The transformation run is therefore traceable to the raw staging files and its own `run_id`, but it does not currently provide an explicit machine-readable parent extraction run ID.

### Transformation Code Version

A transformation code version is also required by the Lab 4 specification. The current implementation does not record a code or rules version in `transformation.log`.



# 9. Log Retention, Rejected Data, and Access

| Requirement | Current implementation |
|---|---|
| Log storage | Local `logs/transformation.log` |
| Log format | Structured text audit entries |
| Retention period | No automatic retention/deletion policy |
| Access | Controlled by permissions on the host filesystem |
| Archiving | Not implemented |
| Automatic deletion | Not implemented |
| Rejected-record storage | No quarantine file/table is implemented |

The transformation log should be retained while it is required for monitoring, troubleshooting, auditing, and recovery.

The current transformation does not create a dedicated quarantine directory.

Records with null IDs are removed from the transformed staging data, but the removed records themselves are not copied to a quarantine file and their count is not recorded in the audit report.

This is a limitation against the Lab 4 requirement that rejected records should be traceable with a rejection reason, batch ID, and rule ID.

No unnecessary source data is intentionally written to the transformation log.



# 10. Transformation Acceptance and Handover Rules

The transformation stage should only hand analytical outputs to the Load Stage when the required inputs and computations have completed successfully.

## Decision Rules

| Overall Condition | Acceptance Decision | Pipeline Action |
|---|---|---|
| Required raw files missing | `REJECTED` | Stop the transformation and correct the extraction handover |
| Required input columns missing | `REJECTED` | Stop the transformation and resolve the schema mismatch |
| Timestamp conversion or analytics calculation fails | `REJECTED` | Record the error and stop the affected analytical computation |
| Net-profit output successfully generated and validated | `APPROVED` for that output | Make `weekly_net_profit_summary.csv` available for Load |
| Attendant ranking output successfully generated and validated | `APPROVED` for that output | Make `weekly_attendant_rankings.csv` available for Load |
| Non-critical data-quality concern not checked by the current code | `MANUAL REVIEW` | Review before relying on the affected output |

### Current Acceptance Behavior

The code does not implement a separate overall approval workflow.

Instead, each analytical calculation independently reports:

```text
SUCCESS / PASS
```

or:

```text
FAILED / FAIL
```

The transformation process itself does not enforce a configurable rejection-rate threshold.

### Handover Package

The intended handover from Transformation to Load consists of:

```text
transformed/
    sale.csv
    oil_sale.csv
    expense.csv

analytics_output/
    weekly_net_profit_summary.csv
    weekly_attendant_rankings.csv

logs/
    transformation.log
```

The two files in `analytics_output` are the main business-ready analytical outputs of this stage.

The `transformed/` files are cleaned intermediate datasets retained for downstream processing and traceability.



# 11. Common Transformation Problems and Mitigation

| Problem | Possible Cause | Impact | Mitigation |
|---|---|---|---|
| Required raw file missing | Extraction did not produce a required CSV | Analytics computation cannot start | Run/review the Extraction Stage and verify `raw_data` contents |
| Required column missing | Source schema changed or extraction output differs from expected schema | Transformation stops | Compare the raw CSV schema with `REQUIRED_SCHEMA` and update the contract/code as appropriate |
| Null transaction/expense IDs | Missing identifiers in source data | Records are removed from transformed staging | Count and log rejected records; optionally quarantine them |
| Duplicate IDs | Duplicate source records or repeated extraction data | Revenue and transaction totals may be inflated | Add duplicate detection and deterministic duplicate handling |
| Invalid timestamp | Source contains an unparseable date/time | Analytics computation fails | Validate timestamps before aggregation and quarantine invalid records |
| Invalid numeric amount | Revenue or expense field contains invalid data | Aggregate calculation can fail or become unreliable | Add numeric validation and reject/quarantine invalid values |
| Negative revenue/expense values | Invalid business data | Net profit may be distorted | Add explicit business-rule validation |
| Inconsistent attendant names | Different casing/whitespace for the same attendant | Rankings may split one attendant into multiple rows | Standardize whitespace/casing before grouping |
| Missing attendant name | Null or blank attendant value | Attendant ranking may contain an incomplete grouping key | Define a missing-attendant policy and validate it |
| Late-arriving transactions | Records arrive after a previous weekly run | Historical weekly summaries may change between runs | Re-run the seven-day window or implement a defined lookback/reprocessing policy |
| Rerun with changed raw files | Extraction output is overwritten | Current analytics may differ from a previous run | Preserve run metadata and source/extraction run IDs |
| Scheduler process stopped | Python process or host is not running | Scheduled Sunday run does not execute | Run the service in a persistent environment |
| Output overwritten | Fixed output filenames are reused | Previous summary version is not retained | Add versioned/run-specific output storage if historical snapshots are required |
| No parent extraction ID | Transformation does not receive extraction metadata | End-to-end lineage is incomplete | Add `parent_run_id` to the handover metadata |
| No quarantine | Rejected records are dropped without a retained copy | Troubleshooting and auditing are limited | Add a rejected-records/quarantine output with reason and rule ID |



# Summary

The GAStoKITA Transformation Stage receives CSV files from the Extraction Stage through the `raw_data` staging directory. The current implementation focuses on three datasets: `sale`, `oil_sale`, and `expense`.

The process first validates the presence of the required files and columns, selects the transformation-specific columns, and removes records with null IDs. It then standardizes timestamps to UTC, applies a rolling seven-day window, and produces two analytical outputs:

```text
analytics_output/weekly_net_profit_summary.csv
analytics_output/weekly_attendant_rankings.csv
```

The weekly net-profit summary calculates fuel revenue, oil revenue, total revenue, expenses, net profit, net margin, and transaction count. The attendant ranking summary combines fuel and oil sales by attendant and ranks attendants by total revenue.

The process runs every Sunday at 12:00 AM through APScheduler and writes transformation audit entries to `logs/transformation.log`.

The implementation satisfies the core transformation flow but has several known gaps against the full Lab 4 documentation requirements: rejected null-ID records are not counted or quarantined, duplicate detection is not implemented, comprehensive business/data-quality validation is not implemented, the extraction parent run ID is not carried forward, and code/rule version metadata is not recorded.

These limitations should be treated as implementation considerations for future enhancement rather than documented as features that the current code already provides.

The Transformation Stage produces the cleaned intermediate files, analytical CSV outputs, and audit logs required to support handover to the Load Stage. The Load Stage itself is outside the scope of this implementation.
