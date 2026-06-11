"""Index for report-only replay substrate schema fixture artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


SAFETY_FLAG_COLUMNS = [
    "report_only",
    "diagnostic_only",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_forward_labels_computed",
    "no_weights_trained",
    "no_active_stock_profile_created",
]

INDEX_COLUMNS = [
    "fixture_id",
    "created_at",
    "generated_at",
    "artifact_path",
    "status",
    "entity_count",
    "validation_issue_count",
    "overclaim_guard_pass_count",
    "overclaim_guard_total_count",
    "forward_labels_computed",
    "weights_trained",
    "active_stock_profile_created",
    "real_buy_review_eligible",
    *SAFETY_FLAG_COLUMNS,
    "missing_safety_flags",
    "report_path",
    "entity_status_path",
    "validation_issues_path",
    "overclaim_guards_path",
    "metadata_path",
]


@dataclass(frozen=True)
class ReplaySubstrateSchemaFixtureIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_replay_substrate_schema_fixture_index(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1/index",
) -> ReplaySubstrateSchemaFixtureIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "replay_substrate_schema_fixture_index.csv",
        "index_report": Path(output_dir) / "replay_substrate_schema_fixture_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ReplaySubstrateSchemaFixtureIndexResult(
        artifact_count=len(frame),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata=_audit_metadata(root, len(frame)),
    )
    write_replay_substrate_schema_fixture_index(result)
    return result


def write_replay_substrate_schema_fixture_index(result: ReplaySubstrateSchemaFixtureIndexResult) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths["index_csv"], index=False)
    metadata = {
        "index_id": _hash_payload(result.index_frame.to_dict("records")),
        "artifact_count": result.artifact_count,
        "warnings": result.warnings,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths["index_report"].write_text(
        "\n".join(
            [
                "# Replay Substrate Schema Fixture Index",
                "",
                "Report-only index; no replay, current-candidates, snapshots, labels, training, stock-profile activation, data writes, or cache mutation was invoked.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False) if not result.index_frame.empty else "No fixture artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Replay substrate schema fixture root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            warnings.append(f"Missing metadata for fixture artifact: {artifact_dir}")
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read fixture metadata {metadata_path}: {exc}")
            continue
        if _text(metadata.get("fixture_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    artifact_paths = metadata.get("artifact_paths") if isinstance(metadata.get("artifact_paths"), dict) else {}
    overclaim_path = Path(artifact_paths.get("overclaim_guards") or artifact_dir / "schema_fixture_overclaim_guards.csv")
    pass_count, total_count = _overclaim_counts(overclaim_path)
    missing = [flag for flag in SAFETY_FLAG_COLUMNS if flag not in metadata]
    created_at = _text(metadata.get("created_at")) or _artifact_mtime(artifact_dir)
    generated_at = _text(metadata.get("generated_at")) or created_at
    return {
        "fixture_id": _text(metadata.get("fixture_id")) or artifact_dir.name,
        "created_at": created_at,
        "generated_at": generated_at,
        "artifact_path": str(artifact_dir),
        "status": _text(metadata.get("status")),
        "entity_count": _to_int(metadata.get("entity_count")),
        "validation_issue_count": _to_int(metadata.get("validation_issue_count")),
        "overclaim_guard_pass_count": pass_count,
        "overclaim_guard_total_count": total_count,
        "forward_labels_computed": not _to_bool(metadata.get("no_forward_labels_computed")),
        "weights_trained": not _to_bool(metadata.get("no_weights_trained")),
        "active_stock_profile_created": not _to_bool(metadata.get("no_active_stock_profile_created")),
        "real_buy_review_eligible": _to_bool(metadata.get("real_buy_review_eligible")),
        "report_only": _to_bool(metadata.get("report_only")),
        "diagnostic_only": _to_bool(metadata.get("diagnostic_only")),
        "no_live_trading": _to_bool(metadata.get("no_live_trading")),
        "no_broker_api": _to_bool(metadata.get("no_broker_api")),
        "no_order_placement": _to_bool(metadata.get("no_order_placement")),
        "no_forward_labels_computed": _to_bool(metadata.get("no_forward_labels_computed")),
        "no_weights_trained": _to_bool(metadata.get("no_weights_trained")),
        "no_active_stock_profile_created": _to_bool(metadata.get("no_active_stock_profile_created")),
        "missing_safety_flags": ";".join(missing),
        "report_path": str(Path(artifact_paths.get("report") or artifact_dir / "replay_substrate_schema_fixture_report.md")),
        "entity_status_path": str(Path(artifact_paths.get("entity_status") or artifact_dir / "schema_fixture_entity_status.csv")),
        "validation_issues_path": str(Path(artifact_paths.get("validation_issues") or artifact_dir / "schema_fixture_validation_issues.csv")),
        "overclaim_guards_path": str(overclaim_path),
        "metadata_path": str(metadata_path),
    }


def _overclaim_counts(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    frame = pd.read_csv(path, dtype=object)
    if "passed" not in frame.columns:
        return 0, len(frame)
    passed = int(frame["passed"].map(_to_bool).sum())
    return passed, len(frame)


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS, dtype=object)
    for column in INDEX_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, INDEX_COLUMNS].astype(object)


def _audit_metadata(root: str | Path, artifact_count: int) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "artifact_count": artifact_count,
        "report_only": True,
        "diagnostic_only": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_forward_labels_computed": True,
        "no_weights_trained": True,
        "no_active_stock_profile_created": True,
        "real_buy_review_eligible": False,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_data_cache_write": True,
        "no_cache_mutation": True,
    }


def _artifact_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _hash_payload(value: Any) -> str:
    return hashlib.sha256(json.dumps(_json_safe(value), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
