"""Health view for report-only replay evidence bundle schema fixture artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.replay_evidence_bundle_schema_fixture import (
    ADMISSIBILITY_STATUSES,
    ALLOWED_TRADE_USAGE,
    BUNDLE_COMPLETENESS_STATUSES,
    BUNDLE_STATUSES,
    COMPLIANCE_CLASSES,
    FORBIDDEN_METADATA_FALSE_FLAGS,
    FORBIDDEN_TRADE_USAGE,
    MANUAL_REVIEW_STATUSES,
    QUALITY_STATUSES,
    REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS,
    RISK_VETO_TYPES,
    ROW_FALSE_FLAGS,
)
from quant_replay_system.replay_evidence_bundle_schema_fixture_index import VIEW_DIR_NAMES


HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]
REQUIRED_ARTIFACTS = {
    "metadata": "replay_evidence_bundle_schema_fixture_metadata.json",
    "schema_fields": "replay_evidence_bundle_schema_fields.csv",
    "fixture_rows": "replay_evidence_bundle_fixture_rows.csv",
    "item_matrix": "replay_evidence_bundle_item_matrix.csv",
    "pit_admissibility_matrix": "replay_evidence_bundle_pit_admissibility_matrix.csv",
    "lineage_matrix": "replay_evidence_bundle_lineage_matrix.csv",
    "quality_compliance_matrix": "replay_evidence_bundle_quality_compliance_matrix.csv",
    "risk_veto_matrix": "replay_evidence_bundle_risk_veto_matrix.csv",
    "forbidden_output_guard_matrix": "replay_evidence_bundle_forbidden_output_guard_matrix.csv",
    "validation_summary": "replay_evidence_bundle_validation_summary.csv",
    "limitations": "replay_evidence_bundle_limitations.md",
    "recommended_next_task": "recommended_next_task.md",
}


@dataclass(frozen=True)
class ReplayEvidenceBundleSchemaFixtureHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_replay_evidence_bundle_schema_fixture_health(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/replay_evidence_bundle_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/replay_evidence_bundle_schema_fixture_v0_1/health",
) -> ReplayEvidenceBundleSchemaFixtureHealthResult:
    candidate_dirs = _candidate_dirs(Path(root))
    issues: list[dict[str, Any]] = []
    for artifact_dir in candidate_dirs:
        issues.extend(_issues_for_artifact_dir(artifact_dir))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "replay_evidence_bundle_schema_fixture_health.csv",
        "health_report": Path(output_dir) / "replay_evidence_bundle_schema_fixture_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ReplayEvidenceBundleSchemaFixtureHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=[] if Path(root).exists() else [f"Replay evidence bundle schema fixture root does not exist: {root}"],
        audit_metadata=_audit_metadata(root, len(candidate_dirs)),
    )
    _write(result)
    return result


def _issues_for_artifact_dir(artifact_dir: Path) -> list[dict[str, Any]]:
    run_id = artifact_dir.name
    issues: list[dict[str, Any]] = []
    paths = {key: artifact_dir / filename for key, filename in REQUIRED_ARTIFACTS.items()}
    for path in paths.values():
        if not path.exists():
            issues.append(_issue(run_id, "ERROR", "MISSING_REQUIRED_ARTIFACT", f"Required artifact missing: {path}", path))

    metadata: dict[str, Any] | None = None
    if paths["metadata"].exists():
        try:
            metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(_issue(run_id, "ERROR", "METADATA_UNREADABLE", f"Metadata cannot be read: {exc}", paths["metadata"]))
    if metadata is not None:
        run_id = _text(metadata.get("replay_evidence_bundle_schema_fixture_id")) or run_id
        issues.extend(_metadata_issues(run_id, metadata, paths["metadata"]))
    if paths["schema_fields"].exists():
        issues.extend(_schema_field_issues(run_id, paths["schema_fields"]))
    if paths["fixture_rows"].exists():
        issues.extend(_fixture_row_issues(run_id, paths["fixture_rows"]))
    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], metadata_path: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    status = _text(metadata.get("status"))
    if status not in {"PASS", "WARN", "FAIL"}:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_STATUS", f"Unknown fixture status: {status}", metadata_path))
    if status != "PASS":
        issues.append(_issue(run_id, "ERROR", "FIXTURE_STATUS_NOT_PASS", "Fixture metadata status is not PASS.", metadata_path))
    if not _to_bool(metadata.get("replay_evidence_bundle_schema_fixture_created")):
        issues.append(_issue(run_id, "ERROR", "CREATED_FLAG_MISSING", "replay_evidence_bundle_schema_fixture_created is not true.", metadata_path))
    if not _to_bool(metadata.get("replay_evidence_bundle_rows_created")):
        issues.append(
            _issue(run_id, "ERROR", "REPLAY_EVIDENCE_BUNDLE_ROWS_CREATED_FLAG_MISSING", "replay_evidence_bundle_rows_created is not true.", metadata_path)
        )
    if _to_int(metadata.get("bundle_count")) != 10:
        issues.append(_issue(run_id, "ERROR", "BUNDLE_COUNT_NOT_10", "bundle_count must be 10.", metadata_path))
    if _to_int(metadata.get("validation_issue_count")) != 0:
        issues.append(_issue(run_id, "ERROR", "VALIDATION_ISSUE_COUNT_NOT_ZERO", "validation_issue_count must be 0.", metadata_path))
    if not _to_bool(metadata.get("report_only")):
        issues.append(_issue(run_id, "ERROR", "METADATA_REPORT_ONLY_NOT_TRUE", "metadata report_only is not true.", metadata_path))
    if not _to_bool(metadata.get("diagnostic_only")):
        issues.append(_issue(run_id, "ERROR", "METADATA_DIAGNOSTIC_ONLY_NOT_TRUE", "metadata diagnostic_only is not true.", metadata_path))
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        if _to_bool(metadata.get(flag)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{flag} is true.", metadata_path))
    artifact_paths = metadata.get("artifact_paths") if isinstance(metadata.get("artifact_paths"), dict) else {}
    for key, value in artifact_paths.items():
        if _unsafe_path_text(value):
            issues.append(_issue(run_id, "ERROR", "UNSAFE_ARTIFACT_PATH", f"Unsafe artifact path for {key}: {value}", metadata_path))
    return issues


def _schema_field_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        fields = pd.read_csv(path, dtype=str)
    except Exception as exc:
        return [_issue(run_id, "ERROR", "SCHEMA_FIELDS_UNREADABLE", f"Schema fields cannot be read: {exc}", path)]
    if "field_name" not in fields.columns:
        return [_issue(run_id, "ERROR", "SCHEMA_FIELDS_REQUIRED_FIELDS_MISSING", "schema fields missing field_name column.", path)]
    missing = sorted(set(REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS) - set(fields["field_name"].dropna().astype(str)))
    if missing:
        return [
            _issue(
                run_id,
                "ERROR",
                "SCHEMA_FIELDS_REQUIRED_FIELDS_MISSING",
                f"schema fields missing required field names: {','.join(missing)}",
                path,
            )
        ]
    return []


def _fixture_row_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        rows = pd.read_csv(path, dtype=str).fillna("")
    except Exception as exc:
        return [_issue(run_id, "ERROR", "FIXTURE_ROWS_UNREADABLE", f"fixture rows cannot be read: {exc}", path)]
    issues: list[dict[str, Any]] = []
    missing = sorted(set(REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS) - set(rows.columns))
    if missing:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "FIXTURE_ROWS_REQUIRED_COLUMNS_MISSING",
                f"fixture rows missing required columns: {','.join(missing)}",
                path,
            )
        )
        return issues

    row_text = " ".join(rows.astype(str).agg(" ".join, axis=1))
    column_text = " ".join(str(column) for column in rows.columns)
    by_id = rows.set_index("replay_evidence_bundle_id", drop=False)

    if _contains_sensitive_text(f"{column_text} {row_text}"):
        issues.append(_issue(run_id, "ERROR", "SENSITIVE_TEXT_DETECTED", "token/secret-looking text appears in fixture rows.", path))
    if len(rows) != 10:
        issues.append(_issue(run_id, "ERROR", "BUNDLE_COUNT_NOT_10", "replay evidence bundle fixture must contain exactly 10 rows.", path))
    if not rows["replay_evidence_bundle_id"].is_unique:
        issues.append(_issue(run_id, "ERROR", "REPLAY_EVIDENCE_BUNDLE_ID_NOT_UNIQUE", "replay_evidence_bundle_id must be unique.", path))

    _non_empty_check(issues, run_id, path, rows, "replay_decision_time", "REPLAY_DECISION_TIME_MISSING")
    if not rows[["entity_id", "symbol", "instrument_type"]].map(_is_non_empty_text).all().all():
        issues.append(_issue(run_id, "ERROR", "ENTITY_CONTEXT_MISSING", "entity_id, symbol, and instrument_type must be populated.", path))
    _non_empty_check(issues, run_id, path, rows, "evidence_item_types", "EVIDENCE_ITEM_REFS_MISSING")
    _non_empty_check(issues, run_id, path, rows, "source_id_refs", "SOURCE_REGISTRY_LINKAGE_MISSING")
    _non_empty_check(issues, run_id, path, rows, "source_registry_run_id", "SOURCE_REGISTRY_LINKAGE_MISSING")
    _non_empty_check(issues, run_id, path, rows, "raw_document_store_run_id", "RAW_DOCUMENT_DATASET_LINKAGE_MISSING")
    _non_empty_check(issues, run_id, path, rows, "factor_definition_run_id", "FACTOR_DEFINITION_LINKAGE_MISSING")

    raw_required = rows[rows["raw_document_or_dataset_required"].map(_to_bool)]
    if not raw_required.empty and not raw_required.apply(_has_raw_document_or_dataset, axis=1).all():
        issues.append(_issue(run_id, "ERROR", "RAW_DOCUMENT_DATASET_LINKAGE_MISSING", "required raw document/dataset linkage is missing.", path))
    factor_rows = rows[(rows["factor_observation_count"].astype(str).replace("", "0").astype(int) > 0)]
    if not factor_rows.empty and not factor_rows[["factor_id_refs", "factor_definition_version_refs"]].map(_is_non_empty_text).all().all():
        issues.append(_issue(run_id, "ERROR", "FACTOR_DEFINITION_LINKAGE_MISSING", "factor evidence rows need factor definition linkage.", path))
    exposure_rows = rows[(rows["exposure_context_count"].astype(str).replace("", "0").astype(int) > 0)]
    if not exposure_rows.empty and not exposure_rows["company_exposure_id_refs"].map(_is_non_empty_text).all():
        issues.append(_issue(run_id, "ERROR", "COMPANY_EXPOSURE_LINKAGE_MISSING", "exposure context rows need company exposure linkage.", path))
    event_rows = rows[(rows["event_count"].astype(str).replace("", "0").astype(int) > 0)]
    if not event_rows.empty and not event_rows["event_structured_id_refs"].map(_is_non_empty_text).all():
        issues.append(_issue(run_id, "ERROR", "EVENT_STRUCTURED_LINKAGE_MISSING", "event context rows need event structured linkage.", path))
    if not factor_rows.empty and not factor_rows["factor_observation_id_refs"].map(_is_non_empty_text).all():
        issues.append(_issue(run_id, "ERROR", "FACTOR_OBSERVATION_LINKAGE_MISSING", "factor observation rows need observation linkage.", path))

    admissible = rows[rows["admissibility_status"] == "ADMISSIBLE"]
    if not admissible.empty and not admissible.apply(lambda row: _timestamp_order_ok(row["available_time_max"], row["replay_decision_time"]), axis=1).all():
        issues.append(
            _issue(run_id, "ERROR", "ADMISSIBLE_AVAILABLE_TIME_AFTER_REPLAY_TIME", "admissible evidence has available_time after replay_decision_time.", path)
        )
    future_available = rows[rows.apply(lambda row: _timestamp_order_strict_after(row["available_time_max"], row["replay_decision_time"]), axis=1)]
    if not future_available.empty and (
        (future_available["admissibility_status"] == "ADMISSIBLE").any()
        or future_available["decision_time_eligible"].map(_to_bool).any()
        or future_available["pit_valid"].map(_to_bool).any()
    ):
        issues.append(_issue(run_id, "ERROR", "FUTURE_AVAILABLE_EVIDENCE_NOT_BLOCKED", "future-available evidence must be blocked.", path))
    if not rows["future_label_excluded"].map(_to_bool).all() or rows["future_labels_joined"].map(_to_bool).any():
        issues.append(_issue(run_id, "ERROR", "FUTURE_LABELS_NOT_EXCLUDED", "future labels must be excluded and not joined.", path))
    if not rows["future_revision_excluded"].map(_to_bool).all():
        issues.append(_issue(run_id, "ERROR", "FUTURE_REVISIONS_NOT_EXCLUDED", "future revisions must be excluded.", path))
    if not rows[["source_hash_coverage", "content_hash_coverage", "metadata_hash_coverage"]].map(_is_non_empty_text).all().all():
        issues.append(_issue(run_id, "ERROR", "HASH_COVERAGE_MISSING", "source/content/metadata hash coverage must be populated.", path))
    if not rows["revision_id_coverage"].map(_is_non_empty_text).all():
        issues.append(_issue(run_id, "ERROR", "REVISION_COVERAGE_MISSING", "revision coverage must be populated.", path))
    if not rows[["parser_version_refs", "extractor_version_refs", "calculation_version_refs"]].map(_is_non_empty_text).all().all():
        issues.append(
            _issue(run_id, "ERROR", "PARSER_EXTRACTOR_CALCULATION_VERSION_MISSING", "parser/extractor/calculation versions must be populated.", path)
        )

    if not admissible.empty and not admissible["source_permission_status"].isin({"ALLOWED", "PUBLIC_ALLOWED"}).all():
        issues.append(_issue(run_id, "ERROR", "ADMISSIBLE_SOURCE_PERMISSION_NOT_ALLOWED", "admissible evidence needs allowed source permission.", path))
    restricted_or_private = rows[
        rows["compliance_class"].isin({"RESTRICTED", "PRIVATE", "ILLEGAL"})
        | (pd.to_numeric(rows["restricted_source_count"], errors="coerce").fillna(0) > 0)
        | (pd.to_numeric(rows["private_source_count"], errors="coerce").fillna(0) > 0)
        | (pd.to_numeric(rows["illegal_source_count"], errors="coerce").fillna(0) > 0)
    ]
    if not restricted_or_private.empty and (
        (restricted_or_private["admissibility_status"] == "ADMISSIBLE").any()
        or (~restricted_or_private["trade_usage"].isin({"no_trade", "diagnostic_only"})).any()
    ):
        issues.append(
            _issue(run_id, "ERROR", "RESTRICTED_PRIVATE_ILLEGAL_NOT_BLOCKED", "restricted/private/illegal evidence must be blocked or no_trade.", path)
        )

    _enum_check(issues, run_id, path, rows, "bundle_status", BUNDLE_STATUSES, "BUNDLE_STATUS_INVALID")
    _enum_check(issues, run_id, path, rows, "bundle_completeness_status", BUNDLE_COMPLETENESS_STATUSES, "BUNDLE_COMPLETENESS_STATUS_INVALID")
    _enum_check(issues, run_id, path, rows, "admissibility_status", ADMISSIBILITY_STATUSES, "ADMISSIBILITY_STATUS_INVALID")
    _enum_check(issues, run_id, path, rows, "quality_status", QUALITY_STATUSES, "QUALITY_STATUS_INVALID")
    _enum_check(issues, run_id, path, rows, "manual_review_status", MANUAL_REVIEW_STATUSES, "MANUAL_REVIEW_STATUS_INVALID")
    _enum_check(issues, run_id, path, rows, "compliance_class", COMPLIANCE_CLASSES, "COMPLIANCE_CLASS_INVALID")
    _enum_check(issues, run_id, path, rows, "risk_veto_type", RISK_VETO_TYPES, "RISK_VETO_TYPE_INVALID")
    if rows["trade_usage"].isin(FORBIDDEN_TRADE_USAGE).any():
        issues.append(_issue(run_id, "ERROR", "TRADE_USAGE_FORBIDDEN", "trade_usage contains buy/sell/trading usage.", path))
    elif not rows["trade_usage"].isin(ALLOWED_TRADE_USAGE).all():
        issues.append(_issue(run_id, "ERROR", "TRADE_USAGE_INVALID", "trade_usage contains invalid values.", path))

    _blocked_contract_issues(issues, run_id, path, by_id)

    for transform_flag in ["normalization_created", "winsorization_created", "direction_adjusted_values_created"]:
        if transform_flag in rows.columns and rows[transform_flag].map(_to_bool).any():
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    "TRANSFORMATION_RUNTIME_FLAG_TRUE",
                    "normalization/winsorization/direction adjusted runtime flags must be false.",
                    path,
                )
            )
            break
    for flag in ROW_FALSE_FLAGS:
        if rows[flag].map(_to_bool).any():
            issues.append(_issue(run_id, "ERROR", f"ROW_{flag.upper()}_TRUE", f"{flag} must be false for every fixture row.", path))
    if not rows["report_only"].map(_to_bool).all():
        issues.append(_issue(run_id, "ERROR", "ROW_REPORT_ONLY_NOT_TRUE", "report_only must be true for every fixture row.", path))
    if not rows["diagnostic_only"].map(_to_bool).all():
        issues.append(_issue(run_id, "ERROR", "ROW_DIAGNOSTIC_ONLY_NOT_TRUE", "diagnostic_only must be true for every fixture row.", path))
    return issues


def _blocked_contract_issues(
    issues: list[dict[str, Any]],
    run_id: str,
    path: Path,
    by_id: pd.DataFrame,
) -> None:
    future = _row_by_id(by_id, "SYNTH_BLOCKED_FUTURE_AVAILABLE_TIME_BUNDLE")
    if future is not None and (
        future["admissibility_status"] != "BLOCKED_FUTURE_AVAILABLE_TIME"
        or _to_bool(future["decision_time_eligible"])
        or _to_bool(future["pit_valid"])
    ):
        issues.append(_issue(run_id, "ERROR", "FUTURE_AVAILABLE_EVIDENCE_NOT_BLOCKED", "future-available fixture row must stay blocked.", path))
    missing_hash = _row_by_id(by_id, "SYNTH_BLOCKED_MISSING_HASH_REVISION_BUNDLE")
    if missing_hash is not None and (
        missing_hash["admissibility_status"] not in {"BLOCKED_MISSING_HASH", "BLOCKED_MISSING_REVISION"}
        or _to_bool(missing_hash["decision_time_eligible"])
        or _to_bool(missing_hash["pit_valid"])
    ):
        issues.append(_issue(run_id, "ERROR", "MISSING_HASH_REVISION_ROW_NOT_BLOCKED", "missing hash/revision row must stay blocked.", path))
    observe = _row_by_id(by_id, "SYNTH_OBSERVE_ONLY_INCOMPLETE_CONTEXT_BUNDLE")
    if observe is not None and (
        observe["admissibility_status"] != "OBSERVE_ONLY"
        or _to_bool(observe["decision_time_eligible"])
        or observe["trade_usage"] != "observe_only"
    ):
        issues.append(_issue(run_id, "ERROR", "OBSERVE_ONLY_INCOMPLETE_DECISION_ELIGIBLE", "observe-only incomplete row cannot be decision-time eligible.", path))
    risk = _row_by_id(by_id, "SYNTH_RISK_VETO_ST_DELIST_BUNDLE")
    if risk is not None and (
        not _to_bool(risk["risk_veto_flag"])
        or risk["risk_veto_type"] == "NONE"
        or _to_bool(risk["decision_time_eligible"])
        or _to_bool(risk["pit_valid"])
        or risk["trade_usage"] not in {"no_trade", "risk_filter"}
    ):
        issues.append(_issue(run_id, "ERROR", "RISK_VETO_ROW_DOES_NOT_BLOCK_ACTIONABILITY", "risk veto row must block actionability.", path))


def _candidate_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and path.name not in VIEW_DIR_NAMES
        and not path.name.startswith("_")
        and any((path / filename).exists() for filename in REQUIRED_ARTIFACTS.values())
    )


def _write(result: ReplayEvidenceBundleSchemaFixtureHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Replay Evidence Bundle Schema Fixture Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                "This health view is report-only. It does not create real replay evidence bundles, replay decisions, forward labels, future labels, real source adapters, real raw document ingestion, factor observations, production factor registry state, active factor libraries, production event ingestion, production company exposure mapping, normalization runtime, winsorization runtime, direction-adjusted values, signal_score implementation, model training, active weights, active thresholds, stock_profile validation, paper validation, buy-review eligibility, performance validation, API calls, broker behavior, orders, messages, current-candidates, snapshots, signal_semantics mutation, or trading.",
                "",
                result.health_frame.to_markdown(index=False) if not result.health_frame.empty else "No issues.",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "warnings": result.warnings,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")


def _non_empty_check(
    issues: list[dict[str, Any]],
    run_id: str,
    path: Path,
    rows: pd.DataFrame,
    column: str,
    code: str,
) -> None:
    if not rows[column].map(_is_non_empty_text).all():
        issues.append(_issue(run_id, "ERROR", code, f"{column} must be populated.", path))


def _enum_check(
    issues: list[dict[str, Any]],
    run_id: str,
    path: Path,
    rows: pd.DataFrame,
    column: str,
    allowed: set[str],
    code: str,
) -> None:
    if not rows[column].isin(allowed).all():
        issues.append(_issue(run_id, "ERROR", code, f"{column} contains invalid values.", path))


def _issue(run_id: str, severity: str, code: str, message: str, path: str | Path) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "status": "OPEN",
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    for column in HEALTH_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, HEALTH_COLUMNS]


def _audit_metadata(root: str | Path, checked_count: int) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "checked_artifact_count": checked_count,
        "report_only": True,
        "diagnostic_only": True,
        "replay_evidence_bundle_schema_fixture_health_created": True,
        **{flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
    }


def _row_by_id(by_id: pd.DataFrame, row_id: str) -> pd.Series | None:
    if row_id not in by_id.index:
        return None
    value = by_id.loc[row_id]
    if isinstance(value, pd.DataFrame):
        return value.iloc[0]
    return value


def _has_raw_document_or_dataset(row: pd.Series) -> bool:
    if _is_non_empty_text(row["document_id_refs"]) or _is_non_empty_text(row["dataset_id_refs"]):
        return True
    return _to_int(row["raw_document_ref_count"]) + _to_int(row["raw_dataset_ref_count"]) > 0


def _unsafe_path_text(value: Any) -> bool:
    text = _text(value).replace("\\", "/").lower()
    unsafe_fragments = [
        "data/raw",
        "data/processed",
        "data/cache",
        "broker",
        "order",
        "trading",
        "current-candidates",
        "current_candidates",
        "snapshot",
        "signal_semantics",
        "model_training",
        "active_weights",
        "active_thresholds",
    ]
    return any(fragment in text for fragment in unsafe_fragments)


def _contains_sensitive_text(text: str) -> bool:
    return bool(re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", text.lower()))


def _timestamp_order_ok(first: Any, second: Any) -> bool:
    first_text = _text(first)
    second_text = _text(second)
    if not first_text or not second_text:
        return False
    first_ts = pd.to_datetime(first_text, errors="coerce")
    second_ts = pd.to_datetime(second_text, errors="coerce")
    if pd.isna(first_ts) or pd.isna(second_ts):
        return False
    return bool(first_ts <= second_ts)


def _timestamp_order_strict_after(first: Any, second: Any) -> bool:
    first_text = _text(first)
    second_text = _text(second)
    if not first_text or not second_text:
        return False
    first_ts = pd.to_datetime(first_text, errors="coerce")
    second_ts = pd.to_datetime(second_text, errors="coerce")
    if pd.isna(first_ts) or pd.isna(second_ts):
        return False
    return bool(first_ts > second_ts)


def _is_non_empty_text(value: Any) -> bool:
    return bool(_text(value))


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
