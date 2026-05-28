"""Local-only index for current-candidates backfill execution manifest artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns


EXECUTION_MANIFEST_INDEX_COLUMNS = [
    "artifact_type",
    "execution_manifest_id",
    "plan_id",
    "status",
    "row_count",
    "ready_count",
    "blocked_count",
    "blocked_missing_snapshot_count",
    "blocked_snapshot_quality_count",
    "blocked_universe_as_of_count",
    "blocked_plan_infeasible_count",
    "reviewed_execution_required_count",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "plan_only",
    "report_path",
    "manifest_csv_path",
    "metadata_path",
    "created_at",
]

INDEX_LIMITATIONS = [
    "Scans local current-candidates backfill execution manifest artifacts only.",
    "Does not run current-candidates, build snapshot manifests, run data-pipeline, or compute forward labels.",
    "Does not mutate cache, call APIs, send messages, place orders, call brokers, or enable live trading.",
]


@dataclass(frozen=True)
class CurrentCandidatesBackfillExecutionManifestIndexPaths:
    artifact_dir: Path
    current_candidates_backfill_execution_manifest_index_csv: Path
    current_candidates_backfill_execution_manifest_index_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "current_candidates_backfill_execution_manifest_index_csv": (
                self.current_candidates_backfill_execution_manifest_index_csv
            ),
            "current_candidates_backfill_execution_manifest_index_report": (
                self.current_candidates_backfill_execution_manifest_index_report
            ),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CurrentCandidatesBackfillExecutionManifestIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_current_candidates_backfill_execution_manifest_artifacts(
    root: str | Path = "outputs/reports/current_candidates_backfill_execution_manifest",
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    rows, _warnings = _scan_artifact_rows(Path(root), include_missing_metadata=include_missing_metadata)
    return _finalize_index_frame(pd.DataFrame(rows))


def build_current_candidates_backfill_execution_manifest_index(
    *,
    root: str | Path = "outputs/reports/current_candidates_backfill_execution_manifest",
    output_dir: str | Path = "outputs/reports/current_candidates_backfill_execution_manifest/index",
    include_missing_metadata: bool = False,
) -> CurrentCandidatesBackfillExecutionManifestIndexResult:
    effective_root = Path(root)
    rows, warnings = _scan_artifact_rows(effective_root, include_missing_metadata=include_missing_metadata)
    index_frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_current_candidates_backfill_execution_manifest_index_paths(output_dir)
    result = CurrentCandidatesBackfillExecutionManifestIndexResult(
        artifact_count=len(index_frame),
        index_frame=index_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=INDEX_LIMITATIONS,
        audit_metadata={
            "root_dir": effective_root,
            "artifact_count": len(index_frame),
            "include_missing_metadata": include_missing_metadata,
            "current_candidates_executed": False,
            "data_pipeline_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "network_api_called": False,
            "external_api_called": False,
            "llm_api_called": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "execution_manifest_artifacts_only": True,
        },
    )
    write_current_candidates_backfill_execution_manifest_index(result)
    return result


def resolve_current_candidates_backfill_execution_manifest_index_paths(
    output_dir: str | Path,
) -> CurrentCandidatesBackfillExecutionManifestIndexPaths:
    artifact_dir = Path(output_dir)
    return CurrentCandidatesBackfillExecutionManifestIndexPaths(
        artifact_dir=artifact_dir,
        current_candidates_backfill_execution_manifest_index_csv=(
            artifact_dir / "current_candidates_backfill_execution_manifest_index.csv"
        ),
        current_candidates_backfill_execution_manifest_index_report=(
            artifact_dir / "current_candidates_backfill_execution_manifest_index_report.md"
        ),
        metadata=artifact_dir / "metadata.json",
    )


def write_current_candidates_backfill_execution_manifest_index(
    result: CurrentCandidatesBackfillExecutionManifestIndexResult,
) -> dict[str, Path]:
    paths = CurrentCandidatesBackfillExecutionManifestIndexPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths.current_candidates_backfill_execution_manifest_index_csv, index=False)
    metadata = build_current_candidates_backfill_execution_manifest_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.current_candidates_backfill_execution_manifest_index_report.write_text(
        render_current_candidates_backfill_execution_manifest_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_current_candidates_backfill_execution_manifest_index_metadata(
    result: CurrentCandidatesBackfillExecutionManifestIndexResult,
    paths: CurrentCandidatesBackfillExecutionManifestIndexPaths,
) -> dict[str, Any]:
    return {
        "index_id": _hash_payload({"rows": result.index_frame.to_dict("records")}, length=12),
        "created_at": _metadata_created_at(result.index_frame),
        "artifact_count": result.artifact_count,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        **result.audit_metadata,
        "no_live_trading_statement": (
            "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
            "order placement, message delivery, or network/API call was invoked."
        ),
    }


def render_current_candidates_backfill_execution_manifest_index_report(
    result: CurrentCandidatesBackfillExecutionManifestIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {}
    return "\n".join(
        [
            "# Current-Candidates Backfill Execution Manifest Index",
            "",
            "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, or network/API call was invoked. This index scans local execution manifest artifacts only.",
            "",
            "## Summary",
            "",
            _dict_table({"index_id": meta.get("index_id", ""), "artifact_count": result.artifact_count}),
            "",
            "## Execution Manifests",
            "",
            _markdown_table(
                result.index_frame,
                [
                    "execution_manifest_id",
                    "plan_id",
                    "row_count",
                    "ready_count",
                    "blocked_count",
                    "blocked_universe_as_of_count",
                    "report_path",
                ],
            ),
            "",
            "## Warnings",
            "",
            _warnings_section(result.warnings),
            "",
        ]
    )


def _scan_artifact_rows(root: Path, *, include_missing_metadata: bool) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not root.exists():
        return rows, [f"Current-candidates backfill execution manifest root does not exist: {root}"]
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"}:
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir))
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read execution manifest metadata {metadata_path}: {exc}")
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, status="UNREADABLE_METADATA"))
            continue
        execution_manifest_id = _string_or_empty(metadata.get("execution_manifest_id"))
        if not execution_manifest_id:
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    manifest_csv = Path(
        output_files.get("execution_manifest_csv")
        or artifact_dir / "current_candidates_backfill_execution_manifest.csv"
    )
    report = Path(output_files.get("report") or artifact_dir / "current_candidates_backfill_execution_manifest_report.md")
    manifest = _read_manifest_csv(manifest_csv)
    readiness_counts = _readiness_counts(manifest, metadata)
    return {
        "artifact_type": "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST",
        "execution_manifest_id": _string_or_empty(metadata.get("execution_manifest_id")) or artifact_dir.name,
        "plan_id": _first_value(manifest, "plan_id"),
        "status": _string_or_empty(metadata.get("status")) or "WARN",
        "row_count": _to_int(metadata.get("row_count", len(manifest))),
        "ready_count": _to_int(metadata.get("ready_count", readiness_counts.get("READY_FOR_REVIEW", 0))),
        "blocked_count": _to_int(metadata.get("blocked_count", _blocked_count_from_counts(readiness_counts))),
        "blocked_missing_snapshot_count": _to_int(readiness_counts.get("BLOCKED_MISSING_SNAPSHOT", 0)),
        "blocked_snapshot_quality_count": _to_int(readiness_counts.get("BLOCKED_SNAPSHOT_QUALITY", 0)),
        "blocked_universe_as_of_count": _to_int(readiness_counts.get("BLOCKED_UNIVERSE_AS_OF", 0)),
        "blocked_plan_infeasible_count": _to_int(readiness_counts.get("BLOCKED_PLAN_INFEASIBLE", 0)),
        "reviewed_execution_required_count": _true_count(manifest, "reviewed_execution_required"),
        "no_live_trading": _to_bool(metadata.get("no_live_trading", _all_true(manifest, "no_live_trading"))),
        "no_broker_api": _to_bool(metadata.get("no_broker_api", _all_true(manifest, "no_broker_api"))),
        "no_order_placement": _to_bool(metadata.get("no_order_placement", _all_true(manifest, "no_order_placement"))),
        "no_message_sent": _to_bool(metadata.get("no_message_sent", _all_true(manifest, "no_message_sent"))),
        "plan_only": _to_bool(metadata.get("plan_only", _all_true(manifest, "plan_only"))),
        "report_path": str(report),
        "manifest_csv_path": str(manifest_csv),
        "metadata_path": str(metadata_path),
        "created_at": _string_or_empty(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
    }


def _missing_metadata_row(artifact_dir: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    row = {column: "" for column in EXECUTION_MANIFEST_INDEX_COLUMNS}
    row.update(
        {
            "artifact_type": "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST",
            "execution_manifest_id": artifact_dir.name,
            "status": status,
            "report_path": str(artifact_dir / "current_candidates_backfill_execution_manifest_report.md"),
            "manifest_csv_path": str(artifact_dir / "current_candidates_backfill_execution_manifest.csv"),
            "metadata_path": str(artifact_dir / "metadata.json"),
            "created_at": _artifact_mtime(artifact_dir),
        }
    )
    return row


def _read_manifest_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception:
        return pd.DataFrame()


def _readiness_counts(manifest: pd.DataFrame, metadata: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    raw_counts = metadata.get("readiness_counts")
    if isinstance(raw_counts, dict):
        counts.update({str(key): _to_int(value) for key, value in raw_counts.items()})
    if not manifest.empty and "readiness_status" in manifest.columns:
        for status, count in manifest["readiness_status"].value_counts().items():
            counts[str(status)] = _to_int(count)
    return counts


def _blocked_count_from_counts(counts: dict[str, int]) -> int:
    return int(sum(value for key, value in counts.items() if str(key).startswith("BLOCKED_")))


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=EXECUTION_MANIFEST_INDEX_COLUMNS)
    output = frame.copy()
    for column in EXECUTION_MANIFEST_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    for column in ["no_live_trading", "no_broker_api", "no_order_placement", "no_message_sent", "plan_only"]:
        output[column] = output[column].map(_to_bool).astype(object)
    return output[EXECUTION_MANIFEST_INDEX_COLUMNS].sort_values(
        ["created_at", "execution_manifest_id"]
    ).reset_index(drop=True)


def _metadata_created_at(frame: pd.DataFrame) -> str:
    if frame.empty or "created_at" not in frame:
        return "1970-01-01T00:00:00+00:00"
    values = [str(value) for value in frame["created_at"].dropna().tolist() if str(value).strip()]
    return max(values) if values else "1970-01-01T00:00:00+00:00"


def _artifact_mtime(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return ""


def _first_value(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    return _string_or_empty(frame[column].iloc[0])


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_to_bool).sum())


def _all_true(frame: pd.DataFrame, column: str) -> bool:
    if frame.empty or column not in frame.columns:
        return False
    return bool(frame[column].map(_to_bool).all())


def _to_int(value: Any) -> int:
    try:
        if pd.isna(value):
            return 0
    except (TypeError, ValueError):
        pass
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item") and value.__class__.__module__.startswith("numpy"):
        return _json_safe(value.item())
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _dict_table(values: dict[str, Any]) -> str:
    return "\n".join(f"- {key}: {_format_markdown_value(value)}" for key, value in values.items())


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 100) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "No rows."
    return frame[available].head(max_rows).to_markdown(index=False)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)


def _format_markdown_value(value: Any) -> str:
    return "" if value is None else str(value).replace("\n", " ").replace("|", "\\|")
