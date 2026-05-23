# Paper Trading Artifact Health Check v0.1

Paper Trading Artifact Health Check verifies that local paper-trading artifacts referenced by `paper_artifact_index.csv` still exist and are readable.

It is local-only. It does not connect to a broker, place orders, submit orders, or automate execution.

## Why Health Checks Are Needed

Paper trading workflows create many local files:

- daily paper reports
- review reports
- reconciliation reports
- decisions CSVs
- reviewed decisions CSVs
- fills CSVs
- metadata JSON files

After files are moved, deleted, or edited manually, the index may contain stale references. The health check catches those broken references before the user relies on the reports.

## What Is Checked

The health check reads an artifact index and validates:

- `report_path`
- `metadata_path`
- `decisions_path`
- `reviewed_decisions_path` when expected
- `fills_path` when expected
- `reconciliation_report_path` when expected

It also checks:

- CSV files are readable by pandas.
- JSON metadata can be parsed.
- required CSV artifacts are not empty.
- markdown reports contain the no-live-trading statement.
- metadata contains required audit fields.
- index rows use supported artifact types.

## Issue Codes

- `MISSING_PATH_VALUE`: a required path field is blank.
- `FILE_NOT_FOUND`: a referenced file no longer exists.
- `CSV_UNREADABLE`: a CSV file cannot be read.
- `JSON_UNREADABLE`: a metadata JSON file cannot be parsed.
- `CSV_EMPTY`: a required CSV artifact has no rows.
- `MISSING_REQUIRED_METADATA_FIELD`: metadata is missing a required audit field.
- `MISSING_NO_LIVE_TRADING_STATEMENT`: markdown report is missing the local-only safety statement.
- `BROKEN_ARTIFACT_REFERENCE`: index row or referenced path is malformed.
- `UNSUPPORTED_ARTIFACT_TYPE`: index row has an unsupported artifact type.

## Status

The health check returns:

- `PASS`: no issues.
- `WARN`: warnings exist, but no errors.
- `FAIL`: at least one error exists.

Missing files, unreadable JSON, unreadable CSVs, malformed references, and unsupported artifact types are errors.

Empty CSVs, missing no-live-trading statements, and missing metadata fields are configurable as `WARN` or `ERROR`. `--strict` escalates configurable warnings to errors.

## Warning Actionability

Health issues also include an `actionability` classification:

- `EXPECTED_DEMO_WARNING`: expected during an explicit local demo flow. For example, an empty `fills.csv` in a reviewed `WATCH_ONLY` daily paper run with no open positions, no closed trades, and no approved paper decisions.
- `ACTIONABLE_WARNING`: a warning that should be reviewed before relying on the artifact.
- `BLOCKING_ERROR`: an error such as a missing file, unreadable CSV, or unreadable JSON.

The raw `WARN` status is preserved. The classification helps dashboards explain whether a warning blocks the active workflow or is expected for a no-fills local demo.

The health summary and metadata include:

- `total_warning_count`
- `expected_demo_warning_count`
- `stale_warning_count`
- `actionable_warning_count`
- `blocking_error_count`

## CLI Usage

Check an existing paper artifact index:

```cmd
python -m quant_replay_system.cli paper-health-check --index outputs\reports\paper_trading\index\paper_artifact_index.csv
```

Scan a paper trading root through the index module, then health-check the discovered artifacts:

```cmd
python -m quant_replay_system.cli paper-health-check --root outputs\reports\paper_trading
```

Write health artifacts to a custom folder:

```cmd
python -m quant_replay_system.cli paper-health-check --index outputs\reports\paper_trading\index\paper_artifact_index.csv --output-dir outputs\reports\paper_trading\health
```

Strict mode:

```cmd
python -m quant_replay_system.cli paper-health-check --index outputs\reports\paper_trading\index\paper_artifact_index.csv --strict
```

Allow warnings to exit zero in strict mode:

```cmd
python -m quant_replay_system.cli paper-health-check --index outputs\reports\paper_trading\index\paper_artifact_index.csv --strict --allow-warn
```

The command prints:

- `PASS`, `WARN`, or `FAIL`
- checked artifact count
- issue counts
- report path
- `No live trading or broker API was invoked.`

It exits non-zero on `FAIL` by default.

## Artifacts

The health check writes:

```cmd
outputs\reports\paper_trading\health\<health_check_id>\artifact_health_report.md
outputs\reports\paper_trading\health\<health_check_id>\artifact_health_issues.csv
outputs\reports\paper_trading\health\<health_check_id>\artifact_health_summary.csv
outputs\reports\paper_trading\health\<health_check_id>\metadata.json
```

## Relationship To paper-index

`paper-index` builds the navigation table.

`paper-health-check` validates that the paths in that table still point to real, readable files.

A typical workflow is:

```cmd
python -m quant_replay_system.cli paper-index --root outputs\reports\paper_trading
python -m quant_replay_system.cli paper-health-check --index outputs\reports\paper_trading\index\paper_artifact_index.csv
```

## Known MVP Limitations

- The health check does not repair broken references.
- It does not re-run reconciliation or accounting.
- CSV checks are intentionally light and do not validate every schema column.
- Permission-related unreadability can vary by operating system.
- It is not live trading and never invokes broker APIs.
