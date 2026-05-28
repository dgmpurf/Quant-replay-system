"""Local-only workflow status for advisory profile calibration artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.advisory_profile_calibration_health import check_advisory_profile_calibration_health
from quant_replay_system.advisory_profile_calibration_index import scan_advisory_profile_calibration_artifacts
from quant_replay_system.config import AdvisoryProfileCalibrationStatusSettings, Settings, load_settings


ADVISORY_PROFILE_CALIBRATION_STATUS_LIMITATIONS = [
    "Scans local advisory profile calibration metadata only.",
    "Does not regenerate candidates, profile thresholds, or quality reports.",
    "Does not send messages, place orders, call brokers, or enable live trading.",
    "Stage inference is conservative when artifacts are missing or health checks fail.",
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
    "latest_calibration_run_id",
    "latest_status",
    "health_status",
    "row_count",
    "review_buy_candidate_count",
    "watch_count",
    "no_action_count",
    "blocked_count",
    "demo_only_count",
    "issue_count",
    "profile",
    "input_path",
    "input_type",
    "report_path",
    "next_manual_action",
]

NO_CALIBRATION_STAGE = "NO_ADVISORY_PROFILE_CALIBRATION_ARTIFACTS"
DEMO_VALIDATED_STAGE = "DEMO_ADVISORY_PROFILE_CALIBRATION_VALIDATED"
READY_STAGE = "ADVISORY_PROFILE_CALIBRATION_READY_FOR_REVIEW"
HEALTH_WARN_STAGE = "ADVISORY_PROFILE_CALIBRATION_HEALTH_WARN"
FAILED_STAGE = "ADVISORY_PROFILE_CALIBRATION_FAILED"

DEMO_NEXT_ACTION = "Demo advisory profile calibration validated; do not treat DEMO_ONLY labels as strategy recommendations."
READY_NEXT_ACTION = "Review calibration labels manually; REVIEW_BUY_CANDIDATE is not an order and auto-order remains disabled."


@dataclass(frozen=True)
class AdvisoryProfileCalibrationStatusPaths:
    artifact_dir: Path
    advisory_profile_calibration_status_report: Path
    advisory_profile_calibration_status_csv: Path
    advisory_profile_calibration_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "advisory_profile_calibration_status_report": self.advisory_profile_calibration_status_report,
            "advisory_profile_calibration_status_csv": self.advisory_profile_calibration_status_csv,
            "advisory_profile_calibration_status_summary": self.advisory_profile_calibration_status_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class AdvisoryProfileCalibrationStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_calibration_run_id: str
    health_status: str
    row_count: int
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_advisory_profile_calibration_status(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    config: Settings | AdvisoryProfileCalibrationStatusSettings | dict[str, Any] | str | Path | None = None,
) -> AdvisoryProfileCalibrationStatusResult:
    """Scan local advisory profile calibration artifacts and write a status dashboard."""

    project_settings, status_settings = _resolve_settings(config)
    if status_settings.enable_live_trading or status_settings.enable_broker_api:
        raise ValueError("Advisory profile calibration status cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else status_settings.root_dir
    effective_output_dir = Path(output_dir) if output_dir is not None else status_settings.output_dir
    index_frame = scan_advisory_profile_calibration_artifacts(effective_root)
    health_settings = project_settings.advisory_profile_calibration_health.model_copy(
        update={
            "root_dir": effective_root,
            "write_artifacts": False,
        }
    )
    health_result = check_advisory_profile_calibration_health(index_df=index_frame, settings=health_settings)
    status_frame = build_advisory_profile_calibration_status_frame(index_frame, health_result=health_result)
    summary_frame = summarize_advisory_profile_calibration_status(index_frame, health_result=health_result)
    summary = summary_frame.iloc[0].to_dict()
    status_id = generate_advisory_profile_calibration_status_id(
        index_frame,
        health_status=health_result.status,
        config_version=status_settings.config_version,
    )
    paths = resolve_advisory_profile_calibration_status_paths(effective_output_dir, status_id)
    warnings = _status_warnings(index_frame, health_result, str(summary.get("workflow_stage", "")))
    audit_metadata = {
        "status_id": status_id,
        "root_dir": effective_root,
        "workflow_stage": summary.get("workflow_stage", ""),
        "status": summary.get("status", ""),
        "latest_calibration_run_id": summary.get("latest_calibration_run_id", ""),
        "health_status": health_result.status if len(index_frame) else "MISSING",
        "strict": status_settings.strict,
        "config_version": status_settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "advisory_profile_calibration_artifacts_only": True,
    }
    result = AdvisoryProfileCalibrationStatusResult(
        status_id=status_id,
        status=str(summary.get("status", "WARN")),
        workflow_stage=str(summary.get("workflow_stage", NO_CALIBRATION_STAGE)),
        latest_calibration_run_id=str(summary.get("latest_calibration_run_id", "")),
        health_status=str(summary.get("health_status", "")),
        row_count=_to_int(summary.get("row_count")),
        next_manual_action=str(summary.get("next_manual_action", "")),
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=ADVISORY_PROFILE_CALIBRATION_STATUS_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if status_settings.write_artifacts:
        write_advisory_profile_calibration_status_artifacts(result)
    return result


def build_advisory_profile_calibration_status_frame(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    latest = _latest_calibration_row(index_frame)
    if latest is None:
        rows.append(
            _status_row(
                component="ADVISORY_PROFILE_CALIBRATION",
                status="MISSING",
                next_action="Run advisory-profile-calibration on a local candidates or scored artifact.",
                notes="No advisory profile calibration artifacts were found.",
            )
        )
    else:
        rows.append(
            _status_row(
                component="ADVISORY_PROFILE_CALIBRATION",
                status=_string_or_empty(latest.get("status")) or "READY",
                latest_artifact_id=_string_or_empty(latest.get("calibration_run_id")),
                report_path=_string_or_empty(latest.get("report_path")),
                metadata_path=_string_or_empty(latest.get("metadata_path")),
                row_count=_to_int(latest.get("row_count")),
                issue_count=_to_int(latest.get("issue_count")),
                next_action="Review advisory profile calibration labels manually before semantics/profile changes.",
                notes="Latest local advisory profile calibration artifact.",
            )
        )
    rows.append(
        _status_row(
            component="ADVISORY_PROFILE_CALIBRATION_HEALTH",
            status=health_result.status if len(index_frame) else "MISSING",
            latest_artifact_id=getattr(health_result, "health_check_id", ""),
            report_path=str(health_result.artifact_paths.get("advisory_profile_calibration_health_report", "")),
            metadata_path=str(health_result.artifact_paths.get("metadata", "")),
            issue_count=health_result.issue_count,
            warning_count=health_result.warning_count,
            error_count=health_result.error_count,
            next_action=_health_next_action(health_result.status if len(index_frame) else "MISSING"),
            notes="Current in-memory health evaluation for advisory profile calibration artifacts.",
        )
    )
    return _finalize_status_frame(pd.DataFrame(rows))


def summarize_advisory_profile_calibration_status(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    latest = _latest_calibration_row(index_frame)
    if latest is None:
        return pd.DataFrame(
            [
                _summary_row(
                    workflow_stage=NO_CALIBRATION_STAGE,
                    status="WARN",
                    health_status="MISSING",
                    next_manual_action="Run advisory-profile-calibration on a local candidates or scored artifact.",
                )
            ]
        )

    latest_health_status = str(health_result.status)
    row_count = _to_int(latest.get("row_count"))
    demo_count = _to_int(latest.get("demo_only_count"))
    review_buy_count = _to_int(latest.get("review_buy_candidate_count"))
    issue_count = _to_int(latest.get("issue_count"))
    profile = _string_or_empty(latest.get("profile"))

    if latest_health_status == "FAIL":
        stage = FAILED_STAGE
        status = "FAIL"
        next_action = "Repair advisory profile calibration artifacts before using threshold analysis."
    elif latest_health_status == "WARN":
        stage = HEALTH_WARN_STAGE
        status = "WARN"
        next_action = "Review advisory profile calibration health warnings before using threshold analysis."
    elif row_count > 0 and demo_count == row_count and review_buy_count == 0:
        stage = DEMO_VALIDATED_STAGE
        status = "WARN"
        next_action = DEMO_NEXT_ACTION
    else:
        stage = READY_STAGE
        status = "WARN" if issue_count else "PASS"
        next_action = READY_NEXT_ACTION

    return pd.DataFrame(
        [
            _summary_row(
                workflow_stage=stage,
                status=status,
                latest_calibration_run_id=_string_or_empty(latest.get("calibration_run_id")),
                latest_status=_string_or_empty(latest.get("status")) or "READY",
                health_status=latest_health_status,
                row_count=row_count,
                review_buy_candidate_count=review_buy_count,
                watch_count=_to_int(latest.get("watch_count")),
                no_action_count=_to_int(latest.get("no_action_count")),
                blocked_count=_to_int(latest.get("blocked_count")),
                demo_only_count=demo_count,
                issue_count=issue_count,
                profile=profile,
                input_path=_string_or_empty(latest.get("input_path")),
                input_type=_string_or_empty(latest.get("input_type")),
                report_path=_string_or_empty(latest.get("report_path")),
                next_manual_action=next_action,
            )
        ]
    )


def resolve_advisory_profile_calibration_status_paths(
    output_dir: str | Path,
    status_id: str,
) -> AdvisoryProfileCalibrationStatusPaths:
    artifact_dir = Path(output_dir) / status_id
    return AdvisoryProfileCalibrationStatusPaths(
        artifact_dir=artifact_dir,
        advisory_profile_calibration_status_report=artifact_dir / "advisory_profile_calibration_status_report.md",
        advisory_profile_calibration_status_csv=artifact_dir / "advisory_profile_calibration_status.csv",
        advisory_profile_calibration_status_summary=artifact_dir / "advisory_profile_calibration_status_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_advisory_profile_calibration_status_artifacts(result: AdvisoryProfileCalibrationStatusResult) -> dict[str, Path]:
    paths = AdvisoryProfileCalibrationStatusPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.status_frame, paths.advisory_profile_calibration_status_csv)
    _export_dataframe(result.summary_frame, paths.advisory_profile_calibration_status_summary)
    metadata = build_advisory_profile_calibration_status_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.advisory_profile_calibration_status_report.write_text(
        render_advisory_profile_calibration_status_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_advisory_profile_calibration_status_metadata(
    result: AdvisoryProfileCalibrationStatusResult,
    paths: AdvisoryProfileCalibrationStatusPaths,
) -> dict[str, Any]:
    return {
        "status_id": result.status_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_calibration_run_id": result.latest_calibration_run_id,
        "health_status": result.health_status,
        "row_count": result.row_count,
        "next_manual_action": result.next_manual_action,
        "summary": result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {},
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "message_sent": False,
        "advisory_profile_calibration_artifacts_only": True,
        "no_live_trading_statement": "No live trading, broker API, order placement, or message delivery was invoked.",
    }


def render_advisory_profile_calibration_status_report(
    result: AdvisoryProfileCalibrationStatusResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {"status_id": result.status_id}
    lines = [
        "# Advisory Profile Calibration Status",
        "",
        "No live trading, broker API, order placement, or message delivery was invoked. This status view summarizes local calibration artifacts only.",
        "",
        "## Summary",
        "",
        _dict_table(
            {
                "status_id": meta.get("status_id", ""),
                "status": result.status,
                "workflow_stage": result.workflow_stage,
                "latest_calibration_run_id": result.latest_calibration_run_id,
                "health_status": result.health_status,
                "row_count": result.row_count,
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


def generate_advisory_profile_calibration_status_id(
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


def _latest_calibration_row(index_frame: pd.DataFrame) -> dict[str, Any] | None:
    if index_frame.empty:
        return None
    frame = index_frame.copy()
    if "created_at" not in frame.columns:
        frame["created_at"] = ""
    frame["_sort_created_at"] = frame["created_at"].astype(str)
    frame["_sort_run_id"] = frame.get("calibration_run_id", "").astype(str)
    return frame.sort_values(["_sort_created_at", "_sort_run_id"]).iloc[-1].to_dict()


def _status_warnings(index_frame: pd.DataFrame, health_result, stage: str) -> list[str]:
    warnings: list[str] = []
    if index_frame.empty:
        warnings.append("No advisory profile calibration artifacts were found.")
    if health_result.status == "WARN":
        warnings.append("Advisory profile calibration health warnings are present.")
    if health_result.status == "FAIL":
        warnings.append("Advisory profile calibration health failures are present.")
    if stage == DEMO_VALIDATED_STAGE:
        warnings.append("Latest calibration run is demo-only validation, not strategy advice.")
    return warnings


def _health_next_action(status: str) -> str:
    if status == "PASS":
        return "Health passed; review calibration labels manually."
    if status == "WARN":
        return "Review advisory profile calibration health warnings."
    if status == "FAIL":
        return "Repair advisory profile calibration artifacts before downstream use."
    return "Run advisory-profile-calibration-index and advisory-profile-calibration-health."


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


def _resolve_settings(
    config: Settings | AdvisoryProfileCalibrationStatusSettings | dict[str, Any] | str | Path | None,
) -> tuple[Settings, AdvisoryProfileCalibrationStatusSettings]:
    if config is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.advisory_profile_calibration_status
    if isinstance(config, Settings):
        return config, config.advisory_profile_calibration_status
    if isinstance(config, AdvisoryProfileCalibrationStatusSettings):
        project = load_settings(Path("config/default.yaml"))
        return project.model_copy(update={"advisory_profile_calibration_status": config}), config
    if isinstance(config, dict):
        project = load_settings(Path("config/default.yaml"))
        updated = project.advisory_profile_calibration_status.model_copy(update=config)
        return project.model_copy(update={"advisory_profile_calibration_status": updated}), updated
    project = load_settings(Path(config))
    return project, project.advisory_profile_calibration_status


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


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| {key} | {_format_markdown_value(value)} |")
    return "\n".join(rows)


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "_No rows._"
    table = frame[available].head(max_rows).copy()
    rows = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
    for record in table.to_dict("records"):
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
