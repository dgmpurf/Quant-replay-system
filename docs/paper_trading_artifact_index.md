# Paper Trading Artifact Index v0.1

Paper Trading Artifact Index scans local paper-trading artifact folders and builds one consolidated navigation table.

It is local-only. It does not connect to a broker, place orders, submit orders, or automate execution.

## Why It Is Useful

Daily paper trading now creates several artifact families:

- daily paper reports
- manual review reports
- fill reconciliation reports
- decisions, fills, reviewed decisions, summary CSVs, and metadata files

The index gives the user one place to find those reports and key status fields without manually opening each folder.

## Scanned Folders

By default the index scans:

```cmd
outputs\reports\paper_trading\daily
outputs\reports\paper_trading\reviews
outputs\reports\paper_trading\reconciliation
```

Each artifact folder is expected to contain `metadata.json`.

Folders without `metadata.json` are skipped by default. Use `--include-missing-metadata` to include them as warning rows.

## Index Outputs

The index writes:

```cmd
outputs\reports\paper_trading\index\paper_artifact_index.md
outputs\reports\paper_trading\index\paper_artifact_index.csv
outputs\reports\paper_trading\index\paper_artifact_index.json
outputs\reports\paper_trading\index\metadata.json
```

The index includes fields such as:

- artifact type and artifact ID
- created date/status
- report path
- metadata path
- decisions/reviewed decisions/fills paths
- reconciliation issue counts
- open and closed position counts
- paper cash and total equity when available
- whether the report contains the no-live-trading statement

## CLI Usage

Build the full paper artifact index:

```cmd
python -m quant_replay_system.cli paper-index --root outputs\reports\paper_trading
```

Write to a custom index folder:

```cmd
python -m quant_replay_system.cli paper-index --root outputs\reports\paper_trading --output-dir outputs\reports\paper_trading\index
```

Scan only daily paper artifacts:

```cmd
python -m quant_replay_system.cli paper-index --root outputs\reports\paper_trading --artifact-type daily
```

Include folders that are missing `metadata.json`:

```cmd
python -m quant_replay_system.cli paper-index --root outputs\reports\paper_trading --include-missing-metadata
```

The command prints the index report path, artifact count, warnings, and:

```text
No live trading or broker API was invoked.
```

## Daily Review Workflow

A typical local paper workflow is:

1. Generate daily decisions with `paper-daily`.
2. Review them with `paper-review-decisions`.
3. Reconcile manual fills with `paper-reconcile-fills`.
4. Generate the final daily paper report with reviewed decisions and fills.
5. Run `paper-index` to collect all daily, review, and reconciliation artifacts into one navigation report.

## Known MVP Limitations

- The index trusts existing `metadata.json` files and does not re-run accounting or reconciliation.
- Missing or malformed metadata is either skipped or included as a warning row.
- Report-path checks are local filesystem checks only.
- It does not deduplicate semantically equivalent reports across different output folders.
- It is not live trading and never invokes broker APIs.
