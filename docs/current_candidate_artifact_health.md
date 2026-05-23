# Current Candidate Artifact Health Check v0.1

Current Candidate Artifact Health Check validates indexed current-candidate artifacts before `candidates.csv` is used in paper trading workflows.

It is local-only. It does not call data APIs, connect to brokers, place orders, automate execution, or change candidate scores.

## Why Health Checks Are Needed

Current-candidate artifacts can become stale if folders are moved, files are deleted, CSVs are edited manually, or reports are regenerated with old metadata.

The health check verifies that indexed file paths still exist, are readable, and contain the minimum fields needed for paper trading review.

## Checks Performed

For each indexed `CURRENT_CANDIDATES` artifact, the health check validates:

- `metadata_path` exists and is JSON-readable.
- `report_path` exists and markdown-readable.
- `candidates_path` exists and CSV-readable.
- `factor_dataset_path` exists and CSV-readable.
- `scored_dataset_path` exists and CSV-readable.
- `candidates.csv` is not empty.
- `candidates.csv` contains:
  - `symbol`
  - `final_score`
  - `action`
- `metadata.json` contains:
  - `decision_date`
  - `universe_name`
  - `run_id`
- markdown report contains a no-live-trading statement.
- snapshot quality status is present when snapshot preflight was enabled.

## PASS / WARN / FAIL

Status rules:

- `PASS`: no warnings or errors.
- `WARN`: warning issues only.
- `FAIL`: one or more error issues.

Default warning cases include:

- empty `candidates.csv`,
- missing no-live-trading statement,
- missing optional metadata fields.

With `--strict`, configurable warnings are treated as errors.

Downstream dashboards can classify warning actionability. For example, a current-candidate health warning from an older dry run can be shown as a stale artifact warning when its `run_id` does not match the active current-candidate run. The health check still preserves the raw warning rows.

## CLI Usage

Health check using an existing index CSV:

```cmd
python -m quant_replay_system.cli current-candidates-health --index outputs\reports\current_candidates\index\current_candidate_artifact_index.csv
```

Health check by scanning a root folder:

```cmd
python -m quant_replay_system.cli current-candidates-health --root outputs\reports\current_candidates
```

Strict mode:

```cmd
python -m quant_replay_system.cli current-candidates-health --index outputs\reports\current_candidates\index\current_candidate_artifact_index.csv --strict
```

Allow warnings in strict CLI mode:

```cmd
python -m quant_replay_system.cli current-candidates-health --index outputs\reports\current_candidates\index\current_candidate_artifact_index.csv --strict --allow-warn
```

The CLI prints status, issue counts, report path, and:

```text
No live trading or broker API was invoked.
```

## Health Outputs

Default output folder:

```text
outputs/reports/current_candidates/health/<health_check_id>/
```

Files:

- `current_candidate_artifact_health_report.md`
- `current_candidate_artifact_health_issues.csv`
- `current_candidate_artifact_health_summary.csv`
- `metadata.json`

## Known MVP Limitations

- Checks local files only.
- Does not regenerate artifacts or repair paths.
- Does not rerun factor dataset, scoring, or candidate selection.
- Does not validate whether candidates should be approved for paper trading.
- No live trading or broker API integration is invoked.
