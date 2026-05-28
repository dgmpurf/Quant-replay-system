"""Local-only status for calibration-to-signal-semantics proposal artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.calibration_to_signal_semantics_health import check_calibration_to_signal_semantics_health
from quant_replay_system.calibration_to_signal_semantics_index import scan_calibration_to_signal_semantics_artifacts


CALIBRATION_TO_SEMANTICS_STATUS_LIMITATIONS = [
    "Scans local calibration-to-signal-semantics proposal metadata only.",
    "Does not regenerate calibration, modify signal semantics defaults, or write config.",
    "Does not send messages, place orders, call brokers, call APIs, or enable live trading.",
    "Stage inference summarizes proposal readiness and evidence needs only.",
]

STATUS_COLUMNS = [
    "component",
    "status",
    "latest_artifact_id",
    "report_path",
    "metadata_path",
    "row_count",
    "issue_count",
    "warning_count",
    "error_count",
    "next_action",
    "notes",
]

SUMMARY_COLUMNS = [
    "workflow_stage",
    "status",
    "latest_proposal_run_id",
    "latest_status",
    "health_status",
    "proposal_categories",
    "defaults_changed",
    "calibration_run_count",
    "observed_review_buy_candidate_count",
    "observed_watch_count",
    "observed_blocked_count",
    "report_path",
    "next_manual_action",
]

NO_PROPOSALS_STAGE = "NO_CALIBRATION_TO_SEMANTICS_PROPOSALS"
READY_STAGE = "CALIBRATION_TO_SEMANTICS_PROPOSAL_READY"
NEEDS_MORE_EVIDENCE_STAGE = "CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE"
HEALTH_WARN_STAGE = "CALIBRATION_TO_SEMANTICS_HEALTH_WARN"
FAILED_STAGE = "CALIBRATION_TO_SEMANTICS_FAILED"

NEXT_ACTION_MORE_EVIDENCE = (
    "Keep current defaults; consider WATCH expansion only after more evidence; do not expand BUY review yet."
)


@dataclass(frozen=True)
class CalibrationToSemanticsStatusSettings:
    root_dir: Path = Path("outputs/reports/calibration_to_signal_semantics")
    output_dir: Path = Path("outputs/reports/calibration_to_signal_semantics/status")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: bool = False
    enable_broker_api: bool = False


@dataclass(frozen=True)
class CalibrationToSemanticsStatusPaths:
    artifact_dir: Path
    calibration_to_signal_semantics_status_report: Path
    calibration_to_signal_semantics_status_csv: Path
    calibration_to_signal_semantics_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "calibration_to_signal_semantics_status_report": self.calibration_to_signal_semantics_status_report,
            "calibration_to_signal_semantics_status_csv": self.calibration_to_signal_semantics_status_csv,
            "calibration_to_signal_semantics_status_summary": self.calibration_to_signal_semantics_status_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CalibrationToSemanticsStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_proposal_run_id: str
    health_status: str
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_calibration_to_signal_semantics_status(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    config: CalibrationToSemanticsStatusSettings | dict[str, Any] | None = None,
) -> CalibrationToSemanticsStatusResult:
    resolved = _resolve_settings(config)
    if resolved.enable_live_trading or resolved.enable_broker_api:
        raise ValueError("Calibration-to-semantics status cannot enable live trading or broker API access")
    effective_root = Path(root) if root is not None else resolved.root_dir
    effective_output_dir = Path(output_dir) if output_dir is not None else resolved.output_dir
    index_frame = scan_calibration_to_signal_semantics_artifacts(effective_root)
    health_result = check_calibration_to_signal_semantics_health(
        index_df=index_frame,
        settings={"root_dir": effective_root, "write_artifacts": False},
    )
    status_frame = build_calibration_to_signal_semantics_status_frame(index_frame, health_result=health_result)
    summary_frame = summarize_calibration_to_signal_semantics_status(index_frame, health_result=health_result)
    summary = summary_frame.iloc[0].to_dict()
    status_id = generate_calibration_to_signal_semantics_status_id(
        index_frame,
        health_status=health_result.status,
        config_version=resolved.config_version,
    )
    paths = resolve_calibration_to_signal_semantics_status_paths(effective_output_dir, status_id)
    warnings = _status_warnings(index_frame, health_result, str(summary.get("workflow_stage", "")))
    audit_metadata = {
        "status_id": status_id,
        "root_dir": effective_root,
        "workflow_stage": summary.get("workflow_stage", ""),
        "status": summary.get("status", ""),
        "latest_proposal_run_id": summary.get("latest_proposal_run_id", ""),
        "health_status": health_result.status if len(index_frame) else "MISSING",
        "strict": resolved.strict,
        "config_version": resolved.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "external_api_called": False,
        "config_mutated": False,
        "proposal_artifacts_only": True,
    }
    result = CalibrationToSemanticsStatusResult(
        status_id=status_id,
        status=str(summary.get("status", "WARN")),
        workflow_stage=str(summary.get("workflow_stage", NO_PROPOSALS_STAGE)),
        latest_proposal_run_id=str(summary.get("latest_proposal_run_id", "")),
        health_status=str(summary.get("health_status", "")),
        next_manual_action=str(summary.get("next_manual_action", "")),
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=CALIBRATION_TO_SEMANTICS_STATUS_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if resolved.write_artifacts:
        write_calibration_to_signal_semantics_status_artifacts(result)
    return result


def build_calibration_to_signal_semantics_status_frame(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    latest = _latest_proposal_row(index_frame)
    if latest is None:
        rows.append(
            _status_row(
                component="CALIBRATION_TO_SIGNAL_SEMANTICS_PROPOSAL",
                status="MISSING",
                next_action="Run calibration-to-signal-semantics after advisory-profile-calibration artifacts exist.",
                notes="No calibration-to-signal-semantics proposal artifacts were found.",
            )
        )
    else:
        rows.append(
            _status_row(
                component="CALIBRATION_TO_SIGNAL_SEMANTICS_PROPOSAL",
                status=_string_or_empty(latest.get("status")) or "READY",
                latest_artifact_id=_string_or_empty(latest.get("proposal_run_id")),
                report_path=_string_or_empty(latest.get("report_path")),
                metadata_path=_string_or_empty(latest.get("metadata_path")),
                row_count=_to_int(latest.get("calibration_run_count")),
                issue_count=0,
                next_action=NEXT_ACTION_MORE_EVIDENCE,
                notes=f"proposal_categories={_string_or_empty(latest.get('proposal_categories'))}; defaults_changed={_to_bool(latest.get('defaults_changed'))}",
            )
        )
    rows.append(
        _status_row(
            component="CALIBRATION_TO_SIGNAL_SEMANTICS_HEALTH",
            status=health_result.status if len(index_frame) else "MISSING",
            latest_artifact_id=getattr(health_result, "health_check_id", ""),
            report_path=str(health_result.artifact_paths.get("calibration_to_signal_semantics_health_report", "")),
            metadata_path=str(health_result.artifact_paths.get("metadata", "")),
            issue_count=health_result.issue_count,
            warning_count=health_result.warning_count,
            error_count=health_result.error_count,
            next_action=_health_next_action(health_result.status if len(index_frame) else "MISSING"),
            notes="Current in-memory health evaluation for proposal artifacts.",
        )
    )
    return _finalize_status_frame(pd.DataFrame(rows))


def summarize_calibration_to_signal_semantics_status(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    latest = _latest_proposal_row(index_frame)
    if latest is None:
        return pd.DataFrame(
            [
                _summary_row(
                    workflow_stage=NO_PROPOSALS_STAGE,
                    status="WARN",
                    health_status="MISSING",
                    next_manual_action="Run calibration-to-signal-semantics after advisory-profile-calibration artifacts exist.",
                )
            ]
        )
    categories = _category_set(latest)
    defaults_changed = _to_bool(latest.get("defaults_changed"))
    if health_result.status == "FAIL" or defaults_changed:
        stage = FAILED_STAGE
        status = "FAIL"
        next_action = "Repair calibration-to-semantics proposal artifacts before dashboard integration."
    elif health_result.status == "WARN":
        stage = HEALTH_WARN_STAGE
        status = "WARN"
        next_action = "Review calibration-to-semantics health warnings before using proposal context."
    elif "REQUIRE_MORE_EVIDENCE" in categories or "DO_NOT_EXPAND_BUY_REVIEW_YET" in categories:
        stage = NEEDS_MORE_EVIDENCE_STAGE
        status = "WARN"
        next_action = NEXT_ACTION_MORE_EVIDENCE
    else:
        stage = READY_STAGE
        status = "PASS"
        next_action = "Review proposal manually; do not change signal_semantics defaults without explicit implementation work."
    return pd.DataFrame(
        [
            _summary_row(
                workflow_stage=stage,
                status=status,
                latest_proposal_run_id=_string_or_empty(latest.get("proposal_run_id")),
                latest_status=_string_or_empty(latest.get("status")) or "READY",
                health_status=health_result.status,
                proposal_categories=_string_or_empty(latest.get("proposal_categories")),
                defaults_changed=defaults_changed,
                calibration_run_count=_to_int(latest.get("calibration_run_count")),
                observed_review_buy_candidate_count=_to_int(latest.get("observed_review_buy_candidate_count")),
                observed_watch_count=_to_int(latest.get("observed_watch_count")),
                observed_blocked_count=_to_int(latest.get("observed_blocked_count")),
                report_path=_string_or_empty(latest.get("report_path")),
                next_manual_action=next_action,
            )
        ]
    )


def resolve_calibration_to_signal_semantics_status_paths(
    output_dir: str | Path,
    status_id: str,
) -> CalibrationToSemanticsStatusPaths:
    artifact_dir = Path(output_dir) / status_id
    return CalibrationToSemanticsStatusPaths(
        artifact_dir=artifact_dir,
        calibration_to_signal_semantics_status_report=artifact_dir / "calibration_to_signal_semantics_status_report.md",
        calibration_to_signal_semantics_status_csv=artifact_dir / "calibration_to_signal_semantics_status.csv",
        calibration_to_signal_semantics_status_summary=artifact_dir / "calibration_to_signal_semantics_status_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_calibration_to_signal_semantics_status_artifacts(result: CalibrationToSemanticsStatusResult) -> dict[str, Path]:
    paths = CalibrationToSemanticsStatusPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.status_frame, paths.calibration_to_signal_semantics_status_csv)
    _export_dataframe(result.summary_frame, paths.calibration_to_signal_semantics_status_summary)
    metadata = build_calibration_to_signal_semantics_status_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.calibration_to_signal_semantics_status_report.write_text(
        render_calibration_to_signal_semantics_status_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_calibration_to_signal_semantics_status_metadata(
    result: CalibrationToSemanticsStatusResult,
    paths: CalibrationToSemanticsStatusPaths,
) -> dict[str, Any]:
    return {
        "status_id": result.status_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_proposal_run_id": result.latest_proposal_run_id,
        "health_status": result.health_status,
        "next_manual_action": result.next_manual_action,
        "summary": result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {},
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "message_sent": False,
        "external_api_called": False,
        "llm_api_called": False,
        "config_mutated": False,
        "proposal_artifacts_only": True,
        "no_live_trading_statement": "No live trading, broker API, order placement, message delivery, LLM API, or external API was invoked.",
    }


def render_calibration_to_signal_semantics_status_report(
    result: CalibrationToSemanticsStatusResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {"status_id": result.status_id}
    lines = [
        "# Calibration-to-Signal Semantics Proposal Status",
        "",
        "No live trading, broker API, order placement, message delivery, LLM API, or external API was invoked. This status view summarizes proposal artifacts only.",
        "",
        "## Summary",
        "",
        _dict_table(
            {
                "status_id": meta.get("status_id", ""),
                "status": result.status,
                "workflow_stage": result.workflow_stage,
                "latest_proposal_run_id": result.latest_proposal_run_id,
                "health_status": result.health_status,
                "next_manual_action": result.next_manual_action,
            }
        ),
        "",
        "## Status Components",
        "",
        _markdown_table(
            result.status_frame,
            ["component", "status", "latest_artifact_id", "issue_count", "warning_count", "error_count", "next_action"],
        ),
        "",
        "## Latest Summary",
        "",
        _markdown_table(result.summary_frame, SUMMARY_COLUMNS),
        "",
        "## Warnings",
        "",
        _warnings_section(result.warnings),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in result.known_limitations),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def generate_calibration_to_signal_semantics_status_id(
    index_frame: pd.DataFrame,
    *,
    health_status: str,
    config_version: str,
) -> str:
    payload = {
        "rows": index_frame.to_dict("records") if index_frame is not None else [],
        "health_status": health_status,
        "config_version": config_version,
    }
    return _hash_payload(payload, length=12)


def _latest_proposal_row(index_frame: pd.DataFrame) -> dict[str, Any] | None:
    if index_frame.empty:
        return None
    frame = index_frame.copy()
    if "created_at" not in frame.columns:
        frame["created_at"] = ""
    frame["_sort_created_at"] = frame["created_at"].astype(str)
    frame["_sort_run_id"] = frame.get("proposal_run_id", "").astype(str)
    return frame.sort_values(["_sort_created_at", "_sort_run_id"]).iloc[-1].to_dict()


def _category_set(row: dict[str, Any]) -> set[str]:
    return {part.strip() for part in _string_or_empty(row.get("proposal_categories")).split(";") if part.strip()}


def _status_warnings(index_frame: pd.DataFrame, health_result, stage: str) -> list[str]:
    warnings: list[str] = []
    if index_frame.empty:
        warnings.append("No calibration-to-signal-semantics proposal artifacts were found.")
    if health_result.status == "WARN":
        warnings.append("Calibration-to-semantics health warnings are present.")
    if health_result.status == "FAIL":
        warnings.append("Calibration-to-semantics health failures are present.")
    if stage == NEEDS_MORE_EVIDENCE_STAGE:
        warnings.append("Proposal says more evidence is needed before changing signal_semantics defaults.")
    return warnings


def _health_next_action(status: str) -> str:
    if status == "PASS":
        return "Health passed; review proposal manually as design context only."
    if status == "WARN":
        return "Review calibration-to-semantics health warnings."
    if status == "FAIL":
        return "Repair proposal artifacts before dashboard integration."
    return "Run calibration-to-signal-semantics-index and calibration-to-signal-semantics-health."


def _status_row(
    *,
    component: str,
    status: str,
    latest_artifact_id: str = "",
    report_path: str = "",
    metadata_path: str = "",
    row_count: int = 0,
    issue_count: int = 0,
    warning_count: int = 0,
    error_count: int = 0,
    next_action: str = "",
    notes: str = "",
) -> dict[str, Any]:
    return {
        "component": component,
        "status": status,
        "latest_artifact_id": latest_artifact_id,
        "report_path": report_path,
        "metadata_path": metadata_path,
        "row_count": row_count,
        "issue_count": issue_count,
        "warning_count": warning_count,
        "error_count": error_count,
        "next_action": next_action,
        "notes": notes,
    }


def _summary_row(**updates: Any) -> dict[str, Any]:
    row = {column: "" for column in SUMMARY_COLUMNS}
    row.update(updates)
    return row


def _finalize_status_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=STATUS_COLUMNS)
    output = frame.copy()
    for column in STATUS_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[STATUS_COLUMNS].reset_index(drop=True)


def _resolve_settings(config: CalibrationToSemanticsStatusSettings | dict[str, Any] | None) -> CalibrationToSemanticsStatusSettings:
    if config is None:
        return CalibrationToSemanticsStatusSettings()
    if isinstance(config, CalibrationToSemanticsStatusSettings):
        return config
    return CalibrationToSemanticsStatusSettings(**{**CalibrationToSemanticsStatusSettings().__dict__, **config})


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


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


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| {key} | {_format_markdown_value(value)} |")
    return "\n".join(rows)


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "_No rows._"
    rows = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
    for record in frame.loc[:, available].head(max_rows).to_dict("records"):
        rows.append("| " + " | ".join(_format_markdown_value(record[column]) for column in available) + " |")
    return "\n".join(rows)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)


def _format_markdown_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ").replace("|", "\\|")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
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
