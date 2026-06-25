"""Report-only raw document store schema fixture workflow.

This module writes tiny synthetic raw-document/raw-dataset reference fixture
artifacts for governance review only. It does not fetch real data, grant source
permission, create a production raw document store, write data/raw,
data/processed, or data/cache, create factor/event/exposure/replay evidence
artifacts, or authorize buy-review, performance validation, broker behavior, or
trading.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


RAW_DOCUMENT_STORE_SCHEMA_FIXTURE_CREATED = "RAW_DOCUMENT_STORE_SCHEMA_FIXTURE_CREATED"

REQUIRED_RAW_DOCUMENT_STORE_FIELDS = [
    "document_id",
    "document_version_id",
    "source_id",
    "source_type",
    "document_family",
    "document_type",
    "document_title",
    "document_url_or_path",
    "local_reference_path",
    "body_or_text_ref",
    "dataset_schema_ref",
    "symbol",
    "instrument_type",
    "entity_scope",
    "industry_scope",
    "event_scope",
    "published_at",
    "available_time",
    "fetched_at",
    "as_of_date",
    "period_start",
    "period_end",
    "source_hash",
    "content_hash",
    "metadata_hash",
    "columns_hash",
    "revision_id",
    "supersedes_document_version_id",
    "parser_version",
    "extraction_version",
    "language",
    "permission_class",
    "storage_policy",
    "manual_review_required",
    "manual_review_status",
    "reviewer",
    "reviewed_at",
    "review_reason",
    "quality_status",
    "pit_valid",
    "decision_time_eligible",
    "copyright_storage_policy",
    "raw_content_stored",
    "pii_flag",
    "restricted_content_flag",
    "rumor_flag",
    "report_only",
    "diagnostic_only",
]

HARD_GATE_FIELDS = [
    "document_id",
    "document_version_id",
    "source_id",
    "available_time",
    "revision_id",
    "permission_class",
    "storage_policy",
    "manual_review_status",
    "quality_status",
    "pit_valid",
    "report_only",
    "diagnostic_only",
]

FORBIDDEN_METADATA_FALSE_FLAGS = [
    "production_raw_document_store_created",
    "real_source_permission_created",
    "real_data_fetched",
    "raw_document_ingestion_created",
    "factor_observations_created",
    "event_ingestion_created",
    "company_exposure_created",
    "replay_evidence_bundle_created",
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

DOCUMENT_FAMILIES = {
    "LOCAL_CSV_DATASET",
    "PUBLIC_OFFICIAL_ANNOUNCEMENT",
    "PUBLIC_EXCHANGE_DISCLOSURE",
    "PUBLIC_POLICY_DOCUMENT",
    "PUBLIC_MACRO_RELEASE",
    "COPYRIGHTED_NEWS_REFERENCE",
    "BLOCKED_PRIVATE_RUMOR",
    "MANUAL_REVIEW_NOTE",
    "DIAGNOSTIC_FIXTURE",
}

PERMISSION_CLASSES = {
    "PUBLIC_PERMITTED",
    "PUBLIC_REVIEW_REQUIRED",
    "USER_PROVIDED_LOCAL",
    "TERMS_UNKNOWN",
    "RESTRICTED",
    "PROHIBITED",
    "DIAGNOSTIC_ONLY",
}

STORAGE_POLICIES = {
    "REFERENCE_ONLY",
    "HASH_ONLY",
    "LOCAL_REVIEWED_COPY_ALLOWED",
    "STRUCTURED_EXTRACT_ONLY",
    "DO_NOT_STORE_CONTENT",
    "BLOCKED",
}


@dataclass(frozen=True)
class RawDocumentStoreSchemaFixtureSettings:
    output_dir: Path = Path("outputs/reports/manual_diagnostics/raw_document_store_schema_fixture_v0_1")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True
    production_raw_document_store_created: bool = False
    real_source_permission_created: bool = False
    real_data_fetched: bool = False
    raw_document_ingestion_created: bool = False
    factor_observations_created: bool = False
    event_ingestion_created: bool = False
    company_exposure_created: bool = False
    replay_evidence_bundle_created: bool = False
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
class RawDocumentStoreSchemaFixtureResult:
    raw_document_store_schema_fixture_id: str
    status: str
    workflow_stage: str
    document_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    artifact_paths: dict[str, Path]


def build_raw_document_store_schema_fixture(
    *,
    output_dir: str | Path | None = None,
    settings: RawDocumentStoreSchemaFixtureSettings | None = None,
) -> RawDocumentStoreSchemaFixtureResult:
    resolved_settings = settings or RawDocumentStoreSchemaFixtureSettings()
    if output_dir is not None:
        resolved_settings = RawDocumentStoreSchemaFixtureSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)

    fixture_rows = build_raw_document_store_fixture_rows()
    fixture_id = _fixture_id(fixture_rows, resolved_settings.config_version)
    paths = resolve_raw_document_store_schema_fixture_paths(resolved_settings.output_dir, fixture_id)
    schema_fields = build_raw_document_store_schema_fields()
    permission_matrix = build_raw_document_store_permission_matrix(fixture_rows)
    storage_policy_matrix = build_raw_document_store_storage_policy_matrix(fixture_rows)
    pit_timing_matrix = build_raw_document_store_pit_timing_matrix(fixture_rows)
    validation_summary = validate_raw_document_store_fixture(
        fixture_rows=fixture_rows,
        settings=resolved_settings,
        output_dir=resolved_settings.output_dir,
    )
    validation_issue_count = int((~validation_summary["passed"]).sum())
    status = "PASS" if validation_issue_count == 0 else "FAIL"
    result = RawDocumentStoreSchemaFixtureResult(
        raw_document_store_schema_fixture_id=fixture_id,
        status=status,
        workflow_stage=RAW_DOCUMENT_STORE_SCHEMA_FIXTURE_CREATED,
        document_count=len(fixture_rows),
        validation_issue_count=validation_issue_count,
        report_only=True,
        diagnostic_only=True,
        artifact_paths=paths,
    )
    if resolved_settings.write_artifacts:
        write_raw_document_store_schema_fixture_artifacts(
            result=result,
            settings=resolved_settings,
            schema_fields=schema_fields,
            fixture_rows=fixture_rows,
            permission_matrix=permission_matrix,
            storage_policy_matrix=storage_policy_matrix,
            pit_timing_matrix=pit_timing_matrix,
            validation_summary=validation_summary,
        )
    return result


def build_raw_document_store_fixture_rows() -> pd.DataFrame:
    rows = [
        _row(
            document_id="LOCAL_CSV_REVIEWED_DATASET_SAMPLE",
            source_id="LOCAL_CSV_REVIEWED_SAMPLE",
            source_type="LOCAL_CSV",
            document_family="LOCAL_CSV_DATASET",
            document_type="DATASET_CSV",
            document_title="Synthetic reviewed local CSV dataset reference",
            document_url_or_path="local://synthetic/reviewed_dataset_sample.csv",
            local_reference_path="outputs/reports/manual_diagnostics/raw_document_store_schema_fixture_v0_1/synthetic/reviewed_dataset_sample.csv",
            body_or_text_ref="",
            dataset_schema_ref="synthetic_schema://local_csv_reviewed_dataset_sample",
            symbol="000001",
            instrument_type="STOCK",
            entity_scope="SYMBOL",
            industry_scope="BANKS",
            event_scope="NONE",
            published_at="2024-04-01T16:30:00",
            available_time="2024-04-01T17:00:00",
            fetched_at="",
            as_of_date="2024-04-01",
            period_start="2024-04-01",
            period_end="2024-04-01",
            permission_class="USER_PROVIDED_LOCAL",
            storage_policy="LOCAL_REVIEWED_COPY_ALLOWED",
            manual_review_status="REVIEW_REQUIRED",
            quality_status="REVIEW_REQUIRED",
            pit_valid=True,
            decision_time_eligible=False,
            copyright_storage_policy="LOCAL_REVIEWED_COPY_ALLOWED",
            raw_content_stored=False,
            review_reason="Synthetic local CSV schema example only; no data/raw or data/processed write.",
        ),
        _row(
            document_id="PUBLIC_OFFICIAL_ANNOUNCEMENT_REFERENCE_SAMPLE",
            source_id="PUBLIC_OFFICIAL_ANNOUNCEMENT_SAMPLE",
            source_type="PUBLIC_OFFICIAL",
            document_family="PUBLIC_OFFICIAL_ANNOUNCEMENT",
            document_type="ANNOUNCEMENT_REFERENCE",
            document_title="Synthetic public official announcement reference",
            document_url_or_path="official-reference://announcement/sample",
            local_reference_path="",
            body_or_text_ref="reference_only://announcement/sample",
            dataset_schema_ref="",
            symbol="000001",
            instrument_type="STOCK",
            entity_scope="SYMBOL",
            industry_scope="BANKS",
            event_scope="DISCLOSURE",
            published_at="2024-04-01T18:00:00",
            available_time="2024-04-01T18:30:00",
            fetched_at="",
            as_of_date="2024-04-01",
            permission_class="PUBLIC_REVIEW_REQUIRED",
            storage_policy="REFERENCE_ONLY",
            manual_review_status="REVIEW_REQUIRED",
            quality_status="REVIEW_REQUIRED",
            pit_valid=True,
            decision_time_eligible=False,
            copyright_storage_policy="REFERENCE_ONLY",
            raw_content_stored=False,
            review_reason="Reference/hash example only; does not verify production source permission.",
        ),
        _row(
            document_id="PUBLIC_EXCHANGE_DISCLOSURE_REFERENCE_SAMPLE",
            source_id="PUBLIC_EXCHANGE_DISCLOSURE_SAMPLE",
            source_type="PUBLIC_EXCHANGE",
            document_family="PUBLIC_EXCHANGE_DISCLOSURE",
            document_type="EXCHANGE_DISCLOSURE_REFERENCE",
            document_title="Synthetic public exchange disclosure reference",
            document_url_or_path="exchange-reference://disclosure/sample",
            local_reference_path="",
            body_or_text_ref="hash_only://exchange_disclosure/sample",
            dataset_schema_ref="",
            symbol="159915",
            instrument_type="ETF",
            entity_scope="FUND",
            industry_scope="BROAD_MARKET",
            event_scope="EXCHANGE_DISCLOSURE",
            published_at="2024-04-01T17:45:00",
            available_time="2024-04-01T18:10:00",
            fetched_at="",
            as_of_date="2024-04-01",
            permission_class="PUBLIC_REVIEW_REQUIRED",
            storage_policy="HASH_ONLY",
            manual_review_status="REVIEW_REQUIRED",
            quality_status="REVIEW_REQUIRED",
            pit_valid=True,
            decision_time_eligible=False,
            copyright_storage_policy="HASH_ONLY",
            raw_content_stored=False,
            review_reason="Hash/reference example only; no exchange data was fetched.",
        ),
        _row(
            document_id="PUBLIC_POLICY_DOCUMENT_REFERENCE_SAMPLE",
            source_id="PUBLIC_POLICY_DOCUMENT_SAMPLE",
            source_type="PUBLIC_POLICY",
            document_family="PUBLIC_POLICY_DOCUMENT",
            document_type="POLICY_DOCUMENT_REFERENCE",
            document_title="Synthetic public policy document reference",
            document_url_or_path="policy-reference://document/sample",
            local_reference_path="",
            body_or_text_ref="reference_only://policy_document/sample",
            dataset_schema_ref="",
            symbol="",
            instrument_type="MARKET",
            entity_scope="MARKET",
            industry_scope="ALL",
            event_scope="POLICY",
            published_at="2024-03-31T09:00:00",
            available_time="2024-03-31T09:30:00",
            fetched_at="",
            as_of_date="2024-03-31",
            permission_class="PUBLIC_REVIEW_REQUIRED",
            storage_policy="REFERENCE_ONLY",
            manual_review_status="REVIEW_REQUIRED",
            quality_status="REVIEW_REQUIRED",
            pit_valid=True,
            decision_time_eligible=False,
            copyright_storage_policy="REFERENCE_ONLY",
            raw_content_stored=False,
            review_reason="Policy reference example only; no production policy corpus created.",
        ),
        _row(
            document_id="PUBLIC_MACRO_RELEASE_DATASET_SAMPLE",
            source_id="PUBLIC_MACRO_RELEASE_SAMPLE",
            source_type="PUBLIC_MACRO",
            document_family="PUBLIC_MACRO_RELEASE",
            document_type="MACRO_DATASET_REFERENCE",
            document_title="Synthetic public macro release dataset reference",
            document_url_or_path="macro-reference://release/sample",
            local_reference_path="",
            body_or_text_ref="",
            dataset_schema_ref="synthetic_schema://macro_release_dataset_sample",
            symbol="",
            instrument_type="MACRO",
            entity_scope="MACRO",
            industry_scope="ALL",
            event_scope="MACRO_RELEASE",
            published_at="2024-03-31T10:00:00",
            available_time="2024-03-31T10:15:00",
            fetched_at="",
            as_of_date="2024-03-31",
            period_start="2024-03-01",
            period_end="2024-03-31",
            permission_class="PUBLIC_REVIEW_REQUIRED",
            storage_policy="STRUCTURED_EXTRACT_ONLY",
            manual_review_status="REVIEW_REQUIRED",
            quality_status="REVIEW_REQUIRED",
            pit_valid=True,
            decision_time_eligible=False,
            copyright_storage_policy="STRUCTURED_EXTRACT_ONLY",
            raw_content_stored=False,
            review_reason="Macro dataset schema example only; no real macro release was fetched.",
        ),
        _row(
            document_id="COPYRIGHTED_NEWS_REFERENCE_ONLY_SAMPLE",
            source_id="COPYRIGHTED_NEWS_SAMPLE",
            source_type="COPYRIGHTED_NEWS",
            document_family="COPYRIGHTED_NEWS_REFERENCE",
            document_type="NEWS_REFERENCE_ONLY",
            document_title="Synthetic copyrighted news reference only",
            document_url_or_path="news-reference://reference-only/sample",
            local_reference_path="",
            body_or_text_ref="reference_only://news_reference/sample",
            dataset_schema_ref="",
            symbol="000001",
            instrument_type="STOCK",
            entity_scope="SYMBOL",
            industry_scope="BANKS",
            event_scope="NEWS_CONTEXT",
            published_at="2024-04-01T12:00:00",
            available_time="2024-04-01T12:30:00",
            fetched_at="",
            as_of_date="2024-04-01",
            permission_class="RESTRICTED",
            storage_policy="REFERENCE_ONLY",
            manual_review_status="REVIEW_REQUIRED",
            quality_status="REVIEW_REQUIRED",
            pit_valid=True,
            decision_time_eligible=False,
            copyright_storage_policy="REFERENCE_ONLY",
            raw_content_stored=False,
            restricted_content_flag=True,
            review_reason="Copyrighted news reference only; full text must not be stored.",
        ),
        _row(
            document_id="BLOCKED_PRIVATE_RUMOR_SAMPLE",
            source_id="BLOCKED_PRIVATE_RUMOR_SAMPLE",
            source_type="BLOCKED_PRIVATE",
            document_family="BLOCKED_PRIVATE_RUMOR",
            document_type="PRIVATE_RUMOR_BLOCKED",
            document_title="Synthetic blocked private rumor sample",
            document_url_or_path="blocked://private-rumor/sample",
            local_reference_path="",
            body_or_text_ref="",
            dataset_schema_ref="",
            symbol="000001",
            instrument_type="STOCK",
            entity_scope="SYMBOL",
            industry_scope="BANKS",
            event_scope="RUMOR",
            published_at="2024-04-01T11:00:00",
            available_time="2024-04-01T11:05:00",
            fetched_at="",
            as_of_date="2024-04-01",
            permission_class="PROHIBITED",
            storage_policy="BLOCKED",
            manual_review_status="BLOCKED",
            quality_status="BLOCKED",
            pit_valid=False,
            decision_time_eligible=False,
            copyright_storage_policy="BLOCKED",
            raw_content_stored=False,
            pii_flag=False,
            restricted_content_flag=True,
            rumor_flag=True,
            review_reason="Blocked private rumor sample; prohibited from PIT, replay, and evidence use.",
        ),
    ]
    return pd.DataFrame(rows, columns=REQUIRED_RAW_DOCUMENT_STORE_FIELDS)


def build_raw_document_store_schema_fields() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "field_name": field,
                "required": True,
                "hard_gate": field in HARD_GATE_FIELDS or field in {"source_hash", "content_hash"},
                "data_type_hint": _data_type_hint(field),
                "description": _field_description(field),
            }
            for field in REQUIRED_RAW_DOCUMENT_STORE_FIELDS
        ]
    )


def build_raw_document_store_permission_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in fixture_rows.to_dict(orient="records"):
        permission_class = _text(row["permission_class"])
        if permission_class == "PROHIBITED":
            decision = "BLOCK"
        elif permission_class in {"RESTRICTED", "TERMS_UNKNOWN", "PUBLIC_REVIEW_REQUIRED"}:
            decision = "REVIEW_REQUIRED"
        else:
            decision = "REVIEW_REQUIRED"
        rows.append(
            {
                "document_id": row["document_id"],
                "source_id": row["source_id"],
                "permission_class": permission_class,
                "permission_decision": decision,
                "fixture_grants_real_permission": False,
                "source_id_implies_permission": False,
                "notes": _permission_note(permission_class),
            }
        )
    return pd.DataFrame(rows)


def build_raw_document_store_storage_policy_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in fixture_rows.to_dict(orient="records"):
        storage_policy = _text(row["storage_policy"])
        raw_content_stored = _bool(row["raw_content_stored"])
        rows.append(
            {
                "document_id": row["document_id"],
                "storage_policy": storage_policy,
                "copyright_storage_policy": row["copyright_storage_policy"],
                "content_storage_allowed": storage_policy
                in {"LOCAL_REVIEWED_COPY_ALLOWED", "STRUCTURED_EXTRACT_ONLY", "REFERENCE_ONLY", "HASH_ONLY"},
                "full_raw_content_allowed": storage_policy == "LOCAL_REVIEWED_COPY_ALLOWED",
                "raw_content_stored": raw_content_stored,
                "fixture_writes_raw_content": False,
                "notes": _storage_note(storage_policy),
            }
        )
    return pd.DataFrame(rows)


def build_raw_document_store_pit_timing_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in fixture_rows.to_dict(orient="records"):
        published_ok = _timestamp_order_ok(row.get("published_at"), row.get("available_time"))
        period_ok = _timestamp_order_ok(row.get("period_end"), row.get("available_time"))
        rows.append(
            {
                "document_id": row["document_id"],
                "available_time": row["available_time"],
                "published_at": row["published_at"],
                "period_end": row["period_end"],
                "available_time_present": bool(_text(row["available_time"])),
                "published_at_before_available_time": published_ok,
                "period_end_before_available_time": period_ok,
                "pit_valid": _bool(row["pit_valid"]),
                "decision_time_eligible": _bool(row["decision_time_eligible"]),
                "pit_check_passed": bool(_text(row["available_time"])) and published_ok and period_ok,
            }
        )
    return pd.DataFrame(rows)


def validate_raw_document_store_fixture(
    *,
    fixture_rows: pd.DataFrame,
    settings: RawDocumentStoreSchemaFixtureSettings,
    output_dir: Path,
) -> pd.DataFrame:
    row_text = " ".join(fixture_rows.fillna("").astype(str).agg(" ".join, axis=1)).lower()
    checks = [
        ("required_fields_present", set(REQUIRED_RAW_DOCUMENT_STORE_FIELDS).issubset(set(fixture_rows.columns))),
        ("document_id_non_empty_string", fixture_rows["document_id"].map(_is_non_empty_string).all()),
        ("document_version_id_non_empty_string", fixture_rows["document_version_id"].map(_is_non_empty_string).all()),
        ("source_id_present", fixture_rows["source_id"].map(_is_non_empty_string).all()),
        ("source_id_does_not_imply_permission", True),
        ("available_time_present", fixture_rows["available_time"].map(_is_non_empty_string).all()),
        (
            "published_at_before_available_time",
            fixture_rows.apply(lambda row: _timestamp_order_ok(row["published_at"], row["available_time"]), axis=1).all(),
        ),
        (
            "period_end_before_available_time",
            fixture_rows.apply(lambda row: _timestamp_order_ok(row["period_end"], row["available_time"]), axis=1).all(),
        ),
        (
            "source_hash_or_content_hash_present",
            fixture_rows.apply(lambda row: bool(_text(row["source_hash"])) or bool(_text(row["content_hash"])), axis=1).all(),
        ),
        ("revision_id_present", fixture_rows["revision_id"].map(_is_non_empty_string).all()),
        ("permission_class_present", fixture_rows["permission_class"].map(_is_non_empty_string).all()),
        ("storage_policy_present", fixture_rows["storage_policy"].map(_is_non_empty_string).all()),
        ("manual_review_status_present", fixture_rows["manual_review_status"].map(_is_non_empty_string).all()),
        ("quality_status_present", fixture_rows["quality_status"].map(_is_non_empty_string).all()),
        ("pit_valid_explicit", fixture_rows["pit_valid"].map(lambda value: _text(value) in {"True", "False", "true", "false"}).all()),
        ("report_only_true", fixture_rows["report_only"].map(_bool).all()),
        ("diagnostic_only_true", fixture_rows["diagnostic_only"].map(_bool).all()),
        ("no_token_or_secret_values", not _contains_secret_like(row_text)),
        (
            "no_pii_unless_blocked",
            fixture_rows[fixture_rows["storage_policy"] != "BLOCKED"]["pii_flag"].map(lambda value: not _bool(value)).all(),
        ),
        (
            "blocked_private_rumor_not_decision_time_eligible",
            fixture_rows.query("document_id == 'BLOCKED_PRIVATE_RUMOR_SAMPLE'")["decision_time_eligible"].map(
                lambda value: not _bool(value)
            ).all(),
        ),
        (
            "copyrighted_news_full_text_not_stored",
            fixture_rows.query("document_id == 'COPYRIGHTED_NEWS_REFERENCE_ONLY_SAMPLE'")["raw_content_stored"].map(
                lambda value: not _bool(value)
            ).all(),
        ),
        ("settings_forbidden_flags_false", all(getattr(settings, flag) is False for flag in FORBIDDEN_METADATA_FALSE_FLAGS)),
        ("no_protected_data_writes", not any((output_dir / part).exists() for part in ["data/raw", "data/processed", "data/cache"])),
        ("no_docs_project_sources", not (output_dir / "docs" / "project_sources").exists()),
    ]
    checks.extend((flag, getattr(settings, flag) is False) for flag in FORBIDDEN_METADATA_FALSE_FLAGS)
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


def resolve_raw_document_store_schema_fixture_paths(output_dir: Path, fixture_id: str) -> dict[str, Path]:
    artifact_dir = output_dir / fixture_id
    return {
        "artifact_dir": artifact_dir,
        "metadata": artifact_dir / "raw_document_store_schema_fixture_metadata.json",
        "schema_fields": artifact_dir / "raw_document_store_schema_fields.csv",
        "fixture_rows": artifact_dir / "raw_document_store_fixture_rows.csv",
        "permission_matrix": artifact_dir / "raw_document_store_permission_matrix.csv",
        "storage_policy_matrix": artifact_dir / "raw_document_store_storage_policy_matrix.csv",
        "pit_timing_matrix": artifact_dir / "raw_document_store_pit_timing_matrix.csv",
        "validation_summary": artifact_dir / "raw_document_store_validation_summary.csv",
        "limitations": artifact_dir / "raw_document_store_limitations.md",
        "recommended_next_task": artifact_dir / "recommended_next_task.md",
    }


def write_raw_document_store_schema_fixture_artifacts(
    *,
    result: RawDocumentStoreSchemaFixtureResult,
    settings: RawDocumentStoreSchemaFixtureSettings,
    schema_fields: pd.DataFrame,
    fixture_rows: pd.DataFrame,
    permission_matrix: pd.DataFrame,
    storage_policy_matrix: pd.DataFrame,
    pit_timing_matrix: pd.DataFrame,
    validation_summary: pd.DataFrame,
) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    schema_fields.to_csv(paths["schema_fields"], index=False)
    fixture_rows.to_csv(paths["fixture_rows"], index=False)
    permission_matrix.to_csv(paths["permission_matrix"], index=False)
    storage_policy_matrix.to_csv(paths["storage_policy_matrix"], index=False)
    pit_timing_matrix.to_csv(paths["pit_timing_matrix"], index=False)
    validation_summary.to_csv(paths["validation_summary"], index=False)
    paths["limitations"].write_text(render_raw_document_store_limitations(result), encoding="utf-8")
    paths["recommended_next_task"].write_text(_recommended_next_task(), encoding="utf-8")
    paths["metadata"].write_text(json.dumps(_metadata(result, settings), indent=2, ensure_ascii=False), encoding="utf-8")


def render_raw_document_store_limitations(result: RawDocumentStoreSchemaFixtureResult) -> str:
    return "\n".join(
        [
            "# Raw Document Store Schema Fixture Limitations v0.1",
            "",
            "This workflow creates tiny synthetic raw-document/raw-dataset reference rows for schema and governance review only.",
            "",
            "## Not Granted",
            "",
            "- No fixture row is a production raw document.",
            "- No fixture row grants real source permission.",
            "- No fixture row proves real data was fetched.",
            "- No fixture row is replay-ready evidence.",
            "- No fixture row creates factor observations, structured events, company exposure mappings, or replay evidence bundles.",
            "- No fixture row creates buy-review eligibility, buy_review_allowed, performance validation, broker behavior, orders, messages, APIs, or trading.",
            "- Copyrighted news rows are reference-only and full raw content is not stored.",
            "",
            "## Current Result",
            "",
            f"- raw_document_store_schema_fixture_id: {result.raw_document_store_schema_fixture_id}",
            f"- status: {result.status}",
            f"- workflow_stage: {result.workflow_stage}",
            f"- document_count: {result.document_count}",
            f"- validation_issue_count: {result.validation_issue_count}",
        ]
    )


def _metadata(
    result: RawDocumentStoreSchemaFixtureResult,
    settings: RawDocumentStoreSchemaFixtureSettings,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "raw_document_store_schema_fixture_id": result.raw_document_store_schema_fixture_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "config_version": settings.config_version,
        "document_count": result.document_count,
        "validation_issue_count": result.validation_issue_count,
        "raw_document_store_schema_fixture_created": True,
        "report_only": True,
        "diagnostic_only": True,
        "artifact_paths": {key: str(path) for key, path in result.artifact_paths.items()},
    }
    metadata.update({flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS})
    return metadata


def _row(**values: Any) -> dict[str, Any]:
    row = {
        "document_id": "",
        "document_version_id": "",
        "source_id": "",
        "source_type": "",
        "document_family": "",
        "document_type": "",
        "document_title": "",
        "document_url_or_path": "",
        "local_reference_path": "",
        "body_or_text_ref": "",
        "dataset_schema_ref": "",
        "symbol": "",
        "instrument_type": "",
        "entity_scope": "",
        "industry_scope": "",
        "event_scope": "",
        "published_at": "",
        "available_time": "",
        "fetched_at": "",
        "as_of_date": "",
        "period_start": "",
        "period_end": "",
        "source_hash": "",
        "content_hash": "",
        "metadata_hash": "",
        "columns_hash": "",
        "revision_id": "",
        "supersedes_document_version_id": "",
        "parser_version": "diagnostic_parser_v0",
        "extraction_version": "diagnostic_extraction_v0",
        "language": "zh-CN",
        "permission_class": "DIAGNOSTIC_ONLY",
        "storage_policy": "REFERENCE_ONLY",
        "manual_review_required": True,
        "manual_review_status": "DIAGNOSTIC_ONLY",
        "reviewer": "diagnostic_fixture",
        "reviewed_at": "",
        "review_reason": "Synthetic schema fixture only.",
        "quality_status": "DIAGNOSTIC_ONLY",
        "pit_valid": False,
        "decision_time_eligible": False,
        "copyright_storage_policy": "REFERENCE_ONLY",
        "raw_content_stored": False,
        "pii_flag": False,
        "restricted_content_flag": False,
        "rumor_flag": False,
        "report_only": True,
        "diagnostic_only": True,
    }
    row.update(values)
    row["document_version_id"] = row["document_version_id"] or f"{row['document_id']}::v0"
    row["revision_id"] = row["revision_id"] or f"REV-{_short_hash(row['document_id'])}"
    row["source_hash"] = row["source_hash"] or f"sha256:{_hash_text('source:' + row['source_id'])}"
    row["content_hash"] = row["content_hash"] or f"sha256:{_hash_text('content:' + row['document_id'])}"
    row["metadata_hash"] = row["metadata_hash"] or f"sha256:{_hash_text('metadata:' + row['document_id'])}"
    row["columns_hash"] = row["columns_hash"] or f"sha256:{_hash_text('columns:' + row['document_id'])}"
    return row


def _assert_settings_safe(settings: RawDocumentStoreSchemaFixtureSettings) -> None:
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Raw document store schema fixture must remain report_only and diagnostic_only.")
    enabled = [flag for flag in FORBIDDEN_METADATA_FALSE_FLAGS if getattr(settings, flag)]
    if enabled:
        raise ValueError(f"Unsafe raw document store fixture settings enabled: {', '.join(enabled)}")


def _fixture_id(fixture_rows: pd.DataFrame, config_version: str) -> str:
    digest = hashlib.sha256(config_version.encode("utf-8"))
    digest.update("|".join(REQUIRED_RAW_DOCUMENT_STORE_FIELDS).encode("utf-8"))
    digest.update(fixture_rows.to_csv(index=False).encode("utf-8"))
    return digest.hexdigest()[:12]


def _recommended_next_task() -> str:
    return "\n".join(
        [
            "# Recommended Next Task",
            "",
            "Raw Document Store Schema Fixture Views Report-Only v0.1",
            "",
            "Add index, health, and status artifact views for this report-only raw document store schema fixture. Keep the fixture synthetic and do not create a production raw document store, real source permissions, raw document ingestion, or downstream evidence bundles.",
        ]
    )


def _field_description(field: str) -> str:
    descriptions = {
        "document_id": "Stable synthetic document or dataset reference identifier.",
        "document_version_id": "Stable synthetic version identifier for the document reference.",
        "source_id": "Source registry reference; does not grant permission by itself.",
        "available_time": "Earliest time this synthetic reference would be available in a PIT workflow.",
        "source_hash": "Synthetic source lineage hash.",
        "content_hash": "Synthetic content/reference hash.",
        "revision_id": "Synthetic revision identifier.",
        "permission_class": "Permission class for governance review.",
        "storage_policy": "Storage policy guard for content/reference handling.",
        "report_only": "Must be true for this workflow.",
        "diagnostic_only": "Must be true for this workflow.",
    }
    return descriptions.get(field, "Raw document store schema fixture field.")


def _data_type_hint(field: str) -> str:
    if field in {
        "manual_review_required",
        "pit_valid",
        "decision_time_eligible",
        "raw_content_stored",
        "pii_flag",
        "restricted_content_flag",
        "rumor_flag",
        "report_only",
        "diagnostic_only",
    }:
        return "boolean"
    if field.endswith("_at") or field in {"available_time", "published_at"}:
        return "timestamp"
    if field in {"as_of_date", "period_start", "period_end"}:
        return "date"
    return "string"


def _permission_note(permission_class: str) -> str:
    if permission_class == "PROHIBITED":
        return "Blocked: prohibited private/rumor source cannot be used."
    if permission_class == "RESTRICTED":
        return "Restricted: reference-only or structured-extract review required."
    if permission_class == "USER_PROVIDED_LOCAL":
        return "User-provided local sample requires manual review and does not write data/raw."
    return "Review required: fixture cannot grant permission by itself."


def _storage_note(storage_policy: str) -> str:
    if storage_policy == "BLOCKED":
        return "Blocked: no storage or downstream use allowed."
    if storage_policy == "LOCAL_REVIEWED_COPY_ALLOWED":
        return "Local reviewed copy policy is synthetic/report-only here."
    if storage_policy in {"REFERENCE_ONLY", "HASH_ONLY"}:
        return "Reference/hash only; full content is not stored."
    return "Structured extract only; no raw content storage in this fixture."


def _timestamp_order_ok(first: Any, second: Any) -> bool:
    first_text = _text(first)
    second_text = _text(second)
    if not first_text or not second_text:
        return True
    first_ts = pd.to_datetime(first_text, errors="coerce")
    second_ts = pd.to_datetime(second_text, errors="coerce")
    if pd.isna(first_ts) or pd.isna(second_ts):
        return False
    return bool(first_ts <= second_ts)


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _contains_secret_like(text: str) -> bool:
    return bool(re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", text))


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _short_hash(text: str) -> str:
    return _hash_text(text)[:10].upper()


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
