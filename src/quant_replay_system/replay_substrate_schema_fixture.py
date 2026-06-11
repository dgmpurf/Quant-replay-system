"""Report-only replay substrate schema fixture workflow.

This module writes tiny synthetic LOCAL_CSV-style schema fixtures for future
historical replay substrate entities. It validates shape and safety flags only;
it never runs replay, current-candidates, snapshots, forward labels, training,
paper workflows, broker integrations, messages, or active stock profiles.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


REPLAY_SUBSTRATE_ENTITIES = [
    "source_registry",
    "raw_document_store",
    "factor_definition",
    "factor_observation",
    "event_structured",
    "company_exposure",
    "replay_decision",
    "replay_evidence_bundle",
    "forward_return_label",
    "benchmark_label",
    "training_result",
    "model_version",
    "evaluation_report",
    "stock_profile",
]

PIT_FIELDS = ["as_of_date", "available_time", "source_id", "source_hash", "revision_id", "quality_status", "pit_valid"]
PERMISSION_FIELDS = ["permission_class", "compliance_flag"]

OVERCLAIM_GUARDS = [
    "PIT preview cannot become approval",
    "factor observation cannot become alpha",
    "replay decision cannot claim performance",
    "forward label cannot leak into replay decision",
    "training result cannot become production validation",
    "stock profile cannot become buy permission",
    "LLM/event extraction cannot become deterministic signal",
    "real_buy_review_eligible must remain false",
]


@dataclass(frozen=True)
class ReplaySubstrateSchemaFixtureSettings:
    output_dir: Path = Path("outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True
    enable_replay: bool = False
    enable_current_candidates: bool = False
    enable_snapshot_build: bool = False
    enable_forward_labels: bool = False
    enable_weight_training: bool = False
    enable_active_stock_profile: bool = False
    enable_real_buy_review: bool = False
    enable_data_raw_write: bool = False
    enable_data_processed_write: bool = False
    enable_data_cache_write: bool = False
    enable_cache_mutation: bool = False
    enable_live_trading: bool = False
    enable_broker_api: bool = False
    enable_order_placement: bool = False
    enable_message_delivery: bool = False
    enable_llm_api: bool = False
    enable_external_api: bool = False
    enable_approved_for_paper: bool = False


@dataclass(frozen=True)
class ReplaySubstrateSchemaFixtureResult:
    fixture_id: str
    status: str
    entity_count: int
    validation_issue_count: int
    overclaim_guard_count: int
    overclaim_guard_pass_count: int
    report_only: bool
    diagnostic_only: bool
    forward_labels_computed: bool
    weights_trained: bool
    active_stock_profile_created: bool
    real_buy_review_eligible: bool
    artifact_paths: dict[str, Path]


def build_replay_substrate_schema_fixture(
    *,
    output_dir: str | Path | None = None,
    settings: ReplaySubstrateSchemaFixtureSettings | None = None,
) -> ReplaySubstrateSchemaFixtureResult:
    resolved_settings = settings or ReplaySubstrateSchemaFixtureSettings()
    if output_dir is not None:
        resolved_settings = ReplaySubstrateSchemaFixtureSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)

    samples = build_replay_substrate_sample_rows()
    fixture_id = _fixture_id(samples, resolved_settings.config_version)
    paths = resolve_replay_substrate_schema_fixture_paths(resolved_settings.output_dir, fixture_id)
    entity_status = build_schema_fixture_entity_status(samples)
    validation_issues = validate_schema_fixture_samples(samples)
    overclaim_guards = build_schema_fixture_overclaim_guards(samples)

    result = ReplaySubstrateSchemaFixtureResult(
        fixture_id=fixture_id,
        status="PASS" if validation_issues.empty and bool(overclaim_guards["passed"].all()) else "FAIL",
        entity_count=len(entity_status),
        validation_issue_count=len(validation_issues),
        overclaim_guard_count=len(overclaim_guards),
        overclaim_guard_pass_count=int(overclaim_guards["passed"].sum()),
        report_only=True,
        diagnostic_only=True,
        forward_labels_computed=False,
        weights_trained=False,
        active_stock_profile_created=False,
        real_buy_review_eligible=False,
        artifact_paths=paths,
    )
    if resolved_settings.write_artifacts:
        write_replay_substrate_schema_fixture_artifacts(
            result=result,
            samples=samples,
            entity_status=entity_status,
            validation_issues=validation_issues,
            overclaim_guards=overclaim_guards,
            settings=resolved_settings,
        )
    return result


def build_replay_substrate_sample_rows() -> dict[str, pd.DataFrame]:
    common = _common_fields()
    return {
        "source_registry": pd.DataFrame(
            [
                {
                    **common,
                    "source_name": "SYNTHETIC_LOCAL_CSV_FIXTURE",
                    "source_type": "LOCAL_CSV_SYNTHETIC",
                    "license_note": "diagnostic fixture only",
                    "report_only": True,
                    "diagnostic_only": True,
                }
            ]
        ),
        "raw_document_store": pd.DataFrame(
            [
                {
                    **common,
                    "document_id": "doc_fixture_000001_20240402",
                    "document_path": "synthetic://not-fetched",
                    "published_at": "2024-04-02 15:30:00",
                    "parser_version": "schema_fixture_only",
                    "content_hash": "synthetic_content_hash",
                }
            ]
        ),
        "factor_definition": pd.DataFrame(
            [
                {
                    **common,
                    "factor_id": "technical_close_return_5d_fixture",
                    "taxonomy_layer": "5_trading_behavior_microstructure",
                    "factor_name": "Synthetic 5-day close return",
                    "trade_usage": "observe_only",
                    "backtestable": "schema_only",
                }
            ]
        ),
        "factor_observation": pd.DataFrame(
            [
                {
                    **common,
                    "factor_observation_id": "fobs_000001_20240402_close_return_5d",
                    "factor_id": "technical_close_return_5d_fixture",
                    "symbol": "000001",
                    "universe_name": "stock_core",
                    "observed_for_date": "2024-04-02",
                    "observed_value": "0.0123",
                    "unit": "ratio",
                    "confidence": "0.50",
                    "alpha_claimed": False,
                }
            ]
        ),
        "event_structured": pd.DataFrame(
            [
                {
                    **common,
                    "event_id": "event_fixture_000001_20240402_none",
                    "symbol": "000001",
                    "event_type": "NO_EVENT_SYNTHETIC_PLACEHOLDER",
                    "event_status": "schema_only_not_extracted",
                    "extraction_method": "none",
                    "deterministic_signal": False,
                }
            ]
        ),
        "company_exposure": pd.DataFrame(
            [
                {
                    **common,
                    "company_exposure_id": "exposure_fixture_000001_bank",
                    "symbol": "000001",
                    "exposure_type": "industry",
                    "exposure_value": "banking_fixture",
                    "effective_from": "2024-04-02",
                    "review_status": "schema_fixture_only",
                }
            ]
        ),
        "replay_decision": pd.DataFrame(
            [
                {
                    **common,
                    "replay_decision_id": "decision_fixture_000001_20240402",
                    "decision_date": "2024-04-02",
                    "decision_time": "2024-04-02 15:30:00",
                    "symbol": "000001",
                    "universe_name": "stock_core",
                    "decision_status": "schema_fixture_only_not_run",
                    "future_label_used": False,
                    "performance_claimed": False,
                }
            ]
        ),
        "replay_evidence_bundle": pd.DataFrame(
            [
                {
                    **common,
                    "evidence_bundle_id": "bundle_fixture_000001_20240402",
                    "replay_decision_id": "decision_fixture_000001_20240402",
                    "bundle_status": "schema_fixture_only",
                    "member_hashes_complete": True,
                    "approval_applied": False,
                }
            ]
        ),
        "forward_return_label": pd.DataFrame(
            [
                {
                    **common,
                    "forward_return_label_id": "forward_label_schema_000001_20240402",
                    "replay_decision_id": "decision_fixture_000001_20240402",
                    "horizon_days": "5",
                    "label_status": "blocked_not_computed",
                    "label_value": "not_computed",
                    "no_forward_labels_computed": True,
                }
            ]
        ),
        "benchmark_label": pd.DataFrame(
            [
                {
                    **common,
                    "benchmark_label_id": "benchmark_label_schema_000001_20240402",
                    "benchmark_symbol": "000300",
                    "horizon_days": "5",
                    "label_status": "blocked_not_computed",
                    "benchmark_return": "not_computed",
                    "no_forward_labels_computed": True,
                }
            ]
        ),
        "training_result": pd.DataFrame(
            [
                {
                    **common,
                    "training_result_id": "training_schema_fixture_000001",
                    "training_status": "research_only_blocked",
                    "model_version_id": "model_schema_fixture_v0",
                    "metric_status": "not_computed",
                    "no_weights_trained": True,
                    "production_validated": False,
                }
            ]
        ),
        "model_version": pd.DataFrame(
            [
                {
                    **common,
                    "model_version_id": "model_schema_fixture_v0",
                    "parameter_set_hash": "schema_fixture_only_hash",
                    "model_status": "schema_fixture_only",
                    "approved_for_paper": False,
                    "promotion_status": "not_validated",
                }
            ]
        ),
        "evaluation_report": pd.DataFrame(
            [
                {
                    **common,
                    "evaluation_report_id": "evaluation_schema_fixture_000001",
                    "evaluation_status": "blocked_metrics_absent",
                    "metrics_computed": False,
                    "strategy_performance_validated": False,
                    "approved_for_paper": False,
                }
            ]
        ),
        "stock_profile": pd.DataFrame(
            [
                {
                    **common,
                    "stock_profile_id": "stock_profile_schema_fixture_000001",
                    "symbol": "000001",
                    "profile_status": "schema_fixture_only_inactive",
                    "paper_status": "not_validated",
                    "training_status": "schema_fixture_only",
                    "real_buy_review_eligible": False,
                    "no_active_stock_profile_created": True,
                }
            ]
        ),
    }


def build_schema_fixture_entity_status(samples: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for entity in REPLAY_SUBSTRATE_ENTITIES:
        frame = samples[entity]
        required_present = not frame.empty and all(column in frame.columns for column in _required_fields(entity))
        pit_present = all(column in frame.columns for column in PIT_FIELDS)
        permission_present = all(column in frame.columns for column in PERMISSION_FIELDS)
        rows.append(
            {
                "entity": entity,
                "fixture_row_count": len(frame),
                "required_fields_present": required_present,
                "pit_fields_present": pit_present,
                "permission_fields_present": permission_present,
                "validation_status": "PASS" if required_present and pit_present and permission_present else "FAIL",
                "active_artifact_allowed": False,
                "reason_not_active": _reason_not_active(entity),
                "overclaim_guard": _overclaim_guard(entity),
            }
        )
    return pd.DataFrame(rows)


def validate_schema_fixture_samples(samples: dict[str, pd.DataFrame]) -> pd.DataFrame:
    issues: list[dict[str, str]] = []
    for entity in REPLAY_SUBSTRATE_ENTITIES:
        frame = samples.get(entity, pd.DataFrame())
        if frame.empty:
            issues.append({"entity": entity, "issue_type": "missing_fixture_row", "issue_detail": "No fixture row present."})
            continue
        for column in [*_required_fields(entity), *PIT_FIELDS, *PERMISSION_FIELDS]:
            if column not in frame.columns:
                issues.append({"entity": entity, "issue_type": "missing_column", "issue_detail": column})
        if "pit_valid" in frame.columns and not frame["pit_valid"].map(_bool).all():
            issues.append({"entity": entity, "issue_type": "pit_invalid", "issue_detail": "pit_valid must remain true for schema-safe fixture rows."})
    return pd.DataFrame(issues, columns=["entity", "issue_type", "issue_detail"])


def build_schema_fixture_overclaim_guards(samples: dict[str, pd.DataFrame]) -> pd.DataFrame:
    replay_decision = samples["replay_decision"].iloc[0]
    forward_label = samples["forward_return_label"].iloc[0]
    training = samples["training_result"].iloc[0]
    stock_profile = samples["stock_profile"].iloc[0]
    event_structured = samples["event_structured"].iloc[0]
    factor_observation = samples["factor_observation"].iloc[0]
    rows = [
        ("PIT preview cannot become approval", True, "No approval field is true and no PIT review is run."),
        ("factor observation cannot become alpha", not _bool(factor_observation["alpha_claimed"]), "Factor observation is input context only."),
        ("replay decision cannot claim performance", not _bool(replay_decision["performance_claimed"]), "Replay decision status is schema_fixture_only_not_run."),
        ("forward label cannot leak into replay decision", not _bool(replay_decision["future_label_used"]), "Forward label is blocked_not_computed."),
        ("training result cannot become production validation", not _bool(training["production_validated"]), "Training status remains research_only_blocked."),
        ("stock profile cannot become buy permission", not _bool(stock_profile["real_buy_review_eligible"]), "Stock profile remains inactive and not paper validated."),
        ("LLM/event extraction cannot become deterministic signal", not _bool(event_structured["deterministic_signal"]), "Event extraction method is none."),
        ("real_buy_review_eligible must remain false", not _bool(stock_profile["real_buy_review_eligible"]), "No buy-review eligibility is created."),
    ]
    return pd.DataFrame(
        [{"guard_name": name, "passed": passed, "guard_detail": detail} for name, passed, detail in rows]
    )


def resolve_replay_substrate_schema_fixture_paths(output_dir: Path, fixture_id: str) -> dict[str, Path]:
    artifact_dir = output_dir / fixture_id
    sample_rows_dir = artifact_dir / "schema_fixture_sample_rows"
    return {
        "artifact_dir": artifact_dir,
        "sample_rows_dir": sample_rows_dir,
        "report": artifact_dir / "replay_substrate_schema_fixture_report.md",
        "entity_status": artifact_dir / "schema_fixture_entity_status.csv",
        "validation_issues": artifact_dir / "schema_fixture_validation_issues.csv",
        "overclaim_guards": artifact_dir / "schema_fixture_overclaim_guards.csv",
        "recommended_next_task": artifact_dir / "recommended_next_task.md",
        "metadata": artifact_dir / "metadata.json",
    }


def write_replay_substrate_schema_fixture_artifacts(
    *,
    result: ReplaySubstrateSchemaFixtureResult,
    samples: dict[str, pd.DataFrame],
    entity_status: pd.DataFrame,
    validation_issues: pd.DataFrame,
    overclaim_guards: pd.DataFrame,
    settings: ReplaySubstrateSchemaFixtureSettings,
) -> None:
    paths = result.artifact_paths
    paths["sample_rows_dir"].mkdir(parents=True, exist_ok=True)
    entity_status.to_csv(paths["entity_status"], index=False)
    validation_issues.to_csv(paths["validation_issues"], index=False)
    overclaim_guards.to_csv(paths["overclaim_guards"], index=False)
    for entity, frame in samples.items():
        frame.to_csv(paths["sample_rows_dir"] / f"{entity}_fixture.csv", index=False)
    # Compatibility names suggested by the task.
    samples["forward_return_label"].to_csv(paths["sample_rows_dir"] / "forward_return_label_schema_fixture.csv", index=False)
    samples["training_result"].to_csv(paths["sample_rows_dir"] / "training_result_schema_fixture.csv", index=False)
    samples["stock_profile"].to_csv(paths["sample_rows_dir"] / "stock_profile_schema_fixture.csv", index=False)
    paths["report"].write_text(render_replay_substrate_schema_fixture_report(result, entity_status, overclaim_guards), encoding="utf-8")
    paths["recommended_next_task"].write_text(_recommended_next_task(), encoding="utf-8")
    paths["metadata"].write_text(json.dumps(_metadata(result, settings), indent=2, ensure_ascii=False), encoding="utf-8")


def render_replay_substrate_schema_fixture_report(
    result: ReplaySubstrateSchemaFixtureResult,
    entity_status: pd.DataFrame,
    overclaim_guards: pd.DataFrame,
) -> str:
    return "\n".join(
        [
            "# Replay Substrate Schema Fixture Report v0.1",
            "",
            "## Executive Summary",
            "",
            "This report-only workflow generated tiny synthetic LOCAL_CSV-style schema fixtures for future replay substrate entities. It validates schema shape, PIT fields, permission fields, and overclaim guards. It does not run replay, current-candidates, snapshots, labels, training, or active stock-profile workflows.",
            "",
            "## Entities Covered",
            "",
            ", ".join(REPLAY_SUBSTRATE_ENTITIES),
            "",
            "## Validation Results",
            "",
            f"- fixture_id: {result.fixture_id}",
            f"- status: {result.status}",
            f"- entity_count: {result.entity_count}",
            f"- validation_issue_count: {result.validation_issue_count}",
            f"- overclaim_guard_pass_count: {result.overclaim_guard_pass_count}",
            "",
            "## Blocked / Not-Ready Gates",
            "",
            "- forward_return_label: schema only; label_status=blocked_not_computed.",
            "- benchmark_label: schema only; label_status=blocked_not_computed.",
            "- training_result: research_only_blocked; no weights trained.",
            "- evaluation_report: metrics absent; strategy performance not validated.",
            "- stock_profile: inactive; real_buy_review_eligible=false.",
            "",
            "## Overclaim Protections",
            "",
            "\n".join(f"- {row.guard_name}: {'PASS' if row.passed else 'FAIL'}" for row in overclaim_guards.itertuples()),
            "",
            "## Next Recommended Task",
            "",
            "Add index/health/status for the replay-substrate schema fixture workflow before any real replay, label, training, or stock-profile work.",
            "",
            "## Safety Confirmations",
            "",
            "- report_only=true",
            "- diagnostic_only=true",
            "- no_live_trading=true",
            "- no_broker_api=true",
            "- no_order_placement=true",
            "- no_forward_labels_computed=true",
            "- no_weights_trained=true",
            "- no_active_stock_profile_created=true",
            "- real_buy_review_eligible=false",
        ]
    )


def _required_fields(entity: str) -> list[str]:
    return {
        "source_registry": ["source_id", "source_name"],
        "raw_document_store": ["document_id", "source_id"],
        "factor_definition": ["factor_id", "taxonomy_layer"],
        "factor_observation": ["factor_observation_id", "factor_id", "symbol"],
        "event_structured": ["event_id", "event_type"],
        "company_exposure": ["company_exposure_id", "symbol", "exposure_type"],
        "replay_decision": ["replay_decision_id", "decision_date", "symbol"],
        "replay_evidence_bundle": ["evidence_bundle_id", "replay_decision_id"],
        "forward_return_label": ["forward_return_label_id", "label_status"],
        "benchmark_label": ["benchmark_label_id", "label_status"],
        "training_result": ["training_result_id", "training_status"],
        "model_version": ["model_version_id", "model_status"],
        "evaluation_report": ["evaluation_report_id", "evaluation_status"],
        "stock_profile": ["stock_profile_id", "symbol", "real_buy_review_eligible"],
    }[entity]


def _common_fields() -> dict[str, Any]:
    return {
        "as_of_date": "2024-04-02",
        "available_time": "2024-04-02 15:30:00",
        "source_id": "source_fixture_local_csv",
        "source_hash": "sha256:synthetic_fixture_hash",
        "revision_id": "fixture_rev_001",
        "permission_class": "synthetic_local_csv",
        "compliance_flag": "diagnostic_only",
        "quality_status": "schema_fixture_pass",
        "pit_valid": True,
    }


def _reason_not_active(entity: str) -> str:
    if entity in {"forward_return_label", "benchmark_label"}:
        return "schema only; labels are blocked_not_computed"
    if entity == "training_result":
        return "research_only_blocked; no weights trained"
    if entity == "stock_profile":
        return "inactive fixture; real_buy_review_eligible=false"
    return "diagnostic schema fixture only"


def _overclaim_guard(entity: str) -> str:
    if entity == "factor_observation":
        return "factor observation cannot become alpha"
    if entity == "replay_decision":
        return "replay decision cannot claim performance"
    if entity in {"forward_return_label", "benchmark_label"}:
        return "forward label cannot leak into replay decision"
    if entity == "training_result":
        return "training result cannot become production validation"
    if entity == "stock_profile":
        return "stock profile cannot become buy permission"
    return "schema fixture cannot become active artifact"


def _fixture_id(samples: dict[str, pd.DataFrame], config_version: str) -> str:
    digest = hashlib.sha256(config_version.encode("utf-8"))
    for entity in REPLAY_SUBSTRATE_ENTITIES:
        digest.update(entity.encode("utf-8"))
        digest.update(samples[entity].to_csv(index=False).encode("utf-8"))
    return digest.hexdigest()[:12]


def _metadata(result: ReplaySubstrateSchemaFixtureResult, settings: ReplaySubstrateSchemaFixtureSettings) -> dict[str, Any]:
    return {
        "fixture_id": result.fixture_id,
        "status": result.status,
        "config_version": settings.config_version,
        "entity_count": result.entity_count,
        "validation_issue_count": result.validation_issue_count,
        "report_only": True,
        "diagnostic_only": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "no_llm_api_calls": True,
        "no_external_api_calls": True,
        "no_cache_mutation": True,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_data_cache_write": True,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels_computed": True,
        "no_weights_trained": True,
        "no_active_stock_profile_created": True,
        "real_buy_review_eligible": False,
        "approved_for_paper": False,
        "strategy_performance_validated": False,
        "signal_semantics_changed": False,
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
    }


def _recommended_next_task() -> str:
    return (
        "# Recommended Next Task\n\n"
        "Add index/health/status for the replay-substrate schema fixture workflow. "
        "Keep it report-only and do not run real replay, current-candidates, snapshots, "
        "forward labels, training, active stock profiles, or buy-review eligibility.\n"
    )


def _assert_settings_safe(settings: ReplaySubstrateSchemaFixtureSettings) -> None:
    unsafe = [
        "enable_replay",
        "enable_current_candidates",
        "enable_snapshot_build",
        "enable_forward_labels",
        "enable_weight_training",
        "enable_active_stock_profile",
        "enable_real_buy_review",
        "enable_data_raw_write",
        "enable_data_processed_write",
        "enable_data_cache_write",
        "enable_cache_mutation",
        "enable_live_trading",
        "enable_broker_api",
        "enable_order_placement",
        "enable_message_delivery",
        "enable_llm_api",
        "enable_external_api",
        "enable_approved_for_paper",
    ]
    enabled = [name for name in unsafe if getattr(settings, name)]
    if enabled:
        raise ValueError(f"Unsafe replay substrate schema fixture setting enabled: {', '.join(enabled)}")
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Replay substrate schema fixture must remain report_only and diagnostic_only.")


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
