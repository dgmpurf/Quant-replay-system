# Current Candidate Artifact Index v0.1

Current Candidate Artifact Index scans local `current-candidates` output folders and builds one consolidated navigation table.

It is local-only. It does not call data APIs, connect to brokers, place orders, automate execution, or change candidate scores.

## Why The Index Exists

`current-candidates` writes one folder per run:

```text
outputs/reports/current_candidates/<decision_date>_<universe_name>_<run_id>/
```

After several runs, it becomes easy to lose track of which folder has the `candidates.csv` that should be reviewed or passed to `paper-daily`.

The index reads `metadata.json` files and summarizes all discovered current-candidate artifacts.

## Scanned Folders

Default root:

```text
outputs/reports/current_candidates
```

The scanner looks at immediate child folders and skips:

- `index/`
- `health/`

Expected files in each run folder:

- `current_candidates_report.md`
- `factor_dataset.csv`
- `scored_dataset.csv`
- `candidates.csv`
- `metadata.json`

## Index Outputs

Default output folder:

```text
outputs/reports/current_candidates/index/
```

Files:

- `current_candidate_artifact_index.md`
- `current_candidate_artifact_index.csv`
- `current_candidate_artifact_index.json`
- `metadata.json`

Index columns include:

- `artifact_type`
- `run_id`
- `decision_date`
- `universe_name`
- `candidate_count`
- `factor_dataset_row_count`
- `scored_dataset_row_count`
- `snapshot_quality_status`
- `report_path`
- `factor_dataset_path`
- `scored_dataset_path`
- `candidates_path`
- `metadata_path`
- `created_at`
- `no_live_trading_statement_present`

## CLI Usage

Build an index from the default root:

```cmd
python -m quant_replay_system.cli current-candidates-index
```

Build an index from a specific root:

```cmd
python -m quant_replay_system.cli current-candidates-index --root outputs\reports\current_candidates
```

Write the index somewhere else:

```cmd
python -m quant_replay_system.cli current-candidates-index --root outputs\reports\current_candidates --output-dir outputs\reports\current_candidates\index
```

Include artifact folders missing `metadata.json`:

```cmd
python -m quant_replay_system.cli current-candidates-index --include-missing-metadata
```

The CLI prints artifact count, index report path, and:

```text
No live trading or broker API was invoked.
```

## Relationship To paper-daily

Use the `candidates_path` column to find the candidate CSV for manual paper trading:

```cmd
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --candidates outputs\reports\current_candidates\...\candidates.csv
```

Run the health check before passing a candidate file into paper trading when the artifact path may be stale.

## Known MVP Limitations

- Scans local current-candidate artifact folders only.
- Does not regenerate candidates or repair broken artifacts.
- Does not validate scoring correctness.
- Does not validate manual review or paper fills.
- No live trading or broker API integration is invoked.
