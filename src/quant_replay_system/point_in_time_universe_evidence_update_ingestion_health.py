"""Health checks for PIT universe evidence update ingestion artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.point_in_time_universe_evidence_update_ingestion import (
    INGESTION_OUTPUT_COLUMNS,
    REVIEW_UPDATE_COLUMNS,
)
from quant_replay_system.point_in_time_universe_evidence_update_ingestion_index import (
    scan_pit_universe_evidence_update_ingestion_artifacts,
)


HEALTH_COLUMNS = [
    "artifact_type",
    "ingestion_id",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]

HEALTH_LIMITATIONS = [
    "Checks local PIT universe evidence update ingestion artifacts only.",
    "Does not apply approvals, export universe files, write data/raw or data/processed, run current-candidates, build snapshots, or compute forward labels.",
    "Does not mutate cache, call APIs, send messages, place orders, call brokers, or enable live trading.",
]


@dataclass(frozen=True)
class PitUniverseEvidenceUpdateIngestionHealthPaths:
    artifact_dir: Path
    pit_universe_evidence_update_ingestion_health_report: Path
    pit_universe_evidence_update_ingestion_health_issues: Path
    pit_universe_evidence_update_ingestion_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "pit_universe_evidence_update_ingestion_health_report": self.pit_universe_evidence_update_ingestion_health_report,
            "pit_universe_evidence_update_ingestion_health_issues": self.pit_universe_evidence_update_ingestion_health_issues,
            "pit_universe_evidence_update_ingestion_health_summary": self.pit_universe_evidence_update_ingestion_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseEvidenceUpdateIngestionHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    health_check_id: str
    audit_metadata: dict[str, Any]


def check_pit_universe_evidence_update_ingestion_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path = "outputs/reports/point_in_time_universe_evidence_update_ingestion",
    output_dir: str | Path = "outputs/reports/point_in_time_universe_evidence_update_ingestion/health",
) -> PitUniverseEvidenceUpdateIngestionHealthResult:
    index_frame, index_source, load_issues = _load_index(index_df=index_df, index_path=index_path, root=root)
    health_frame = build_pit_universe_evidence_update_ingestion_health_frame(index_frame)
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_pit_universe_evidence_update_ingestion_health(
        health_frame,
        checked_artifact_count=len(index_frame),
    )
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = _hash_payload({"rows": index_frame.to_dict("records"), "status": status}, length=12)
    paths = resolve_pit_universe_evidence_update_ingestion_health_paths(output_dir, health_check_id)
    result = PitUniverseEvidenceUpdateIngestionHealthResult(
        status=status,
        checked_artifact_count=len(index_frame),
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=[],
        known_limitations=HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata={
            "index_source": index_source,
            "checked_artifact_count": len(index_frame),
            "approval_applied": False,
            "universe_exported": False,
            "would_write_data_raw": False,
            "would_write_data_processed": False,
            "current_candidates_executed": False,
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
            "pit_universe_evidence_update_ingestion_artifacts_only": True,
        },
    )
    write_pit_universe_evidence_update_ingestion_health_artifacts(result)
    return result


def build_pit_universe_evidence_update_ingestion_health_frame(index_df: pd.DataFrame) -> pd.DataFrame:
    issues: list[dict[str, Any]] = []
    for row in index_df.to_dict("records"):
        metadata = _check_metadata(row, Path(_string(row.get("metadata_path"))), issues)
        ingestion = _check_csv(
            row,
            Path(_string(row.get("ingestion_csv_path"))),
            issues,
            path_field="ingestion_csv_path",
            missing_code="MISSING_INGESTION_CSV",
            required_columns=INGESTION_OUTPUT_COLUMNS,
        )
        review_updates = _check_csv(
            row,
            Path(_string(row.get("review_updates_path"))),
            issues,
            path_field="review_updates_path",
            missing_code="MISSING_REVIEW_UPDATES_CSV",
            required_columns=REVIEW_UPDATE_COLUMNS,
        )
        _check_report(row, Path(_string(row.get("report_path"))), issues)
        if metadata is not None and ingestion is not None and review_updates is not None:
            _check_ingestion_contract(row, metadata, ingestion, review_updates, issues)
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_pit_universe_evidence_update_ingestion_health(
    health_frame: pd.DataFrame,
    *,
    checked_artifact_count: int,
) -> pd.DataFrame:
    frame = _finalize_health_frame(health_frame)
    issue_count = len(frame)
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARN").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    rows = [
        {
            "status": status,
            "checked_artifact_count": checked_artifact_count,
            "issue_count": issue_count,
            "error_count": error_count,
            "warning_count": warning_count,
        }
    ]
    if not frame.empty:
        for issue_code, group in frame.groupby("issue_code", dropna=False):
            rows.append(
                {
                    "status": status,
                    "checked_artifact_count": checked_artifact_count,
                    "issue_count": len(group),
                    "error_count": int((group["severity"] == "ERROR").sum()),
                    "warning_count": int((group["severity"] == "WARN").sum()),
                    "issue_code": issue_code,
                }
            )
    return pd.DataFrame(rows)


def resolve_pit_universe_evidence_update_ingestion_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> PitUniverseEvidenceUpdateIngestionHealthPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return PitUniverseEvidenceUpdateIngestionHealthPaths(
        artifact_dir=artifact_dir,
        pit_universe_evidence_update_ingestion_health_report=artifact_dir
        / "pit_universe_evidence_update_ingestion_health_report.md",
        pit_universe_evidence_update_ingestion_health_issues=artifact_dir
        / "pit_universe_evidence_update_ingestion_health_issues.csv",
        pit_universe_evidence_update_ingestion_health_summary=artifact_dir
        / "pit_universe_evidence_update_ingestion_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_pit_universe_evidence_update_ingestion_health_artifacts(
    result: PitUniverseEvidenceUpdateIngestionHealthResult,
) -> dict[str, Path]:
    paths = PitUniverseEvidenceUpdateIngestionHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths.pit_universe_evidence_update_ingestion_health_issues, index=False)
    result.summary_frame.to_csv(paths.pit_universe_evidence_update_ingestion_health_summary, index=False)
    metadata = build_pit_universe_evidence_update_ingestion_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.pit_universe_evidence_update_ingestion_health_report.write_text(
        render_pit_universe_evidence_update_ingestion_health_report(result),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_pit_universe_evidence_update_ingestion_health_metadata(
    result: PitUniverseEvidenceUpdateIngestionHealthResult,
    paths: PitUniverseEvidenceUpdateIngestionHealthPaths,
) -> dict[str, Any]:
    return {
        "health_check_id": result.health_check_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        **result.audit_metadata,
        "no_live_trading_statement": _safety_statement(),
    }


def render_pit_universe_evidence_update_ingestion_health_report(
    result: PitUniverseEvidenceUpdateIngestionHealthResult,
) -> str:
    return "\n".join(
        [
            "# PIT Universe Evidence Update Ingestion Health",
            "",
            _safety_statement(),
            "",
            "## Summary",
            "",
            _dict_table(
                {
                    "health_check_id": result.health_check_id,
                    "status": result.status,
                    "checked_artifact_count": result.checked_artifact_count,
                    "issue_count": result.issue_count,
                    "error_count": result.error_count,
                    "warning_count": result.warning_count,
                }
            ),
            "",
            "## Issues",
            "",
            _markdown_table(
                result.health_frame,
                ["ingestion_id", "severity", "issue_code", "path_field", "issue_message", "suggested_action"],
            ),
            "",
        ]
    )


def _load_index(
    *,
    index_df: pd.DataFrame | None,
    index_path: str | Path | None,
    root: str | Path,
) -> tuple[pd.DataFrame, str, list[dict[str, Any]]]:
    if index_df is not None:
        return index_df.copy(), "in_memory", []
    if index_path is not None:
        path = Path(index_path)
        if not path.exists():
            issue = _issue({}, "metadata_path", path, "ERROR", "MISSING_METADATA", f"Index CSV not found: {path}", "Run pit-universe-evidence-update-ingestion-index.")
            return pd.DataFrame(), str(path), [issue]
        return pd.read_csv(path, keep_default_na=False), str(path), []
    return scan_pit_universe_evidence_update_ingestion_artifacts(root), str(root), []


def _check_metadata(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", "metadata.json is missing.", "Regenerate the ingestion artifact."))
        return None
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", f"metadata.json is unreadable: {exc}", "Regenerate the ingestion artifact."))
        return None
    return metadata if isinstance(metadata, dict) else {}


def _check_csv(
    row: dict[str, Any],
    path: Path,
    issues: list[dict[str, Any]],
    *,
    path_field: str,
    missing_code: str,
    required_columns: list[str],
) -> pd.DataFrame | None:
    if not path.exists():
        issues.append(_issue(row, path_field, path, "ERROR", missing_code, f"{path_field} is missing.", "Regenerate the ingestion artifact."))
        return None
    try:
        frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception as exc:
        issues.append(_issue(row, path_field, path, "ERROR", missing_code, f"{path_field} is unreadable: {exc}", "Regenerate the ingestion artifact."))
        return None
    missing = [column for column in required_columns if column not in frame.columns]
    if missing:
        issues.append(_issue(row, path_field, path, "ERROR", "MISSING_REQUIRED_COLUMNS", f"Missing required columns: {', '.join(missing)}", "Regenerate the ingestion artifact."))
    return frame


def _check_report(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> None:
    if not path.exists():
        issues.append(_issue(row, "report_path", path, "ERROR", "MISSING_REPORT", "Report file is missing.", "Regenerate the ingestion artifact."))


def _check_ingestion_contract(
    row: dict[str, Any],
    metadata: dict[str, Any],
    ingestion: pd.DataFrame,
    review_updates: pd.DataFrame,
    issues: list[dict[str, Any]],
) -> None:
    ingestion_id = _string(row.get("ingestion_id"))
    ready = ingestion[ingestion["ready_for_review_update"].map(_is_true)] if "ready_for_review_update" in ingestion.columns else pd.DataFrame()
    blocked = ingestion[~ingestion["ready_for_review_update"].map(_is_true)] if "ready_for_review_update" in ingestion.columns else ingestion
    if len(ready) != len(review_updates):
        issues.append(_issue(row, "review_updates_path", row.get("review_updates_path"), "ERROR", "READY_COUNT_MISMATCH", "ready_for_review_update_count does not match clean review_updates row count.", "Regenerate ingestion artifacts."))
    if not blocked.empty and _blocked_keys_in_clean(blocked, review_updates):
        issues.append(_issue(row, "review_updates_path", row.get("review_updates_path"), "ERROR", "BLOCKED_ROWS_IN_CLEAN_REVIEW_UPDATES", "Blocked ingestion rows appear in clean review_updates.csv.", "Regenerate ingestion artifacts and remove blocked rows from clean updates."))
    for count_field in ["duplicate_identity_count", "missing_identity_count", "suggested_copy_risk_count"]:
        if count_field not in row:
            issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "WARN", "MISSING_COUNT_FIELD", f"{count_field} is missing from index.", "Regenerate the index."))
    safety_checks = [
        ("no_universe_export", "UNIVERSE_EXPORT_DETECTED"),
        ("no_data_raw_write", "DATA_RAW_WRITE_DETECTED"),
        ("no_data_processed_write", "DATA_PROCESSED_WRITE_DETECTED"),
        ("no_current_candidates_generated", "CURRENT_CANDIDATES_GENERATED"),
        ("no_snapshot_built", "SNAPSHOT_BUILT"),
        ("no_forward_labels", "FORWARD_LABELS_COMPUTED"),
        ("no_live_trading", "LIVE_TRADING_DETECTED"),
        ("no_broker_api", "BROKER_DETECTED"),
        ("no_order_placement", "ORDER_PLACEMENT_DETECTED"),
        ("no_message_sent", "MESSAGE_DELIVERY_DETECTED"),
        ("ingestion_only", "INGESTION_ONLY_FLAG_MISSING"),
    ]
    for field, code in safety_checks:
        if not _is_true(row.get(field)) or (field in metadata and not _is_true(metadata.get(field))):
            issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", code, f"{field} must remain true.", "Regenerate safe ingestion artifacts."))
    if _is_true(metadata.get("approval_applied")):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "APPROVAL_APPLIED_DETECTED", "Ingestion metadata says approval was applied.", "Use ingestion as validation only."))
    if ingestion_id and ingestion_id != _string(metadata.get("ingestion_id", ingestion_id)):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "WARN", "INGESTION_ID_MISMATCH", "Index and metadata ingestion ids differ.", "Regenerate the index."))


def _blocked_keys_in_clean(blocked: pd.DataFrame, clean: pd.DataFrame) -> bool:
    if clean.empty or not {"signal_date", "symbol", "universe_name"}.issubset(clean.columns):
        return False
    blocked_keys = set(blocked[["signal_date", "symbol", "universe_name"]].astype(str).agg("|".join, axis=1))
    clean_keys = set(clean[["signal_date", "symbol", "universe_name"]].astype(str).agg("|".join, axis=1))
    return bool(blocked_keys & clean_keys)


def _issue(row: dict[str, Any], path_field: str, path_value: Any, severity: str, issue_code: str, message: str, action: str) -> dict[str, Any]:
    return {
        "artifact_type": "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION",
        "ingestion_id": _string(row.get("ingestion_id")),
        "path_field": path_field,
        "path_value": _string(path_value),
        "severity": severity,
        "issue_code": issue_code,
        "issue_message": message,
        "suggested_action": action,
    }


def _finalize_health_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    output = frame.copy()
    for column in HEALTH_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[HEALTH_COLUMNS].reset_index(drop=True)


def _string(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _string(value).lower() in {"1", "true", "yes", "y", "是"}


def _hash_payload(payload: dict[str, Any], *, length: int = 12) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def _dict_table(values: dict[str, Any]) -> str:
    lines = ["| field | value |", "|---|---|"]
    for key, value in values.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "_No issues._"
    output = frame.copy()
    for column in columns:
        if column not in output.columns:
            output[column] = ""
    return output[columns].to_markdown(index=False)


def _safety_statement() -> str:
    return (
        "No approval applied, universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, "
        "external API, or cache mutation was invoked."
    )
