# Current Candidate To Paper Handoff v0.1

Current Candidate To Paper Handoff selects a local `candidates.csv` from current-candidate artifacts and launches the daily paper trading runner.

It is local-only. It does not connect to brokers, place orders, automate execution, print secrets, or call market data APIs.

## Purpose

The handoff helper connects two existing workflows:

```text
current-candidates -> current-candidates-index -> current-candidates-health -> current-to-paper -> paper-review-decisions
```

It makes the selected current-candidate source explicit, records handoff metadata, and writes a small audit report before manual review and fills continue.

## Direct Candidates Path Flow

Use an explicit `candidates.csv` when the file path is already known:

```cmd
python -m quant_replay_system.cli current-to-paper --candidates outputs\reports\current_candidates\example\candidates.csv --paper-date 2024-05-20
```

Direct path mode records:

- `source_type = DIRECT_CANDIDATES_PATH`
- selected `candidates.csv`
- inferred `run_id` from candidate columns or folder name
- inferred decision date when available

Artifact health checks are skipped for direct path mode unless an index/root workflow is used.

## Index Or Root Flow

Use an index CSV to select by decision date, universe, or run id:

```cmd
python -m quant_replay_system.cli current-to-paper --index outputs\reports\current_candidates\index\current_candidate_artifact_index.csv --decision-date 2024-05-20 --universe etf_core
```

Use a root folder when the index should be scanned from local artifacts:

```cmd
python -m quant_replay_system.cli current-to-paper --root outputs\reports\current_candidates --decision-date 2024-05-20
```

If multiple artifacts match, selection prefers:

1. latest `decision_date`,
2. highest `candidate_count`,
3. deterministic path sort.

## Health Requirements

Index and root handoffs run the current-candidate artifact health check by default.

Default behavior:

- `PASS`: accepted.
- `WARN`: rejected when `require_health_pass = true`.
- `FAIL`: rejected.

Allow warning artifacts explicitly:

```cmd
python -m quant_replay_system.cli current-to-paper --index outputs\reports\current_candidates\index\current_candidate_artifact_index.csv --allow-health-warn
```

Skip health checks explicitly:

```cmd
python -m quant_replay_system.cli current-to-paper --index outputs\reports\current_candidates\index\current_candidate_artifact_index.csv --skip-health-check
```

## Artifact Outputs

Default output folder:

```text
outputs/reports/current_to_paper_handoff/<handoff_id>/
```

Files:

- `handoff_report.md`
- `selected_current_candidate.json`
- `handoff_metadata.json`
- `paper_daily_artifacts.json`

The handoff also launches `paper-daily`, which writes its usual daily paper artifacts under the configured daily paper output directory.

## Paper Daily Relationship

The helper calls `run_daily_paper_trading(...)` with the selected `candidates.csv`.

The daily paper `metadata.json` is augmented with:

- `handoff_id`
- selected candidate path
- selected current-candidate report path
- selected metadata path
- selected run id
- selected decision date
- selected universe name
- health status

This keeps the paper decision log traceable back to the current-candidate run.

## CLI Usage

Direct path:

```cmd
python -m quant_replay_system.cli current-to-paper --candidates outputs\reports\current_candidates\example\candidates.csv --paper-date 2024-05-20
```

Index selection:

```cmd
python -m quant_replay_system.cli current-to-paper --index outputs\reports\current_candidates\index\current_candidate_artifact_index.csv --decision-date 2024-05-20 --universe etf_core
```

With fills:

```cmd
python -m quant_replay_system.cli current-to-paper --index outputs\reports\current_candidates\index\current_candidate_artifact_index.csv --decision-date 2024-05-20 --fills data\paper\fills.csv
```

The CLI prints selected candidates path, paper report path, handoff report path, and:

```text
No live trading or broker API was invoked.
```

## Workflow Example

```cmd
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5
python -m quant_replay_system.cli current-candidates-index --root outputs\reports\current_candidates
python -m quant_replay_system.cli current-candidates-health --index outputs\reports\current_candidates\index\current_candidate_artifact_index.csv
python -m quant_replay_system.cli current-to-paper --index outputs\reports\current_candidates\index\current_candidate_artifact_index.csv --decision-date 2024-05-20
python -m quant_replay_system.cli paper-review-decisions --decisions outputs\reports\paper_trading\daily\example\decisions.csv --updates data\paper\review_updates.csv
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --reviewed-decisions outputs\reports\paper_trading\reviews\example\reviewed_decisions.csv
python -m quant_replay_system.cli paper-reconcile-fills --decisions outputs\reports\paper_trading\daily\example\decisions.csv --fills data\paper\fills.csv
```

## Known MVP Limitations

- Uses local CSV/mock data only.
- Does not regenerate current candidates.
- Does not repair missing or stale artifacts.
- Direct `candidates.csv` mode skips health checks by default.
- Manual review is still required before fills should be entered.
- No live trading or broker API integration is implemented.
