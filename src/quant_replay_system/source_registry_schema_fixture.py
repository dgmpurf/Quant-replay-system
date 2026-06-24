"""Report-only source registry schema fixture workflow.

This module writes tiny synthetic source-registry fixture artifacts for the
Factor / Source Registry / Raw Document Store foundation branch. It validates
shape and conservative policy flags only; it never fetches data, calls APIs,
writes data/raw, data/processed, or data/cache, runs current-candidates, builds
snapshots, changes signal semantics, creates active stock profiles, or grants
buy-review, paper, performance, broker, order, message, or trading permission.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_SOURCE_REGISTRY_FIELDS = [
    "source_id",
    "source_name",
    "source_type",
    "upstream_family",
    "access_method",
    "permission_class",
    "license_or_terms_note",
    "commercial_use_risk",
    "manual_review_required",
    "update_cadence",
    "expected_latency",
    "revision_risk",
    "reliability_status",
    "project_role",
    "replay_suitability",
    "allowed_dataset_types",
    "allowed_instrument_types",
    "first_allowed_as_of_date",
    "last_reviewed_at",
    "reviewer",
    "review_reason",
    "quality_status",
    "report_only",
    "diagnostic_only",
]

FORBIDDEN_SIDE_EFFECT_FLAGS = [
    "live_trading_enabled",
    "broker_api_called",
    "external_api_called",
    "llm_api_called",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "active_stock_profile_created",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "strategy_performance_validated",
    "trading_allowed",
    "operational_global_approved_for_paper_granted",
]


@dataclass(frozen=True)
class SourceRegistrySchemaFixtureSettings:
    output_dir: Path = Path("outputs/reports/manual_diagnostics/source_registry_schema_fixture_v0_1")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True
    live_trading_enabled: bool = False
    broker_api_called: bool = False
    external_api_called: bool = False
    llm_api_called: bool = False
    data_raw_written: bool = False
    data_processed_written: bool = False
    data_cache_written: bool = False
    current_candidates_run: bool = False
    snapshot_built: bool = False
    signal_semantics_changed: bool = False
    active_stock_profile_created: bool = False
    real_buy_review_eligible: bool = False
    buy_review_allowed: bool = False
    strategy_performance_validated: bool = False
    trading_allowed: bool = False
    operational_global_approved_for_paper_granted: bool = False


@dataclass(frozen=True)
class SourceRegistrySchemaFixtureResult:
    source_registry_schema_fixture_id: str
    status: str
    source_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    artifact_paths: dict[str, Path]


def build_source_registry_schema_fixture(
    *,
    output_dir: str | Path | None = None,
    settings: SourceRegistrySchemaFixtureSettings | None = None,
) -> SourceRegistrySchemaFixtureResult:
    resolved_settings = settings or SourceRegistrySchemaFixtureSettings()
    if output_dir is not None:
        resolved_settings = SourceRegistrySchemaFixtureSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)

    fixture_rows = build_source_registry_fixture_rows()
    fixture_id = _fixture_id(fixture_rows, resolved_settings.config_version)
    paths = resolve_source_registry_schema_fixture_paths(resolved_settings.output_dir, fixture_id)
    schema_fields = build_source_registry_schema_fields()
    permission_matrix = build_source_registry_permission_matrix(fixture_rows)
    replay_suitability_matrix = build_source_registry_replay_suitability_matrix(fixture_rows)
    validation_summary = validate_source_registry_fixture(
        fixture_rows=fixture_rows,
        settings=resolved_settings,
        output_dir=resolved_settings.output_dir,
    )
    validation_issue_count = int((~validation_summary["passed"]).sum())

    result = SourceRegistrySchemaFixtureResult(
        source_registry_schema_fixture_id=fixture_id,
        status="PASS" if validation_issue_count == 0 else "FAIL",
        source_count=len(fixture_rows),
        validation_issue_count=validation_issue_count,
        report_only=True,
        diagnostic_only=True,
        artifact_paths=paths,
    )
    if resolved_settings.write_artifacts:
        write_source_registry_schema_fixture_artifacts(
            result=result,
            settings=resolved_settings,
            schema_fields=schema_fields,
            fixture_rows=fixture_rows,
            permission_matrix=permission_matrix,
            replay_suitability_matrix=replay_suitability_matrix,
            validation_summary=validation_summary,
        )
    return result


def build_source_registry_fixture_rows() -> pd.DataFrame:
    rows = [
        {
            "source_id": "LOCAL_CSV_REVIEWED_SAMPLE",
            "source_name": "Reviewed local CSV sample fixture",
            "source_type": "LOCAL_CSV",
            "upstream_family": "LOCAL_FILE",
            "access_method": "LOCAL_FILE",
            "permission_class": "USER_PROVIDED_LOCAL",
            "license_or_terms_note": "Diagnostic fixture only; reviewer must confirm rights before use.",
            "commercial_use_risk": "LOW",
            "manual_review_required": True,
            "update_cadence": "MANUAL",
            "expected_latency": "REVIEWED_BEFORE_USE",
            "revision_risk": "LOW",
            "reliability_status": "PARTIALLY_VERIFIED",
            "project_role": "PRIMARY_LOCAL_FALLBACK",
            "replay_suitability": "REPLAY_READY_AFTER_REVIEW",
            "allowed_dataset_types": "market,universe,trading_calendar,benchmark,corporate_actions",
            "allowed_instrument_types": "STOCK,ETF,INDEX",
            "first_allowed_as_of_date": "",
            "last_reviewed_at": "",
            "reviewer": "diagnostic_fixture",
            "review_reason": "Schema fixture only; no production source permission granted.",
            "quality_status": "REVIEW_REQUIRED",
            "report_only": True,
            "diagnostic_only": True,
        },
        {
            "source_id": "PUBLIC_OFFICIAL_ANNOUNCEMENT_SAMPLE",
            "source_name": "Public official announcement sample fixture",
            "source_type": "PUBLIC_OFFICIAL",
            "upstream_family": "PUBLIC_OFFICIAL_DISCLOSURE",
            "access_method": "PUBLIC_PAGE",
            "permission_class": "PUBLIC_REVIEW_REQUIRED",
            "license_or_terms_note": "Diagnostic fixture only; terms and coverage need reviewer confirmation.",
            "commercial_use_risk": "LOW",
            "manual_review_required": True,
            "update_cadence": "SOURCE_DEFINED",
            "expected_latency": "AFTER_PUBLICATION",
            "revision_risk": "MEDIUM",
            "reliability_status": "PARTIALLY_VERIFIED",
            "project_role": "OPTIONAL_VALIDATION",
            "replay_suitability": "REPLAY_CONTEXT_ONLY",
            "allowed_dataset_types": "disclosure,listing_status,corporate_actions",
            "allowed_instrument_types": "STOCK,ETF",
            "first_allowed_as_of_date": "",
            "last_reviewed_at": "",
            "reviewer": "diagnostic_fixture",
            "review_reason": "Official-style context sample only; not a production permission record.",
            "quality_status": "REVIEW_REQUIRED",
            "report_only": True,
            "diagnostic_only": True,
        },
        {
            "source_id": "PUBLIC_WRAPPER_OPTIONAL_SAMPLE",
            "source_name": "Public wrapper optional sample fixture",
            "source_type": "PUBLIC_WRAPPER",
            "upstream_family": "PUBLIC_WRAPPER_SAMPLE",
            "access_method": "OPTIONAL_API",
            "permission_class": "TERMS_UNKNOWN",
            "license_or_terms_note": "Diagnostic fixture only; wrapper terms and upstream provenance require review.",
            "commercial_use_risk": "MEDIUM",
            "manual_review_required": True,
            "update_cadence": "WRAPPER_DEFINED",
            "expected_latency": "UNKNOWN",
            "revision_risk": "HIGH",
            "reliability_status": "PARTIALLY_VERIFIED",
            "project_role": "OPTIONAL_VALIDATION",
            "replay_suitability": "VALIDATION_ONLY",
            "allowed_dataset_types": "cross_check,exploratory_validation",
            "allowed_instrument_types": "STOCK,ETF,INDEX",
            "first_allowed_as_of_date": "",
            "last_reviewed_at": "",
            "reviewer": "diagnostic_fixture",
            "review_reason": "Wrapper sample requires separate validation and cannot define canonical permission.",
            "quality_status": "REVIEW_REQUIRED",
            "report_only": True,
            "diagnostic_only": True,
        },
        {
            "source_id": "PAID_VENDOR_FUTURE_BACKUP_SAMPLE",
            "source_name": "Paid vendor future backup sample fixture",
            "source_type": "PAID_VENDOR",
            "upstream_family": "FUTURE_VENDOR_BACKUP",
            "access_method": "PAID_EXPORT",
            "permission_class": "RESTRICTED",
            "license_or_terms_note": "Diagnostic fixture only; requires future contract review before any use.",
            "commercial_use_risk": "HIGH",
            "manual_review_required": True,
            "update_cadence": "CONTRACT_DEFINED",
            "expected_latency": "CONTRACT_DEFINED",
            "revision_risk": "UNKNOWN",
            "reliability_status": "UNVERIFIED",
            "project_role": "FUTURE_BACKUP",
            "replay_suitability": "REPLAY_CONTEXT_ONLY",
            "allowed_dataset_types": "future_backup_only",
            "allowed_instrument_types": "STOCK,ETF,INDEX",
            "first_allowed_as_of_date": "",
            "last_reviewed_at": "",
            "reviewer": "diagnostic_fixture",
            "review_reason": "Future backup sample only; cannot be a current dependency.",
            "quality_status": "REVIEW_REQUIRED",
            "report_only": True,
            "diagnostic_only": True,
        },
        {
            "source_id": "BLOCKED_PRIVATE_UNVERIFIED_SAMPLE",
            "source_name": "Blocked private unverified sample fixture",
            "source_type": "BLOCKED_PRIVATE",
            "upstream_family": "PRIVATE_UNVERIFIED",
            "access_method": "BLOCKED",
            "permission_class": "PROHIBITED",
            "license_or_terms_note": "Diagnostic fixture only; prohibited until explicit permission is documented.",
            "commercial_use_risk": "PROHIBITED",
            "manual_review_required": True,
            "update_cadence": "N_A",
            "expected_latency": "N_A",
            "revision_risk": "UNKNOWN",
            "reliability_status": "BLOCKED",
            "project_role": "BLOCKED",
            "replay_suitability": "BLOCKED",
            "allowed_dataset_types": "none",
            "allowed_instrument_types": "none",
            "first_allowed_as_of_date": "",
            "last_reviewed_at": "",
            "reviewer": "diagnostic_fixture",
            "review_reason": "Blocked sample demonstrates rejection of private unverified sources.",
            "quality_status": "BLOCKED",
            "report_only": True,
            "diagnostic_only": True,
        },
    ]
    return pd.DataFrame(rows, columns=REQUIRED_SOURCE_REGISTRY_FIELDS)


def build_source_registry_schema_fields() -> pd.DataFrame:
    descriptions = {
        "source_id": "Stable source registry identifier; preserve as text.",
        "source_name": "Human-readable source name.",
        "source_type": "Enum-style source family.",
        "upstream_family": "Upstream source lineage family.",
        "access_method": "How the source would be accessed if later approved.",
        "permission_class": "Permission and terms review classification.",
        "license_or_terms_note": "Reviewer-facing terms note.",
        "commercial_use_risk": "Commercial-use risk class.",
        "manual_review_required": "Whether human review is required before use.",
        "update_cadence": "Expected update cadence.",
        "expected_latency": "Expected source availability latency.",
        "revision_risk": "Risk of source revision or restatement.",
        "reliability_status": "Reliability review status.",
        "project_role": "Allowed project role if later accepted.",
        "replay_suitability": "Replay suitability after review.",
        "allowed_dataset_types": "Dataset categories the source may support.",
        "allowed_instrument_types": "Instrument categories the source may support.",
        "first_allowed_as_of_date": "Earliest allowed as-of date after review.",
        "last_reviewed_at": "Reviewer completion timestamp.",
        "reviewer": "Reviewer identifier or diagnostic fixture marker.",
        "review_reason": "Why the row exists and what it can support.",
        "quality_status": "Fixture quality status.",
        "report_only": "Must remain true for this workflow.",
        "diagnostic_only": "Must remain true for this workflow.",
    }
    return pd.DataFrame(
        [
            {
                "field_name": field,
                "required": True,
                "data_type_hint": "boolean" if field in {"manual_review_required", "report_only", "diagnostic_only"} else "string",
                "description": descriptions[field],
            }
            for field in REQUIRED_SOURCE_REGISTRY_FIELDS
        ]
    )


def build_source_registry_permission_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in fixture_rows.to_dict(orient="records"):
        permission_class = _text(row["permission_class"])
        if permission_class == "PROHIBITED":
            decision = "BLOCK"
        elif permission_class in {"RESTRICTED", "TERMS_UNKNOWN"}:
            decision = "REVIEW_REQUIRED"
        else:
            decision = "REVIEW_REQUIRED"
        rows.append(
            {
                "source_id": row["source_id"],
                "permission_class": permission_class,
                "permission_decision": decision,
                "manual_review_required": True,
                "can_grant_permission_by_fixture": False,
                "notes": _permission_note(permission_class),
            }
        )
    return pd.DataFrame(rows)


def build_source_registry_replay_suitability_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in fixture_rows.to_dict(orient="records"):
        source_id = _text(row["source_id"])
        replay_suitability = _text(row["replay_suitability"])
        rows.append(
            {
                "source_id": source_id,
                "replay_suitability": replay_suitability,
                "replay_allowed_without_review": False,
                "current_dependency_allowed": source_id
                not in {"PAID_VENDOR_FUTURE_BACKUP_SAMPLE", "BLOCKED_PRIVATE_UNVERIFIED_SAMPLE"},
                "canonical_permission_source": source_id
                not in {"PUBLIC_WRAPPER_OPTIONAL_SAMPLE", "PAID_VENDOR_FUTURE_BACKUP_SAMPLE", "BLOCKED_PRIVATE_UNVERIFIED_SAMPLE"},
                "active_signal_allowed": False,
                "notes": _replay_note(source_id, replay_suitability),
            }
        )
    return pd.DataFrame(rows)


def validate_source_registry_fixture(
    *,
    fixture_rows: pd.DataFrame,
    settings: SourceRegistrySchemaFixtureSettings,
    output_dir: Path,
) -> pd.DataFrame:
    row_text = " ".join(fixture_rows.fillna("").astype(str).agg(" ".join, axis=1)).lower()
    checks = [
        ("required_fields_present", set(REQUIRED_SOURCE_REGISTRY_FIELDS).issubset(set(fixture_rows.columns))),
        ("source_id_non_empty_string", fixture_rows["source_id"].map(lambda value: isinstance(value, str) and bool(value)).all()),
        ("source_id_preserves_text", fixture_rows["source_id"].map(type).eq(str).all()),
        ("report_only_true", fixture_rows["report_only"].map(_bool).all()),
        ("diagnostic_only_true", fixture_rows["diagnostic_only"].map(_bool).all()),
        ("forbidden_side_effect_flags_false", all(getattr(settings, flag) is False for flag in FORBIDDEN_SIDE_EFFECT_FLAGS)),
        ("no_sensitive_columns_or_values", "token" not in row_text and "secret" not in row_text),
        (
            "blocked_sources_not_replay_ready",
            not fixture_rows.query("source_id == 'BLOCKED_PRIVATE_UNVERIFIED_SAMPLE'")["replay_suitability"].eq(
                "REPLAY_READY_AFTER_REVIEW"
            ).any(),
        ),
        (
            "paid_vendor_not_current_dependency",
            fixture_rows.query("source_id == 'PAID_VENDOR_FUTURE_BACKUP_SAMPLE'")["project_role"].eq("FUTURE_BACKUP").all(),
        ),
        (
            "public_wrapper_not_automatically_verified",
            fixture_rows.query("source_id == 'PUBLIC_WRAPPER_OPTIONAL_SAMPLE'")["reliability_status"].ne("VERIFIED").all(),
        ),
        (
            "local_csv_requires_manual_review",
            fixture_rows.query("source_id == 'LOCAL_CSV_REVIEWED_SAMPLE'")["manual_review_required"].map(_bool).all(),
        ),
        ("permission_class_present", fixture_rows["permission_class"].map(lambda value: bool(_text(value))).all()),
        ("replay_suitability_present", fixture_rows["replay_suitability"].map(lambda value: bool(_text(value))).all()),
        ("quality_status_present", fixture_rows["quality_status"].map(lambda value: bool(_text(value))).all()),
        ("no_protected_data_writes", not any((output_dir / part).exists() for part in ["data/raw", "data/processed", "data/cache"])),
    ]
    return pd.DataFrame(
        [
            {
                "check_name": name,
                "passed": bool(passed),
                "issue_detail": "" if passed else f"{name} failed",
            }
            for name, passed in checks
        ]
    )


def resolve_source_registry_schema_fixture_paths(output_dir: Path, fixture_id: str) -> dict[str, Path]:
    artifact_dir = output_dir / fixture_id
    return {
        "artifact_dir": artifact_dir,
        "metadata": artifact_dir / "source_registry_schema_fixture_metadata.json",
        "schema_fields": artifact_dir / "source_registry_schema_fields.csv",
        "fixture_rows": artifact_dir / "source_registry_fixture_rows.csv",
        "permission_matrix": artifact_dir / "source_registry_permission_matrix.csv",
        "replay_suitability_matrix": artifact_dir / "source_registry_replay_suitability_matrix.csv",
        "validation_summary": artifact_dir / "source_registry_validation_summary.csv",
        "limitations": artifact_dir / "source_registry_limitations.md",
        "recommended_next_task": artifact_dir / "recommended_next_task.md",
    }


def write_source_registry_schema_fixture_artifacts(
    *,
    result: SourceRegistrySchemaFixtureResult,
    settings: SourceRegistrySchemaFixtureSettings,
    schema_fields: pd.DataFrame,
    fixture_rows: pd.DataFrame,
    permission_matrix: pd.DataFrame,
    replay_suitability_matrix: pd.DataFrame,
    validation_summary: pd.DataFrame,
) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    schema_fields.to_csv(paths["schema_fields"], index=False)
    fixture_rows.to_csv(paths["fixture_rows"], index=False)
    permission_matrix.to_csv(paths["permission_matrix"], index=False)
    replay_suitability_matrix.to_csv(paths["replay_suitability_matrix"], index=False)
    validation_summary.to_csv(paths["validation_summary"], index=False)
    paths["limitations"].write_text(render_source_registry_limitations(result), encoding="utf-8")
    paths["recommended_next_task"].write_text(_recommended_next_task(), encoding="utf-8")
    paths["metadata"].write_text(
        json.dumps(_metadata(result, settings), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def render_source_registry_limitations(result: SourceRegistrySchemaFixtureResult) -> str:
    return "\n".join(
        [
            "# Source Registry Schema Fixture Limitations v0.1",
            "",
            "This workflow creates tiny synthetic source-registry rows for schema and governance validation only.",
            "",
            "## Not Granted",
            "",
            "- No fixture row grants real source permission.",
            "- No fixture row is a production source.",
            "- No fixture row authorizes API access or data collection.",
            "- No fixture row creates current-candidates, snapshots, signal semantics, stock profiles, advisory predictions, probabilities, buy-review eligibility, performance validation, broker behavior, orders, messages, or trading.",
            "",
            "## Current Result",
            "",
            f"- source_registry_schema_fixture_id: {result.source_registry_schema_fixture_id}",
            f"- status: {result.status}",
            f"- source_count: {result.source_count}",
            f"- validation_issue_count: {result.validation_issue_count}",
        ]
    )


def _metadata(
    result: SourceRegistrySchemaFixtureResult,
    settings: SourceRegistrySchemaFixtureSettings,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "source_registry_schema_fixture_id": result.source_registry_schema_fixture_id,
        "status": result.status,
        "config_version": settings.config_version,
        "source_count": result.source_count,
        "validation_issue_count": result.validation_issue_count,
        "source_registry_schema_fixture_created": True,
        "report_only": True,
        "diagnostic_only": True,
        "artifact_paths": {key: str(path) for key, path in result.artifact_paths.items()},
    }
    metadata.update({flag: False for flag in FORBIDDEN_SIDE_EFFECT_FLAGS})
    return metadata


def _assert_settings_safe(settings: SourceRegistrySchemaFixtureSettings) -> None:
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Source registry schema fixture must remain report_only and diagnostic_only.")
    enabled = [flag for flag in FORBIDDEN_SIDE_EFFECT_FLAGS if getattr(settings, flag)]
    if enabled:
        raise ValueError(f"Unsafe source registry fixture settings enabled: {', '.join(enabled)}")


def _fixture_id(fixture_rows: pd.DataFrame, config_version: str) -> str:
    digest = hashlib.sha256(config_version.encode("utf-8"))
    digest.update("|".join(REQUIRED_SOURCE_REGISTRY_FIELDS).encode("utf-8"))
    digest.update(fixture_rows.to_csv(index=False).encode("utf-8"))
    return digest.hexdigest()[:12]


def _permission_note(permission_class: str) -> str:
    if permission_class == "PROHIBITED":
        return "Blocked: prohibited source class cannot be used."
    if permission_class == "RESTRICTED":
        return "Restricted: future contract review required before any use."
    if permission_class == "TERMS_UNKNOWN":
        return "Terms unknown: validation-only until reviewer accepts terms and provenance."
    return "Review required: fixture cannot grant permission by itself."


def _replay_note(source_id: str, replay_suitability: str) -> str:
    if source_id == "BLOCKED_PRIVATE_UNVERIFIED_SAMPLE":
        return "Blocked private source cannot enter replay inputs."
    if source_id == "PAID_VENDOR_FUTURE_BACKUP_SAMPLE":
        return "Future backup only; cannot be a current dependency."
    if source_id == "PUBLIC_WRAPPER_OPTIONAL_SAMPLE":
        return "Validation-only wrapper context; not canonical permission."
    return f"{replay_suitability} remains manual-review/report-only in this fixture."


def _recommended_next_task() -> str:
    return "\n".join(
        [
            "# Recommended Next Task",
            "",
            "Source Registry Schema Fixture Views Report-Only v0.1",
            "",
            "Add index, health, and status artifact views for the report-only source registry schema fixture before research-status integration or any raw document store fixture work.",
        ]
    )


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()
