"""Report-only reviewed LOCAL_CSV replay prototype input contract fixture.

This module writes tiny deterministic contract artifacts for future reviewed
LOCAL_CSV replay prototype inputs. It does not create real input packages,
does not load data from CSV files, does not validate PIT admissibility, does
not run replay, does not create replay evidence bundles or decisions, does not
derive labels, and does not authorize training, stock_profile, paper workflow,
buy-review, performance validation, current-candidates, snapshots, or trading.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED = (
    "REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED"
)

WORKFLOW_STATUSES = {"PASS", "WARN", "FAIL", "NO_INPUT"}

CONTRACT_FILE_NAMES = [
    "source_registry_reviewed.csv",
    "raw_document_store_reviewed.csv",
    "factor_definition_reviewed.csv",
    "company_exposure_reviewed.csv",
    "event_structured_reviewed.csv",
    "factor_observation_reviewed.csv",
    "replay_evidence_bundle_reviewed.csv",
    "replay_decision_reviewed.csv",
    "forward_return_label_reviewed.csv",
    "market_data_reviewed.csv",
    "benchmark_data_reviewed.csv",
    "trading_calendar_reviewed.csv",
]

SAFETY_FALSE_FLAGS = [
    "real_reviewed_input_package_created",
    "active_reviewed_input_candidate_created",
    "pit_admissibility_validator_implemented",
    "real_replay_input_created",
    "real_replay_evidence_bundle_created",
    "real_replay_decision_created",
    "replay_decision_frozen",
    "real_forward_labels_created",
    "future_labels_joined",
    "future_label_joined_to_decision_input",
    "training_dataset_created",
    "metric_computation_performed",
    "signal_score_implemented",
    "signal_score_input_authorized",
    "model_training_performed",
    "active_weights_created",
    "active_thresholds_created",
    "stock_profile_validation_created",
    "paper_validation_created",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "strategy_performance_validated",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "broker_api_called",
    "external_api_called",
    "llm_api_called",
    "message_sent",
    "order_placed",
    "trading_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "reviewed_local_csv_replay_prototype_input_contract_fixture_report.md",
    "contract_matrix": "reviewed_local_csv_contract_matrix.csv",
    "field_contract": "reviewed_local_csv_field_contract.csv",
    "pit_rule_matrix": "reviewed_local_csv_pit_rule_matrix.csv",
    "lineage_rule_matrix": "reviewed_local_csv_lineage_rule_matrix.csv",
    "quality_review_rule_matrix": "reviewed_local_csv_quality_review_rule_matrix.csv",
    "forbidden_interpretation_matrix": "reviewed_local_csv_forbidden_interpretation_matrix.csv",
    "safety_flags": "reviewed_local_csv_safety_flags.json",
    "recommended_next_task": "recommended_next_task.md",
}


@dataclass(frozen=True)
class ReviewedLocalCsvReplayPrototypeInputContractFixtureSettings:
    output_dir: Path = Path(
        "outputs/reports/manual_diagnostics/reviewed_local_csv_replay_prototype_input_contract_fixture_v0_1"
    )
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ReviewedLocalCsvReplayPrototypeInputContractFixtureResult:
    reviewed_local_csv_replay_prototype_input_contract_fixture_id: str
    status: str
    workflow_stage: str
    contract_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    artifact_paths: dict[str, Path]


def build_reviewed_local_csv_replay_prototype_input_contract_fixture(
    *,
    output_dir: str | Path | None = None,
    settings: ReviewedLocalCsvReplayPrototypeInputContractFixtureSettings | None = None,
) -> ReviewedLocalCsvReplayPrototypeInputContractFixtureResult:
    resolved_settings = settings or ReviewedLocalCsvReplayPrototypeInputContractFixtureSettings()
    if output_dir is not None:
        resolved_settings = ReviewedLocalCsvReplayPrototypeInputContractFixtureSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)

    contract_matrix = build_reviewed_local_csv_contract_matrix()
    field_contract = build_reviewed_local_csv_field_contract(contract_matrix)
    pit_rule_matrix = build_reviewed_local_csv_pit_rule_matrix()
    lineage_rule_matrix = build_reviewed_local_csv_lineage_rule_matrix()
    quality_review_rule_matrix = build_reviewed_local_csv_quality_review_rule_matrix()
    forbidden_interpretation_matrix = build_reviewed_local_csv_forbidden_interpretation_matrix(contract_matrix)
    validation_issue_count = validate_reviewed_local_csv_contract_fixture(
        contract_matrix=contract_matrix,
        field_contract=field_contract,
        pit_rule_matrix=pit_rule_matrix,
        lineage_rule_matrix=lineage_rule_matrix,
        quality_review_rule_matrix=quality_review_rule_matrix,
        forbidden_interpretation_matrix=forbidden_interpretation_matrix,
        settings=resolved_settings,
    )
    fixture_id = _fixture_id(
        contract_matrix=contract_matrix,
        field_contract=field_contract,
        pit_rule_matrix=pit_rule_matrix,
        config_version=resolved_settings.config_version,
    )
    paths = resolve_reviewed_local_csv_replay_prototype_input_contract_fixture_paths(
        resolved_settings.output_dir,
        fixture_id,
    )
    result = ReviewedLocalCsvReplayPrototypeInputContractFixtureResult(
        reviewed_local_csv_replay_prototype_input_contract_fixture_id=fixture_id,
        status="PASS" if validation_issue_count == 0 else "FAIL",
        workflow_stage=REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED,
        contract_count=len(contract_matrix),
        validation_issue_count=validation_issue_count,
        report_only=True,
        diagnostic_only=True,
        artifact_paths=paths,
    )

    if resolved_settings.write_artifacts:
        write_reviewed_local_csv_replay_prototype_input_contract_fixture_artifacts(
            result=result,
            settings=resolved_settings,
            contract_matrix=contract_matrix,
            field_contract=field_contract,
            pit_rule_matrix=pit_rule_matrix,
            lineage_rule_matrix=lineage_rule_matrix,
            quality_review_rule_matrix=quality_review_rule_matrix,
            forbidden_interpretation_matrix=forbidden_interpretation_matrix,
        )
    return result


def build_reviewed_local_csv_contract_matrix() -> pd.DataFrame:
    rows = [
        _contract(
            file_name="source_registry_reviewed.csv",
            contract_role="Reviewed source registry permission and source identity contract.",
            required_minimum_fields=[
                "source_id",
                "source_name",
                "source_type",
                "source_permission_scope",
                "as_of_date",
                "available_time",
                "source_hash",
                "revision_id",
                "quality_status",
                "reviewer_id",
                "reviewed_at",
                "review_status",
            ],
            pit_fields=["as_of_date", "available_time", "revision_id"],
            source_lineage_fields=["source_id", "source_name", "source_type", "source_hash"],
            quality_fields=["quality_status", "review_status"],
            reviewer_fields=["reviewer_id", "reviewed_at", "review_status", "review_notes"],
            forbidden_interpretation="Not production source permission, not live fetch authorization, not an API adapter.",
            current_allowed_status="REPORT_ONLY_CONTRACT_ALLOWED",
            future_gate_required="Reviewed source permission gate before real ingestion or replay input use.",
        ),
        _contract(
            file_name="raw_document_store_reviewed.csv",
            contract_role="Reviewed raw document metadata and document availability contract.",
            required_minimum_fields=[
                "document_id",
                "source_id",
                "document_type",
                "document_date",
                "publish_time",
                "available_time",
                "local_path_or_reference",
                "source_hash",
                "revision_id",
                "quality_status",
                "reviewer_id",
                "reviewed_at",
                "review_status",
            ],
            pit_fields=["document_date", "publish_time", "available_time"],
            source_lineage_fields=["document_id", "source_id", "source_hash", "revision_id"],
            quality_fields=["quality_status", "review_status"],
            reviewer_fields=["reviewer_id", "reviewed_at", "review_status", "review_notes"],
            forbidden_interpretation="Not production raw document ingestion, not crawler output, not replay-ready evidence by itself.",
            current_allowed_status="REPORT_ONLY_CONTRACT_ALLOWED",
            future_gate_required="Reviewed raw document store gate before real evidence assembly.",
        ),
        _contract(
            file_name="factor_definition_reviewed.csv",
            contract_role="Reviewed factor definition and observation-rule contract.",
            required_minimum_fields=[
                "factor_id",
                "factor_name",
                "factor_layer",
                "factor_family",
                "observation_rule",
                "availability_rule",
                "as_of_date",
                "available_time",
                "source_id",
                "source_hash",
                "revision_id",
                "quality_status",
                "reviewer_id",
                "reviewed_at",
                "review_status",
            ],
            pit_fields=["as_of_date", "available_time", "availability_rule"],
            source_lineage_fields=["factor_id", "source_id", "source_hash", "revision_id"],
            quality_fields=["quality_status", "review_status"],
            reviewer_fields=["reviewer_id", "reviewed_at", "review_status", "review_notes"],
            forbidden_interpretation="Not active factor library, not signal_score implementation, not model input authorization.",
            current_allowed_status="REPORT_ONLY_CONTRACT_ALLOWED",
            future_gate_required="Reviewed factor-definition gate before real factor observations.",
        ),
        _contract(
            file_name="company_exposure_reviewed.csv",
            contract_role="Reviewed company exposure mapping contract.",
            required_minimum_fields=[
                "exposure_id",
                "symbol",
                "entity_id",
                "entity_name",
                "exposure_type",
                "period_end",
                "publish_time",
                "available_time",
                "source_id",
                "source_hash",
                "revision_id",
                "quality_status",
                "reviewer_id",
                "reviewed_at",
                "review_status",
            ],
            pit_fields=["period_end", "publish_time", "available_time"],
            source_lineage_fields=["source_id", "source_hash", "revision_id"],
            quality_fields=["quality_status", "review_status"],
            reviewer_fields=["reviewer_id", "reviewed_at", "review_status", "review_notes"],
            forbidden_interpretation="Not production company exposure mapping, not active knowledge graph, not ETF holdings ingestion.",
            current_allowed_status="REPORT_ONLY_CONTRACT_ALLOWED",
            future_gate_required="Reviewed company-exposure gate before real evidence bundles.",
        ),
        _contract(
            file_name="event_structured_reviewed.csv",
            contract_role="Reviewed structured event contract.",
            required_minimum_fields=[
                "event_id",
                "symbol",
                "event_type",
                "event_date",
                "event_time",
                "publish_time",
                "available_time",
                "source_id",
                "document_id",
                "source_hash",
                "revision_id",
                "quality_status",
                "reviewer_id",
                "reviewed_at",
                "review_status",
            ],
            pit_fields=["event_date", "event_time", "publish_time", "available_time"],
            source_lineage_fields=["source_id", "document_id", "source_hash", "revision_id"],
            quality_fields=["quality_status", "review_status"],
            reviewer_fields=["reviewer_id", "reviewed_at", "review_status", "review_notes"],
            forbidden_interpretation="Not production event ingestion, not active event library, not LLM extraction runtime.",
            current_allowed_status="REPORT_ONLY_CONTRACT_ALLOWED",
            future_gate_required="Reviewed event-structured gate before factor observations or evidence bundles.",
        ),
        _contract(
            file_name="factor_observation_reviewed.csv",
            contract_role="Reviewed PIT factor observation contract.",
            required_minimum_fields=[
                "observation_id",
                "symbol",
                "factor_id",
                "observation_value",
                "observation_date",
                "period_end",
                "publish_time",
                "available_time",
                "source_id",
                "document_id",
                "source_hash",
                "revision_id",
                "quality_status",
                "reviewer_id",
                "reviewed_at",
                "review_status",
            ],
            pit_fields=["observation_date", "period_end", "publish_time", "available_time"],
            source_lineage_fields=["factor_id", "source_id", "document_id", "source_hash", "revision_id"],
            quality_fields=["quality_status", "review_status"],
            reviewer_fields=["reviewer_id", "reviewed_at", "review_status", "review_notes"],
            forbidden_interpretation="Not live factor observation runtime, not normalized runtime, not signal_score input authorization.",
            current_allowed_status="REPORT_ONLY_CONTRACT_ALLOWED",
            future_gate_required="Reviewed factor-observation gate before signal or model-adjacent use.",
        ),
        _contract(
            file_name="replay_evidence_bundle_reviewed.csv",
            contract_role="Reviewed evidence bundle membership contract.",
            required_minimum_fields=[
                "bundle_id",
                "symbol",
                "replay_decision_time",
                "evidence_item_id",
                "evidence_item_type",
                "source_id",
                "available_time",
                "source_hash",
                "revision_id",
                "quality_status",
                "reviewer_id",
                "reviewed_at",
                "review_status",
            ],
            pit_fields=["replay_decision_time", "available_time"],
            source_lineage_fields=["bundle_id", "source_id", "source_hash", "revision_id"],
            quality_fields=["quality_status", "review_status"],
            reviewer_fields=["reviewer_id", "reviewed_at", "review_status", "review_notes"],
            forbidden_interpretation="Not real replay evidence bundle construction.",
            current_allowed_status="REPORT_ONLY_CONTRACT_ALLOWED",
            future_gate_required="Explicit replay evidence bundle construction approval.",
        ),
        _contract(
            file_name="replay_decision_reviewed.csv",
            contract_role="Reviewed replay decision contract before future freeze workflows.",
            required_minimum_fields=[
                "replay_decision_id",
                "symbol",
                "replay_as_of_date",
                "replay_decision_time",
                "bundle_id",
                "decision_status",
                "frozen_decision_flag",
                "available_time_cutoff_passed",
                "source_hash",
                "revision_id",
                "quality_status",
                "reviewer_id",
                "reviewed_at",
                "review_status",
            ],
            pit_fields=["replay_as_of_date", "replay_decision_time", "available_time_cutoff_passed"],
            source_lineage_fields=["bundle_id", "source_hash", "revision_id"],
            quality_fields=["decision_status", "quality_status", "review_status"],
            reviewer_fields=["reviewer_id", "reviewed_at", "review_status", "review_notes"],
            forbidden_interpretation="Not real replay decision creation, not decision freeze, not trade recommendation.",
            current_allowed_status="REPORT_ONLY_CONTRACT_ALLOWED",
            future_gate_required="Explicit replay decision creation and later freeze approval.",
        ),
        _contract(
            file_name="forward_return_label_reviewed.csv",
            contract_role="Future-only post-freeze label contract.",
            required_minimum_fields=[
                "forward_label_id",
                "replay_decision_id",
                "symbol",
                "replay_decision_time",
                "label_window_start",
                "label_window_end",
                "entry_price",
                "exit_price",
                "forward_return",
                "source_hash",
                "revision_id",
                "quality_status",
                "reviewer_id",
                "reviewed_at",
                "review_status",
            ],
            pit_fields=["replay_decision_time", "label_window_start", "label_window_end"],
            source_lineage_fields=["replay_decision_id", "source_hash", "revision_id"],
            quality_fields=["quality_status", "review_status"],
            reviewer_fields=["reviewer_id", "reviewed_at", "review_status", "review_notes"],
            forbidden_interpretation="Future-only; blocked as decision-time input; not training, stock_profile, paper, buy-review, performance, or trading authorization.",
            current_allowed_status="FUTURE_ONLY_BLOCKED_AS_DECISION_TIME_INPUT",
            future_gate_required="Frozen replay decision plus explicit forward-label derivation approval.",
        ),
        _contract(
            file_name="market_data_reviewed.csv",
            contract_role="Reviewed historical market data contract.",
            required_minimum_fields=[
                "market_data_id",
                "symbol",
                "trade_date",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "available_time",
                "source_id",
                "source_hash",
                "revision_id",
                "quality_status",
                "reviewer_id",
                "reviewed_at",
                "review_status",
            ],
            pit_fields=["trade_date", "available_time"],
            source_lineage_fields=["source_id", "source_hash", "revision_id"],
            quality_fields=["quality_status", "review_status"],
            reviewer_fields=["reviewer_id", "reviewed_at", "review_status", "review_notes"],
            forbidden_interpretation="Not market-cache mutation, not current-candidates input, not trading signal.",
            current_allowed_status="REPORT_ONLY_CONTRACT_ALLOWED",
            future_gate_required="Reviewed local market data gate before real replay or label use.",
        ),
        _contract(
            file_name="benchmark_data_reviewed.csv",
            contract_role="Optional benchmark context contract.",
            required_minimum_fields=[
                "benchmark_id",
                "benchmark_name",
                "trade_date",
                "close",
                "return",
                "available_time",
                "source_id",
                "source_hash",
                "revision_id",
                "quality_status",
                "reviewer_id",
                "reviewed_at",
                "review_status",
            ],
            pit_fields=["trade_date", "available_time"],
            source_lineage_fields=["benchmark_id", "source_id", "source_hash", "revision_id"],
            quality_fields=["quality_status", "review_status"],
            reviewer_fields=["reviewer_id", "reviewed_at", "review_status", "review_notes"],
            forbidden_interpretation="Optional future context only; not benchmark outperformance proof or performance validation.",
            current_allowed_status="OPTIONAL_REPORT_ONLY_CONTEXT",
            future_gate_required="Reviewed benchmark context gate before relative-label or metric use.",
        ),
        _contract(
            file_name="trading_calendar_reviewed.csv",
            contract_role="Reviewed trading calendar contract.",
            required_minimum_fields=[
                "calendar_id",
                "market",
                "trade_date",
                "is_trading_day",
                "previous_trading_day",
                "next_trading_day",
                "available_time",
                "source_id",
                "source_hash",
                "revision_id",
                "quality_status",
                "reviewer_id",
                "reviewed_at",
                "review_status",
            ],
            pit_fields=["trade_date", "available_time"],
            source_lineage_fields=["calendar_id", "source_id", "source_hash", "revision_id"],
            quality_fields=["quality_status", "review_status"],
            reviewer_fields=["reviewer_id", "reviewed_at", "review_status", "review_notes"],
            forbidden_interpretation="Not market data, not replay decision, not label authorization.",
            current_allowed_status="REPORT_ONLY_CONTRACT_ALLOWED",
            future_gate_required="Reviewed trading-calendar gate before replay date or label-window use.",
        ),
    ]
    return pd.DataFrame(rows)


def build_reviewed_local_csv_field_contract(contract_matrix: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for contract in contract_matrix.to_dict("records"):
        for field_name in _split(contract["required_minimum_fields"]):
            rows.append(
                {
                    "file_name": contract["file_name"],
                    "field_name": field_name,
                    "required_for_contract_fixture": "True",
                    "pit_role": "PIT_FIELD" if field_name in _split(contract["pit_fields"]) else "NON_PIT_FIELD",
                    "source_lineage_role": (
                        "SOURCE_LINEAGE_FIELD"
                        if field_name in _split(contract["source_lineage_fields"])
                        else "NON_SOURCE_LINEAGE_FIELD"
                    ),
                    "quality_role": "QUALITY_FIELD" if field_name in _split(contract["quality_fields"]) else "NON_QUALITY_FIELD",
                    "reviewer_role": (
                        "REVIEWER_FIELD" if field_name in _split(contract["reviewer_fields"]) else "NON_REVIEWER_FIELD"
                    ),
                    "data_type_hint": _data_type_hint(field_name),
                    "notes": f"{field_name} is required for {contract['file_name']} contract governance.",
                }
            )
    return pd.DataFrame(rows)


def build_reviewed_local_csv_pit_rule_matrix() -> pd.DataFrame:
    rules = [
        (
            "available_time_cutoff",
            "available_time <= replay_decision_time for all decision-time inputs",
            "BLOCK_IF_AVAILABLE_AFTER_DECISION_TIME",
        ),
        ("event_date_not_available_time", "event_date is not automatically available_time", "REQUIRE_EXPLICIT_AVAILABLE_TIME"),
        ("period_end_not_available_time", "period_end is not automatically available_time", "REQUIRE_EXPLICIT_AVAILABLE_TIME"),
        ("publish_time_not_available_time", "publish_time is not automatically available_time", "REQUIRE_EXPLICIT_AVAILABLE_TIME"),
        ("fetched_at_not_available_time", "fetched_at is not automatically available_time", "REQUIRE_EXPLICIT_AVAILABLE_TIME"),
        ("reviewed_at_audit_only", "reviewed_at is audit metadata, not historical availability", "REQUIRE_EXPLICIT_AVAILABLE_TIME"),
        ("future_prices_excluded", "future prices are excluded from decision inputs", "BLOCK_FUTURE_PRICE_AS_DECISION_INPUT"),
        ("future_labels_excluded", "future labels are excluded from decision inputs", "BLOCK_FUTURE_LABEL_AS_DECISION_INPUT"),
        ("source_hash_required", "source_hash is required", "BLOCK_IF_SOURCE_HASH_MISSING"),
        ("revision_id_required", "revision_id is required", "BLOCK_IF_REVISION_ID_MISSING"),
        ("permission_gate_required", "permission gate is required", "BLOCK_IF_PERMISSION_GATE_MISSING"),
        ("quality_gate_required", "quality gate is required", "BLOCK_IF_QUALITY_GATE_MISSING"),
        (
            "reviewer_approval_no_pit_override",
            "reviewer approval does not override PIT failure",
            "BLOCK_IF_PIT_FAILS_EVEN_WHEN_REVIEWED",
        ),
    ]
    return pd.DataFrame(
        [
            {
                "rule_id": rule_id,
                "rule_text": rule_text,
                "required_for_future_pit_admissibility": True,
                "failure_status": failure_status,
                "report_only_fixture_status": "DOCUMENTED_ONLY",
            }
            for rule_id, rule_text, failure_status in rules
        ]
    )


def build_reviewed_local_csv_lineage_rule_matrix() -> pd.DataFrame:
    rules = [
        ("source_id", "Every source-backed contract row must carry source_id where applicable."),
        ("source_hash", "Every source-backed contract row must carry source_hash."),
        ("revision_id", "Every reviewed contract row must carry revision_id."),
        ("document_id", "Document-derived rows should preserve document_id when applicable."),
        ("factor_id", "Factor observations should preserve factor_id lineage."),
        ("bundle_id", "Replay decision rows should preserve bundle_id lineage."),
        ("replay_decision_id", "Forward label rows must preserve replay_decision_id and remain post-freeze only."),
    ]
    return pd.DataFrame(
        [
            {
                "lineage_rule": rule,
                "required": True,
                "notes": notes,
                "forbidden_interpretation": "Lineage metadata is not production permission or replay execution.",
            }
            for rule, notes in rules
        ]
    )


def build_reviewed_local_csv_quality_review_rule_matrix() -> pd.DataFrame:
    rules = [
        ("quality_status", "Quality status is required before future admissibility review."),
        ("reviewer_id", "Reviewer identity is required for audit traceability."),
        ("reviewed_at", "Reviewed timestamp is audit metadata only, not historical availability."),
        ("review_status", "Review status is required and must not override PIT failures."),
        ("review_notes", "Review notes should describe judgment and remaining caveats."),
    ]
    return pd.DataFrame(
        [
            {
                "quality_review_rule": rule,
                "required": True,
                "notes": notes,
                "forbidden_interpretation": "Reviewer metadata is not automatic approval for replay, labels, training, buy-review, or trading.",
            }
            for rule, notes in rules
        ]
    )


def build_reviewed_local_csv_forbidden_interpretation_matrix(contract_matrix: pd.DataFrame) -> pd.DataFrame:
    return contract_matrix[
        [
            "file_name",
            "contract_role",
            "forbidden_interpretation",
            "current_allowed_status",
            "future_gate_required",
        ]
    ].copy()


def validate_reviewed_local_csv_contract_fixture(
    *,
    contract_matrix: pd.DataFrame,
    field_contract: pd.DataFrame,
    pit_rule_matrix: pd.DataFrame,
    lineage_rule_matrix: pd.DataFrame,
    quality_review_rule_matrix: pd.DataFrame,
    forbidden_interpretation_matrix: pd.DataFrame,
    settings: ReviewedLocalCsvReplayPrototypeInputContractFixtureSettings,
) -> int:
    checks = [
        len(contract_matrix) == 12,
        set(contract_matrix["file_name"]) == set(CONTRACT_FILE_NAMES),
        "source_hash" in set(field_contract["field_name"]),
        "revision_id" in set(field_contract["field_name"]),
        "available_time" in set(field_contract["field_name"]),
        "reviewer_id" in set(field_contract["field_name"]),
        "reviewed_at" in set(field_contract["field_name"]),
        "review_status" in set(field_contract["field_name"]),
        set(pit_rule_matrix["rule_id"]) >= {
            "available_time_cutoff",
            "future_prices_excluded",
            "future_labels_excluded",
            "source_hash_required",
            "revision_id_required",
            "permission_gate_required",
            "quality_gate_required",
            "reviewer_approval_no_pit_override",
        },
        not lineage_rule_matrix.empty,
        not quality_review_rule_matrix.empty,
        len(forbidden_interpretation_matrix) == 12,
        _contract_value(contract_matrix, "forward_return_label_reviewed.csv", "current_allowed_status")
        == "FUTURE_ONLY_BLOCKED_AS_DECISION_TIME_INPUT",
        _contract_value(contract_matrix, "benchmark_data_reviewed.csv", "current_allowed_status")
        == "OPTIONAL_REPORT_ONLY_CONTEXT",
        "market-cache mutation" in _contract_value(contract_matrix, "market_data_reviewed.csv", "forbidden_interpretation"),
        not _path_targets_forbidden_storage(settings.output_dir),
        settings.report_only is True,
        settings.diagnostic_only is True,
        _no_private_credential_like_values(contract_matrix, field_contract, pit_rule_matrix),
    ]
    return len([passed for passed in checks if not passed])


def write_reviewed_local_csv_replay_prototype_input_contract_fixture_artifacts(
    *,
    result: ReviewedLocalCsvReplayPrototypeInputContractFixtureResult,
    settings: ReviewedLocalCsvReplayPrototypeInputContractFixtureSettings,
    contract_matrix: pd.DataFrame,
    field_contract: pd.DataFrame,
    pit_rule_matrix: pd.DataFrame,
    lineage_rule_matrix: pd.DataFrame,
    quality_review_rule_matrix: pd.DataFrame,
    forbidden_interpretation_matrix: pd.DataFrame,
) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    contract_matrix.to_csv(paths["contract_matrix"], index=False)
    field_contract.to_csv(paths["field_contract"], index=False)
    pit_rule_matrix.to_csv(paths["pit_rule_matrix"], index=False)
    lineage_rule_matrix.to_csv(paths["lineage_rule_matrix"], index=False)
    quality_review_rule_matrix.to_csv(paths["quality_review_rule_matrix"], index=False)
    forbidden_interpretation_matrix.to_csv(paths["forbidden_interpretation_matrix"], index=False)
    paths["safety_flags"].write_text(json.dumps(_safety_flags(), indent=2, sort_keys=True), encoding="utf-8")
    paths["report"].write_text(
        render_reviewed_local_csv_replay_prototype_input_contract_fixture_report(result),
        encoding="utf-8",
    )
    paths["recommended_next_task"].write_text(_recommended_next_task(), encoding="utf-8")
    paths["metadata"].write_text(
        json.dumps(_metadata(result, settings), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def render_reviewed_local_csv_replay_prototype_input_contract_fixture_report(
    result: ReviewedLocalCsvReplayPrototypeInputContractFixtureResult,
) -> str:
    return "\n".join(
        [
            "# Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture Report v0.1",
            "",
            "This workflow creates deterministic report-only contract artifacts for a future reviewed LOCAL_CSV replay prototype input package.",
            "",
            "It follows the Real LOCAL_CSV / Reviewed-Input Historical Replay Prototype Planning report and remains contract-only.",
            "",
            "## Current Result",
            "",
            f"- reviewed_local_csv_replay_prototype_input_contract_fixture_id: {result.reviewed_local_csv_replay_prototype_input_contract_fixture_id}",
            f"- status: {result.status}",
            f"- workflow_stage: {result.workflow_stage}",
            f"- contract_count: {result.contract_count}",
            f"- validation_issue_count: {result.validation_issue_count}",
            "",
            "## Contract Groups",
            "",
            "\n".join(f"- `{name}`" for name in CONTRACT_FILE_NAMES),
            "",
            "## PIT Rules",
            "",
            "- `available_time <= replay_decision_time` is required for all decision-time inputs.",
            "- `event_date`, `period_end`, `publish_time`, `fetched_at`, and `reviewed_at` are not automatically `available_time`.",
            "- Future prices and future labels are excluded from decision inputs.",
            "- `source_hash`, `revision_id`, source permission gates, and quality gates are required.",
            "- Reviewer approval is audit metadata and does not override PIT failure.",
            "",
            "## Source Lineage and Quality Rules",
            "",
            "- Source lineage must preserve source ids, hashes, revisions, document ids, factor ids, bundle ids, and decision ids where applicable.",
            "- Quality and reviewer fields are required for future admissibility review but are not replay approval.",
            "",
            "## Future-Only Label Rules",
            "",
            "- `forward_return_label_reviewed.csv` is future-only.",
            "- It must be blocked as a decision-time input.",
            "- Labels require frozen replay decisions and a separate explicit approval workflow.",
            "- Labels do not authorize training, stock_profile validation, paper validation, buy-review, performance validation, or trading.",
            "",
            "## Forbidden Downstream Interpretations",
            "",
            "- No real reviewed input package is created.",
            "- No active reviewed input candidate is created.",
            "- No PIT admissibility validator is implemented.",
            "- No real replay input, evidence bundle, decision, decision freeze, or forward labels are created.",
            "- No future labels are joined to decision inputs.",
            "- No training dataset, metric computation, signal_score, model training, active weights, or active thresholds are created.",
            "- No stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, strategy performance validation, current-candidates, snapshots, signal_semantics mutation, broker/API/order/message behavior, or trading is created.",
            "- No data/raw, data/processed, or data/cache writes are created.",
            "",
            "## Safety Flags",
            "",
            "All safety flags in `reviewed_local_csv_safety_flags.json` remain false.",
            "",
            "## Known Limitations",
            "",
            "- This is not real input creation.",
            "- This is not PIT admissibility validation.",
            "- This is not replay execution.",
            "- This is not forward label derivation.",
            "- Views, health, status, research-status integration, checkpoint docs, and Source updates are intentionally deferred.",
            "",
            "## Recommended Next Task",
            "",
            "Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture Views Report-Only v0.1",
        ]
    )


def resolve_reviewed_local_csv_replay_prototype_input_contract_fixture_paths(
    output_dir: Path,
    fixture_id: str,
) -> dict[str, Path]:
    artifact_dir = output_dir / fixture_id
    paths = {"artifact_dir": artifact_dir}
    paths.update({key: artifact_dir / filename for key, filename in ARTIFACT_FILENAMES.items()})
    return paths


def _contract(
    *,
    file_name: str,
    contract_role: str,
    required_minimum_fields: list[str],
    pit_fields: list[str],
    source_lineage_fields: list[str],
    quality_fields: list[str],
    reviewer_fields: list[str],
    forbidden_interpretation: str,
    current_allowed_status: str,
    future_gate_required: str,
) -> dict[str, str]:
    return {
        "file_name": file_name,
        "contract_role": contract_role,
        "required_minimum_fields": ";".join(required_minimum_fields),
        "pit_fields": ";".join(pit_fields),
        "source_lineage_fields": ";".join(source_lineage_fields),
        "quality_fields": ";".join(quality_fields),
        "reviewer_fields": ";".join(reviewer_fields),
        "forbidden_interpretation": forbidden_interpretation,
        "current_allowed_status": current_allowed_status,
        "future_gate_required": future_gate_required,
    }


def _metadata(
    result: ReviewedLocalCsvReplayPrototypeInputContractFixtureResult,
    settings: ReviewedLocalCsvReplayPrototypeInputContractFixtureSettings,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "reviewed_local_csv_replay_prototype_input_contract_fixture_id": (
            result.reviewed_local_csv_replay_prototype_input_contract_fixture_id
        ),
        "workflow_name": "reviewed_local_csv_replay_prototype_input_contract_fixture",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "config_version": settings.config_version,
        "contract_count": result.contract_count,
        "validation_issue_count": result.validation_issue_count,
        "report_only": True,
        "diagnostic_only": True,
        "schema_fixture": True,
        "artifact_paths": {key: str(path) for key, path in result.artifact_paths.items()},
        "recommended_next_task": "Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture Views Report-Only v0.1",
    }
    metadata.update(_safety_flags())
    return metadata


def _safety_flags() -> dict[str, bool]:
    return {flag: False for flag in SAFETY_FALSE_FLAGS}


def _recommended_next_task() -> str:
    return "\n".join(
        [
            "# Recommended Next Task",
            "",
            "Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture Views Report-Only v0.1",
            "",
            "Add index, health, and status artifact views for this report-only contract fixture. Do not create a real reviewed input package, PIT admissibility validator, replay input, replay evidence bundle, replay decision, replay decision freeze, forward label, training dataset, metric computation, signal_score, model training, active weights, active thresholds, stock_profile validation, paper validation, buy-review, current-candidates, snapshots, signal_semantics mutation, broker/API/order/message behavior, trading, or data/raw, data/processed, or data/cache writes.",
        ]
    )


def _fixture_id(
    *,
    contract_matrix: pd.DataFrame,
    field_contract: pd.DataFrame,
    pit_rule_matrix: pd.DataFrame,
    config_version: str,
) -> str:
    digest = hashlib.sha256(config_version.encode("utf-8"))
    digest.update(contract_matrix.to_csv(index=False).encode("utf-8"))
    digest.update(field_contract.to_csv(index=False).encode("utf-8"))
    digest.update(pit_rule_matrix.to_csv(index=False).encode("utf-8"))
    return digest.hexdigest()[:12]


def _assert_settings_safe(settings: ReviewedLocalCsvReplayPrototypeInputContractFixtureSettings) -> None:
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Reviewed LOCAL_CSV contract fixture must remain report_only and diagnostic_only.")
    if _path_targets_forbidden_storage(settings.output_dir):
        raise ValueError("Reviewed LOCAL_CSV contract fixture output must stay out of protected paths.")


def _path_targets_forbidden_storage(path: Path) -> bool:
    normalized_parts = {part.lower() for part in Path(path).parts}
    path_text = str(path).replace("\\", "/").lower()
    return (
        ("data" in normalized_parts and {"raw", "processed", "cache"} & normalized_parts)
        or "docs/project_sources" in path_text
    )


def _contract_value(frame: pd.DataFrame, file_name: str, column: str) -> str:
    return str(frame.loc[frame["file_name"] == file_name, column].iloc[0])


def _split(value: Any) -> list[str]:
    return [item for item in str(value).split(";") if item]


def _data_type_hint(field_name: str) -> str:
    if field_name.endswith("_time") or field_name in {"available_time", "publish_time", "reviewed_at"}:
        return "timestamp"
    if field_name.endswith("_date") or field_name in {"period_end", "trade_date", "replay_as_of_date"}:
        return "date"
    if field_name in {"open", "high", "low", "close", "volume", "return", "entry_price", "exit_price", "forward_return"}:
        return "decimal"
    if field_name in {"is_trading_day", "available_time_cutoff_passed", "frozen_decision_flag"}:
        return "boolean"
    return "string"


def _no_private_credential_like_values(*frames: pd.DataFrame) -> bool:
    all_text = "\n".join(
        "\n".join(frame.astype(str).to_numpy().ravel().tolist())
        for frame in frames
    )
    return re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", all_text.lower()) is None

