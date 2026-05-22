# Snapshot Quality Preflight v0.1

Snapshot Quality Preflight lets replay-like workflows run the Snapshot Quality Gate before they start.

It is optional and disabled by default. It is local-only, uses local CSV snapshot manifests, and never connects to brokers, places orders, automates execution, or calls market data APIs.

## Why Preflight Exists

Data Quality Summary Reports check individual files, and Snapshot Quality Gate checks a snapshot manifest as a complete unit.

Preflight connects that gate to downstream workflows so unsafe snapshots can stop replay-like runs before:

- single-date replay,
- batch replay,
- parameter calibration,
- walk-forward validation.

This keeps bad required datasets from silently entering research outputs.

## Configuration

Default settings live in `config/default.yaml`:

```yaml
snapshot_quality_preflight:
  enabled: false
  manifest_path:
  block_on_fail: true
  block_on_warn: false
  attach_report_paths: true
```

Behavior:

- `enabled: false`: workflows behave as before.
- `enabled: true`: a manifest path is required through config or a function argument.
- `block_on_fail: true`: a `FAIL` gate status raises `SnapshotQualityPreflightError`.
- `block_on_warn: true`: a `WARN` gate status also raises.
- `attach_report_paths: true`: preflight metadata includes the snapshot gate report and artifact paths.

## PASS / WARN / FAIL Behavior

- `PASS`: the workflow continues normally.
- `WARN` with `block_on_warn: false`: the workflow continues and records a warning.
- `WARN` with `block_on_warn: true`: the workflow stops with a clear error.
- `FAIL` with `block_on_fail: true`: the workflow stops with a clear error.
- `FAIL` with `block_on_fail: false`: the workflow can continue, but this is not recommended for replay research.

Failures are not silently ignored when preflight is enabled.

## Integration Points

Supported entry points:

- `run_replay(..., snapshot_manifest_path=...)`
- `run_batch_replay(..., snapshot_manifest_path=...)`
- `run_parameter_calibration(..., snapshot_manifest_path=...)`
- `run_walk_forward_validation(..., snapshot_manifest_path=...)`

Batch replay runs preflight once per batch, then disables nested preflight for per-date `run_replay` calls.

Parameter calibration runs preflight once per calibration run, then disables nested preflight for the batch runs in the parameter grid.

Walk-forward validation runs preflight once per walk-forward run, then disables nested preflight for train/validation/test calibration calls.

## Result Metadata

When preflight runs, result metadata includes:

- `snapshot_quality_preflight_enabled`
- `snapshot_quality_status`
- `snapshot_quality_report_path`
- `snapshot_quality_gate_id`
- `snapshot_quality_warnings`
- `snapshot_quality_manifest_path`
- `snapshot_quality_artifact_paths`

For replay, these fields are recorded in `audit_metadata`.

For batch replay, calibration, and walk-forward validation, these fields are recorded in artifact metadata and report sections.

## Example

Config-driven usage:

```yaml
snapshot_quality_preflight:
  enabled: true
  manifest_path: data/snapshots/example_snapshot_manifest.json
  block_on_fail: true
  block_on_warn: false
```

Function argument usage:

```python
from quant_replay_system.replay_run import run_replay

result = run_replay(
    "2024-01-03",
    snapshot_manifest_path="data/snapshots/example_snapshot_manifest.json",
)
```

CLI usage is documented in [snapshot_quality_preflight_cli.md](snapshot_quality_preflight_cli.md). Example:

```cmd
python -m quant_replay_system.cli replay-run --date 2024-01-03 --snapshot-manifest data\snapshots\example_snapshot_manifest.json
```

## How This Protects Research

Preflight is a checkpoint before replay-like workflows consume data. It helps ensure:

- required market data exists and passes quality checks,
- required universe data exists and passes quality checks,
- the trading calendar exists and passes quality checks,
- optional benchmark and corporate action issues are visible,
- downstream artifacts record the snapshot quality status.

## Known MVP Limitations

- Preflight is disabled by default and must be explicitly enabled.
- It checks snapshot structure and file-level quality, but does not repair data.
- It does not yet enforce coverage between universe symbols and market rows.
- It does not yet provide a current candidate generation command.
- It uses local CSV/mock data only.
- It never invokes live trading or broker APIs.
