# Snapshot Quality Preflight CLI v0.1

Snapshot Quality Preflight CLI flags let local replay-like commands run the Snapshot Quality Gate before the workflow starts.

This is local-only. It does not call market data APIs, require API tokens, connect to brokers, place orders, or automate execution.

## Purpose

Snapshot Quality Preflight already exists at the Python function level for:

- `run_replay(...)`
- `run_batch_replay(...)`
- `run_parameter_calibration(...)`
- `run_walk_forward_validation(...)`

The CLI flags expose the same behavior from Windows CMD or a local shell so users can block unsafe snapshots before replay, batch replay, calibration, or walk-forward validation runs.

## Supported Commands

The following local workflow commands support snapshot preflight flags:

- `replay-run`
- `replay` alias for `replay-run`
- `batch-replay`
- `parameter-calibration`
- `calibrate` alias for `parameter-calibration`
- `walk-forward`
- `current-candidates`

These commands are thin wrappers over existing Python workflow functions. They use local config and mock/local CSV data only.

## Common Flags

All supported workflow commands accept:

```text
--snapshot-manifest PATH
--enable-snapshot-preflight
--disable-snapshot-preflight
--block-on-fail
--allow-fail
--block-on-warn
--allow-warn
```

### --snapshot-manifest

Path to a local snapshot manifest JSON file.

If `--snapshot-manifest` is provided without `--enable-snapshot-preflight`, preflight is enabled by default.

### --enable-snapshot-preflight

Forces preflight on. A manifest must be supplied through `--snapshot-manifest` or config:

```yaml
snapshot_quality_preflight:
  enabled: true
  manifest_path: data/snapshots/example_snapshot_manifest.json
```

### --disable-snapshot-preflight

Forces preflight off for the command, even if `--snapshot-manifest` is also provided.

### --block-on-fail / --allow-fail

Default behavior is to block on `FAIL`.

- `--block-on-fail`: exit non-zero when the snapshot gate returns `FAIL`.
- `--allow-fail`: allow the workflow to continue after `FAIL`.

Allowing `FAIL` is not recommended for research runs.

### --block-on-warn / --allow-warn

Default behavior is to allow `WARN`.

- `--block-on-warn`: exit non-zero when the snapshot gate returns `WARN`.
- `--allow-warn`: continue after `WARN` and print warnings.

## Examples

Single-date replay:

```cmd
python -m quant_replay_system.cli replay-run --date 2024-01-03 --horizon 2 --snapshot-manifest data\snapshots\example_snapshot_manifest.json
```

Replay alias:

```cmd
python -m quant_replay_system.cli replay --date 2024-01-03 --snapshot-manifest data\snapshots\example_snapshot_manifest.json --allow-warn
```

Batch replay:

```cmd
python -m quant_replay_system.cli batch-replay --dates 2024-01-03,2024-01-04 --horizon 2 --snapshot-manifest data\snapshots\example_snapshot_manifest.json
```

Parameter calibration:

```cmd
python -m quant_replay_system.cli parameter-calibration --dates 2024-01-03,2024-01-04 --snapshot-manifest data\snapshots\example_snapshot_manifest.json --block-on-warn
```

Calibration alias:

```cmd
python -m quant_replay_system.cli calibrate --dates 2024-01-03 --snapshot-manifest data\snapshots\example_snapshot_manifest.json
```

Walk-forward validation:

```cmd
python -m quant_replay_system.cli walk-forward --train-dates 2024-01-03 --validation-dates 2024-01-04 --snapshot-manifest data\snapshots\example_snapshot_manifest.json
```

Current candidate generation:

```cmd
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5 --snapshot-manifest data\snapshots\example_snapshot_manifest.json
```

Disable preflight explicitly:

```cmd
python -m quant_replay_system.cli replay-run --date 2024-01-03 --snapshot-manifest data\snapshots\example_snapshot_manifest.json --disable-snapshot-preflight
```

## CLI Output

When preflight runs, commands print:

- snapshot quality status,
- snapshot quality report path,
- snapshot quality gate id,
- preflight warnings when present,
- workflow report path,
- `No live trading or broker API was invoked.`

If preflight blocks the workflow, the command exits non-zero and prints a clear error.

## Relationship To snapshot-quality

`snapshot-quality` runs the Snapshot Quality Gate directly.

The preflight flags run the same gate as a guard before replay-like workflows.

Use:

```cmd
python -m quant_replay_system.cli snapshot-quality --manifest data\snapshots\example_snapshot_manifest.json
```

when you want only the gate report.

Use `--snapshot-manifest` on replay-like commands when you want the gate checked immediately before a workflow.

## Known MVP Limitations

- CLI wrappers expose common workflow arguments only, not every function parameter.
- Commands use local config and mock/local CSV data only.
- Large calibration grids can still take time; keep MVP grids small.
- Current-candidate generation produces candidate artifacts only; it does not simulate T+1 execution or future returns.
- Preflight checks snapshot/file quality but does not repair data.
- No live trading or broker API integration is invoked.
