"""Health checks for PIT universe evidence completion helper artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.point_in_time_universe_evidence_completion_helper import HELPER_OUTPUT_COLUMNS
from quant_replay_system.point_in_time_universe_evidence_completion_helper_index import (
    PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_INDEX_COLUMNS,
    scan_pit_universe_evidence_completion_helper_artifacts,
)


HEALTH_COLUMNS = [
    "artifact_type",
    "helper_id",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]

HEALTH_LIMITATIONS = [
    "Checks local PIT universe evidence completion helper artifacts only.",
    "Does not approve rows, export universe files, write data/raw or data/processed, run current-candidates, build snapshots, or compute forward labels.",
    "Does not mutate cache, call APIs, send messages, place orders, call brokers, or enable live trading.",
]


@dataclass(frozen=True)
class PitUniverseEvidenceCompletionHelperHealthPaths:
    artifact_dir: Path
    pit_universe_evidence_completion_helper_health_report: Path
    pit_universe_evidence_completion_helper_health_issues: Path
    pit_universe_evidence_completion_helper_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "pit_universe_evidence_completion_helper_health_report": (
                self.pit_universe_evidence_completion_helper_health_report
            ),
            "pit_universe_evidence_completion_helper_health_issues": (
                self.pit_universe_evidence_completion_helper_health_issues
            ),
            "pit_universe_evidence_completion_helper_health_summary": (
                self.pit_universe_evidence_completion_helper_health_summary
            ),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseEvidenceCompletionHelperHealthResult:
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


def check_pit_universe_evidence_completion_helper_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path = "outputs/reports/point_in_time_universe_evidence_completion_helper",
    output_dir: str | Path = "outputs/reports/point_in_time_universe_evidence_completion_helper/health",
) -> PitUniverseEvidenceCompletionHelperHealthResult:
    index_frame, index_source, load_issues = _load_index(index_df=index_df, index_path=index_path, root=root)
    health_frame = build_pit_universe_evidence_completion_helper_health_frame(index_frame)
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_pit_universe_evidence_completion_helper_health(
        health_frame,
        checked_artifact_count=len(index_frame),
    )
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = _hash_payload({"rows": index_frame.to_dict("records"), "status": status}, length=12)
    paths = resolve_pit_universe_evidence_completion_helper_health_paths(output_dir, health_check_id)
    result = PitUniverseEvidenceCompletionHelperHealthResult(
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
            "pit_universe_evidence_completion_helper_artifacts_only": True,
        },
    )
    write_pit_universe_evidence_completion_helper_health_artifacts(result)
    return result


def build_pit_universe_evidence_completion_helper_health_frame(index_df: pd.DataFrame) -> pd.DataFrame:
    index_frame = _prepare_index_frame(index_df)
    issues: list[dict[str, Any]] = []
    for row in index_frame.to_dict("records"):
        metadata = _check_metadata(row, Path(_string_or_empty(row.get("metadata_path"))), issues)
        template = _check_csv(
            row,
            Path(_string_or_empty(row.get("template_csv_path"))),
            issues,
            path_field="template_csv_path",
            missing_code="MISSING_TEMPLATE_CSV",
            required_columns=HELPER_OUTPUT_COLUMNS,
        )
        _check_report(row, Path(_string_or_empty(row.get("report_path"))), issues)
        if metadata is not None and template is not None:
            _check_helper_contract(row, metadata, template, issues)
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_pit_universe_evidence_completion_helper_health(
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


def resolve_pit_universe_evidence_completion_helper_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> PitUniverseEvidenceCompletionHelperHealthPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return PitUniverseEvidenceCompletionHelperHealthPaths(
        artifact_dir=artifact_dir,
        pit_universe_evidence_completion_helper_health_report=artifact_dir
        / "pit_universe_evidence_completion_helper_health_report.md",
        pit_universe_evidence_completion_helper_health_issues=artifact_dir
        / "pit_universe_evidence_completion_helper_health_issues.csv",
        pit_universe_evidence_completion_helper_health_summary=artifact_dir
        / "pit_universe_evidence_completion_helper_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_pit_universe_evidence_completion_helper_health_artifacts(
    result: PitUniverseEvidenceCompletionHelperHealthResult,
) -> dict[str, Path]:
    paths = PitUniverseEvidenceCompletionHelperHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths.pit_universe_evidence_completion_helper_health_issues, index=False)
    result.summary_frame.to_csv(paths.pit_universe_evidence_completion_helper_health_summary, index=False)
    metadata = build_pit_universe_evidence_completion_helper_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.pit_universe_evidence_completion_helper_health_report.write_text(
        render_pit_universe_evidence_completion_helper_health_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_pit_universe_evidence_completion_helper_health_metadata(
    result: PitUniverseEvidenceCompletionHelperHealthResult,
    paths: PitUniverseEvidenceCompletionHelperHealthPaths,
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
        "no_live_trading_statement": (
            "No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, "
            "forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, "
            "or cache mutation was invoked."
        ),
    }


def render_pit_universe_evidence_completion_helper_health_report(
    result: PitUniverseEvidenceCompletionHelperHealthResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    return "\n".join(
        [
            "# PIT Universe Evidence Completion Helper Health",
            "",
            "No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked. This health check reads local evidence-completion helper artifacts only.",
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
                ["helper_id", "severity", "issue_code", "path_field", "issue_message", "suggested_action"],
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
        return _prepare_index_frame(index_df), "in_memory", []
    if index_path is not None:
        path = Path(index_path)
        if not path.exists():
            issue = _issue(
                {},
                "metadata_path",
                path,
                "ERROR",
                "MISSING_METADATA",
                f"Index CSV not found: {path}",
                "Run pit-universe-evidence-completion-helper-index.",
            )
            return _prepare_index_frame(pd.DataFrame()), str(path), [issue]
        return _prepare_index_frame(pd.read_csv(path, keep_default_na=False)), str(path), []
    frame = scan_pit_universe_evidence_completion_helper_artifacts(root)
    return _prepare_index_frame(frame), str(root), []


def _check_metadata(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(
            _issue(
                row,
                "metadata_path",
                path,
                "ERROR",
                "MISSING_METADATA",
                "metadata.json is missing.",
                "Regenerate the PIT universe evidence completion helper artifact.",
            )
        )
        return None
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(
            _issue(
                row,
                "metadata_path",
                path,
                "ERROR",
                "MISSING_METADATA",
                f"metadata.json is unreadable: {exc}",
                "Regenerate the PIT universe evidence completion helper artifact.",
            )
        )
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
        issues.append(
            _issue(
                row,
                path_field,
                path,
                "ERROR",
                missing_code,
                f"{path_field} is missing.",
                "Regenerate the PIT universe evidence completion helper artifact.",
            )
        )
        return None
    try:
        frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception as exc:
        issues.append(
            _issue(
                row,
                path_field,
                path,
                "ERROR",
                missing_code,
                f"{path_field} is unreadable: {exc}",
                "Regenerate the PIT universe evidence completion helper artifact.",
            )
        )
        return None
    missing = [column for column in required_columns if column not in frame.columns]
    if missing:
        issues.append(
            _issue(
                row,
                path_field,
                row.get(path_field),
                "ERROR",
                "MISSING_REQUIRED_COLUMNS",
                f"Missing required columns: {', '.join(missing)}",
                "Regenerate the PIT universe evidence completion helper artifact with the current schema.",
            )
        )
    return frame


def _check_report(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> None:
    if not path.exists():
        issues.append(
            _issue(
                row,
                "report_path",
                path,
                "ERROR",
                "MISSING_REPORT",
                "PIT universe evidence completion helper report is missing.",
                "Regenerate the PIT universe evidence completion helper artifact.",
            )
        )


def _check_helper_contract(
    row: dict[str, Any],
    metadata: dict[str, Any],
    template: pd.DataFrame,
    issues: list[dict[str, Any]],
) -> None:
    _check_no_export_or_execution(row, metadata, issues)
    _check_safety_flags(row, metadata, template, issues)
    _check_non_authoritative_helper_contract(row, metadata, template, issues)


def _check_no_export_or_execution(row: dict[str, Any], metadata: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    false_flags = {
        "would_write_data_raw": "DATA_RAW_WRITE_DETECTED",
        "would_write_data_processed": "DATA_PROCESSED_WRITE_DETECTED",
        "universe_exported": "UNIVERSE_EXPORT_DETECTED",
        "current_candidates_executed": "CURRENT_CANDIDATES_GENERATED",
        "snapshot_manifest_built": "SNAPSHOT_BUILT",
        "snapshot_manifests_built": "SNAPSHOT_BUILT",
        "forward_returns_computed": "FORWARD_LABELS_COMPUTED",
        "cache_mutated": "CACHE_MUTATION_DETECTED",
        "network_api_called": "NETWORK_OR_API_DETECTED",
        "external_api_called": "NETWORK_OR_API_DETECTED",
        "llm_api_called": "NETWORK_OR_API_DETECTED",
    }
    for flag, code in false_flags.items():
        if _to_bool(metadata.get(flag)):
            issues.append(
                _issue(
                    row,
                    "metadata_path",
                    row.get("metadata_path"),
                    "ERROR",
                    code,
                    f"{flag}=true detected.",
                    "Regenerate evidence completion helper artifacts as report/template-only artifacts.",
                )
            )
    true_flags = {
        "no_universe_export": "UNIVERSE_EXPORT_DETECTED",
        "no_data_raw_write": "DATA_RAW_WRITE_DETECTED",
        "no_data_processed_write": "DATA_PROCESSED_WRITE_DETECTED",
        "no_current_candidates_generated": "CURRENT_CANDIDATES_GENERATED",
        "no_snapshot_built": "SNAPSHOT_BUILT",
        "no_forward_labels": "FORWARD_LABELS_COMPUTED",
    }
    for flag, code in true_flags.items():
        if not _to_bool(metadata.get(flag, False)):
            issues.append(
                _issue(
                    row,
                    "metadata_path",
                    row.get("metadata_path"),
                    "ERROR",
                    code,
                    f"{flag}=true is missing from metadata.",
                    "Regenerate evidence completion helper artifacts with report-only safety metadata.",
                )
            )


def _check_safety_flags(
    row: dict[str, Any],
    metadata: dict[str, Any],
    template: pd.DataFrame,
    issues: list[dict[str, Any]],
) -> None:
    checks = [
        ("no_live_trading", "LIVE_TRADING_DETECTED"),
        ("no_broker_api", "BROKER_DETECTED"),
        ("no_order_placement", "ORDER_PLACEMENT_DETECTED"),
        ("no_message_sent", "MESSAGE_DELIVERY_DETECTED"),
    ]
    for field, code in checks:
        if not _to_bool(metadata.get(field, False)):
            issues.append(
                _issue(
                    row,
                    "metadata_path",
                    row.get("metadata_path"),
                    "ERROR",
                    code,
                    f"{field}=true is missing from metadata.",
                    "Regenerate evidence completion helper artifacts with safety metadata.",
                )
            )
        if field in template.columns and (~template[field].map(_to_bool)).any():
            issues.append(
                _issue(
                    row,
                    "template_csv_path",
                    row.get("template_csv_path"),
                    "ERROR",
                    code,
                    f"A row does not have {field}=true.",
                    "Regenerate evidence completion helper artifacts with safety row fields.",
                )
            )
    unsafe_flags = {
        "live_trading_enabled": "LIVE_TRADING_DETECTED",
        "broker_api_invoked": "BROKER_DETECTED",
        "order_placement_enabled": "ORDER_PLACEMENT_DETECTED",
        "message_delivery_enabled": "MESSAGE_DELIVERY_DETECTED",
        "message_sent": "MESSAGE_DELIVERY_DETECTED",
    }
    for flag, code in unsafe_flags.items():
        if _to_bool(metadata.get(flag)):
            issues.append(
                _issue(
                    row,
                    "metadata_path",
                    row.get("metadata_path"),
                    "ERROR",
                    code,
                    f"{flag}=true detected.",
                    "Regenerate local-only evidence completion helper artifacts.",
                )
            )


def _check_non_authoritative_helper_contract(
    row: dict[str, Any],
    metadata: dict[str, Any],
    template: pd.DataFrame,
    issues: list[dict[str, Any]],
) -> None:
    if _to_int(metadata.get("approved_count")) > 0 or _approved_count(template) > 0:
        issues.append(
            _issue(
                row,
                "template_csv_path",
                row.get("template_csv_path"),
                "ERROR",
                "HELPER_APPROVED_ROWS",
                "Evidence completion helper artifact contains approved rows.",
                "Keep helper outputs non-approval-only; perform approval in the separate PIT universe review workflow.",
            )
        )
    if _to_int(metadata.get("valid_for_signal_date_count")) > 0 or _true_count(template, "current_valid_for_signal_date") > 0:
        issues.append(
            _issue(
                row,
                "template_csv_path",
                row.get("template_csv_path"),
                "ERROR",
                "HELPER_SET_VALID_FOR_SIGNAL_DATE",
                "Evidence completion helper artifact contains valid_for_signal_date=true rows.",
                "Keep helper outputs invalid until the separate review workflow validates evidence.",
            )
        )
    if _to_int(metadata.get("authoritative_hint_count")) > 0 or _true_count(template, "hint_authoritative_for_pit") > 0:
        issues.append(
            _issue(
                row,
                "template_csv_path",
                row.get("template_csv_path"),
                "ERROR",
                "AUTHORITATIVE_HINT_DETECTED",
                "Evidence completion helper hints must remain non-authoritative for PIT approval.",
                "Set hint_authoritative_for_pit=false and require manual evidence review.",
            )
        )
    if (
        "hint_is_future_dated_for_signal_date" in template.columns
        and "hint_authoritative_for_pit" in template.columns
        and (
            template["hint_is_future_dated_for_signal_date"].map(_to_bool)
            & template["hint_authoritative_for_pit"].map(_to_bool)
        ).any()
    ):
        issues.append(
            _issue(
                row,
                "template_csv_path",
                row.get("template_csv_path"),
                "ERROR",
                "AUTHORITATIVE_FUTURE_HINT",
                "A future-dated hint was marked authoritative for PIT approval.",
                "Keep future-dated hints non-authoritative and preserve survivorship-bias warnings.",
            )
        )


def _prepare_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_INDEX_COLUMNS)
    output = frame.copy()
    for column in PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_INDEX_COLUMNS].reset_index(drop=True)


def _finalize_health_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    output = frame.copy()
    for column in HEALTH_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[HEALTH_COLUMNS].reset_index(drop=True)


def _issue(
    row: dict[str, Any],
    path_field: str,
    path_value: Any,
    severity: str,
    issue_code: str,
    issue_message: str,
    suggested_action: str,
) -> dict[str, Any]:
    return {
        "artifact_type": "PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER",
        "helper_id": _string_or_empty(row.get("helper_id")),
        "path_field": path_field,
        "path_value": str(path_value or ""),
        "severity": severity,
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


def _approved_count(frame: pd.DataFrame) -> int:
    if frame.empty or "current_review_status" not in frame.columns:
        return 0
    return int(frame["current_review_status"].map(_string_or_empty).str.upper().eq("APPROVED_FOR_PIT_UNIVERSE").sum())


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_to_bool).sum())


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
    return str(value).strip().lower() in {"true", "1", "yes", "y", "t"}


def _string_or_empty(value: Any) -> str:
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
    return "\n".join(f"- {key}: {value}" for key, value in values.items())


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 200) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "No rows."
    return frame[available].head(max_rows).to_markdown(index=False)
