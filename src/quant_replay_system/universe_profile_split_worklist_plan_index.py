"""Local-only index for universe profile split-worklist plan artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns


UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_INDEX_COLUMNS = [
    "artifact_type",
    "plan_id",
    "status",
    "row_count",
    "stock_row_count",
    "etf_row_count",
    "legacy_mixed_demo_row_count",
    "recommended_stock_core_count",
    "recommended_etf_core_count",
    "recommended_mixed_demo_core_count",
    "profile_conflict_count",
    "active_worklist_mutated",
    "no_approval_applied",
    "no_rejection_applied",
    "no_universe_export",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "plan_only",
    "report_path",
    "plan_csv_path",
    "summary_csv_path",
    "registry_snapshot_path",
    "stock_core_guidance_path",
    "etf_core_guidance_path",
    "mixed_demo_core_guidance_path",
    "metadata_path",
    "created_at",
]


@dataclass(frozen=True)
class UniverseProfileSplitWorklistPlanIndexPaths:
    artifact_dir: Path
    universe_profile_split_worklist_plan_index_csv: Path
    universe_profile_split_worklist_plan_index_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "universe_profile_split_worklist_plan_index_csv": self.universe_profile_split_worklist_plan_index_csv,
            "universe_profile_split_worklist_plan_index_report": self.universe_profile_split_worklist_plan_index_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class UniverseProfileSplitWorklistPlanIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def scan_universe_profile_split_worklist_plan_artifacts(
    root: str | Path = "outputs/reports/universe_profile_split_worklist_plan",
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    rows, _warnings = _scan_artifact_rows(Path(root), include_missing_metadata=include_missing_metadata)
    return _finalize_index_frame(pd.DataFrame(rows))


def build_universe_profile_split_worklist_plan_index(
    *,
    root: str | Path = "outputs/reports/universe_profile_split_worklist_plan",
    output_dir: str | Path = "outputs/reports/universe_profile_split_worklist_plan/index",
    include_missing_metadata: bool = False,
) -> UniverseProfileSplitWorklistPlanIndexResult:
    rows, warnings = _scan_artifact_rows(Path(root), include_missing_metadata=include_missing_metadata)
    index_frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_universe_profile_split_worklist_plan_index_paths(output_dir)
    result = UniverseProfileSplitWorklistPlanIndexResult(
        artifact_count=len(index_frame),
        index_frame=index_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        audit_metadata={
            "root_dir": str(root),
            "artifact_count": len(index_frame),
            "include_missing_metadata": include_missing_metadata,
            "active_worklist_mutated": False,
            "no_approval_applied": True,
            "no_rejection_applied": True,
            "no_universe_export": True,
            "no_data_raw_write": True,
            "no_data_processed_write": True,
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "network_api_called": False,
            "external_api_called": False,
            "llm_api_called": False,
            "broker_api_invoked": False,
            "message_sent": False,
            "universe_profile_split_worklist_plan_artifacts_only": True,
        },
    )
    write_universe_profile_split_worklist_plan_index(result)
    return result


def resolve_universe_profile_split_worklist_plan_index_paths(
    output_dir: str | Path,
) -> UniverseProfileSplitWorklistPlanIndexPaths:
    artifact_dir = Path(output_dir)
    return UniverseProfileSplitWorklistPlanIndexPaths(
        artifact_dir=artifact_dir,
        universe_profile_split_worklist_plan_index_csv=artifact_dir / "universe_profile_split_worklist_plan_index.csv",
        universe_profile_split_worklist_plan_index_report=artifact_dir / "universe_profile_split_worklist_plan_index_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_universe_profile_split_worklist_plan_index(
    result: UniverseProfileSplitWorklistPlanIndexResult,
) -> dict[str, Path]:
    paths = UniverseProfileSplitWorklistPlanIndexPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths.universe_profile_split_worklist_plan_index_csv, index=False)
    metadata = {
        "index_id": _hash_payload({"rows": result.index_frame.to_dict("records")}, 12),
        "created_at": _metadata_created_at(result.index_frame),
        "artifact_count": result.artifact_count,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        **result.audit_metadata,
        "no_live_trading_statement": (
            "No approval, rejection, active worklist mutation, universe export, data/raw write, "
            "data/processed write, current-candidates generation, snapshot build, forward labels, "
            "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
            "or cache mutation was invoked."
        ),
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.universe_profile_split_worklist_plan_index_report.write_text(
        render_universe_profile_split_worklist_plan_index_report(result),
        encoding="utf-8",
    )
    return paths.as_dict()


def render_universe_profile_split_worklist_plan_index_report(
    result: UniverseProfileSplitWorklistPlanIndexResult,
) -> str:
    return "\n".join(
        [
            "# Universe Profile Split-Worklist Plan Index",
            "",
            "No approval, rejection, active worklist mutation, universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, network/API, LLM/API, or cache mutation was invoked.",
            "",
            f"- artifact_count: {result.artifact_count}",
            "",
            result.index_frame.to_markdown(index=False) if not result.index_frame.empty else "No rows.",
        ]
    )


def _scan_artifact_rows(root: Path, *, include_missing_metadata: bool) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not root.exists():
        return rows, [f"Universe profile split-worklist plan root does not exist: {root}"]
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir))
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read universe profile split-worklist metadata {metadata_path}: {exc}")
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, status="UNREADABLE_METADATA"))
            continue
        if not _text(metadata.get("plan_id")):
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    plan_csv = Path(output_files.get("plan_csv") or artifact_dir / "universe_profile_split_worklist_plan.csv")
    summary_csv = Path(output_files.get("summary_csv") or artifact_dir / "universe_profile_split_summary.csv")
    report = Path(output_files.get("report") or artifact_dir / "universe_profile_split_worklist_plan_report.md")
    registry_snapshot = Path(output_files.get("registry_snapshot") or artifact_dir / "universe_profile_registry_snapshot.yaml")
    stock_guidance = Path(output_files.get("stock_core_guidance") or artifact_dir / "universe_profile_split_guidance_stock_core.csv")
    etf_guidance = Path(output_files.get("etf_core_guidance") or artifact_dir / "universe_profile_split_guidance_etf_core.csv")
    mixed_guidance = Path(output_files.get("mixed_demo_core_guidance") or artifact_dir / "universe_profile_split_guidance_mixed_demo_core.csv")
    plan_frame = _read_csv(plan_csv)
    return {
        "artifact_type": "UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN",
        "plan_id": _text(metadata.get("plan_id")) or artifact_dir.name,
        "status": _text(metadata.get("status")) or "WARN",
        "row_count": _to_int(metadata.get("row_count", len(plan_frame))),
        "stock_row_count": _to_int(metadata.get("stock_row_count", _equals_count(plan_frame, "resolved_instrument_type", "STOCK"))),
        "etf_row_count": _to_int(metadata.get("etf_row_count", _equals_count(plan_frame, "resolved_instrument_type", "ETF"))),
        "legacy_mixed_demo_row_count": _to_int(metadata.get("legacy_mixed_demo_row_count", _equals_count(plan_frame, "legacy_classification", "legacy_mixed_demo_universe"))),
        "recommended_stock_core_count": _to_int(metadata.get("recommended_stock_core_count", _equals_count(plan_frame, "recommended_future_universe", "stock_core"))),
        "recommended_etf_core_count": _to_int(metadata.get("recommended_etf_core_count", _equals_count(plan_frame, "recommended_future_universe", "etf_core"))),
        "recommended_mixed_demo_core_count": _to_int(metadata.get("recommended_mixed_demo_core_count", _equals_count(plan_frame, "recommended_future_universe", "mixed_demo_core"))),
        "profile_conflict_count": _to_int(metadata.get("profile_conflict_count", _true_count(plan_frame, "profile_conflict"))),
        "active_worklist_mutated": _to_bool(metadata.get("active_worklist_mutated")),
        "no_approval_applied": _to_bool(metadata.get("no_approval_applied")),
        "no_rejection_applied": _to_bool(metadata.get("no_rejection_applied")),
        "no_universe_export": _to_bool(metadata.get("no_universe_export")),
        "no_data_raw_write": _to_bool(metadata.get("no_data_raw_write")),
        "no_data_processed_write": _to_bool(metadata.get("no_data_processed_write")),
        "no_current_candidates_generated": _to_bool(metadata.get("no_current_candidates_generated")),
        "no_snapshot_built": _to_bool(metadata.get("no_snapshot_built")),
        "no_forward_labels": _to_bool(metadata.get("no_forward_labels")),
        "no_live_trading": _to_bool(metadata.get("no_live_trading")),
        "no_broker_api": _to_bool(metadata.get("no_broker_api")),
        "no_order_placement": _to_bool(metadata.get("no_order_placement")),
        "no_message_sent": _to_bool(metadata.get("no_message_sent")),
        "plan_only": _to_bool(metadata.get("plan_only")),
        "report_path": str(report),
        "plan_csv_path": str(plan_csv),
        "summary_csv_path": str(summary_csv),
        "registry_snapshot_path": str(registry_snapshot),
        "stock_core_guidance_path": str(stock_guidance),
        "etf_core_guidance_path": str(etf_guidance),
        "mixed_demo_core_guidance_path": str(mixed_guidance),
        "metadata_path": str(metadata_path),
        "created_at": _text(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
    }


def _missing_metadata_row(artifact_dir: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    row = {column: "" for column in UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_INDEX_COLUMNS}
    row.update(
        {
            "artifact_type": "UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN",
            "plan_id": artifact_dir.name,
            "status": status,
            "report_path": str(artifact_dir / "universe_profile_split_worklist_plan_report.md"),
            "plan_csv_path": str(artifact_dir / "universe_profile_split_worklist_plan.csv"),
            "summary_csv_path": str(artifact_dir / "universe_profile_split_summary.csv"),
            "registry_snapshot_path": str(artifact_dir / "universe_profile_registry_snapshot.yaml"),
            "stock_core_guidance_path": str(artifact_dir / "universe_profile_split_guidance_stock_core.csv"),
            "etf_core_guidance_path": str(artifact_dir / "universe_profile_split_guidance_etf_core.csv"),
            "mixed_demo_core_guidance_path": str(artifact_dir / "universe_profile_split_guidance_mixed_demo_core.csv"),
            "metadata_path": str(artifact_dir / "metadata.json"),
            "created_at": _artifact_mtime(artifact_dir),
        }
    )
    return row


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_INDEX_COLUMNS)
    output = frame.copy()
    for column in UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    for column in [
        "active_worklist_mutated",
        "no_approval_applied",
        "no_rejection_applied",
        "no_universe_export",
        "no_data_raw_write",
        "no_data_processed_write",
        "no_current_candidates_generated",
        "no_snapshot_built",
        "no_forward_labels",
        "no_live_trading",
        "no_broker_api",
        "no_order_placement",
        "no_message_sent",
        "plan_only",
    ]:
        output[column] = output[column].map(_to_bool)
    return output[UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_INDEX_COLUMNS].sort_values(["created_at", "plan_id"]).reset_index(drop=True)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception:
        return pd.DataFrame()


def _equals_count(frame: pd.DataFrame, column: str, value: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].astype(str).str.upper().eq(value.upper()).sum())


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_to_bool).sum())


def _metadata_created_at(index_frame: pd.DataFrame) -> str:
    if index_frame.empty or "created_at" not in index_frame.columns:
        return datetime.now(timezone.utc).isoformat()
    values = [_text(value) for value in index_frame["created_at"].tolist() if _text(value)]
    return max(values) if values else datetime.now(timezone.utc).isoformat()


def _artifact_mtime(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return ""


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y", "t"}


def _to_int(value: Any) -> int:
    try:
        if _text(value) == "":
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return "" if text.lower() in {"nan", "nat", "none", "null"} else text


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value
