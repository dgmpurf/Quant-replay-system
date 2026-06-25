"""Health view for report-only factor definition schema fixture artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.factor_definition_schema_fixture import (
    CANONICAL_TAXONOMY_LAYERS,
    ENTITY_SCOPES,
    EXPECTED_DIRECTIONS,
    FACTOR_KINDS,
    FORBIDDEN_METADATA_FALSE_FLAGS,
    MOJIBAKE_LAYER_NAME_FRAGMENTS,
    REQUIRED_FACTOR_DEFINITION_FIELDS,
    TRADE_USAGE_ALLOWED,
    TRADE_USAGE_FORBIDDEN,
)
from quant_replay_system.factor_definition_schema_fixture_index import VIEW_DIR_NAMES


HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]
REQUIRED_ARTIFACTS = {
    "metadata": "factor_definition_schema_fixture_metadata.json",
    "schema_fields": "factor_definition_schema_fields.csv",
    "fixture_rows": "factor_definition_fixture_rows.csv",
    "taxonomy_layer_matrix": "factor_definition_taxonomy_layer_matrix.csv",
    "usage_boundary_matrix": "factor_definition_usage_boundary_matrix.csv",
    "validation_summary": "factor_definition_validation_summary.csv",
    "limitations": "factor_definition_limitations.md",
    "recommended_next_task": "recommended_next_task.md",
}


@dataclass(frozen=True)
class FactorDefinitionSchemaFixtureHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_factor_definition_schema_fixture_health(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/factor_definition_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/factor_definition_schema_fixture_v0_1/health",
) -> FactorDefinitionSchemaFixtureHealthResult:
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
        "health_csv": Path(output_dir) / "factor_definition_schema_fixture_health.csv",
        "health_report": Path(output_dir) / "factor_definition_schema_fixture_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = FactorDefinitionSchemaFixtureHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=[] if Path(root).exists() else [f"Factor definition schema fixture root does not exist: {root}"],
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
        run_id = _text(metadata.get("factor_definition_schema_fixture_id")) or run_id
        issues.extend(_metadata_issues(run_id, metadata, paths["metadata"]))

    if paths["schema_fields"].exists():
        issues.extend(_schema_field_issues(run_id, paths["schema_fields"]))
    if paths["fixture_rows"].exists():
        issues.extend(_fixture_row_issues(run_id, paths["fixture_rows"]))
    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], metadata_path: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    status = _text(metadata.get("status"))
    if status not in {"PASS", "FAIL"}:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_STATUS", f"Unknown fixture status: {status}", metadata_path))
    if status == "FAIL":
        issues.append(_issue(run_id, "ERROR", "FIXTURE_STATUS_NOT_PASS", "Fixture metadata status is FAIL.", metadata_path))
    if not _to_bool(metadata.get("factor_definition_schema_fixture_created")):
        issues.append(_issue(run_id, "ERROR", "CREATED_FLAG_MISSING", "factor_definition_schema_fixture_created is not true.", metadata_path))
    if not _to_bool(metadata.get("factor_definition_rows_created")):
        issues.append(_issue(run_id, "ERROR", "FACTOR_ROWS_CREATED_FLAG_MISSING", "factor_definition_rows_created is not true.", metadata_path))
    if _to_int(metadata.get("factor_count")) != 8:
        issues.append(_issue(run_id, "ERROR", "FACTOR_COUNT_NOT_8", "factor_count must be 8.", metadata_path))
    if _to_int(metadata.get("taxonomy_layer_count")) != 8:
        issues.append(_issue(run_id, "ERROR", "TAXONOMY_LAYER_COUNT_NOT_8", "taxonomy_layer_count must be 8.", metadata_path))
    if not _to_bool(metadata.get("taxonomy_primary_classification")):
        issues.append(_issue(run_id, "ERROR", "TAXONOMY_NOT_PRIMARY", "8-layer taxonomy must be primary classification.", metadata_path))
    if not _to_bool(metadata.get("legacy_12_factor_tags_checklist_only")):
        issues.append(_issue(run_id, "ERROR", "LEGACY_TAGS_TREATED_AS_PRIMARY", "legacy_12_factor_tags must remain checklist-only.", metadata_path))
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
    missing = sorted(set(REQUIRED_FACTOR_DEFINITION_FIELDS) - set(fields["field_name"].dropna().astype(str)))
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
    missing = sorted(set(REQUIRED_FACTOR_DEFINITION_FIELDS) - set(rows.columns))
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
    if _contains_secret_like(f"{column_text} {row_text}"):
        issues.append(_issue(run_id, "ERROR", "SENSITIVE_TEXT_DETECTED", "token/secret-looking text appears in fixture rows.", path))
    if len(rows) != 8:
        issues.append(_issue(run_id, "ERROR", "FACTOR_ROW_COUNT_NOT_8", "factor definition fixture must contain exactly 8 rows.", path))
    layer_counts = rows["taxonomy_layer_id"].value_counts().to_dict()
    if set(layer_counts) != set(CANONICAL_TAXONOMY_LAYERS) or any(count != 1 for count in layer_counts.values()):
        issues.append(_issue(run_id, "ERROR", "CANONICAL_LAYER_IDS_NOT_ONCE", "canonical layer ids must each appear exactly once.", path))
    name_mismatch = rows.apply(
        lambda row: CANONICAL_TAXONOMY_LAYERS.get(row["taxonomy_layer_id"]) != row["taxonomy_layer_name"],
        axis=1,
    )
    if name_mismatch.any():
        issues.append(_issue(run_id, "ERROR", "CANONICAL_LAYER_NAME_MISMATCH", "taxonomy_layer_name does not match canonical layer name.", path))
    if any(fragment in row_text for fragment in MOJIBAKE_LAYER_NAME_FRAGMENTS):
        issues.append(_issue(run_id, "ERROR", "MOJIBAKE_LAYER_NAME_DETECTED", "taxonomy_layer_name contains blocked mojibake-like text.", path))
    if not rows["factor_kind"].isin(FACTOR_KINDS).all():
        issues.append(_issue(run_id, "ERROR", "FACTOR_KIND_INVALID", "factor_kind contains invalid values.", path))
    if not rows["entity_scope"].isin(ENTITY_SCOPES).all():
        issues.append(_issue(run_id, "ERROR", "ENTITY_SCOPE_INVALID", "entity_scope contains invalid values.", path))
    if rows["trade_usage"].isin(TRADE_USAGE_FORBIDDEN).any():
        issues.append(_issue(run_id, "ERROR", "TRADE_USAGE_FORBIDDEN", "trade_usage contains buy/sell/trading usage.", path))
    elif not rows["trade_usage"].isin(TRADE_USAGE_ALLOWED).all():
        issues.append(_issue(run_id, "ERROR", "TRADE_USAGE_INVALID", "trade_usage contains invalid values.", path))
    if not rows["expected_direction"].isin(EXPECTED_DIRECTIONS).all():
        issues.append(_issue(run_id, "ERROR", "EXPECTED_DIRECTION_INVALID", "expected_direction contains invalid values.", path))
    mixed = rows[rows["expected_direction"].isin({"MIXED_BY_EXPOSURE", "MIXED_BY_REGIME"})]
    if not mixed.empty and not mixed["direction_rule_detail"].map(_is_non_empty_text).all():
        issues.append(_issue(run_id, "ERROR", "MIXED_DIRECTION_DETAIL_MISSING", "mixed direction rows need direction_rule_detail.", path))
    risk_veto = rows[rows["factor_kind"].eq("RISK_VETO")]
    if not risk_veto.empty and risk_veto["expected_direction"].eq("POSITIVE").any():
        issues.append(_issue(run_id, "ERROR", "RISK_VETO_POSITIVE_DIRECTION", "risk veto rows cannot have POSITIVE direction.", path))
    if not risk_veto.empty and not risk_veto["trade_usage"].isin({"risk_filter", "no_trade", "diagnostic_only"}).all():
        issues.append(_issue(run_id, "ERROR", "RISK_VETO_USAGE_INVALID", "risk veto rows need risk_filter/no_trade/diagnostic_only usage.", path))
    l6 = rows[rows["taxonomy_layer_id"].eq("L6_INFORMATION_DISCLOSURE_SENTIMENT_TRANSMISSION")]
    l6_text = " ".join(l6.astype(str).agg(" ".join, axis=1)).lower()
    actionable_l6_fragments = ["direct buy signal", "direct sell signal", "buy_signal", "sell_signal"]
    if any(fragment in l6_text for fragment in actionable_l6_fragments):
        issues.append(_issue(run_id, "ERROR", "L6_DIRECT_BUY_SELL_IMPLIED", "L6 disclosure/sentiment rows cannot imply direct buy/sell.", path))

    row_checks = [
        ("source_registry_required", True, "SOURCE_REGISTRY_REQUIRED_NOT_TRUE"),
        ("raw_document_store_required", True, "RAW_DOCUMENT_STORE_REQUIRED_NOT_TRUE"),
        ("report_only", True, "ROW_REPORT_ONLY_NOT_TRUE"),
        ("diagnostic_only", True, "ROW_DIAGNOSTIC_ONLY_NOT_TRUE"),
        ("is_live_signal", False, "ROW_IS_LIVE_SIGNAL_TRUE"),
        ("is_alpha_claim", False, "ROW_IS_ALPHA_CLAIM_TRUE"),
        ("model_training_allowed", False, "ROW_MODEL_TRAINING_ALLOWED_TRUE"),
        ("active_weight_allowed", False, "ROW_ACTIVE_WEIGHT_ALLOWED_TRUE"),
        ("active_threshold_allowed", False, "ROW_ACTIVE_THRESHOLD_ALLOWED_TRUE"),
        ("real_buy_review_allowed", False, "ROW_REAL_BUY_REVIEW_ALLOWED_TRUE"),
        ("trading_allowed", False, "ROW_TRADING_ALLOWED_TRUE"),
    ]
    for column, expected, code in row_checks:
        actual = rows[column].map(_to_bool)
        failed = not actual.all() if expected else actual.any()
        if failed:
            issues.append(_issue(run_id, "ERROR", code, f"{column} must be {expected} for every fixture row.", path))

    non_empty_checks = [
        ("available_time_policy", "AVAILABLE_TIME_POLICY_MISSING"),
        ("revision_policy", "REVISION_POLICY_MISSING"),
        ("compliance_class", "COMPLIANCE_CLASS_MISSING"),
    ]
    for column, code in non_empty_checks:
        if not rows[column].map(_is_non_empty_text).all():
            issues.append(_issue(run_id, "ERROR", code, f"{column} must be populated for every fixture row.", path))
    return issues


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


def _write(result: FactorDefinitionSchemaFixtureHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Factor Definition Schema Fixture Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                "This health view is report-only. It does not create factor observations, event ingestion, company exposure mappings, replay evidence bundles, signal_score implementation, model training, active weights, active thresholds, stock_profile validation, paper validation, buy-review eligibility, performance validation, API calls, broker behavior, orders, messages, or trading.",
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
        "factor_definition_schema_fixture_health_created": True,
        **{flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
    }


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


def _contains_secret_like(text: str) -> bool:
    return bool(re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", text.lower()))


def _is_non_empty_text(value: Any) -> bool:
    return bool(_text(value))


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
